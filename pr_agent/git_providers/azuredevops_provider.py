import os
from typing import Optional, Tuple
from urllib.parse import urlparse

from ..log import get_logger
from ..algo.language_handler import is_valid_file
from ..algo.utils import clip_tokens, load_large_diff
from ..config_loader import get_settings
from .git_provider import EDIT_TYPE, FilePatchInfo, GitProvider

AZURE_DEVOPS_AVAILABLE = True

try:
    # noinspection PyUnresolvedReferences
    from msrest.authentication import BasicAuthentication
    # noinspection PyUnresolvedReferences
    from azure.devops.connection import Connection
    # noinspection PyUnresolvedReferences
    from azure.devops.v7_1.git.models import (
        Comment,
        CommentThread,
        GitVersionDescriptor,
        GitPullRequest,
    )
except ImportError:
    AZURE_DEVOPS_AVAILABLE = False


class AzureDevopsProvider(GitProvider):

    def __init__(
            self, pr_url: Optional[str] = None, incremental: Optional[bool] = False
    ):
        if not AZURE_DEVOPS_AVAILABLE:
            raise ImportError(
                "Azure DevOps provider is not available. Please install the required dependencies."
            )

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

    def publish_code_suggestions(self, code_suggestions: list) -> bool:
        """
        Publishes code suggestions as comments on the PR.
        """
        post_parameters_list = []
        for suggestion in code_suggestions:
            body = suggestion['body']
            relevant_file = suggestion['relevant_file']
            relevant_lines_start = suggestion['relevant_lines_start']
            relevant_lines_end = suggestion['relevant_lines_end']

            if not relevant_lines_start or relevant_lines_start == -1:
                if get_settings().config.verbosity_level >= 2:
                    get_logger().exception(
                        f"Failed to publish code suggestion, relevant_lines_start is {relevant_lines_start}")
                continue

            if relevant_lines_end < relevant_lines_start:
                if get_settings().config.verbosity_level >= 2:
                    get_logger().exception(f"Failed to publish code suggestion, "
                                           f"relevant_lines_end is {relevant_lines_end} and "
                                           f"relevant_lines_start is {relevant_lines_start}")
                continue

            if relevant_lines_end > relevant_lines_start:
                post_parameters = {
                    "body": body,
                    "path": relevant_file,
                    "line": relevant_lines_end,
                    "start_line": relevant_lines_start,
                    "start_side": "RIGHT",
                }
            else:  # API is different for single line comments
                post_parameters = {
                    "body": body,
                    "path": relevant_file,
                    "line": relevant_lines_start,
                    "side": "RIGHT",
                }
            post_parameters_list.append(post_parameters)

        try:
            for post_parameters in post_parameters_list:
                comment = Comment(content=post_parameters["body"], comment_type=1)
                thread = CommentThread(comments=[comment],
                                       thread_context={
                                           "filePath": post_parameters["path"],
                                           "rightFileStart": {
                                               "line": post_parameters["start_line"],
                                               "offset": 1,
                                           },
                                           "rightFileEnd": {
                                               "line": post_parameters["line"],
                                               "offset": 1,
                                           },
                                       })
                self.azure_devops_client.create_thread(
                    comment_thread=thread,
                    project=self.workspace_slug,
                    repository_id=self.repo_slug,
                    pull_request_id=self.pr_num
                )
                if get_settings().config.verbosity_level >= 2:
                    get_logger().info(
                        f"Published code suggestion on {self.pr_num} at {post_parameters['path']}"
                    )
            return True
        except Exception as e:
            if get_settings().config.verbosity_level >= 2:
                get_logger().error(f"Failed to publish code suggestion, error: {e}")
            return False

    def get_pr_description_full(self) -> str:
        return self.pr.description

    def remove_comment(self, comment):
        try:
            self.azure_devops_client.delete_comment(
                repository_id=self.repo_slug,
                pull_request_id=self.pr_num,
                thread_id=comment["thread_id"],
                comment_id=comment["comment_id"],
                project=self.workspace_slug,
            )
        except Exception as e:
            get_logger().exception(f"Failed to remove comment, error: {e}")

    def publish_labels(self, pr_types):
        try:
            for pr_type in pr_types:
                self.azure_devops_client.create_pull_request_label(
                    label={"name": pr_type},
                    project=self.workspace_slug,
                    repository_id=self.repo_slug,
                    pull_request_id=self.pr_num,
                )
        except Exception as e:
            get_logger().exception(f"Failed to publish labels, error: {e}")

    def get_pr_labels(self):
        try:
            labels = self.azure_devops_client.get_pull_request_labels(
                project=self.workspace_slug,
                repository_id=self.repo_slug,
                pull_request_id=self.pr_num,
            )
            return [label.name for label in labels]
        except Exception as e:
            get_logger().exception(f"Failed to get labels, error: {e}")
            return []

    def is_supported(self, capability: str) -> bool:
        if capability in [
            "get_issue_comments",
            "create_inline_comment",
            "publish_inline_comments",
        ]:
            return False
        return True

    def set_pr(self, pr_url: str):
        self.workspace_slug, self.repo_slug, self.pr_num = self._parse_pr_url(pr_url)
        self.pr = self._get_pr()

    def get_repo_settings(self):
        try:
            contents = self.azure_devops_client.get_item_content(
                repository_id=self.repo_slug,
                project=self.workspace_slug,
                download=False,
                include_content_metadata=False,
                include_content=True,
                path=".pr_agent.toml",
            )
            return contents
        except Exception as e:
            if get_settings().config.verbosity_level >= 2:
                get_logger().error(f"Failed to get repo settings, error: {e}")
            return ""

    def get_files(self):
        files = []
        for i in self.azure_devops_client.get_pull_request_commits(
                project=self.workspace_slug,
                repository_id=self.repo_slug,
                pull_request_id=self.pr_num,
        ):
            changes_obj = self.azure_devops_client.get_changes(
                project=self.workspace_slug,
                repository_id=self.repo_slug,
                commit_id=i.commit_id,
            )

            for c in changes_obj.changes:
                files.append(c["item"]["path"])
        return list(set(files))

    def get_diff_files(self) -> list[FilePatchInfo]:
        try:
            base_sha = self.pr.last_merge_target_commit
            head_sha = self.pr.last_merge_source_commit

            commits = self.azure_devops_client.get_pull_request_commits(
                project=self.workspace_slug,
                repository_id=self.repo_slug,
                pull_request_id=self.pr_num,
            )

            diff_files = []
            diffs = []
            diff_types = {}

            for c in commits:
                changes_obj = self.azure_devops_client.get_changes(
                    project=self.workspace_slug,
                    repository_id=self.repo_slug,
                    commit_id=c.commit_id,
                )
                for i in changes_obj.changes:
                    if i["item"]["gitObjectType"] == "tree":
                        continue
                    diffs.append(i["item"]["path"])
                    diff_types[i["item"]["path"]] = i["changeType"]

            diffs = list(set(diffs))

            for file in diffs:
                if not is_valid_file(file):
                    continue

                version = GitVersionDescriptor(
                    version=head_sha.commit_id, version_type="commit"
                )
                try:
                    new_file_content_str = self.azure_devops_client.get_item(
                        repository_id=self.repo_slug,
                        path=file,
                        project=self.workspace_slug,
                        version_descriptor=version,
                        download=False,
                        include_content=True,
                    )

                    new_file_content_str = new_file_content_str.content
                except Exception as error:
                    get_logger().error(
                        "Failed to retrieve new file content of %s at version %s. Error: %s",
                        file,
                        version,
                        str(error),
                    )
                    new_file_content_str = ""

                edit_type = EDIT_TYPE.MODIFIED
                if diff_types[file] == "add":
                    edit_type = EDIT_TYPE.ADDED
                elif diff_types[file] == "delete":
                    edit_type = EDIT_TYPE.DELETED
                elif diff_types[file] == "rename":
                    edit_type = EDIT_TYPE.RENAMED

                version = GitVersionDescriptor(
                    version=base_sha.commit_id, version_type="commit"
                )
                try:
                    original_file_content_str = self.azure_devops_client.get_item(
                        repository_id=self.repo_slug,
                        path=file,
                        project=self.workspace_slug,
                        version_descriptor=version,
                        download=False,
                        include_content=True,
                    )
                    original_file_content_str = original_file_content_str.content
                except Exception as error:
                    get_logger().error(
                        "Failed to retrieve original file content of %s at version %s. Error: %s",
                        file,
                        version,
                        str(error),
                    )
                    original_file_content_str = ""

                patch = load_large_diff(
                    file, new_file_content_str, original_file_content_str
                )

                diff_files.append(
                    FilePatchInfo(
                        original_file_content_str,
                        new_file_content_str,
                        patch=patch,
                        filename=file,
                        edit_type=edit_type,
                    )
                )

            return diff_files
        except Exception as e:
            print(f"Error: {str(e)}")
            return []

    def publish_comment(self, pr_comment: str, is_temporary: bool = False):
        comment = Comment(content=pr_comment)
        thread = CommentThread(comments=[comment])
        thread_response = self.azure_devops_client.create_thread(
            comment_thread=thread,
            project=self.workspace_slug,
            repository_id=self.repo_slug,
            pull_request_id=self.pr_num,
        )
        if is_temporary:
            self.temp_comments.append(
                {"thread_id": thread_response.id, "comment_id": thread_response.comments[0].id}
            )

    def publish_description(self, pr_title: str, pr_body: str):
        try:
            updated_pr = GitPullRequest()
            updated_pr.title = pr_title
            updated_pr.description = pr_body
            self.azure_devops_client.update_pull_request(
                project=self.workspace_slug,
                repository_id=self.repo_slug,
                pull_request_id=self.pr_num,
                git_pull_request_to_update=updated_pr,
            )
        except Exception as e:
            get_logger().exception(
                f"Could not update pull request {self.pr_num} description: {e}"
            )

    def remove_initial_comment(self):
        try:
            for comment in self.temp_comments:
                self.remove_comment(comment)
        except Exception as e:
            get_logger().exception(f"Failed to remove temp comments, error: {e}")

    def publish_inline_comment(
            self, body: str, relevant_file: str, relevant_line_in_file: str
    ):
        raise NotImplementedError(
            "Azure DevOps provider does not support publishing inline comment yet"
        )

    def publish_inline_comments(self, comments: list[dict]):
        raise NotImplementedError(
            "Azure DevOps provider does not support publishing inline comments yet"
        )

    def get_title(self):
        return self.pr.title

    def get_languages(self):
        languages = []
        files = self.azure_devops_client.get_items(
            project=self.workspace_slug,
            repository_id=self.repo_slug,
            recursion_level="Full",
            include_content_metadata=True,
            include_links=False,
            download=False,
        )
        for f in files:
            if f.git_object_type == "blob":
                file_name, file_extension = os.path.splitext(f.path)
                languages.append(file_extension[1:])

        extension_counts = {}
        for ext in languages:
            if ext != "":
                extension_counts[ext] = extension_counts.get(ext, 0) + 1

        total_extensions = sum(extension_counts.values())

        extension_percentages = {
            ext: (count / total_extensions) * 100
            for ext, count in extension_counts.items()
        }

        return extension_percentages

    def get_pr_branch(self):
        pr_info = self.azure_devops_client.get_pull_request_by_id(
            project=self.workspace_slug, pull_request_id=self.pr_num
        )
        source_branch = pr_info.source_ref_name.split("/")[-1]
        return source_branch

    def get_pr_description(self, *, full: bool = True) -> str:
        max_tokens = get_settings().get("CONFIG.MAX_DESCRIPTION_TOKENS", None)
        if max_tokens:
            return clip_tokens(self.pr.description, max_tokens)
        return self.pr.description

    def get_user_id(self):
        return 0

    def get_issue_comments(self):
        raise NotImplementedError(
            "Azure DevOps provider does not support issue comments yet"
        )

    def add_eyes_reaction(self, issue_comment_id: int) -> Optional[int]:
        return True

    def remove_reaction(self, issue_comment_id: int, reaction_id: int) -> bool:
        return True

    @staticmethod
    def _parse_pr_url(pr_url: str) -> Tuple[str, str, int]:
        parsed_url = urlparse(pr_url)

        path_parts = parsed_url.path.strip("/").split("/")

        if len(path_parts) < 6 or path_parts[4] != "pullrequest":
            raise ValueError(
                "The provided URL does not appear to be a Azure DevOps PR URL"
            )

        workspace_slug = path_parts[1]
        repo_slug = path_parts[3]
        try:
            pr_number = int(path_parts[5])
        except ValueError as e:
            raise ValueError("Unable to convert PR number to integer") from e

        return workspace_slug, repo_slug, pr_number

    @staticmethod
    def _get_azure_devops_client():
        try:
            pat = get_settings().azure_devops.pat
            org = get_settings().azure_devops.org
        except AttributeError as e:
            raise ValueError("Azure DevOps PAT token is required ") from e

        credentials = BasicAuthentication("", pat)
        azure_devops_connection = Connection(base_url=org, creds=credentials)
        azure_devops_client = azure_devops_connection.clients.get_git_client()

        return azure_devops_client

    def _get_repo(self):
        if self.repo is None:
            self.repo = self.azure_devops_client.get_repository(
                project=self.workspace_slug, repository_id=self.repo_slug
            )
        return self.repo

    def _get_pr(self):
        self.pr = self.azure_devops_client.get_pull_request_by_id(
            pull_request_id=self.pr_num, project=self.workspace_slug
        )
        return self.pr

    def get_commit_messages(self):
        return ""  # not implemented yet

    def get_pr_id(self):
        try:
            pr_id = f"{self.workspace_slug}/{self.repo_slug}/{self.pr_num}"
            return pr_id
        except Exception as e:
            if get_settings().config.verbosity_level >= 2:
                get_logger().error(f"Failed to get pr id, error: {e}")
            return ""
