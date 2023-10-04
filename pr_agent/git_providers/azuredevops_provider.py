import json
import logging
from typing import Optional, Tuple
from urllib.parse import urlparse

import os

AZURE_DEVOPS_AVAILABLE = True
try:
    from msrest.authentication import BasicAuthentication
    from azure.devops.connection import Connection
    from azure.devops.v7_1.git.models import Comment, CommentThread, GitVersionDescriptor, GitPullRequest
except ImportError:
    AZURE_DEVOPS_AVAILABLE = False

from ..algo.pr_processing import clip_tokens
from ..config_loader import get_settings
from ..algo.utils import load_large_diff
from ..algo.language_handler import is_valid_file
from .git_provider import EDIT_TYPE, FilePatchInfo


class AzureDevopsProvider:
    def __init__(self, pr_url: Optional[str] = None, incremental: Optional[bool] = False):
        if not AZURE_DEVOPS_AVAILABLE:
            raise ImportError("Azure DevOps provider is not available. Please install the required dependencies.")

        self.azure_devops_client = self._get_azure_devops_client()

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
        if capability in ['get_issue_comments', 'create_inline_comment', 'publish_inline_comments', 'get_labels',
                          'remove_initial_comment', 'gfm_markdown']:
            return False
        return True

    def set_pr(self, pr_url: str):
        self.workspace_slug, self.repo_slug, self.pr_num = self._parse_pr_url(pr_url)
        self.pr = self._get_pr()

    def get_repo_settings(self):
        try:
            contents = self.azure_devops_client.get_item_content(repository_id=self.repo_slug,
                                                                 project=self.workspace_slug, download=False,
                                                                 include_content_metadata=False, include_content=True,
                                                                 path=".pr_agent.toml")
            return contents
        except Exception as e:
            logging.exception("get repo settings error")
            return ""

    def get_files(self):
        files = []
        for i in self.azure_devops_client.get_pull_request_commits(project=self.workspace_slug,
                                                                   repository_id=self.repo_slug,
                                                                   pull_request_id=self.pr_num):

            changes_obj = self.azure_devops_client.get_changes(project=self.workspace_slug,
                                                               repository_id=self.repo_slug, commit_id=i.commit_id)

            for c in changes_obj.changes:
                files.append(c['item']['path'])
        return list(set(files))

    def get_diff_files(self) -> list[FilePatchInfo]:
        try:
            base_sha = self.pr.last_merge_target_commit
            head_sha = self.pr.last_merge_source_commit

            commits = self.azure_devops_client.get_pull_request_commits(project=self.workspace_slug,
                                                                        repository_id=self.repo_slug,
                                                                        pull_request_id=self.pr_num)

            diff_files = []
            diffs = []
            diff_types = {}

            for c in commits:
                changes_obj = self.azure_devops_client.get_changes(project=self.workspace_slug,
                                                                   repository_id=self.repo_slug, commit_id=c.commit_id)
                for i in changes_obj.changes:
                    if(i['item']['gitObjectType'] == 'tree'):
                        continue
                    diffs.append(i['item']['path'])
                    diff_types[i['item']['path']] = i['changeType']

            diffs = list(set(diffs))

            for file in diffs:
                if not is_valid_file(file):
                    continue

                version = GitVersionDescriptor(version=head_sha.commit_id, version_type='commit')
                try:
                    new_file_content_str = self.azure_devops_client.get_item(repository_id=self.repo_slug,
                                                                            path=file,
                                                                            project=self.workspace_slug,
                                                                            version_descriptor=version,
                                                                            download=False,
                                                                            include_content=True)

                    new_file_content_str = new_file_content_str.content
                except Exception as error:
                    logging.error("Failed to retrieve new file content of %s at version %s. Error: %s", file, version, str(error))
                    new_file_content_str = ""

                edit_type = EDIT_TYPE.MODIFIED
                if diff_types[file] == 'add':
                    edit_type = EDIT_TYPE.ADDED
                elif diff_types[file] == 'delete':
                    edit_type = EDIT_TYPE.DELETED
                elif diff_types[file] == 'rename':
                    edit_type = EDIT_TYPE.RENAMED

                version = GitVersionDescriptor(version=base_sha.commit_id, version_type='commit')
                try:
                    original_file_content_str = self.azure_devops_client.get_item(repository_id=self.repo_slug,
                                                                              path=file,
                                                                              project=self.workspace_slug,
                                                                              version_descriptor=version,
                                                                              download=False,
                                                                              include_content=True)
                    original_file_content_str = original_file_content_str.content
                except Exception as error:
                    logging.error("Failed to retrieve original file content of %s at version %s. Error: %s", file, version, str(error))
                    original_file_content_str = ""

                patch = load_large_diff(file, new_file_content_str, original_file_content_str)

                diff_files.append(FilePatchInfo(original_file_content_str, new_file_content_str,
                                                patch=patch,
                                                filename=file,
                                                edit_type=edit_type))

            self.diff_files = diff_files
            return diff_files
        except Exception as e:
            print(f"Error: {str(e)}")
            return []

    def publish_comment(self, pr_comment: str, is_temporary: bool = False):
        comment = Comment(content=pr_comment)
        thread = CommentThread(comments=[comment])
        thread_response = self.azure_devops_client.create_thread(comment_thread=thread, project=self.workspace_slug,
                                                                 repository_id=self.repo_slug,
                                                                 pull_request_id=self.pr_num)
        if is_temporary:
            self.temp_comments.append({'thread_id': thread_response.id, 'comment_id': comment.id})

    def publish_description(self, pr_title: str, pr_body: str):
        try:
            updated_pr = GitPullRequest()
            updated_pr.title = pr_title
            updated_pr.description = pr_body
            self.azure_devops_client.update_pull_request(project=self.workspace_slug,
                                                         repository_id=self.repo_slug,
                                                         pull_request_id=self.pr_num,
                                                         git_pull_request_to_update=updated_pr)
        except Exception as e:
            logging.exception(f"Could not update pull request {self.pr_num} description: {e}")

    def remove_initial_comment(self):
        return ""  # not implemented yet

    def publish_inline_comment(self, body: str, relevant_file: str, relevant_line_in_file: str):
        raise NotImplementedError("Azure DevOps provider does not support publishing inline comment yet")

    def create_inline_comment(self, body: str, relevant_file: str, relevant_line_in_file: str):
        raise NotImplementedError("Azure DevOps provider does not support creating inline comments yet")

    def publish_inline_comments(self, comments: list[dict]):
        raise NotImplementedError("Azure DevOps provider does not support publishing inline comments yet")

    def get_title(self):
        return self.pr.title

    def get_languages(self):
        languages = []
        files = self.azure_devops_client.get_items(project=self.workspace_slug, repository_id=self.repo_slug,
                                                   recursion_level="Full", include_content_metadata=True,
                                                   include_links=False, download=False)
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

        return extension_percentages

    def get_pr_branch(self):
        pr_info = self.azure_devops_client.get_pull_request_by_id(project=self.workspace_slug,
                                                                  pull_request_id=self.pr_num)
        source_branch = pr_info.source_ref_name.split('/')[-1]
        return source_branch

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

    def get_issue_comments(self):
        raise NotImplementedError("Azure DevOps provider does not support issue comments yet")

    @staticmethod
    def _parse_pr_url(pr_url: str) -> Tuple[str, int]:
        parsed_url = urlparse(pr_url)

        if 'azure.com' not in parsed_url.netloc:
            raise ValueError("The provided URL is not a valid Azure DevOps URL")

        path_parts = parsed_url.path.strip('/').split('/')

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
            self.repo = self.azure_devops_client.get_repository(project=self.workspace_slug,
                                                                repository_id=self.repo_slug)
        return self.repo

    def _get_pr(self):
        self.pr = self.azure_devops_client.get_pull_request_by_id(pull_request_id=self.pr_num, project=self.workspace_slug)
        return self.pr

    def get_commit_messages(self):
        return ""  # not implemented yet
