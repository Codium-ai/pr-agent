import json
from typing import Optional, Tuple
from urllib.parse import urlparse

import requests
from atlassian.bitbucket import Cloud
from starlette_context import context

from pr_agent.algo.types import FilePatchInfo, EDIT_TYPE
from ..algo.utils import find_line_number_of_relevant_line_in_file
from ..config_loader import get_settings
from ..log import get_logger
from .git_provider import GitProvider


class BitbucketProvider(GitProvider):
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
            ] = f'Bearer {get_settings().get("BITBUCKET.BEARER_TOKEN", None)}'
        s.headers["Content-Type"] = "application/json"
        self.headers = s.headers
        self.bitbucket_client = Cloud(session=s)
        self.workspace_slug = None
        self.repo_slug = None
        self.repo = None
        self.pr_num = None
        self.pr = None
        self.pr_url = pr_url
        self.temp_comments = []
        self.incremental = incremental
        self.diff_files = None
        if pr_url:
            self.set_pr(pr_url)
        self.bitbucket_comment_api_url = self.pr._BitbucketBase__data["links"]["comments"]["href"]
        self.bitbucket_pull_request_api_url = self.pr._BitbucketBase__data["links"]['self']['href']

    def get_repo_settings(self):
        try:
            url = (f"https://api.bitbucket.org/2.0/repositories/{self.workspace_slug}/{self.repo_slug}/src/"
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
        if capability in ['get_issue_comments', 'publish_inline_comments', 'get_labels', 'gfm_markdown']:
            return False
        return True

    def set_pr(self, pr_url: str):
        self.workspace_slug, self.repo_slug, self.pr_num = self._parse_pr_url(pr_url)
        self.pr = self._get_pr()

    def get_files(self):
        return [diff.new.path for diff in self.pr.diffstat()]

    def get_diff_files(self) -> list[FilePatchInfo]:
        if self.diff_files:
            return self.diff_files

        diffs = self.pr.diffstat()
        diff_split = [
            "diff --git%s" % x for x in self.pr.diff().split("diff --git") if x.strip()
        ]

        diff_files = []
        for index, diff in enumerate(diffs):
            original_file_content_str = self._get_pr_file_content(
                diff.old.get_data("links")
            )
            new_file_content_str = self._get_pr_file_content(diff.new.get_data("links"))
            file_patch_canonic_structure = FilePatchInfo(
                original_file_content_str,
                new_file_content_str,
                diff_split[index],
                diff.new.path,
            )

            if diff.data['status'] == 'added':
                file_patch_canonic_structure.edit_type = EDIT_TYPE.ADDED
            elif diff.data['status'] == 'removed':
                file_patch_canonic_structure.edit_type = EDIT_TYPE.DELETED
            elif diff.data['status'] == 'modified':
                file_patch_canonic_structure.edit_type = EDIT_TYPE.MODIFIED
            elif diff.data['status'] == 'renamed':
                file_patch_canonic_structure.edit_type = EDIT_TYPE.RENAMED
            diff_files.append(file_patch_canonic_structure)


        self.diff_files = diff_files
        return diff_files

    def get_latest_commit_url(self):
        return self.pr.data['source']['commit']['links']['html']['href']

    def get_comment_url(self, comment):
        return comment.data['links']['html']['href']

    def publish_persistent_comment(self, pr_comment: str,
                                   initial_header: str,
                                   update_header: bool = True,
                                   name='review',
                                   final_update_message=True):
        try:
            for comment in self.pr.comments():
                body = comment.raw
                if initial_header in body:
                    latest_commit_url = self.get_latest_commit_url()
                    comment_url = self.get_comment_url(comment)
                    if update_header:
                        updated_header = f"{initial_header}\n\n#### ({name.capitalize()} updated until commit {latest_commit_url})\n"
                        pr_comment_updated = pr_comment.replace(initial_header, updated_header)
                    else:
                        pr_comment_updated = pr_comment
                    get_logger().info(f"Persistent mode - updating comment {comment_url} to latest {name} message")
                    d = {"content": {"raw": pr_comment_updated}}
                    response = comment._update_data(comment.put(None, data=d))
                    if final_update_message:
                        self.publish_comment(
                            f"**[Persistent {name}]({comment_url})** updated to latest commit {latest_commit_url}")
                    return
        except Exception as e:
            get_logger().exception(f"Failed to update persistent review, error: {e}")
            pass
        self.publish_comment(pr_comment)

    def publish_comment(self, pr_comment: str, is_temporary: bool = False):
        comment = self.pr.comment(pr_comment)
        if is_temporary:
            self.temp_comments.append(comment["id"])
        return comment

    def edit_comment(self, comment, body: str):
        try:
            comment.update(body)
        except Exception as e:
            get_logger().exception(f"Failed to update comment, error: {e}")

    def remove_initial_comment(self):
        try:
            for comment in self.temp_comments:
                self.remove_comment(comment)
        except Exception as e:
            get_logger().exception(f"Failed to remove temp comments, error: {e}")

    def remove_comment(self, comment):
        try:
            self.pr.delete(f"comments/{comment}")
        except Exception as e:
            get_logger().exception(f"Failed to remove comment, error: {e}")

    # funtion to create_inline_comment
    def create_inline_comment(self, body: str, relevant_file: str, relevant_line_in_file: str, absolute_position: int = None):
        position, absolute_position = find_line_number_of_relevant_line_in_file(self.get_diff_files(),
                                                                            relevant_file.strip('`'),
                                                                            relevant_line_in_file, absolute_position)
        if position == -1:
            if get_settings().config.verbosity_level >= 2:
                get_logger().info(f"Could not find position for {relevant_file} {relevant_line_in_file}")
            subject_type = "FILE"
        else:
            subject_type = "LINE"
        path = relevant_file.strip()
        return dict(body=body, path=path, position=absolute_position) if subject_type == "LINE" else {}


    def publish_inline_comment(self, comment: str, from_line: int, file: str):
        payload = json.dumps( {
            "content": {
                "raw": comment,
            },
            "inline": {
                "to": from_line,
                "path": file
            },
        })
        response = requests.request(
            "POST", self.bitbucket_comment_api_url, data=payload, headers=self.headers
        )
        return response

    def get_line_link(self, relevant_file: str, relevant_line_start: int, relevant_line_end: int = None) -> str:
        if relevant_line_start == -1:
            link = f"{self.pr_url}/#L{relevant_file}"
        else:
            link = f"{self.pr_url}/#L{relevant_file}T{relevant_line_start}"
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

            if absolute_position != -1 and self.pr_url:
                link = f"{self.pr_url}/#L{relevant_file}T{absolute_position}"
                return link
        except Exception as e:
            if get_settings().config.verbosity_level >= 2:
                get_logger().info(f"Failed adding line link, error: {e}")

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
                get_logger().error(f"Could not publish inline comment {comment}")

    def get_title(self):
        return self.pr.title

    def get_languages(self):
        languages = {self._get_repo().get_data("language"): 0}
        return languages

    def get_pr_branch(self):
        return self.pr.source_branch

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
    def _parse_pr_url(pr_url: str) -> Tuple[str, int]:
        parsed_url = urlparse(pr_url)

        if "bitbucket.org" not in parsed_url.netloc:
            raise ValueError("The provided URL is not a valid Bitbucket URL")

        path_parts = parsed_url.path.strip("/").split("/")

        if len(path_parts) < 4 or path_parts[2] != "pull-requests":
            raise ValueError(
                "The provided URL does not appear to be a Bitbucket PR URL"
            )

        workspace_slug = path_parts[0]
        repo_slug = path_parts[1]
        try:
            pr_number = int(path_parts[3])
        except ValueError as e:
            raise ValueError("Unable to convert PR number to integer") from e

        return workspace_slug, repo_slug, pr_number

    def _get_repo(self):
        if self.repo is None:
            self.repo = self.bitbucket_client.workspaces.get(
                self.workspace_slug
            ).repositories.get(self.repo_slug)
        return self.repo

    def _get_pr(self):
        return self._get_repo().pullrequests.get(self.pr_num)

    def get_pr_file_content(self, file_path: str, branch: str) -> str:
        try:
            if branch == self.pr.source_branch:
                branch = self.pr.data["source"]["commit"]["hash"]
            elif branch == self.pr.destination_branch:
                branch = self.pr.data["destination"]["commit"]["hash"]
            url = (f"https://api.bitbucket.org/2.0/repositories/{self.workspace_slug}/{self.repo_slug}/src/"
                   f"{branch}/{file_path}")
            response = requests.request("GET", url, headers=self.headers)
            if response.status_code == 404:  # not found
                return ""
            contents = response.text
            return contents
        except Exception:
            return ""


    def create_or_update_pr_file(self, file_path: str, branch: str, contents="", message="") -> None:
        url = (f"https://api.bitbucket.org/2.0/repositories/{self.workspace_slug}/{self.repo_slug}/src/")
        if not message:
            if contents:
                message = f"Update {file_path}"
            else:
                message = f"Create {file_path}"
        files={file_path: contents}
        data={
            "message": message,
            "branch": branch
        }
        headers = {'Authorization':self.headers['Authorization']} if 'Authorization' in self.headers else {}
        try:
            requests.request("POST", url, headers=headers, data=data, files=files)
        except Exception:
            get_logger().exception(f"Failed to create empty file {file_path} in branch {branch}")

    def _get_pr_file_content(self, remote_link: str):
        return ""

    def get_commit_messages(self):
        return ""  # not implemented yet
    
    # bitbucket does not support labels
    def publish_description(self, pr_title: str, description: str):
        payload = json.dumps({
            "description": description,
            "title": pr_title

            })

        response = requests.request("PUT", self.bitbucket_pull_request_api_url, headers=self.headers, data=payload)
        try:
            if response.status_code != 200:
                get_logger().info(f"Failed to update description, error code: {response.status_code}")
        except:
            pass
        return response

    # bitbucket does not support labels
    def publish_labels(self, pr_types: list):
        pass
    
    # bitbucket does not support labels
    def get_pr_labels(self, update=False):
        pass
