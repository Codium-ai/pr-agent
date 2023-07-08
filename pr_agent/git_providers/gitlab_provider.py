from urllib.parse import urlparse
import gitlab
from typing import Optional, Tuple

from pr_agent.config_loader import settings

from .git_provider import FilePatchInfo, GitProvider


class GitLabProvider(GitProvider):
    def __init__(self, merge_request_url: Optional[str] = None):
        self.gl = gitlab.Gitlab(
            settings.get("GITLAB.URL"),
            private_token=settings.get("GITLAB.PERSONAL_ACCESS_TOKEN")
        )

        self.id_project = None
        self.id_mr = None
        self.mr = None
        self.temp_comments = []

        self.set_merge_request(merge_request_url)

    @property
    def pr(self):
        '''The GitLab terminology is merge request (MR) instead of pull request (PR)'''
        return self.mr

    def set_merge_request(self, merge_request_url: str):
        self.id_project, self.id_mr = self._parse_merge_request_url(merge_request_url)
        self.mr = self._get_merge_request()

    def get_diff_files(self) -> list[FilePatchInfo]:
        diffs = self.mr.changes()['changes']
        diff_files = [FilePatchInfo("", "", diff['diff'], diff['new_path']) for diff in diffs]
        return diff_files

    def get_files(self):
        return [change['new_path'] for change in self.mr.changes()['changes']]

    def publish_comment(self, mr_comment: str, is_temporary: bool = False):
        comment = self.mr.notes.create({'body': mr_comment})
        if is_temporary:
            self.temp_comments.append(comment)

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
