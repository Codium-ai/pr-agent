import logging
from typing import Optional, Tuple
from urllib.parse import urlparse

import os

import requests

from msrest.authentication import BasicAuthentication
from azure.devops.connection import Connection

from ..algo.pr_processing import clip_tokens
from ..config_loader import get_settings
from .git_provider import FilePatchInfo

class AzureDevopsProvider:
    def __init__(self, pr_url: Optional[str] = None, incremental: Optional[bool] = False):

        self.azure_devops_client = self._get_azure_devops_client()
        logging.info(self.azure_devops_client)

        self.workspace_slug = None
        self.repo_slug = None
        self.repo = None
        self.pr_num = None
        self.pr = None
        self.temp_comments = []
        self.incremental = incremental
        if pr_url:
            self.set_pr(pr_url)

    def is_supported(self, capability: str) -> bool:
        if capability in ['get_issue_comments', 'create_inline_comment', 'publish_inline_comments', 'get_labels']:
            return False
        return True

    def set_pr(self, pr_url: str):
        self.workspace_slug, self.repo_slug, self.pr_num = self._parse_pr_url(pr_url)
        self.pr = self._get_pr()

    def get_repo_settings(self):
        try:
            contents = self.azure_devops_client.get_item_content(repository_id=self.repo_slug, project=self.workspace_slug, download=False, include_content_metadata=False, include_content=True, path=".pr_agent.toml")
            logging.info("get repo settings")
            logging.info(contents)
            return contents
        except Exception as e:
            logging.info("get repo settings error")
            logging.info(e)
            return ""

    def get_files(self):
        files = []
        for i in self.azure_devops_client.get_pull_request_commits(project=self.workspace_slug, repository_id=self.repo_slug, pull_request_id=self.pr_num):
            #logging.info(i)
            changes_obj = self.azure_devops_client.get_changes(project=self.workspace_slug, repository_id=self.repo_slug, commit_id=i.commit_id)
            #logging.info(changes_obj)
            #logging.info("***********")
            for c in changes_obj.changes:
                files.append(c['item']['path'])
            #logging.info("###########")
        return files

    def get_diff_files(self) -> list[FilePatchInfo]:
        diffs = self.pr.diffstat()
        diff_split = ['diff --git%s' % x for x in self.pr.diff().split('diff --git') if x.strip()]
        
        diff_files = []
        for index, diff in enumerate(diffs):
            original_file_content_str = self._get_pr_file_content(diff.old.get_data('links'))
            new_file_content_str = self._get_pr_file_content(diff.new.get_data('links'))
            diff_files.append(FilePatchInfo(original_file_content_str, new_file_content_str,
                                            diff_split[index], diff.new.path))
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

    def create_inline_comment(self, body: str, relevant_file: str, relevant_line_in_file: str):
        raise NotImplementedError("Azure DevOps provider does not support creating inline comments yet")

    def publish_inline_comments(self, comments: list[dict]):
        raise NotImplementedError("Azure DevOps provider does not support publishing inline comments yet")

    def get_title(self):
        return self.pr.title

    def get_languages(self):
        languages = []
        files = self.azure_devops_client.get_items(project=self.workspace_slug, repository_id=self.repo_slug, recursion_level="Full", include_content_metadata=True, include_links=False, download=False)
        for f in files:
            if f.git_object_type == 'blob':
                file_name, file_extension = os.path.splitext(f.path)
                languages.append(file_extension[1:])

        extension_counts = {}
        for ext in languages:
            if ext != '':
                extension_counts[ext] = extension_counts.get(ext, 0) + 1

        total_extensions = sum(extension_counts.values())

        extension_percentages = {ext: (count / total_extensions) * 100 for ext, count in extension_counts.items()}
        logging.info(extension_percentages)

        return extension_percentages

    def get_pr_branch(self):
        return self.pr.source_branch

    def get_pr_description(self):
        max_tokens = get_settings().get("CONFIG.MAX_DESCRIPTION_TOKENS", None)
        if max_tokens:
            return clip_tokens(self.pr.description, max_tokens)
        return self.pr.description

    def get_user_id(self):
        return 0

    def get_issue_comments(self):
        raise NotImplementedError("Azure DevOps provider does not support issue comments yet")

    def add_eyes_reaction(self, issue_comment_id: int) -> Optional[int]:
        return True

    def remove_reaction(self, issue_comment_id: int, reaction_id: int) -> bool:
        return True

    @staticmethod
    def _parse_pr_url(pr_url: str) -> Tuple[str, int]:
        parsed_url = urlparse(pr_url)
        
        if 'azure.com' not in parsed_url.netloc:
            raise ValueError("The provided URL is not a valid Azure DevOps URL")

        path_parts = parsed_url.path.strip('/').split('/')
        logging.info(path_parts)
        
        if len(path_parts) < 6 or path_parts[4] != 'pullrequest':
            raise ValueError("The provided URL does not appear to be a Azure DevOps PR URL")

        workspace_slug = path_parts[1]
        repo_slug = path_parts[3]
        try:
            pr_number = int(path_parts[5])
        except ValueError as e:
            raise ValueError("Unable to convert PR number to integer") from e

        return workspace_slug, repo_slug, pr_number

    def _get_azure_devops_client(self):
        try:
            pat = get_settings().azure_devops.pat
            org = get_settings().azure_devops.org
        except AttributeError as e:
            raise ValueError(
                "Azure DevOps PAT token is required ") from e

        credentials = BasicAuthentication('', pat)
        azure_devops_connection = Connection(base_url=org, creds=credentials)
        azure_devops_client = azure_devops_connection.clients.get_git_client()

        return azure_devops_client

    def _get_repo(self):
        if self.repo is None:
            self.repo = self.azure_devops_client.get_repository(project=self.workspace_slug, repository_id=self.repo_slug)
            #logging.info(self.repo)
        return self.repo

    def _get_pr(self):
        logging.info(self.azure_devops_client.get_pull_request_by_id(pull_request_id=self.pr_num, project=self.workspace_slug))
        return self.azure_devops_client.get_pull_request_by_id(pull_request_id=self.pr_num, project=self.workspace_slug)

    def _get_pr_file_content(self, remote_link: str):
        return ""

    def get_commit_messages(self):
        return ""  # not implemented yet
