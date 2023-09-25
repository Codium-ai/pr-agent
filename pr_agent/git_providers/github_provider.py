import logging
import hashlib

from datetime import datetime
from typing import Optional, Tuple, Any
from urllib.parse import urlparse

from github import AppAuthentication, Auth, Github, GithubException, Reaction
from retry import retry
from starlette_context import context

from .git_provider import FilePatchInfo, GitProvider, IncrementalPR
from ..algo.language_handler import is_valid_file
from ..algo.utils import load_large_diff
from ..algo.pr_processing import find_line_number_of_relevant_line_in_file, clip_tokens
from ..config_loader import get_settings
from ..servers.utils import RateLimitExceeded


class GithubProvider(GitProvider):
    def __init__(self, pr_url: Optional[str] = None, incremental=IncrementalPR(False)):
        self.repo_obj = None
        try:
            self.installation_id = context.get("installation_id", None)
        except Exception:
            self.installation_id = None
        self.github_client = self._get_github_client()
        self.repo = None
        self.pr_num = None
        self.pr = None
        self.github_user_id = None
        self.diff_files = None
        self.git_files = None
        self.incremental = incremental
        if pr_url and 'pull' in pr_url:
            self.set_pr(pr_url)
            self.last_commit_id = list(self.pr.get_commits())[-1]

    def is_supported(self, capability: str) -> bool:
        return True

    def get_pr_url(self) -> str:
        return f"https://github.com/{self.repo}/pull/{self.pr_num}"

    def set_pr(self, pr_url: str):
        self.repo, self.pr_num = self._parse_pr_url(pr_url)
        self.pr = self._get_pr()
        if self.incremental.is_incremental:
            self.get_incremental_commits()

    def get_incremental_commits(self):
        self.commits = list(self.pr.get_commits())

        self.get_previous_review()
        if self.previous_review:
            self.incremental.commits_range = self.get_commit_range()
            # Get all files changed during the commit range
            self.file_set = dict()
            for commit in self.incremental.commits_range:
                if commit.commit.message.startswith(f"Merge branch '{self._get_repo().default_branch}'"):
                    logging.info(f"Skipping merge commit {commit.commit.message}")
                    continue
                self.file_set.update({file.filename: file for file in commit.files})

    def get_commit_range(self):
        last_review_time = self.previous_review.created_at
        first_new_commit_index = 0
        for index in range(len(self.commits) - 1, -1, -1):
            if self.commits[index].commit.author.date > last_review_time:
                self.incremental.first_new_commit_sha = self.commits[index].sha
                first_new_commit_index = index
            else:
                self.incremental.last_seen_commit_sha = self.commits[index].sha
                break
        return self.commits[first_new_commit_index:]

    def get_previous_review(self):
        self.previous_review = None
        self.comments = list(self.pr.get_issue_comments())
        for index in range(len(self.comments) - 1, -1, -1):
            if self.comments[index].body.startswith("## PR Analysis"):
                self.previous_review = self.comments[index]
                break

    def get_files(self):
        if self.incremental.is_incremental and self.file_set:
            return self.file_set.values()
        if not self.git_files:
            # bring files from GitHub only once
            self.git_files = self.pr.get_files()
        return self.git_files

    @retry(exceptions=RateLimitExceeded,
           tries=get_settings().github.ratelimit_retries, delay=2, backoff=2, jitter=(1, 3))
    def get_diff_files(self) -> list[FilePatchInfo]:
        """
        Retrieves the list of files that have been modified, added, deleted, or renamed in a pull request in GitHub,
        along with their content and patch information.

        Returns:
            diff_files (List[FilePatchInfo]): List of FilePatchInfo objects representing the modified, added, deleted,
            or renamed files in the merge request.
        """
        try:
            if self.diff_files:
                return self.diff_files

            files = self.get_files()
            diff_files = []

            for file in files:
                if not is_valid_file(file.filename):
                    continue

                new_file_content_str = self._get_pr_file_content(file, self.pr.head.sha)  # communication with GitHub
                patch = file.patch

                if self.incremental.is_incremental and self.file_set:
                    original_file_content_str = self._get_pr_file_content(file, self.incremental.last_seen_commit_sha)
                    patch = load_large_diff(file.filename, new_file_content_str, original_file_content_str)
                    self.file_set[file.filename] = patch
                else:
                    original_file_content_str = self._get_pr_file_content(file, self.pr.base.sha)
                    if not patch:
                        patch = load_large_diff(file.filename, new_file_content_str, original_file_content_str)

                diff_files.append(FilePatchInfo(original_file_content_str, new_file_content_str, patch, file.filename))

            self.diff_files = diff_files
            return diff_files

        except GithubException.RateLimitExceededException as e:
            logging.error(f"Rate limit exceeded for GitHub API. Original message: {e}")
            raise RateLimitExceeded("Rate limit exceeded for GitHub API.") from e

    def publish_description(self, pr_title: str, pr_body: str):
        self.pr.edit(title=pr_title, body=pr_body)

    def publish_comment(self, pr_comment: str, is_temporary: bool = False):
        if is_temporary and not get_settings().config.publish_output_progress:
            logging.debug(f"Skipping publish_comment for temporary comment: {pr_comment}")
            return
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
        position, absolute_position = find_line_number_of_relevant_line_in_file(self.diff_files, relevant_file.strip('`'), relevant_line_in_file)
        if position == -1:
            if get_settings().config.verbosity_level >= 2:
                logging.info(f"Could not find position for {relevant_file} {relevant_line_in_file}")
            subject_type = "FILE"
        else:
            subject_type = "LINE"
        path = relevant_file.strip()
        return dict(body=body, path=path, position=position) if subject_type == "LINE" else {}

    def publish_inline_comments(self, comments: list[dict]):
        self.pr.create_review(commit=self.last_commit_id, comments=comments)

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
                    logging.exception(
                        f"Failed to publish code suggestion, relevant_lines_start is {relevant_lines_start}")
                continue

            if relevant_lines_end < relevant_lines_start:
                if get_settings().config.verbosity_level >= 2:
                    logging.exception(f"Failed to publish code suggestion, "
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
            self.pr.create_review(commit=self.last_commit_id, comments=post_parameters_list)
            return True
        except Exception as e:
            if get_settings().config.verbosity_level >= 2:
                logging.error(f"Failed to publish code suggestion, error: {e}")
            return False

    def remove_initial_comment(self):
        try:
            for comment in getattr(self.pr, 'comments_list', []):
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

    def get_pr_description_full(self):
        return self.pr.body

    def get_user_id(self):
        if not self.github_user_id:
            try:
                self.github_user_id = self.github_client.get_user().raw_data['login']
            except Exception as e:
                self.github_user_id = ""
                # logging.exception(f"Failed to get user id, error: {e}")
        return self.github_user_id

    def get_notifications(self, since: datetime):
        deployment_type = get_settings().get("GITHUB.DEPLOYMENT_TYPE", "user")

        if deployment_type != 'user':
            raise ValueError("Deployment mode must be set to 'user' to get notifications")

        notifications = self.github_client.get_user().get_notifications(since=since)
        return notifications

    def get_issue_comments(self):
        return self.pr.get_issue_comments()

    def get_repo_settings(self):
        try:
            contents = self.repo_obj.get_contents(".pr_agent.toml", ref=self.pr.head.sha).decoded_content
            return contents
        except Exception:
            return ""

    def add_eyes_reaction(self, issue_comment_id: int) -> Optional[int]:
        try:
            reaction = self.pr.get_issue_comment(issue_comment_id).create_reaction("eyes")
            return reaction.id
        except Exception as e:
            logging.exception(f"Failed to add eyes reaction, error: {e}")
            return None

    def remove_reaction(self, issue_comment_id: int, reaction_id: int) -> bool:
        try:
            self.pr.get_issue_comment(issue_comment_id).delete_reaction(reaction_id)
            return True
        except Exception as e:
            logging.exception(f"Failed to remove eyes reaction, error: {e}")
            return False


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

    @staticmethod
    def _parse_issue_url(issue_url: str) -> Tuple[str, int]:
        parsed_url = urlparse(issue_url)

        if 'github.com' not in parsed_url.netloc:
            raise ValueError("The provided URL is not a valid GitHub URL")

        path_parts = parsed_url.path.strip('/').split('/')
        if 'api.github.com' in parsed_url.netloc:
            if len(path_parts) < 5 or path_parts[3] != 'issues':
                raise ValueError("The provided URL does not appear to be a GitHub ISSUE URL")
            repo_name = '/'.join(path_parts[1:3])
            try:
                issue_number = int(path_parts[4])
            except ValueError as e:
                raise ValueError("Unable to convert issue number to integer") from e
            return repo_name, issue_number

        if len(path_parts) < 4 or path_parts[2] != 'issues':
            raise ValueError("The provided URL does not appear to be a GitHub PR issue")

        repo_name = '/'.join(path_parts[:2])
        try:
            issue_number = int(path_parts[3])
        except ValueError as e:
            raise ValueError("Unable to convert issue number to integer") from e

        return repo_name, issue_number

    def _get_github_client(self):
        deployment_type = get_settings().get("GITHUB.DEPLOYMENT_TYPE", "user")

        if deployment_type == 'app':
            try:
                private_key = get_settings().github.private_key
                app_id = get_settings().github.app_id
            except AttributeError as e:
                raise ValueError("GitHub app ID and private key are required when using GitHub app deployment") from e
            if not self.installation_id:
                raise ValueError("GitHub app installation ID is required when using GitHub app deployment")
            auth = AppAuthentication(app_id=app_id, private_key=private_key,
                                     installation_id=self.installation_id)
            return Github(app_auth=auth)

        if deployment_type == 'user':
            try:
                token = get_settings().github.user_token
            except AttributeError as e:
                raise ValueError(
                    "GitHub token is required when using user deployment. See: "
                    "https://github.com/Codium-ai/pr-agent#method-2-run-from-source") from e
            return Github(auth=Auth.Token(token))

    def _get_repo(self):
        if hasattr(self, 'repo_obj') and \
                hasattr(self.repo_obj, 'full_name') and \
                self.repo_obj.full_name == self.repo:
            return self.repo_obj
        else:
            self.repo_obj = self.github_client.get_repo(self.repo)
            return self.repo_obj


    def _get_pr(self):
        return self._get_repo().get_pull(self.pr_num)

    def _get_pr_file_content(self, file: FilePatchInfo, sha: str) -> str:
        try:
            file_content_str = str(self._get_repo().get_contents(file.filename, ref=sha).decoded_content.decode())
        except Exception:
            file_content_str = ""
        return file_content_str

    def publish_labels(self, pr_types):
        try:
            label_color_map = {"Bug fix": "1d76db", "Tests": "e99695", "Bug fix with tests": "c5def5",
                               "Refactoring": "bfdadc", "Enhancement": "bfd4f2", "Documentation": "d4c5f9",
                               "Other": "d1bcf9"}
            post_parameters = []
            for p in pr_types:
                color = label_color_map.get(p, "d1bcf9")  # default to "Other" color
                post_parameters.append({"name": p, "color": color})
            headers, data = self.pr._requester.requestJsonAndCheck(
                "PUT", f"{self.pr.issue_url}/labels", input=post_parameters
            )
        except Exception as e:
            logging.exception(f"Failed to publish labels, error: {e}")

    def get_labels(self):
        try:
            return [label.name for label in self.pr.labels]
        except Exception as e:
            logging.exception(f"Failed to get labels, error: {e}")
            return []

    def get_commit_messages(self):
        """
        Retrieves the commit messages of a pull request.

        Returns:
            str: A string containing the commit messages of the pull request.
        """
        max_tokens = get_settings().get("CONFIG.MAX_COMMITS_TOKENS", None)
        try:
            commit_list = self.pr.get_commits()
            commit_messages = [commit.commit.message for commit in commit_list]
            commit_messages_str = "\n".join([f"{i + 1}. {message}" for i, message in enumerate(commit_messages)])
        except Exception:
            commit_messages_str = ""
        if max_tokens:
            commit_messages_str = clip_tokens(commit_messages_str, max_tokens)
        return commit_messages_str

    def generate_link_to_relevant_line_number(self, suggestion) -> str:
        try:
            relevant_file = suggestion['relevant file'].strip('`').strip("'")
            relevant_line_str = suggestion['relevant line']
            if not relevant_line_str:
                return ""

            position, absolute_position = find_line_number_of_relevant_line_in_file \
                (self.diff_files, relevant_file, relevant_line_str)

            if absolute_position != -1:
                # # link to right file only
                # link = f"https://github.com/{self.repo}/blob/{self.pr.head.sha}/{relevant_file}" \
                #        + "#" + f"L{absolute_position}"

                # link to diff
                sha_file = hashlib.sha256(relevant_file.encode('utf-8')).hexdigest()
                link = f"https://github.com/{self.repo}/pull/{self.pr_num}/files#diff-{sha_file}R{absolute_position}"
                return link
        except Exception as e:
            if get_settings().config.verbosity_level >= 2:
                logging.info(f"Failed adding line link, error: {e}")

        return ""

    def get_pr_id(self):
        try:
            pr_id = f"{self.repo}/{self.pr_num}"
            return pr_id
        except:
            return ""
