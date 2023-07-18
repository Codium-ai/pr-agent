import logging
from datetime import datetime
from typing import Optional, Tuple
from urllib.parse import urlparse

from github import AppAuthentication, Github

from pr_agent.config_loader import settings

from .git_provider import FilePatchInfo, GitProvider
from ..algo.language_handler import is_valid_file
from ..algo.utils import load_large_diff


class GithubProvider(GitProvider):
    def __init__(self, pr_url: Optional[str] = None, incremental: Optional[bool] = False):
        self.installation_id = settings.get("GITHUB.INSTALLATION_ID")
        self.github_client = self._get_github_client()
        self.repo = None
        self.pr_num = None
        self.pr = None
        self.github_user_id = None
        self.diff_files = None
        self.incremental = incremental
        if pr_url:
            self.set_pr(pr_url)
            self.last_commit_id = list(self.pr.get_commits())[-1]

    def is_supported(self, capability: str) -> bool:
        return True

    def set_pr(self, pr_url: str):
        self.repo, self.pr_num = self._parse_pr_url(pr_url)
        self.pr = self._get_pr()
        if self.incremental:
            self.commits = list(self.pr.get_commits())
            self.comments = list(self.pr.get_issue_comments())
            self.previous_review = None
            self.first_new_commit_sha = None
            self.incremental_files = None

            for index in range(len(self.comments) - 1, -1, -1):
                if self.comments[index].user.login == "github-actions[bot]" or \
                        self.comments[index].user.login == "CodiumAI-Agent" and \
                        self.comments[index].body.startswith("## PR Analysis"):
                            self.previous_review = self.comments[index]
                            break
            if self.previous_review:
                last_review_time = self.previous_review.created_at
                first_new_commit_index = 0
                self.last_seen_commit_sha = None
                for index in range(len(self.commits) - 1, -1, -1):
                    if self.commits[index].commit.author.date > last_review_time:
                        self.first_new_commit_sha = self.commits[index].sha
                        first_new_commit_index = index
                    else:
                        self.last_seen_commit_sha = self.commits[index].sha
                        break

                self.commits = self.commits[first_new_commit_index:]
                self.file_set = dict()
                for commit in self.commits:
                    self.file_set.update({file.filename: file for file in commit.files})

    def get_files(self):
        if self.incremental and self.file_set:
            return self.file_set.values()
        return self.pr.get_files()

    def get_diff_files(self) -> list[FilePatchInfo]:
        files = self.get_files()
        diff_files = []
        for file in files:
            if is_valid_file(file.filename):
                new_file_content_str = self._get_pr_file_content(file, self.pr.head.sha)
                patch = file.patch
                if self.incremental and self.file_set:
                    original_file_content_str = self._get_pr_file_content(file, self.last_seen_commit_sha)
                    patch = load_large_diff(file,
                                            new_file_content_str,
                                            original_file_content_str,
                                             None)
                    self.file_set[file.filename] = patch
                else:
                    original_file_content_str = self._get_pr_file_content(file, self.pr.base.sha)

                diff_files.append(
                    FilePatchInfo(original_file_content_str, new_file_content_str, patch, file.filename))
        self.diff_files = diff_files
        return diff_files

    def publish_description(self, pr_title: str, pr_body: str):
        self.pr.edit(title=pr_title, body=pr_body)
        # self.pr.create_issue_comment(pr_comment)

    def publish_comment(self, pr_comment: str, is_temporary: bool = False):
        response = self.pr.create_issue_comment(pr_comment)
        if hasattr(response, "user") and hasattr(response.user, "login"):
            self.github_user_id = response.user.login
        response.is_temporary = is_temporary
        if not hasattr(self.pr, 'comments_list'):
            self.pr.comments_list = []
        self.pr.comments_list.append(response)

    def publish_inline_comment(self, body: str, relevant_file: str, relevant_line_in_file: str):
        self.diff_files = self.diff_files if self.diff_files else self.get_diff_files()
        position = -1
        for file in self.diff_files:
            if file.filename.strip() == relevant_file:
                patch = file.patch
                patch_lines = patch.splitlines()
                for i, line in enumerate(patch_lines):
                    if relevant_line_in_file in line:
                        position = i
                        break
                    elif relevant_line_in_file[0] == '+' and relevant_line_in_file[1:].lstrip() in line:
                        # The model often adds a '+' to the beginning of the relevant_line_in_file even if originally
                        # it's a context line
                        position = i
                        break
        if position == -1:
            if settings.config.verbosity_level >= 2:
                logging.info(f"Could not find position for {relevant_file} {relevant_line_in_file}")
        else:
            path = relevant_file.strip()
            self.pr.create_review_comment(body=body, commit_id=self.last_commit_id, path=path, position=position)

    def publish_code_suggestion(self, body: str,
                                relevant_file: str,
                                relevant_lines_start: int,
                                relevant_lines_end: int):
        if not relevant_lines_start or relevant_lines_start == -1:
            if settings.config.verbosity_level >= 2:
                logging.exception(f"Failed to publish code suggestion, relevant_lines_start is {relevant_lines_start}")
            return False

        if relevant_lines_end < relevant_lines_start:
            if settings.config.verbosity_level >= 2:
                logging.exception(f"Failed to publish code suggestion, "
                                  f"relevant_lines_end is {relevant_lines_end} and "
                                  f"relevant_lines_start is {relevant_lines_start}")
            return False

        try:
            import github.PullRequestComment
            if relevant_lines_end > relevant_lines_start:
                post_parameters = {
                    "body": body,
                    "commit_id": self.last_commit_id._identity,
                    "path": relevant_file,
                    "line": relevant_lines_end,
                    "start_line": relevant_lines_start,
                    "start_side": "RIGHT",
                }
            else:  # API is different for single line comments
                post_parameters = {
                    "body": body,
                    "commit_id": self.last_commit_id._identity,
                    "path": relevant_file,
                    "line": relevant_lines_start,
                    "side": "RIGHT",
                }
            headers, data = self.pr._requester.requestJsonAndCheck(
                "POST", f"{self.pr.url}/comments", input=post_parameters
            )
            github.PullRequestComment.PullRequestComment(
                self.pr._requester, headers, data, completed=True
            )
            return True
        except Exception as e:
            if settings.config.verbosity_level >= 2:
                logging.error(f"Failed to publish code suggestion, error: {e}")
            return False

    def remove_initial_comment(self):
        try:
            for comment in self.pr.comments_list:
                if comment.is_temporary:
                    comment.delete()
        except Exception as e:
            logging.exception(f"Failed to remove initial comment, error: {e}")

    def get_title(self):
        return self.pr.title

    def get_languages(self):
        languages = self._get_repo().get_languages()
        return languages

    def get_pr_branch(self):
        return self.pr.head.ref

    def get_pr_description(self):
        return self.pr.body

    def get_user_id(self):
        if not self.github_user_id:
            try:
                self.github_user_id = self.github_client.get_user().login
            except Exception as e:
                logging.exception(f"Failed to get user id, error: {e}")
        return self.github_user_id

    def get_notifications(self, since: datetime):
        deployment_type = settings.get("GITHUB.DEPLOYMENT_TYPE", "user")

        if deployment_type != 'user':
            raise ValueError("Deployment mode must be set to 'user' to get notifications")

        notifications = self.github_client.get_user().get_notifications(since=since)
        return notifications

    def get_issue_comments(self):
        return self.pr.get_issue_comments()

    @staticmethod
    def _parse_pr_url(pr_url: str) -> Tuple[str, int]:
        parsed_url = urlparse(pr_url)

        if 'github.com' not in parsed_url.netloc:
            raise ValueError("The provided URL is not a valid GitHub URL")

        path_parts = parsed_url.path.strip('/').split('/')
        if 'api.github.com' in parsed_url.netloc:
            if len(path_parts) < 5 or path_parts[3] != 'pulls':
                raise ValueError("The provided URL does not appear to be a GitHub PR URL")
            repo_name = '/'.join(path_parts[1:3])
            try:
                pr_number = int(path_parts[4])
            except ValueError as e:
                raise ValueError("Unable to convert PR number to integer") from e
            return repo_name, pr_number

        if len(path_parts) < 4 or path_parts[2] != 'pull':
            raise ValueError("The provided URL does not appear to be a GitHub PR URL")

        repo_name = '/'.join(path_parts[:2])
        try:
            pr_number = int(path_parts[3])
        except ValueError as e:
            raise ValueError("Unable to convert PR number to integer") from e

        return repo_name, pr_number

    def _get_github_client(self):
        deployment_type = settings.get("GITHUB.DEPLOYMENT_TYPE", "user")

        if deployment_type == 'app':
            try:
                private_key = settings.github.private_key
                app_id = settings.github.app_id
            except AttributeError as e:
                raise ValueError("GitHub app ID and private key are required when using GitHub app deployment") from e
            if not self.installation_id:
                raise ValueError("GitHub app installation ID is required when using GitHub app deployment")
            auth = AppAuthentication(app_id=app_id, private_key=private_key,
                                     installation_id=self.installation_id)
            return Github(app_auth=auth)

        if deployment_type == 'user':
            try:
                token = settings.github.user_token
            except AttributeError as e:
                raise ValueError(
                    "GitHub token is required when using user deployment. See: "
                    "https://github.com/Codium-ai/pr-agent#method-2-run-from-source") from e
            return Github(token)

    def _get_repo(self):
        return self.github_client.get_repo(self.repo)

    def _get_pr(self):
        return self._get_repo().get_pull(self.pr_num)

    def _get_pr_file_content(self, file: FilePatchInfo, sha: str) -> str:
        try:
            file_content_str = str(self._get_repo().get_contents(file.filename, ref=sha).decoded_content.decode())
        except Exception:
            file_content_str = ""
        return file_content_str
