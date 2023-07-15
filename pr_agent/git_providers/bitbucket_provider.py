import logging
from datetime import datetime
from typing import Optional, Tuple
from urllib.parse import urlparse

import requests
from atlassian.bitbucket import Cloud

from pr_agent.config_loader import settings

from .git_provider import FilePatchInfo

class BitbucketProvider:
    def __init__(self, pr_url: Optional[str] = None):
        s = requests.Session()
        s.headers['Authorization'] = f'Bearer {settings.get("BITBUCKET.BEARER_TOKEN", None)}'
        self.bitbucket_client = Cloud(session=s)

        self.workspace_slug = None
        self.repo_slug = None
        self.repo = None
        self.pr_num = None
        self.pr = None
        self.temp_comments = []
        if pr_url:
            self.set_pr(pr_url)

    def set_pr(self, pr_url: str):
        self.workspace_slug, self.repo_slug, self.pr_num = self._parse_pr_url(pr_url)
        self.pr = self._get_pr()

    def get_files(self):
        return [diff.new.path for diff in self.pr.diffstat()]

    def get_diff_files(self) -> list[FilePatchInfo]:
        diffs = self.pr.diffstat()
        diff_split = ['diff --git%s' % x for x in self.pr.diff().split('diff --git') if x.strip()]
        
        diff_files = []
        for index, diff in enumerate(diffs):
            original_file_content_str = self._get_pr_file_content(diff.old.get_data('links'))
            new_file_content_str = self._get_pr_file_content(diff.new.get_data('links'))
            diff_files.append(FilePatchInfo(original_file_content_str, new_file_content_str, diff_split[index], diff.new.path))
        return diff_files

    def publish_comment(self, pr_comment: str, is_temporary: bool = False):
        comment = self.pr.comment(pr_comment)
        if is_temporary:
            self.temp_comments.append(comment['id'])

    def remove_initial_comment(self):
        try:
            for comment in self.temp_comments:
                self.pr.delete(f'comments/{comment}')
        except Exception as e:
            logging.exception(f"Failed to remove temp comments, error: {e}")

    def publish_inline_comment(self, body: str, relevant_file: str, relevant_line_in_file: str):
        pass

    def get_title(self):
        return self.pr.title

    def get_description(self):
        return self.pr.body

    def get_languages(self):
        languages = {self._get_repo().get_data('language'): 0}
        return languages

    def get_pr_branch(self):
        return self.pr.source_branch

    def get_pr_description(self):
        return self.pr.description

    def get_user_id(self):
        return 0

    @staticmethod
    def _parse_pr_url(pr_url: str) -> Tuple[str, int]:
        parsed_url = urlparse(pr_url)
        
        if 'bitbucket.org' not in parsed_url.netloc:
            raise ValueError("The provided URL is not a valid GitHub URL")

        path_parts = parsed_url.path.strip('/').split('/')
        
        if len(path_parts) < 4 or path_parts[2] != 'pull-requests':
            raise ValueError("The provided URL does not appear to be a Bitbucket PR URL")

        workspace_slug = path_parts[0]
        repo_slug = path_parts[1]
        try:
            pr_number = int(path_parts[3])
        except ValueError as e:
            raise ValueError("Unable to convert PR number to integer") from e

        return workspace_slug, repo_slug, pr_number

    def _get_repo(self):
        if self.repo is None:
            self.repo = self.bitbucket_client.workspaces.get(self.workspace_slug).repositories.get(self.repo_slug)
        return self.repo

    def _get_pr(self):
        return self._get_repo().pullrequests.get(self.pr_num)

    def _get_pr_file_content(self, remote_link: str):
        return ""
