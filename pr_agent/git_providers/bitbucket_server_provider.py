import difflib
import re

from packaging.version import parse as parse_version
from typing import Optional, Tuple
from urllib.parse import quote_plus, urlparse

from atlassian.bitbucket import Bitbucket
from requests.exceptions import HTTPError

from ..algo.git_patch_processing import decode_if_bytes
from ..algo.language_handler import is_valid_file
from ..algo.types import EDIT_TYPE, FilePatchInfo
from ..algo.utils import (find_line_number_of_relevant_line_in_file,
                          load_large_diff)
from ..config_loader import get_settings
from ..log import get_logger
from .git_provider import GitProvider


class BitbucketServerProvider(GitProvider):
    def __init__(
            self, pr_url: Optional[str] = None, incremental: Optional[bool] = False,
            bitbucket_client: Optional[Bitbucket] = None,
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
        self.bitbucket_client = bitbucket_client or Bitbucket(url=self.bitbucket_server_url,
                                                              token=get_settings().get("BITBUCKET_SERVER.BEARER_TOKEN",
                                                                                       None))
        try:
            self.bitbucket_api_version = parse_version(self.bitbucket_client.get("rest/api/1.0/application-properties").get('version'))
        except Exception:
            self.bitbucket_api_version = None

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
            original_suggestion = suggestion.get('original_suggestion', None)  # needed for diff code
            if original_suggestion:
                try:
                    existing_code = original_suggestion['existing_code'].rstrip() + "\n"
                    improved_code = original_suggestion['improved_code'].rstrip() + "\n"
                    diff = difflib.unified_diff(existing_code.split('\n'),
                                                improved_code.split('\n'), n=999)
                    patch_orig = "\n".join(diff)
                    patch = "\n".join(patch_orig.splitlines()[5:]).strip('\n')
                    diff_code = f"\n\n```diff\n{patch.rstrip()}\n```"
                    # replace ```suggestion ... ``` with diff_code, using regex:
                    body = re.sub(r'```suggestion.*?```', diff_code, body, flags=re.DOTALL)
                except Exception as e:
                    get_logger().exception(f"Bitbucket failed to get diff code for publishing, error: {e}")
                    continue
            relevant_file = suggestion["relevant_file"]
            relevant_lines_start = suggestion["relevant_lines_start"]
            relevant_lines_end = suggestion["relevant_lines_end"]

            if not relevant_lines_start or relevant_lines_start == -1:
                get_logger().warning(
                    f"Failed to publish code suggestion, relevant_lines_start is {relevant_lines_start}"
                )
                continue

            if relevant_lines_end < relevant_lines_start:
                get_logger().warning(
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
        except HTTPError as e:
            get_logger().debug(f"File {path} not found at commit id: {commit_id}")
        return file_content

    def get_files(self):
        changes = self.bitbucket_client.get_pull_requests_changes(self.workspace_slug, self.repo_slug, self.pr_num)
        diffstat = [change["path"]['toString'] for change in changes]
        return diffstat

    #gets the best common ancestor: https://git-scm.com/docs/git-merge-base
    @staticmethod
    def get_best_common_ancestor(source_commits_list, destination_commits_list, guaranteed_common_ancestor) -> str:
        destination_commit_hashes = {commit['id'] for commit in destination_commits_list} | {guaranteed_common_ancestor}

        for commit in source_commits_list:
            for parent_commit in commit['parents']:
                if parent_commit['id'] in destination_commit_hashes:
                    return parent_commit['id']

        return guaranteed_common_ancestor

    def get_diff_files(self) -> list[FilePatchInfo]:
        if self.diff_files:
            return self.diff_files

        head_sha = self.pr.fromRef['latestCommit']

        # if Bitbucket api version is >= 8.16 then use the merge-base api for 2-way diff calculation
        if self.bitbucket_api_version is not None and self.bitbucket_api_version >= parse_version("8.16"):
            try:
                base_sha = self.bitbucket_client.get(self._get_merge_base())['id']
            except Exception as e:
                get_logger().error(f"Failed to get the best common ancestor for PR: {self.pr_url}, \nerror: {e}")
                raise e
        else:
            source_commits_list = list(self.bitbucket_client.get_pull_requests_commits(
                self.workspace_slug,
                self.repo_slug,
                self.pr_num
            ))
            # if Bitbucket api version is None or < 7.0 then do a simple diff with a guaranteed common ancestor
            base_sha = source_commits_list[-1]['parents'][0]['id']
            # if Bitbucket api version is 7.0-8.15 then use 2-way diff functionality for the base_sha
            if self.bitbucket_api_version is not None and self.bitbucket_api_version >= parse_version("7.0"):
                try:
                    destination_commits = list(
                        self.bitbucket_client.get_commits(self.workspace_slug, self.repo_slug, base_sha,
                                                          self.pr.toRef['latestCommit']))
                    base_sha = self.get_best_common_ancestor(source_commits_list, destination_commits, base_sha)
                except Exception as e:
                    get_logger().error(
                        f"Failed to get the commit list for calculating best common ancestor for PR: {self.pr_url}, \nerror: {e}")
                    raise e

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
                    new_file_content_str = decode_if_bytes(new_file_content_str)
                    original_file_content_str = ""
                case 'DELETE':
                    edit_type = EDIT_TYPE.DELETED
                    new_file_content_str = ""
                    original_file_content_str = self.get_file(file_path, base_sha)
                    original_file_content_str = decode_if_bytes(original_file_content_str)
                case 'RENAME':
                    edit_type = EDIT_TYPE.RENAMED
                case _:
                    edit_type = EDIT_TYPE.MODIFIED
                    original_file_content_str = self.get_file(file_path, base_sha)
                    original_file_content_str = decode_if_bytes(original_file_content_str)
                    new_file_content_str = self.get_file(file_path, head_sha)
                    new_file_content_str = decode_if_bytes(new_file_content_str)

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

    def publish_inline_comment(self, comment: str, from_line: int, file: str, original_suggestion=None):
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
            elif 'start_line' in comment: # multi-line comment
                # note that bitbucket does not seem to support range - only a comment on a single line - https://community.developer.atlassian.com/t/api-post-endpoint-for-inline-pull-request-comments/60452
                self.publish_inline_comment(comment['body'], comment['start_line'], comment['path'])
            elif 'line' in comment: # single-line comment
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

    def _get_merge_base(self):
        return f"rest/api/latest/projects/{self.workspace_slug}/repos/{self.repo_slug}/pull-requests/{self.pr_num}/merge-base"
