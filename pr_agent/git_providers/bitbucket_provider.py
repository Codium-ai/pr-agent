import json
from typing import Optional, Tuple
from urllib.parse import urlparse

import requests
from atlassian.bitbucket import Cloud
from starlette_context import context

from ..algo.pr_processing import find_line_number_of_relevant_line_in_file
from ..config_loader import get_settings
from ..log import get_logger
from .git_provider import FilePatchInfo, GitProvider
import ast


class BitbucketProvider(GitProvider):
    def __init__(self, pr_url: Optional[str] = None, incremental: Optional[bool] = False):
        self.set_authorization_header()
        self.headers["Content-Type"] = "application/json"
        self.bitbucket_client = Cloud(session=s)
        self.workspace_slug = None
        self.repo_slug = None
        self.repo = None
        self.pr_num = None
        self.pr = None
        self.feature = None
        self.issue_num = None
        self.issue_name = None
        self.temp_comments = []
        self.incremental = incremental
        if pr_url and 'pull' in pr_url:
            self.set_pr(pr_url)
            self.bitbucket_comment_api_url = self.pr._BitbucketBase__data["links"]["comments"]["href"]
            self.bitbucket_pull_request_api_url = self.pr._BitbucketBase__data["links"]['self']['href']

    def set_authorization_header(self):
        s = requests.Session()
        try:
            bearer = context.get("bitbucket_bearer_token")
            if not bearer:
                raise ValueError("Bearer token not found in context")
        except Exception as e:
            get_logger().warning(f"Failed to get bearer token from context: {e}")
            bearer = get_settings().get("BITBUCKET.BEARER_TOKEN")
            if not bearer:
                raise ValueError("Bearer token not found in settings")
        s.headers["Authorization"] = f"Bearer {bearer}"
        self.headers = s.headers

    def get_repo_settings(self):
        try:
            contents = self.repo_obj.get_contents(".pr_agent.toml", ref=self.pr.head.sha).decoded_content
            return contents
        except Exception:
            return ""

    def publish_code_suggestions(self, code_suggestions: list) -> bool:
        post_parameters_list = []
        for suggestion in code_suggestions:
            body = suggestion["body"]
            relevant_file = suggestion["relevant_file"]
            relevant_lines_start = suggestion["relevant_lines_start"]
            relevant_lines_end = suggestion["relevant_lines_end"]

            if not relevant_lines_start or relevant_lines_start == -1:
                if get_settings().config.verbosity_level >= 2:
                    get_logger().exception(f"Failed to publish code suggestion, relevant_lines_start is {relevant_lines_start}")
                continue

            if relevant_lines_end < relevant_lines_start:
                if get_settings().config.verbosity_level >= 2:
                    get_logger().exception(f"Failed to publish code suggestion, relevant_lines_end is {relevant_lines_end} and relevant_lines_start is {relevant_lines_start}")
                continue

            if relevant_lines_end > relevant_lines_start:
                post_parameters = {
                    "body": body,
                    "path": relevant_file,
                    "line": relevant_lines_end,
                    "start_line": relevant_lines_start,
                    "start_side": "RIGHT",
                }
            else:
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
        return capability not in ['get_issue_comments', 'publish_inline_comments', 'get_labels', 'gfm_markdown']

    def set_pr(self, pr_url: str):
        self.workspace_slug, self.repo_slug, self.pr_num = self._parse_pr_url(pr_url)
        self.pr = self._get_pr()

    def get_files(self):
        return [diff.new.path for diff in self.pr.diffstat()]

    def get_diff_files(self) -> list[FilePatchInfo]:
        diffs = self.pr.diffstat()
        diff_split = ["diff --git%s" % x for x in self.pr.diff().split("diff --git") if x.strip()]
        diff_files = []
        for index, diff in enumerate(diffs):
            original_file_content_str = self._get_pr_file_content(diff.old.get_data("links"))
            new_file_content_str = self._get_pr_file_content(diff.new.get_data("links"))
            diff_files.append(FilePatchInfo(original_file_content_str, new_file_content_str, diff_split[index], diff.new.path))
        return diff_files

    def publish_comment(self, pr_comment: str, is_temporary: bool = False):
        comment = self.pr.comment(pr_comment)
        if is_temporary:
            self.temp_comments.append(comment["id"])

    def remove_initial_comment(self):
        try:
            for comment in self.temp_comments:
                self.pr.delete(f"comments/{comment}")
        except Exception as e:
            get_logger().exception(f"Failed to remove temp comments, error: {e}")

    def create_inline_comment(self, body: str, relevant_file: str, relevant_line_in_file: str):
        position, absolute_position = find_line_number_of_relevant_line_in_file(self.get_diff_files(), relevant_file.strip('`'), relevant_line_in_file)
        if position == -1:
            if get_settings().config.verbosity_level >= 2:
                get_logger().info(f"Could not find position for {relevant_file} {relevant_line_in_file}")
            subject_type = "FILE"
        else:
            subject_type = "LINE"
        path = relevant_file.strip()
        return dict(body=body, path=path, position=absolute_position) if subject_type == "LINE" else {}

    def publish_inline_comment(self, comment: str, from_line: int, file: str):
        payload = json.dumps({"content": {"raw": comment}, "inline": {"to": from_line, "path": file}})
        response = requests.request("POST", self.bitbucket_comment_api_url, data=payload, headers=self.headers)
        return response

    def publish_inline_comments(self, comments: list[dict]):
        for comment in comments:
            self.publish_inline_comment(comment['body'], comment['start_line'], comment['path'])

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
        raise NotImplementedError("Bitbucket provider does not support issue comments yet")

    def add_eyes_reaction(self, issue_comment_id: int) -> Optional[int]:
        return True

    def remove_reaction(self, issue_comment_id: int, reaction_id: int) -> bool:
        return True

    @staticmethod
    def _parse_pr_url(pr_url: str) -> Tuple[str, str, int]:
        parsed_url = urlparse(pr_url)
        if "bitbucket.org" not in parsed_url.netloc:
            raise ValueError("The provided URL is not a valid Bitbucket URL")
        path_parts = parsed_url.path.strip("/").split("/")
        if len(path_parts) < 4 or path_parts[2] != "pull-requests":
            raise ValueError("The provided URL does not appear to be a Bitbucket PR URL")
        workspace_slug = path_parts[0]
        repo_slug = path_parts[1]
        try:
            pr_number = int(path_parts[3])
        except ValueError:
            raise ValueError("Unable to convert PR number to integer")
        return workspace_slug, repo_slug, pr_number

    @staticmethod
    def _parse_issue_url(issue_url: str) -> Tuple[str, int]:
        parsed_url = urlparse(issue_url)
        if "bitbucket.org" not in parsed_url.netloc:
            raise ValueError("The provided URL is not a valid Bitbucket URL")
        path_parts = parsed_url.path.strip('/').split('/')
        if len(path_parts) < 5 or path_parts[2] != "issues":
            raise ValueError("The provided URL does not appear to be a Bitbucket issue URL")
        workspace_slug = path_parts[0]
        repo_slug = path_parts[1]
        try:
            issue_number = int(path_parts[3])
        except ValueError:
            raise ValueError("Unable to convert issue number to integer")
        return workspace_slug, repo_slug, issue_number

    def _get_repo(self):
        if self.repo is None:
            self.repo = self.bitbucket_client.workspaces.get(self.workspace_slug).repositories.get(self.repo_slug)
        return self.repo

    def _get_pr(self):
        return self._get_repo().pullrequests.get(self.pr_num)

    def _get_pr_file_content(self, remote_link: str) -> str:
        response = requests.get(remote_link, headers=self.headers)
        response.raise_for_status()
        return response.text

    def get_commit_messages(self) -> str:
        commits = self.pr.commits()
        return "\n".join(commit["message"] for commit in commits)

    def publish_description(self, pr_title: str, description: str):
        payload = json.dumps({"description": description, "title": pr_title})
        response = requests.request("PUT", self.bitbucket_pull_request_api_url, headers=self.headers, data=payload)
        return response

    def get_issue(self, issue_url):
        workspace_slug, repo_name, original_issue_number = self._parse_issue_url(issue_url)
        issue = self.bitbucket_client.repositories.get(workspace_slug, repo_name).issues.get(original_issue_number)
        return issue, original_issue_number

    def get_issue_url(self, issue):
        return issue._BitbucketBase__data['links']['html']['href']

    def get_issue_body(self, issue):
        return issue.content['raw']

    def get_issue_number(self, issue):
        return issue.id

    def get_issue_comment_body(self, comment):
        return comment['content']['raw']

    def get_issue_comment_user(self, comment):
        return comment['user']['display_name']

    def get_issue_created_at(self, issue):
        return str(issue.created_on)

    def get_username(self, issue, issue_url):
        workspace_slug, repo_name, original_issue_numbers = self._parse_issue_url(issue_url)
        return workspace_slug

    def get_repo_issues(self, repo_obj):
        return repo_obj._Repository__issues.each()

    def parse_issue_url_and_get_comments(self, issue: str) -> list[dict]:
        workspace_slug, repo_name, original_issue_number = self._parse_issue_url(issue)
        url = f"https://api.bitbucket.org/2.0/repositories/{workspace_slug}/{repo_name}/issues/{original_issue_number}/comments"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json().get('values', [])
        except requests.RequestException as e:
            get_logger().error(f"Failed to get comments for issue {issue}: {e}")
            return []

    def parse_issue_url_and_create_comment(self, similar_issues_str, issue_url, original_issue_number):
        workspace_slug, repo_name, original_issue_number = self._parse_issue_url(issue_url)
        url = f"https://api.bitbucket.org/2.0/repositories/{workspace_slug}/{repo_name}/issues/{original_issue_number}/comments"
        payload = json.dumps({"content": {"raw": similar_issues_str}})
        headers = {'Authorization': f'Bearer {get_settings().get("BITBUCKET.BEARER_TOKEN", None)}', 'Content-Type': 'application/json'}
        response = requests.request("POST", url, headers=headers, data=payload)

    def parse_issue_url_and_get_repo_obj(self, issue_url):
        workspace_slug, repo_name, original_issue_number = self._parse_issue_url(issue_url)
        return self.bitbucket_client.repositories.get(workspace_slug, repo_name)

    def get_repo_name_for_indexing(self, repo_obj):
        return repo_obj._BitbucketBase__data['full_name'].lower().replace('/', '-').replace('_/', '-')

    def check_if_issue_pull_request(self, issue):
        return False

    def get_issue_numbers_from_list(self, issues: str) -> list[int]:
        int_list = ast.literal_eval(issues)
        return [int(x) for x in int_list]

    def parse_issue_url_and_get_similar_issues(self, issue_url, issue_number_similar):
        workspace_slug, repo_name, original_issue_number = self._parse_issue_url(issue_url)
        issue = self.bitbucket_client.repositories.get(workspace_slug, repo_name).issues.get(issue_number_similar)
        return issue

    def parse_issue_url_and_get_main_issue(self, issue_url):
        workspace_slug, repo_name, original_issue_number = self._parse_issue_url(issue_url)
        issue = self.bitbucket_client.repositories.get(workspace_slug, repo_name).issues.get(original_issue_number)
        return issue
