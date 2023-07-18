import logging
from datetime import datetime
from typing import Optional, Tuple
from urllib.parse import urlparse

from github import AppAuthentication, Github, Auth

from pr_agent.config_loader import settings

from .git_provider import FilePatchInfo, GitProvider


class GithubProvider(GitProvider):
    def __init__(self, pr_url: Optional[str] = None):
        self.installation_id = settings.get("GITHUB.INSTALLATION_ID")
        self.github_client = self._get_github_client()
        self.repo = None
        self.pr_num = None
        self.pr = None
        self.github_user_id = None
        self.diff_files = None
        if pr_url:
            self.set_pr(pr_url)
            self.last_commit_id = list(self.pr.get_commits())[-1]

    def is_supported(self, capability: str) -> bool:
        return True

    def set_pr(self, pr_url: str):
        self.repo, self.pr_num = self._parse_pr_url(pr_url)
        self.pr = self._get_pr()

    def get_files(self):
        return self.pr.get_files()

    def get_diff_files(self) -> list[FilePatchInfo]:
        files = self.pr.get_files()
        diff_files = []
        for file in files:
            original_file_content_str = self._get_pr_file_content(file, self.pr.base.sha)
            new_file_content_str = self._get_pr_file_content(file, self.pr.head.sha)
            diff_files.append(FilePatchInfo(original_file_content_str, new_file_content_str, file.patch, file.filename))
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
        self.publish_inline_comments([self.create_inline_comment(body, relevant_file, relevant_line_in_file)])

    def create_inline_comment(self, body: str, relevant_file: str, relevant_line_in_file: str):
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
            subject_type = "FILE"
        else:
            subject_type = "LINE"
        path = relevant_file.strip()
        # placeholder for future API support (already supported in single inline comment)
        # return dict(body=body, path=path, position=position, subject_type=subject_type)
        return dict(body=body, path=path, position=position) if subject_type == "LINE" else {}

    def publish_inline_comments(self, comments: list[dict]):
        self.pr.create_review(commit=self.last_commit_id, comments=comments)

    def publish_code_suggestion(self, body: str,
                                relevant_file: str,
                                relevant_lines_start: int,
                                relevant_lines_end: int):
        if not relevant_lines_start or relevant_lines_start == -1:
            if settings.config.verbosity_level >= 2:
                logging.exception(f"Failed to publish code suggestion, relevant_lines_start is {relevant_lines_start}")
            return False

        if relevant_lines_end<relevant_lines_start:
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
            return Github(auth=Auth.Token(token))

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
