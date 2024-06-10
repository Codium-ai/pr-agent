import hashlib
import re
from typing import Optional, Tuple
from urllib.parse import urlparse

import gitlab
from gitlab import GitlabGetError

from ..algo.language_handler import is_valid_file
from ..algo.utils import load_large_diff, clip_tokens, find_line_number_of_relevant_line_in_file
from ..config_loader import get_settings
from .git_provider import GitProvider
from pr_agent.algo.types import EDIT_TYPE, FilePatchInfo
from ..log import get_logger


class DiffNotFoundError(Exception):
    """Raised when the diff for a merge request cannot be found."""
    pass

class GitLabProvider(GitProvider):

    def __init__(self, merge_request_url: Optional[str] = None, incremental: Optional[bool] = False):
        gitlab_url = get_settings().get("GITLAB.URL", None)
        if not gitlab_url:
            raise ValueError("GitLab URL is not set in the config file")
        gitlab_access_token = get_settings().get("GITLAB.PERSONAL_ACCESS_TOKEN", None)
        if not gitlab_access_token:
            raise ValueError("GitLab personal access token is not set in the config file")
        self.gl = gitlab.Gitlab(
            url=gitlab_url,
            oauth_token=gitlab_access_token
        )
        self.id_project = None
        self.id_mr = None
        self.mr = None
        self.diff_files = None
        self.git_files = None
        self.temp_comments = []
        self.pr_url = merge_request_url
        self._set_merge_request(merge_request_url)
        self.RE_HUNK_HEADER = re.compile(
            r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@[ ]?(.*)")
        self.incremental = incremental

    def is_supported(self, capability: str) -> bool:
        if capability in ['get_issue_comments', 'create_inline_comment', 'publish_inline_comments']: # gfm_markdown is supported in gitlab !
            return False
        return True

    @property
    def pr(self):
        '''The GitLab terminology is merge request (MR) instead of pull request (PR)'''
        return self.mr

    def _set_merge_request(self, merge_request_url: str):
        self.id_project, self.id_mr = self._parse_merge_request_url(merge_request_url)
        self.mr = self._get_merge_request()
        try:
            self.last_diff = self.mr.diffs.list(get_all=True)[-1]
        except IndexError as e:
            get_logger().error(f"Could not get diff for merge request {self.id_mr}")
            raise DiffNotFoundError(f"Could not get diff for merge request {self.id_mr}") from e


    def get_pr_file_content(self, file_path: str, branch: str) -> str:
        try:
            return self.gl.projects.get(self.id_project).files.get(file_path, branch).decode()
        except GitlabGetError:
            # In case of file creation the method returns GitlabGetError (404 file not found).
            # In this case we return an empty string for the diff.
            return ''

    def get_diff_files(self) -> list[FilePatchInfo]:
        """
        Retrieves the list of files that have been modified, added, deleted, or renamed in a pull request in GitLab,
        along with their content and patch information.

        Returns:
            diff_files (List[FilePatchInfo]): List of FilePatchInfo objects representing the modified, added, deleted,
            or renamed files in the merge request.
        """

        if self.diff_files:
            return self.diff_files

        diffs = self.mr.changes()['changes']
        diff_files = []
        for diff in diffs:
            if is_valid_file(diff['new_path']):
                original_file_content_str = self.get_pr_file_content(diff['old_path'], self.mr.diff_refs['base_sha'])
                new_file_content_str = self.get_pr_file_content(diff['new_path'], self.mr.diff_refs['head_sha'])

                try:
                    if isinstance(original_file_content_str, bytes):
                        original_file_content_str = bytes.decode(original_file_content_str, 'utf-8')
                    if isinstance(new_file_content_str, bytes):
                        new_file_content_str = bytes.decode(new_file_content_str, 'utf-8')
                except UnicodeDecodeError:
                    get_logger().warning(
                        f"Cannot decode file {diff['old_path']} or {diff['new_path']} in merge request {self.id_mr}")

                edit_type = EDIT_TYPE.MODIFIED
                if diff['new_file']:
                    edit_type = EDIT_TYPE.ADDED
                elif diff['deleted_file']:
                    edit_type = EDIT_TYPE.DELETED
                elif diff['renamed_file']:
                    edit_type = EDIT_TYPE.RENAMED

                filename = diff['new_path']
                patch = diff['diff']
                if not patch:
                    patch = load_large_diff(filename, new_file_content_str, original_file_content_str)


                # count number of lines added and removed
                patch_lines = patch.splitlines(keepends=True)
                num_plus_lines = len([line for line in patch_lines if line.startswith('+')])
                num_minus_lines = len([line for line in patch_lines if line.startswith('-')])
                diff_files.append(
                    FilePatchInfo(original_file_content_str, new_file_content_str,
                                  patch=patch,
                                  filename=filename,
                                  edit_type=edit_type,
                                  old_filename=None if diff['old_path'] == diff['new_path'] else diff['old_path'],
                                  num_plus_lines=num_plus_lines,
                                  num_minus_lines=num_minus_lines, ))

        self.diff_files = diff_files
        return diff_files

    def get_files(self):
        if not self.git_files:
            self.git_files = [change['new_path'] for change in self.mr.changes()['changes']]
        return self.git_files

    def publish_description(self, pr_title: str, pr_body: str):
        try:
            self.mr.title = pr_title
            self.mr.description = pr_body
            self.mr.save()
        except Exception as e:
            get_logger().exception(f"Could not update merge request {self.id_mr} description: {e}")

    def get_latest_commit_url(self):
        return self.mr.commits().next().web_url

    def get_comment_url(self, comment):
        return f"{self.mr.web_url}#note_{comment.id}"

    def publish_persistent_comment(self, pr_comment: str,
                                   initial_header: str,
                                   update_header: bool = True,
                                   name='review',
                                   final_update_message=True):
        try:
            for comment in self.mr.notes.list(get_all=True)[::-1]:
                if comment.body.startswith(initial_header):
                    latest_commit_url = self.get_latest_commit_url()
                    comment_url = self.get_comment_url(comment)
                    if update_header:
                        updated_header = f"{initial_header}\n\n#### ({name.capitalize()} updated until commit {latest_commit_url})\n"
                        pr_comment_updated = pr_comment.replace(initial_header, updated_header)
                    else:
                        pr_comment_updated = pr_comment
                    get_logger().info(f"Persistent mode - updating comment {comment_url} to latest {name} message")
                    response = self.mr.notes.update(comment.id, {'body': pr_comment_updated})
                    if final_update_message:
                        self.publish_comment(
                            f"**[Persistent {name}]({comment_url})** updated to latest commit {latest_commit_url}")
                    return
        except Exception as e:
            get_logger().exception(f"Failed to update persistent review, error: {e}")
            pass
        self.publish_comment(pr_comment)

    def publish_comment(self, mr_comment: str, is_temporary: bool = False):
        comment = self.mr.notes.create({'body': mr_comment})
        if is_temporary:
            self.temp_comments.append(comment)
        return comment

    def edit_comment(self, comment, body: str):
        self.mr.notes.update(comment.id,{'body': body} )

    def reply_to_comment_from_comment_id(self, comment_id: int, body: str):
        discussion = self.mr.discussions.get(comment_id)
        discussion.notes.create({'body': body})

    def publish_inline_comment(self, body: str, relevant_file: str, relevant_line_in_file: str):
        edit_type, found, source_line_no, target_file, target_line_no = self.search_line(relevant_file,
                                                                                         relevant_line_in_file)
        self.send_inline_comment(body, edit_type, found, relevant_file, relevant_line_in_file, source_line_no,
                                 target_file, target_line_no)

    def create_inline_comment(self, body: str, relevant_file: str, relevant_line_in_file: str, absolute_position: int = None):
        raise NotImplementedError("Gitlab provider does not support creating inline comments yet")

    def create_inline_comments(self, comments: list[dict]):
        raise NotImplementedError("Gitlab provider does not support publishing inline comments yet")

    def send_inline_comment(self,body: str,edit_type: str,found: bool,relevant_file: str,relevant_line_in_file: int,
                            source_line_no: int, target_file: str,target_line_no: int) -> None:
        if not found:
            get_logger().info(f"Could not find position for {relevant_file} {relevant_line_in_file}")
        else:
            # in order to have exact sha's we have to find correct diff for this change
            diff = self.get_relevant_diff(relevant_file, relevant_line_in_file)
            if diff is None:
                get_logger().error(f"Could not get diff for merge request {self.id_mr}")
                raise DiffNotFoundError(f"Could not get diff for merge request {self.id_mr}")
            pos_obj = {'position_type': 'text',
                       'new_path': target_file.filename,
                       'old_path': target_file.old_filename if target_file.old_filename else target_file.filename,
                       'base_sha': diff.base_commit_sha, 'start_sha': diff.start_commit_sha, 'head_sha': diff.head_commit_sha}
            if edit_type == 'deletion':
                pos_obj['old_line'] = source_line_no - 1
            elif edit_type == 'addition':
                pos_obj['new_line'] = target_line_no - 1
            else:
                pos_obj['new_line'] = target_line_no - 1
                pos_obj['old_line'] = source_line_no - 1
            get_logger().debug(f"Creating comment in {self.id_mr} with body {body} and position {pos_obj}")
            try:
                self.mr.discussions.create({'body': body, 'position': pos_obj})
            except Exception as e:
                get_logger().debug(
                    f"Failed to create comment in {self.id_mr} with position {pos_obj} (probably not a '+' line)")

    def get_relevant_diff(self, relevant_file: str, relevant_line_in_file: int) -> Optional[dict]:
        changes = self.mr.changes()  # Retrieve the changes for the merge request once
        if not changes:
            get_logger().error('No changes found for the merge request.')
            return None
        all_diffs = self.mr.diffs.list(get_all=True)
        if not all_diffs:
            get_logger().error('No diffs found for the merge request.')
            return None
        for diff in all_diffs:
            for change in changes['changes']:
                if change['new_path'] == relevant_file and relevant_line_in_file in change['diff']:
                    return diff
            get_logger().debug(
                f'No relevant diff found for {relevant_file} {relevant_line_in_file}. Falling back to last diff.')
        return self.last_diff  # fallback to last_diff if no relevant diff is found

    def publish_code_suggestions(self, code_suggestions: list) -> bool:
        for suggestion in code_suggestions:
            try:
                body = suggestion['body']
                relevant_file = suggestion['relevant_file']
                relevant_lines_start = suggestion['relevant_lines_start']
                relevant_lines_end = suggestion['relevant_lines_end']

                diff_files = self.get_diff_files()
                target_file = None
                for file in diff_files:
                    if file.filename == relevant_file:
                        if file.filename == relevant_file:
                            target_file = file
                            break
                range = relevant_lines_end - relevant_lines_start # no need to add 1
                body = body.replace('```suggestion', f'```suggestion:-0+{range}')
                lines = target_file.head_file.splitlines()
                relevant_line_in_file = lines[relevant_lines_start - 1]

                # edit_type, found, source_line_no, target_file, target_line_no = self.find_in_file(target_file,
                #                                                                            relevant_line_in_file)
                # for code suggestions, we want to edit the new code
                source_line_no = None
                target_line_no = relevant_lines_start + 1
                found = True
                edit_type = 'addition'

                self.send_inline_comment(body, edit_type, found, relevant_file, relevant_line_in_file, source_line_no,
                                         target_file, target_line_no)
            except Exception as e:
                get_logger().exception(f"Could not publish code suggestion:\nsuggestion: {suggestion}\nerror: {e}")

        # note that we publish suggestions one-by-one. so, if one fails, the rest will still be published
        return True

    def search_line(self, relevant_file, relevant_line_in_file):
        target_file = None

        edit_type = self.get_edit_type(relevant_line_in_file)
        for file in self.get_diff_files():
            if file.filename == relevant_file:
                edit_type, found, source_line_no, target_file, target_line_no = self.find_in_file(file,
                                                                                                  relevant_line_in_file)
        return edit_type, found, source_line_no, target_file, target_line_no

    def find_in_file(self, file, relevant_line_in_file):
        edit_type = 'context'
        source_line_no = 0
        target_line_no = 0
        found = False
        target_file = file
        patch = file.patch
        patch_lines = patch.splitlines()
        for line in patch_lines:
            if line.startswith('@@'):
                match = self.RE_HUNK_HEADER.match(line)
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
            elif relevant_line_in_file[0] == '+' and relevant_line_in_file[1:].lstrip() in line:
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
                self.remove_comment(comment)
        except Exception as e:
            get_logger().exception(f"Failed to remove temp comments, error: {e}")

    def remove_comment(self, comment):
        try:
            comment.delete()
        except Exception as e:
            get_logger().exception(f"Failed to remove comment, error: {e}")

    def get_title(self):
        return self.mr.title

    def get_languages(self):
        languages = self.gl.projects.get(self.id_project).languages()
        return languages

    def get_pr_branch(self):
        return self.mr.source_branch

    def get_pr_description_full(self):
        return self.mr.description

    def get_issue_comments(self):
        raise NotImplementedError("GitLab provider does not support issue comments yet")

    def get_repo_settings(self):
        try:
            contents = self.gl.projects.get(self.id_project).files.get(file_path='.pr_agent.toml', ref=self.mr.target_branch).decode()
            return contents
        except Exception:
            return ""

    def add_eyes_reaction(self, issue_comment_id: int, disable_eyes: bool = False) -> Optional[int]:
        return True

    def remove_reaction(self, issue_comment_id: int, reaction_id: int) -> bool:
        return True

    def _parse_merge_request_url(self, merge_request_url: str) -> Tuple[str, int]:
        parsed_url = urlparse(merge_request_url)

        path_parts = parsed_url.path.strip('/').split('/')
        if 'merge_requests' not in path_parts:
            raise ValueError("The provided URL does not appear to be a GitLab merge request URL")

        mr_index = path_parts.index('merge_requests')
        # Ensure there is an ID after 'merge_requests'
        if len(path_parts) <= mr_index + 1:
            raise ValueError("The provided URL does not contain a merge request ID")

        try:
            mr_id = int(path_parts[mr_index + 1])
        except ValueError as e:
            raise ValueError("Unable to convert merge request ID to integer") from e

        # Handle special delimiter (-)
        project_path = "/".join(path_parts[:mr_index])
        if project_path.endswith('/-'):
            project_path = project_path[:-2]

        # Return the path before 'merge_requests' and the ID
        return project_path, mr_id

    def _get_merge_request(self):
        mr = self.gl.projects.get(self.id_project).mergerequests.get(self.id_mr)
        return mr

    def get_user_id(self):
        return None

    def publish_labels(self, pr_types):
        try:
            self.mr.labels = list(set(pr_types))
            self.mr.save()
        except Exception as e:
            get_logger().exception(f"Failed to publish labels, error: {e}")

    def publish_inline_comments(self, comments: list[dict]):
        pass

    def get_pr_labels(self, update=False):
        return self.mr.labels

    def get_repo_labels(self):
        return self.gl.projects.get(self.id_project).labels.list()

    def get_commit_messages(self):
        """
        Retrieves the commit messages of a pull request.

        Returns:
            str: A string containing the commit messages of the pull request.
        """
        max_tokens = get_settings().get("CONFIG.MAX_COMMITS_TOKENS", None)
        try:
            commit_messages_list = [commit['message'] for commit in self.mr.commits()._list]
            commit_messages_str = "\n".join([f"{i + 1}. {message}" for i, message in enumerate(commit_messages_list)])
        except Exception:
            commit_messages_str = ""
        if max_tokens:
            commit_messages_str = clip_tokens(commit_messages_str, max_tokens)
        return commit_messages_str

    def get_pr_id(self):
        try:
            pr_id = self.mr.web_url
            return pr_id
        except:
            return ""

    def get_line_link(self, relevant_file: str, relevant_line_start: int, relevant_line_end: int = None) -> str:
        if relevant_line_start == -1:
            link = f"{self.gl.url}/{self.id_project}/-/blob/{self.mr.source_branch}/{relevant_file}?ref_type=heads"
        elif relevant_line_end:
            link = f"{self.gl.url}/{self.id_project}/-/blob/{self.mr.source_branch}/{relevant_file}?ref_type=heads#L{relevant_line_start}-L{relevant_line_end}"
        else:
            link = f"{self.gl.url}/{self.id_project}/-/blob/{self.mr.source_branch}/{relevant_file}?ref_type=heads#L{relevant_line_start}"
        return link


    def generate_link_to_relevant_line_number(self, suggestion) -> str:
        try:
            relevant_file = suggestion['relevant_file'].strip('`').strip("'").rstrip()
            relevant_line_str = suggestion['relevant_line'].rstrip()
            if not relevant_line_str:
                return ""

            position, absolute_position = find_line_number_of_relevant_line_in_file \
                (self.diff_files, relevant_file, relevant_line_str)

            if absolute_position != -1:
                # link to right file only
                link = f"{self.gl.url}/{self.id_project}/-/blob/{self.mr.source_branch}/{relevant_file}?ref_type=heads#L{absolute_position}"

                # # link to diff
                # sha_file = hashlib.sha1(relevant_file.encode('utf-8')).hexdigest()
                # link = f"{self.pr.web_url}/diffs#{sha_file}_{absolute_position}_{absolute_position}"
                return link
        except Exception as e:
            if get_settings().config.verbosity_level >= 2:
                get_logger().info(f"Failed adding line link, error: {e}")

        return ""
