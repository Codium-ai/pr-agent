import json
from typing import Optional, Tuple
from urllib.parse import urlparse

import requests
from atlassian.bitbucket import Bitbucket
from starlette_context import context

from .git_provider import GitProvider
from pr_agent.algo.types import FilePatchInfo
from ..algo.utils import load_large_diff, find_line_number_of_relevant_line_in_file
from ..config_loader import get_settings
from ..log import get_logger


class BitbucketServerProvider(GitProvider):
    def __init__(
        self, pr_url: Optional[str] = None, incremental: Optional[bool] = False
    ):
        s = requests.Session()
        try:
            bearer = context.get("bitbucket_bearer_token", None)
            s.headers["Authorization"] = f"Bearer {bearer}"
        except Exception:
            s.headers[
                "Authorization"
            ] = f'Bearer {get_settings().get("BITBUCKET_SERVER.BEARER_TOKEN", None)}'

        s.headers["Content-Type"] = "application/json"
        self.headers = s.headers
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
                                          token=get_settings().get("BITBUCKET_SERVER.BEARER_TOKEN", None))

        if pr_url:
            self.set_pr(pr_url)

    def get_repo_settings(self):
        try:
            url = (f"{self.bitbucket_server_url}/projects/{self.workspace_slug}/repos/{self.repo_slug}/src/"
                   f"{self.pr.destination_branch}/.pr_agent.toml")
            response = requests.request("GET", url, headers=self.headers)
            if response.status_code == 404:  # not found
                return ""
            contents = response.text.encode('utf-8')
            return contents
        except Exception:
            return ""

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

    def is_supported(self, capability: str) -> bool:
        if capability in ['get_issue_comments', 'get_labels', 'gfm_markdown']:
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

        commits_in_pr = self.bitbucket_client.get_pull_requests_commits(
            self.workspace_slug,
            self.repo_slug,
            self.pr_num
        )

        commit_list = list(commits_in_pr)
        base_sha, head_sha = commit_list[0]['parents'][0]['id'], commit_list[-1]['id']

        diff_files = []
        original_file_content_str = ""
        new_file_content_str = ""

        changes = self.bitbucket_client.get_pull_requests_changes(self.workspace_slug, self.repo_slug, self.pr_num)
        for change in changes:
            file_path = change['path']['toString']
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

    # funtion to create_inline_comment
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

        response = requests.post(url=self._get_pr_comments_url(), json=payload, headers=self.headers)
        return response

    def generate_link_to_relevant_line_number(self, suggestion) -> str:
        try:
            relevant_file = suggestion['relevant_file'].strip('`').strip("'").rstrip()
            relevant_line_str = suggestion['relevant_line'].rstrip()
            if not relevant_line_str:
                return ""

            diff_files = self.get_diff_files()
            position, absolute_position = find_line_number_of_relevant_line_in_file \
                (diff_files, relevant_file, relevant_line_str)

            if absolute_position != -1 and self.pr_url:
                link = f"{self.pr_url}/#L{relevant_file}T{absolute_position}"
                return link
        except Exception as e:
            if get_settings().config.verbosity_level >= 2:
                get_logger().info(f"Failed adding line link, error: {e}")

        return ""

    def publish_inline_comments(self, comments: list[dict]):
        for comment in comments:
            self.publish_inline_comment(comment['body'], comment['position'], comment['path'])

    def get_title(self):
        return self.pr.title

    def get_languages(self):
        return {"yaml": 0}  # devops LOL

    def get_pr_branch(self):
        return self.pr.fromRef['displayId']

    def get_pr_description_full(self):
        return self.pr.description

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
        parsed_url = urlparse(url)
        return f"{parsed_url.scheme}://{parsed_url.netloc}"

    @staticmethod
    def _parse_pr_url(pr_url: str) -> Tuple[str, str, int]:
        parsed_url = urlparse(pr_url)
        path_parts = parsed_url.path.strip("/").split("/")
        if len(path_parts) < 6 or path_parts[4] != "pull-requests":
            raise ValueError(
                "The provided URL does not appear to be a Bitbucket PR URL"
            )

        workspace_slug = path_parts[1]
        repo_slug = path_parts[3]
        try:
            pr_number = int(path_parts[5])
        except ValueError as e:
            raise ValueError("Unable to convert PR number to integer") from e

        return workspace_slug, repo_slug, pr_number

    def _get_repo(self):
        if self.repo is None:
            self.repo = self.bitbucket_client.get_repo(self.workspace_slug, self.repo_slug)
        return self.repo

    def _get_pr(self):
        pr = self.bitbucket_client.get_pull_request(self.workspace_slug, self.repo_slug, pull_request_id=self.pr_num)
        return type('new_dict', (object,), pr)

    def _get_pr_file_content(self, remote_link: str):
        return ""

    def get_commit_messages(self):
        def get_commit_messages(self):
            raise NotImplementedError("Get commit messages function not implemented yet.")
    # bitbucket does not support labels
    def publish_description(self, pr_title: str, description: str):
        payload = json.dumps({
            "description": description,
            "title": pr_title
        })

        response = requests.put(url=self.bitbucket_pull_request_api_url, headers=self.headers, data=payload)
        return response

    # bitbucket does not support labels
    def publish_labels(self, pr_types: list):
        pass
    
    # bitbucket does not support labels
    def get_pr_labels(self, update=False):
        pass

    def _get_pr_comments_url(self):
        return f"{self.bitbucket_server_url}/rest/api/latest/projects/{self.workspace_slug}/repos/{self.repo_slug}/pull-requests/{self.pr_num}/comments"
