import json
from typing import Optional, Tuple
from urllib.parse import quote_plus, urlparse

from requests.exceptions import HTTPError
from atlassian.bitbucket import Bitbucket
from starlette_context import context

from .git_provider import GitProvider
from ..algo.types import EDIT_TYPE, FilePatchInfo
from ..algo.language_handler import is_valid_file
from ..algo.utils import load_large_diff, find_line_number_of_relevant_line_in_file
from ..config_loader import get_settings
from ..log import get_logger


class BitbucketServerProvider(GitProvider):
    def __init__(
            self, pr_url: Optional[str] = None, incremental: Optional[bool] = False
    ):
        self.bitbucket_server_url = None
        self.workspace_slug = None
        self.repo_slug = None
        self.repo = None
        self.pr_num = None
        self.pr = None
        self.pr_url = pr_url
        self.temp_comments = []
        self.incremental = incremental
        self.diff_files = None
        self.bitbucket_pull_request_api_url = pr_url

        self.bitbucket_server_url = self._parse_bitbucket_server(url=pr_url)
        self.bitbucket_client = Bitbucket(url=self.bitbucket_server_url,
                                          token=get_settings().get("BITBUCKET_SERVER.BEARER_TOKEN", None),
                                          username=get_settings().get("BITBUCKET_SERVER.USERNAME", None),
                                          password=get_settings().get("BITBUCKET_SERVER.PASSWORD", None)
                                          )

        if pr_url:
            self.set_pr(pr_url)

    def get_repo_settings(self):
        try:
            content = self.bitbucket_client.get_content_of_file(self.workspace_slug, self.repo_slug, ".pr_agent.toml", self.get_pr_branch())

            return content
        except Exception as e:
            if isinstance(e, HTTPError):
                if e.response.status_code == 404:  # not found
                    return ""

            get_logger().error(f"Failed to load .pr_agent.toml file, error: {e}")
            return ""

    def get_pr_id(self):
        return self.pr_num

    def publish_code_suggestions(self, code_suggestions: list) -> bool:
        """
        Publishes code suggestions as comments on the PR.
        """
        post_parameters_list = []
        for suggestion in code_suggestions:
            body = suggestion["body"]
            relevant_file = suggestion["relevant_file"]
            relevant_lines_start = suggestion["relevant_lines_start"]
            relevant_lines_end = suggestion["relevant_lines_end"]

            if not relevant_lines_start or relevant_lines_start == -1:
                if get_settings().config.verbosity_level >= 2:
                    get_logger().exception(
                        f"Failed to publish code suggestion, relevant_lines_start is {relevant_lines_start}"
                    )
                continue

            if relevant_lines_end < relevant_lines_start:
                if get_settings().config.verbosity_level >= 2:
                    get_logger().exception(
                        f"Failed to publish code suggestion, "
                        f"relevant_lines_end is {relevant_lines_end} and "
                        f"relevant_lines_start is {relevant_lines_start}"
                    )
                continue

            if relevant_lines_end > relevant_lines_start:
                # Bitbucket does not support multi-line suggestions so use a code block instead - https://jira.atlassian.com/browse/BSERV-4553
                body = body.replace("```suggestion", "```")
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
            self.publish_inline_comments(post_parameters_list)
            return True
        except Exception as e:
            if get_settings().config.verbosity_level >= 2:
                get_logger().error(f"Failed to publish code suggestion, error: {e}")
            return False

    def publish_file_comments(self, file_comments: list) -> bool:
        pass

    def is_supported(self, capability: str) -> bool:
        if capability in ['get_issue_comments', 'get_labels', 'gfm_markdown', 'publish_file_comments']:
            return False
        return True

    def set_pr(self, pr_url: str):
        self.workspace_slug, self.repo_slug, self.pr_num = self._parse_pr_url(pr_url)
        self.pr = self._get_pr()

    def get_file(self, path: str, commit_id: str):
        file_content = ""
        try:
            file_content = self.bitbucket_client.get_content_of_file(self.workspace_slug,
                                                                     self.repo_slug,
                                                                     path,
                                                                     commit_id)
        except requests.HTTPError as e:
            get_logger().debug(f"File {path} not found at commit id: {commit_id}")
        return file_content

    def get_files(self):
        changes = self.bitbucket_client.get_pull_requests_changes(self.workspace_slug, self.repo_slug, self.pr_num)
        diffstat = [change["path"]['toString'] for change in changes]
        return diffstat

    def get_diff_files(self) -> list[FilePatchInfo]:
        if self.diff_files:
            return self.diff_files

        base_sha = self.pr.toRef['latestCommit']
        head_sha = self.pr.fromRef['latestCommit']

        diff_files = []
        original_file_content_str = ""
        new_file_content_str = ""

        changes = self.bitbucket_client.get_pull_requests_changes(self.workspace_slug, self.repo_slug, self.pr_num)
        for change in changes:
            file_path = change['path']['toString']
            if not is_valid_file(file_path.split("/")[-1]):
                get_logger().info(f"Skipping a non-code file: {file_path}")
                continue

            match change['type']:
                case 'ADD':
                    edit_type = EDIT_TYPE.ADDED
                    new_file_content_str = self.get_file(file_path, head_sha)
                    if isinstance(new_file_content_str, (bytes, bytearray)):
                        new_file_content_str = new_file_content_str.decode("utf-8")
                    original_file_content_str = ""
                case 'DELETE':
                    edit_type = EDIT_TYPE.DELETED
                    new_file_content_str = ""
                    original_file_content_str = self.get_file(file_path, base_sha)
                    if isinstance(original_file_content_str, (bytes, bytearray)):
                        original_file_content_str = original_file_content_str.decode("utf-8")
                case 'RENAME':
                    edit_type = EDIT_TYPE.RENAMED
                case _:
                    edit_type = EDIT_TYPE.MODIFIED
                    original_file_content_str = self.get_file(file_path, base_sha)
                    if isinstance(original_file_content_str, (bytes, bytearray)):
                        original_file_content_str = original_file_content_str.decode("utf-8")
                    new_file_content_str = self.get_file(file_path, head_sha)
                    if isinstance(new_file_content_str, (bytes, bytearray)):
                        new_file_content_str = new_file_content_str.decode("utf-8")

            patch = load_large_diff(file_path, new_file_content_str, original_file_content_str)

            diff_files.append(
                FilePatchInfo(
                    original_file_content_str,
                    new_file_content_str,
                    patch,
                    file_path,
                    edit_type=edit_type,
                )
            )

        self.diff_files = diff_files
        return diff_files

    def publish_comment(self, pr_comment: str, is_temporary: bool = False):
        if not is_temporary:
            self.bitbucket_client.add_pull_request_comment(self.workspace_slug, self.repo_slug, self.pr_num, pr_comment)

    def remove_initial_comment(self):
        try:
            for comment in self.temp_comments:
                self.remove_comment(comment)
        except ValueError as e:
            get_logger().exception(f"Failed to remove temp comments, error: {e}")

    def remove_comment(self, comment):
        pass

    # function to create_inline_comment
    def create_inline_comment(self, body: str, relevant_file: str, relevant_line_in_file: str,
                              absolute_position: int = None):

        position, absolute_position = find_line_number_of_relevant_line_in_file(
            self.get_diff_files(),
            relevant_file.strip('`'),
            relevant_line_in_file,
            absolute_position
        )
        if position == -1:
            if get_settings().config.verbosity_level >= 2:
                get_logger().info(f"Could not find position for {relevant_file} {relevant_line_in_file}")
            subject_type = "FILE"
        else:
            subject_type = "LINE"
        path = relevant_file.strip()
        return dict(body=body, path=path, position=absolute_position) if subject_type == "LINE" else {}

    def publish_inline_comment(self, comment: str, from_line: int, file: str):
        payload = {
            "text": comment,
            "severity": "NORMAL",
            "anchor": {
                "diffType": "EFFECTIVE",
                "path": file,
                "lineType": "ADDED",
                "line": from_line,
                "fileType": "TO"
            }
        }

        try:
            self.bitbucket_client.post(self._get_pr_comments_path(), data=payload)
        except Exception as e:
            get_logger().error(f"Failed to publish inline comment to '{file}' at line {from_line}, error: {e}")
            raise e

    def get_line_link(self, relevant_file: str, relevant_line_start: int, relevant_line_end: int = None) -> str:
        if relevant_line_start == -1:
            link = f"{self.pr_url}/diff#{quote_plus(relevant_file)}"
        else:
            link = f"{self.pr_url}/diff#{quote_plus(relevant_file)}?t={relevant_line_start}"
        return link

    def generate_link_to_relevant_line_number(self, suggestion) -> str:
        try:
            relevant_file = suggestion['relevant_file'].strip('`').strip("'").rstrip()
            relevant_line_str = suggestion['relevant_line'].rstrip()
            if not relevant_line_str:
                return ""

            diff_files = self.get_diff_files()
            position, absolute_position = find_line_number_of_relevant_line_in_file \
                (diff_files, relevant_file, relevant_line_str)

            if absolute_position != -1:
                if self.pr:
                    link = f"{self.pr_url}/diff#{quote_plus(relevant_file)}?t={absolute_position}"
                    return link
                else:
                    if get_settings().config.verbosity_level >= 2:
                        get_logger().info(f"Failed adding line link to '{relevant_file}' since PR not set")
            else:
                if get_settings().config.verbosity_level >= 2:
                    get_logger().info(f"Failed adding line link to '{relevant_file}' since position not found")

            if absolute_position != -1 and self.pr_url:
                link = f"{self.pr_url}/diff#{quote_plus(relevant_file)}?t={absolute_position}"
                return link
        except Exception as e:
            if get_settings().config.verbosity_level >= 2:
                get_logger().info(f"Failed adding line link to '{relevant_file}', error: {e}")

        return ""

    def publish_inline_comments(self, comments: list[dict]):
        for comment in comments:
            if 'position' in comment:
                self.publish_inline_comment(comment['body'], comment['position'], comment['path'])
            elif 'start_line' in comment:  # multi-line comment
                # note that bitbucket does not seem to support range - only a comment on a single line - https://community.developer.atlassian.com/t/api-post-endpoint-for-inline-pull-request-comments/60452
                self.publish_inline_comment(comment['body'], comment['start_line'], comment['path'])
            elif 'line' in comment:  # single-line comment
                self.publish_inline_comment(comment['body'], comment['line'], comment['path'])
            else:
                get_logger().error(f"Could not publish inline comment: {comment}")

    def get_title(self):
        return self.pr.title

    def get_languages(self):
        return {"yaml": 0}  # devops LOL

    def get_pr_branch(self):
        return self.pr.fromRef['displayId']

    def get_pr_owner_id(self) -> str | None:
        return self.workspace_slug

    def get_pr_description_full(self):
        if hasattr(self.pr, "description"):
            return self.pr.description
        else:
            return None

    def get_user_id(self):
        return 0

    def get_issue_comments(self):
        raise NotImplementedError(
            "Bitbucket provider does not support issue comments yet"
        )

    def add_eyes_reaction(self, issue_comment_id: int, disable_eyes: bool = False) -> Optional[int]:
        return True

    def remove_reaction(self, issue_comment_id: int, reaction_id: int) -> bool:
        return True

    @staticmethod
    def _parse_bitbucket_server(url: str) -> str:
        # pr url format: f"{bitbucket_server}/projects/{project_name}/repos/{repository_name}/pull-requests/{pr_id}"
        parsed_url = urlparse(url)
        server_path = parsed_url.path.split("/projects/")
        if len(server_path) > 1:
            server_path = server_path[0].strip("/")
            return f"{parsed_url.scheme}://{parsed_url.netloc}/{server_path}".strip("/")
        return f"{parsed_url.scheme}://{parsed_url.netloc}"

    @staticmethod
    def _parse_pr_url(pr_url: str) -> Tuple[str, str, int]:
        # pr url format: f"{bitbucket_server}/projects/{project_name}/repos/{repository_name}/pull-requests/{pr_id}"
        parsed_url = urlparse(pr_url)

        path_parts = parsed_url.path.strip("/").split("/")

        try:
            projects_index = path_parts.index("projects")
        except ValueError as e:
            raise ValueError(f"The provided URL '{pr_url}' does not appear to be a Bitbucket PR URL")

        path_parts = path_parts[projects_index:]

        if len(path_parts) < 6 or path_parts[2] != "repos" or path_parts[4] != "pull-requests":
            raise ValueError(
                f"The provided URL '{pr_url}' does not appear to be a Bitbucket PR URL"
            )

        workspace_slug = path_parts[1]
        repo_slug = path_parts[3]
        try:
            pr_number = int(path_parts[5])
        except ValueError as e:
            raise ValueError(f"Unable to convert PR number '{path_parts[5]}' to integer") from e

        return workspace_slug, repo_slug, pr_number

    def _get_repo(self):
        if self.repo is None:
            self.repo = self.bitbucket_client.get_repo(self.workspace_slug, self.repo_slug)
        return self.repo

    def _get_pr(self):
        try:
            pr = self.bitbucket_client.get_pull_request(self.workspace_slug, self.repo_slug,
                                                        pull_request_id=self.pr_num)
            return type('new_dict', (object,), pr)
        except Exception as e:
            get_logger().error(f"Failed to get pull request, error: {e}")
            raise e

    def _get_pr_file_content(self, remote_link: str):
        return ""

    def get_commit_messages(self):
        return ""

    # bitbucket does not support labels
    def publish_description(self, pr_title: str, description: str):
        payload = {
            "version": self.pr.version,
            "description": description,
            "title": pr_title,
            "reviewers": self.pr.reviewers  # needs to be sent otherwise gets wiped
        }
        try:
            self.bitbucket_client.update_pull_request(self.workspace_slug, self.repo_slug, str(self.pr_num), payload)
        except Exception as e:
            get_logger().error(f"Failed to update pull request, error: {e}")
            raise e

    # bitbucket does not support labels
    def publish_labels(self, pr_types: list):
        pass

    # bitbucket does not support labels
    def get_pr_labels(self, update=False):
        pass

    def _get_pr_comments_path(self):
        return f"rest/api/latest/projects/{self.workspace_slug}/repos/{self.repo_slug}/pull-requests/{self.pr_num}/comments"
