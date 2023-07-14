import logging
import re
from typing import Optional, Tuple
from urllib.parse import urlparse

import gitlab

from pr_agent.config_loader import settings

from .git_provider import FilePatchInfo, GitProvider, EDIT_TYPE


class GitLabProvider(GitProvider):
    def __init__(self, merge_request_url: Optional[str] = None):
        gitlab_url = settings.get("GITLAB.URL", None)
        if not gitlab_url:
            raise ValueError("GitLab URL is not set in the config file")
        gitlab_access_token = settings.get("GITLAB.PERSONAL_ACCESS_TOKEN", None)
        if not gitlab_access_token:
            raise ValueError("GitLab personal access token is not set in the config file")
        self.gl = gitlab.Gitlab(
            gitlab_url,
            gitlab_access_token
        )
        self.id_project = None
        self.id_mr = None
        self.mr = None
        self.diff_files = None
        self.temp_comments = []
        self._set_merge_request(merge_request_url)

    @property
    def pr(self):
        '''The GitLab terminology is merge request (MR) instead of pull request (PR)'''
        return self.mr

    def _set_merge_request(self, merge_request_url: str):
        self.id_project, self.id_mr = self._parse_merge_request_url(merge_request_url)
        self.mr = self._get_merge_request()
        self.last_diff = self.mr.diffs.list()[-1]

    def _get_pr_file_content(self, file_path: str, branch: str) -> str:
        return self.gl.projects.get(self.id_project).files.get(file_path, branch).decode()

    def get_diff_files(self) -> list[FilePatchInfo]:
        diffs = self.mr.changes()['changes']
        diff_files = []
        for diff in diffs:
            original_file_content_str = self._get_pr_file_content(diff['old_path'], self.mr.target_branch)
            new_file_content_str = self._get_pr_file_content(diff['new_path'], self.mr.source_branch)
            edit_type = EDIT_TYPE.MODIFIED
            if diff['new_file']:
                edit_type = EDIT_TYPE.ADDED
            elif diff['deleted_file']:
                edit_type = EDIT_TYPE.DELETED
            elif diff['renamed_file']:
                edit_type = EDIT_TYPE.RENAMED
            try:
                original_file_content_str = bytes.decode(original_file_content_str, 'utf-8')
                new_file_content_str = bytes.decode(new_file_content_str, 'utf-8')
            except UnicodeDecodeError:
                logging.warning(
                    f"Cannot decode file {diff['old_path']} or {diff['new_path']} in merge request {self.id_mr}")
            diff_files.append(
                FilePatchInfo(original_file_content_str, new_file_content_str, diff['diff'], diff['new_path'],
                              edit_type=edit_type,
                              old_filename=None if diff['old_path'] == diff['new_path'] else diff['old_path']))
        self.diff_files = diff_files
        return diff_files

    def get_files(self):
        return [change['new_path'] for change in self.mr.changes()['changes']]

    def publish_description(self, pr_title: str, pr_body: str):
        logging.exception("Not implemented yet")
        pass

    def publish_comment(self, mr_comment: str, is_temporary: bool = False):
        comment = self.mr.notes.create({'body': mr_comment})
        if is_temporary:
            self.temp_comments.append(comment)

    def publish_inline_comment(self, body: str, relevant_file: str, relevant_line_in_file: str):
        self.diff_files = self.diff_files if self.diff_files else self.get_diff_files()
        edit_type, found, source_line_no, target_file, target_line_no = self.search_line(relevant_file,
                                                                                         relevant_line_in_file)
        if not found:
            logging.info(f"Could not find position for {relevant_file} {relevant_line_in_file}")
        else:
            if edit_type == 'addition':
                position = target_line_no - 1
            else:
                position = source_line_no - 1
            d = self.last_diff
            pos_obj = {'position_type': 'text',
                        'new_path': target_file.filename,
                        'old_path': target_file.old_filename if target_file.old_filename else target_file.filename,
                        'base_sha': d.base_commit_sha, 'start_sha': d.start_commit_sha, 'head_sha': d.head_commit_sha}
            if edit_type == 'deletion':
                pos_obj['old_line'] = position
            elif edit_type == 'addition':
                pos_obj['new_line'] = position
            else:
                pos_obj['new_line'] = position
                pos_obj['old_line'] = position
            self.mr.discussions.create({'body': body,
                                        'position': pos_obj})

    def search_line(self, relevant_file, relevant_line_in_file):
        RE_HUNK_HEADER = re.compile(
            r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@[ ]?(.*)")
        target_file = None
        source_line_no = 0
        target_line_no = 0
        found = False
        edit_type = self.get_edit_type(relevant_line_in_file)
        for file in self.diff_files:
            if file.filename == relevant_file:
                target_file = file
                patch = file.patch
                patch_lines = patch.splitlines()
                for i, line in enumerate(patch_lines):
                    if line.startswith('@@'):
                        match = RE_HUNK_HEADER.match(line)
                        if not match:
                            continue
                        start_old, size_old, start_new, size_new, _ = match.groups()
                        source_line_no = int(start_old)
                        target_line_no = int(start_new)
                        continue
                    if line.startswith('-'):
                        source_line_no += 1
                    elif line.startswith('+'):
                        target_line_no += 1
                    elif line.startswith(' '):
                        source_line_no += 1
                        target_line_no += 1
                    if relevant_line_in_file in line:
                        found = True
                        edit_type = self.get_edit_type(line)
                        break
                    elif relevant_line_in_file[0] == '+' and relevant_line_in_file[1:] in line:
                        # The model often adds a '+' to the beginning of the relevant_line_in_file even if originally
                        # it's a context line
                        found = True
                        edit_type = self.get_edit_type(line)
                        break
        return edit_type, found, source_line_no, target_file, target_line_no

    def get_edit_type(self, relevant_line_in_file):
        edit_type = 'context'
        if relevant_line_in_file[0] == '-':
            edit_type = 'deletion'
        elif relevant_line_in_file[0] == '+':
            edit_type = 'addition'
        return edit_type

    def remove_initial_comment(self):
        try:
            for comment in self.temp_comments:
                comment.delete()
        except Exception as e:
            logging.exception(f"Failed to remove temp comments, error: {e}")

    def get_title(self):
        return self.mr.title

    def get_description(self):
        return self.mr.description

    def get_languages(self):
        languages = self.gl.projects.get(self.id_project).languages()
        return languages

    def get_pr_branch(self):
        return self.mr.source_branch

    def get_pr_description(self):
        return self.mr.description

    def _parse_merge_request_url(self, merge_request_url: str) -> Tuple[int, int]:
        parsed_url = urlparse(merge_request_url)

        path_parts = parsed_url.path.strip('/').split('/')
        if path_parts[-2] != 'merge_requests':
            raise ValueError("The provided URL does not appear to be a GitLab merge request URL")

        try:
            mr_id = int(path_parts[-1])
        except ValueError as e:
            raise ValueError("Unable to convert merge request ID to integer") from e

        # Gitlab supports access by both project numeric ID as well as 'namespace/project_name'
        return "/".join(path_parts[:2]), mr_id

    def _get_merge_request(self):
        mr = self.gl.projects.get(self.id_project).mergerequests.get(self.id_mr)
        return mr

    def get_user_id(self):
        return None
