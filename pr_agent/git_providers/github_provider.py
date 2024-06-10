import time
import hashlib
from datetime import datetime
from typing import Optional, Tuple
from urllib.parse import urlparse

from github import AppAuthentication, Auth, Github, GithubException
from retry import retry
from starlette_context import context

from ..algo.language_handler import is_valid_file
from ..algo.utils import load_large_diff, clip_tokens, find_line_number_of_relevant_line_in_file
from ..config_loader import get_settings
from ..log import get_logger
from ..servers.utils import RateLimitExceeded
from .git_provider import GitProvider, IncrementalPR
from pr_agent.algo.types import EDIT_TYPE, FilePatchInfo


class GithubProvider(GitProvider):
    def __init__(self, pr_url: Optional[str] = None, incremental=IncrementalPR(False)):
        self.repo_obj = None
        try:
            self.installation_id = context.get("installation_id", None)
        except Exception:
            self.installation_id = None
        self.base_url = get_settings().get("GITHUB.BASE_URL", "https://api.github.com").rstrip("/")
        self.base_url_html = self.base_url.split("api/")[0].rstrip("/") if "api/" in self.base_url else "https://github.com"
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
            self.pr_commits = list(self.pr.get_commits())
            if self.incremental.is_incremental:
                self.unreviewed_files_set = dict()
                self.get_incremental_commits()
            self.last_commit_id = self.pr_commits[-1]
            self.pr_url = self.get_pr_url() # pr_url for github actions can be as api.github.com, so we need to get the url from the pr object
        else:
            self.pr_commits = None

    def is_supported(self, capability: str) -> bool:
        return True

    def get_pr_url(self) -> str:
        return self.pr.html_url

    def set_pr(self, pr_url: str):
        self.repo, self.pr_num = self._parse_pr_url(pr_url)
        self.pr = self._get_pr()

    def get_incremental_commits(self):
        if not self.pr_commits:
            self.pr_commits = list(self.pr.get_commits())

        self.previous_review = self.get_previous_review(full=True, incremental=True)
        if self.previous_review:
            self.incremental.commits_range = self.get_commit_range()
            # Get all files changed during the commit range

            for commit in self.incremental.commits_range:
                if commit.commit.message.startswith(f"Merge branch '{self._get_repo().default_branch}'"):
                    get_logger().info(f"Skipping merge commit {commit.commit.message}")
                    continue
                self.unreviewed_files_set.update({file.filename: file for file in commit.files})
        else:
            get_logger().info("No previous review found, will review the entire PR")
            self.incremental.is_incremental = False

    def get_commit_range(self):
        last_review_time = self.previous_review.created_at
        first_new_commit_index = None
        for index in range(len(self.pr_commits) - 1, -1, -1):
            if self.pr_commits[index].commit.author.date > last_review_time:
                self.incremental.first_new_commit = self.pr_commits[index]
                first_new_commit_index = index
            else:
                self.incremental.last_seen_commit = self.pr_commits[index]
                break
        return self.pr_commits[first_new_commit_index:] if first_new_commit_index is not None else []

    def get_previous_review(self, *, full: bool, incremental: bool):
        if not (full or incremental):
            raise ValueError("At least one of full or incremental must be True")
        if not getattr(self, "comments", None):
            self.comments = list(self.pr.get_issue_comments())
        prefixes = []
        if full:
            prefixes.append("## PR Reviewer Guide")
        if incremental:
            prefixes.append("## Incremental PR Reviewer Guide")
        for index in range(len(self.comments) - 1, -1, -1):
            if any(self.comments[index].body.startswith(prefix) for prefix in prefixes):
                return self.comments[index]

    def get_files(self):
        if self.incremental.is_incremental and self.unreviewed_files_set:
            return self.unreviewed_files_set.values()
        try:
            git_files = context.get("git_files", None)
            if git_files:
                return git_files
            self.git_files = self.pr.get_files()
            context["git_files"] = self.git_files
            return self.git_files
        except Exception:
            if not self.git_files:
                self.git_files = self.pr.get_files()
            return self.git_files

    def get_num_of_files(self):
        if self.git_files:
            return self.git_files.totalCount
        else:
            return -1

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
            try:
                diff_files = context.get("diff_files", None)
                if diff_files:
                    return diff_files
            except Exception:
                pass

            if self.diff_files:
                return self.diff_files

            files = self.get_files()
            diff_files = []

            for file in files:
                if not is_valid_file(file.filename):
                    get_logger().info(f"Skipping a non-code file: {file.filename}")
                    continue

                new_file_content_str = self._get_pr_file_content(file, self.pr.head.sha)  # communication with GitHub
                patch = file.patch

                if self.incremental.is_incremental and self.unreviewed_files_set:
                    original_file_content_str = self._get_pr_file_content(file, self.incremental.last_seen_commit_sha)
                    patch = load_large_diff(file.filename, new_file_content_str, original_file_content_str)
                    self.unreviewed_files_set[file.filename] = patch
                else:
                    original_file_content_str = self._get_pr_file_content(file, self.pr.base.sha)
                    if not patch:
                        patch = load_large_diff(file.filename, new_file_content_str, original_file_content_str)

                if file.status == 'added':
                    edit_type = EDIT_TYPE.ADDED
                elif file.status == 'removed':
                    edit_type = EDIT_TYPE.DELETED
                elif file.status == 'renamed':
                    edit_type = EDIT_TYPE.RENAMED
                elif file.status == 'modified':
                    edit_type = EDIT_TYPE.MODIFIED
                else:
                    get_logger().error(f"Unknown edit type: {file.status}")
                    edit_type = EDIT_TYPE.UNKNOWN

                # count number of lines added and removed
                patch_lines = patch.splitlines(keepends=True)
                num_plus_lines = len([line for line in patch_lines if line.startswith('+')])
                num_minus_lines = len([line for line in patch_lines if line.startswith('-')])
                file_patch_canonical_structure = FilePatchInfo(original_file_content_str, new_file_content_str, patch,
                                                               file.filename, edit_type=edit_type,
                                                               num_plus_lines=num_plus_lines,
                                                               num_minus_lines=num_minus_lines,)
                diff_files.append(file_patch_canonical_structure)

            self.diff_files = diff_files
            try:
                context["diff_files"] = diff_files
            except Exception:
                pass

            return diff_files

        except GithubException.RateLimitExceededException as e:
            get_logger().error(f"Rate limit exceeded for GitHub API. Original message: {e}")
            raise RateLimitExceeded("Rate limit exceeded for GitHub API.") from e

    def publish_description(self, pr_title: str, pr_body: str):
        self.pr.edit(title=pr_title, body=pr_body)

    def get_latest_commit_url(self) -> str:
        return self.last_commit_id.html_url

    def get_comment_url(self, comment) -> str:
        return comment.html_url

    def publish_persistent_comment(self, pr_comment: str,
                                   initial_header: str,
                                   update_header: bool = True,
                                   name='review',
                                   final_update_message=True):
        prev_comments = list(self.pr.get_issue_comments())
        for comment in prev_comments:
            body = comment.body
            if body.startswith(initial_header):
                latest_commit_url = self.get_latest_commit_url()
                comment_url = self.get_comment_url(comment)
                if update_header:
                    updated_header = f"{initial_header}\n\n#### ({name.capitalize()} updated until commit {latest_commit_url})\n"
                    pr_comment_updated = pr_comment.replace(initial_header, updated_header)
                else:
                    pr_comment_updated = pr_comment
                get_logger().info(f"Persistent mode- updating comment {comment_url} to latest review message")
                response = comment.edit(pr_comment_updated)
                if final_update_message:
                    self.publish_comment(
                        f"**[Persistent {name}]({comment_url})** updated to latest commit {latest_commit_url}")
                return
        self.publish_comment(pr_comment)

    def publish_comment(self, pr_comment: str, is_temporary: bool = False):
        if is_temporary and not get_settings().config.publish_output_progress:
            get_logger().debug(f"Skipping publish_comment for temporary comment: {pr_comment}")
            return

        response = self.pr.create_issue_comment(pr_comment)
        if hasattr(response, "user") and hasattr(response.user, "login"):
            self.github_user_id = response.user.login
        response.is_temporary = is_temporary
        if not hasattr(self.pr, 'comments_list'):
            self.pr.comments_list = []
        self.pr.comments_list.append(response)
        return response

    def publish_inline_comment(self, body: str, relevant_file: str, relevant_line_in_file: str):
        self.publish_inline_comments([self.create_inline_comment(body, relevant_file, relevant_line_in_file)])


    def create_inline_comment(self, body: str, relevant_file: str, relevant_line_in_file: str,
                              absolute_position: int = None):
        position, absolute_position = find_line_number_of_relevant_line_in_file(self.diff_files,
                                                                                relevant_file.strip('`'),
                                                                                relevant_line_in_file,
                                                                                absolute_position)
        if position == -1:
            if get_settings().config.verbosity_level >= 2:
                get_logger().info(f"Could not find position for {relevant_file} {relevant_line_in_file}")
            subject_type = "FILE"
        else:
            subject_type = "LINE"
        path = relevant_file.strip()
        return dict(body=body, path=path, position=position) if subject_type == "LINE" else {}

    def publish_inline_comments(self, comments: list[dict], disable_fallback: bool = False):
        try:
            # publish all comments in a single message
            self.pr.create_review(commit=self.last_commit_id, comments=comments)
        except Exception as e:
            if get_settings().config.verbosity_level >= 2:
                get_logger().error(f"Failed to publish inline comments")

            if (getattr(e, "status", None) == 422
                    and get_settings().github.publish_inline_comments_fallback_with_verification and not disable_fallback):
                pass  # continue to try _publish_inline_comments_fallback_with_verification
            else:
                raise e # will end up with publishing the comments one by one

            try:
                self._publish_inline_comments_fallback_with_verification(comments)
            except Exception as e:
                if get_settings().config.verbosity_level >= 2:
                    get_logger().error(f"Failed to publish inline code comments fallback, error: {e}")
                raise e

    def _publish_inline_comments_fallback_with_verification(self, comments: list[dict]):
        """
        Check each inline comment separately against the GitHub API and discard of invalid comments,
        then publish all the remaining valid comments in a single review.
        For invalid comments, also try removing the suggestion part and posting the comment just on the first line.
        """
        verified_comments, invalid_comments = self._verify_code_comments(comments)

        # publish as a group the verified comments
        if verified_comments:
            try:
                self.pr.create_review(commit=self.last_commit_id, comments=verified_comments)
            except:
                pass

        # try to publish one by one the invalid comments as a one-line code comment
        if invalid_comments and get_settings().github.try_fix_invalid_inline_comments:
            fixed_comments_as_one_liner = self._try_fix_invalid_inline_comments(
                [comment for comment, _ in invalid_comments])
            for comment in fixed_comments_as_one_liner:
                try:
                    self.publish_inline_comments([comment], disable_fallback=True)
                    if get_settings().config.verbosity_level >= 2:
                        get_logger().info(f"Published invalid comment as a single line comment: {comment}")
                except:
                    if get_settings().config.verbosity_level >= 2:
                        get_logger().error(f"Failed to publish invalid comment as a single line comment: {comment}")

    def _verify_code_comment(self, comment: dict):
        is_verified = False
        e = None
        try:
            # event ="" # By leaving this blank, you set the review action state to PENDING
            input = dict(commit_id=self.last_commit_id.sha, comments=[comment])
            headers, data = self.pr._requester.requestJsonAndCheck(
                "POST", f"{self.pr.url}/reviews", input=input)
            pending_review_id = data["id"]
            is_verified = True
        except Exception as err:
            is_verified = False
            pending_review_id = None
            e = err
        if pending_review_id is not None:
            try:
                self.pr._requester.requestJsonAndCheck("DELETE", f"{self.pr.url}/reviews/{pending_review_id}")
            except Exception:
                pass
        return is_verified, e

    def _verify_code_comments(self, comments: list[dict]) -> tuple[list[dict], list[tuple[dict, Exception]]]:
        """Very each comment against the GitHub API and return 2 lists: 1 of verified and 1 of invalid comments"""
        verified_comments = []
        invalid_comments = []
        for comment in comments:
            time.sleep(1)  # for avoiding secondary rate limit
            is_verified, e = self._verify_code_comment(comment)
            if is_verified:
                verified_comments.append(comment)
            else:
                invalid_comments.append((comment, e))
        return verified_comments, invalid_comments

    def _try_fix_invalid_inline_comments(self, invalid_comments: list[dict]) -> list[dict]:
        """
        Try fixing invalid comments by removing the suggestion part and setting the comment just on the first line.
        Return only comments that have been modified in some way.
        This is a best-effort attempt to fix invalid comments, and should be verified accordingly.
        """
        import copy
        fixed_comments = []
        for comment in invalid_comments:
            try:
                fixed_comment = copy.deepcopy(comment)  # avoid modifying the original comment dict for later logging
                if "```suggestion" in comment["body"]:
                    fixed_comment["body"] = comment["body"].split("```suggestion")[0]
                if "start_line" in comment:
                    fixed_comment["line"] = comment["start_line"]
                    del fixed_comment["start_line"]
                if "start_side" in comment:
                    fixed_comment["side"] = comment["start_side"]
                    del fixed_comment["start_side"]
                if fixed_comment != comment:
                    fixed_comments.append(fixed_comment)
            except Exception as e:
                if get_settings().config.verbosity_level >= 2:
                    get_logger().error(f"Failed to fix inline comment, error: {e}")
        return fixed_comments

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
            self.publish_inline_comments(post_parameters_list)
            return True
        except Exception as e:
            if get_settings().config.verbosity_level >= 2:
                get_logger().error(f"Failed to publish code suggestion, error: {e}")
            return False

    def edit_comment(self, comment, body: str):
        comment.edit(body=body)

    def reply_to_comment_from_comment_id(self, comment_id: int, body: str):
        try:
            # self.pr.get_issue_comment(comment_id).edit(body)
            headers, data_patch = self.pr._requester.requestJsonAndCheck(
                "POST", f"{self.base_url}/repos/{self.repo}/pulls/{self.pr_num}/comments/{comment_id}/replies",
                input={"body": body}
            )
        except Exception as e:
            get_logger().exception(f"Failed to reply comment, error: {e}")

    def remove_initial_comment(self):
        try:
            for comment in getattr(self.pr, 'comments_list', []):
                if comment.is_temporary:
                    self.remove_comment(comment)
        except Exception as e:
            get_logger().exception(f"Failed to remove initial comment, error: {e}")

    def remove_comment(self, comment):
        try:
            comment.delete()
        except Exception as e:
            get_logger().exception(f"Failed to remove comment, error: {e}")

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
            # contents = self.repo_obj.get_contents(".pr_agent.toml", ref=self.pr.head.sha).decoded_content

            # more logical to take 'pr_agent.toml' from the default branch
            contents = self.repo_obj.get_contents(".pr_agent.toml").decoded_content
            return contents
        except Exception:
            return ""

    def add_eyes_reaction(self, issue_comment_id: int, disable_eyes: bool = False) -> Optional[int]:
        if disable_eyes:
            return None
        try:
            headers, data_patch = self.pr._requester.requestJsonAndCheck(
                "POST", f"{self.base_url}/repos/{self.repo}/issues/comments/{issue_comment_id}/reactions",
                input={"content": "eyes"}
            )
            return data_patch.get("id", None)
        except Exception as e:
            get_logger().exception(f"Failed to add eyes reaction, error: {e}")
            return None

    def remove_reaction(self, issue_comment_id: int, reaction_id: str) -> bool:
        try:
            # self.pr.get_issue_comment(issue_comment_id).delete_reaction(reaction_id)
            headers, data_patch = self.pr._requester.requestJsonAndCheck(
                "DELETE",
                f"{self.base_url}/repos/{self.repo}/issues/comments/{issue_comment_id}/reactions/{reaction_id}"
            )
            return True
        except Exception as e:
            get_logger().exception(f"Failed to remove eyes reaction, error: {e}")
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
            return Github(app_auth=auth, base_url=self.base_url)

        if deployment_type == 'user':
            try:
                token = get_settings().github.user_token
            except AttributeError as e:
                raise ValueError(
                    "GitHub token is required when using user deployment. See: "
                    "https://github.com/Codium-ai/pr-agent#method-2-run-from-source") from e
            return Github(auth=Auth.Token(token), base_url=self.base_url)

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

    def get_pr_file_content(self, file_path: str, branch: str) -> str:
        try:
            file_content_str = str(
                self._get_repo()
                .get_contents(file_path, ref=branch)
                .decoded_content.decode()
            )
        except Exception:
            file_content_str = ""
        return file_content_str

    def create_or_update_pr_file(
        self, file_path: str, branch: str, contents="", message=""
    ) -> None:
        try:
            file_obj = self._get_repo().get_contents(file_path, ref=branch)
            sha1=file_obj.sha
        except Exception:
            sha1=""
        self.repo_obj.update_file(
            path=file_path,
            message=message,
            content=contents,
            sha=sha1,
            branch=branch,
        )

    def _get_pr_file_content(self, file: FilePatchInfo, sha: str) -> str:
        return self.get_pr_file_content(file.filename, sha)

    def publish_labels(self, pr_types):
        try:
            label_color_map = {"Bug fix": "1d76db", "Tests": "e99695", "Bug fix with tests": "c5def5",
                               "Enhancement": "bfd4f2", "Documentation": "d4c5f9",
                               "Other": "d1bcf9"}
            post_parameters = []
            for p in pr_types:
                color = label_color_map.get(p, "d1bcf9")  # default to "Other" color
                post_parameters.append({"name": p, "color": color})
            headers, data = self.pr._requester.requestJsonAndCheck(
                "PUT", f"{self.pr.issue_url}/labels", input=post_parameters
            )
        except Exception as e:
            get_logger().exception(f"Failed to publish labels, error: {e}")

    def get_pr_labels(self, update=False):
        try:
            if not update:
                labels =self.pr.labels
                return [label.name for label in labels]
            else: # obtain the latest labels. Maybe they changed while the AI was running
                headers, labels = self.pr._requester.requestJsonAndCheck(
                    "GET", f"{self.pr.issue_url}/labels")
                return [label['name'] for label in labels]

        except Exception as e:
            get_logger().exception(f"Failed to get labels, error: {e}")
            return []

    def get_repo_labels(self):
        labels = self.repo_obj.get_labels()
        return [label for label in labels]

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
            relevant_file = suggestion['relevant_file'].strip('`').strip("'").strip('\n')
            relevant_line_str = suggestion['relevant_line'].strip('\n')
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
                link = f"{self.base_url_html}/{self.repo}/pull/{self.pr_num}/files#diff-{sha_file}R{absolute_position}"
                return link
        except Exception as e:
            if get_settings().config.verbosity_level >= 2:
                get_logger().info(f"Failed adding line link, error: {e}")

        return ""

    def get_line_link(self, relevant_file: str, relevant_line_start: int, relevant_line_end: int = None) -> str:
        sha_file = hashlib.sha256(relevant_file.encode('utf-8')).hexdigest()
        if relevant_line_start == -1:
            link = f"{self.base_url_html}/{self.repo}/pull/{self.pr_num}/files#diff-{sha_file}"
        elif relevant_line_end:
            link = f"{self.base_url_html}/{self.repo}/pull/{self.pr_num}/files#diff-{sha_file}R{relevant_line_start}-R{relevant_line_end}"
        else:
            link = f"{self.base_url_html}/{self.repo}/pull/{self.pr_num}/files#diff-{sha_file}R{relevant_line_start}"
        return link


    def get_pr_id(self):
        try:
            pr_id = f"{self.repo}/{self.pr_num}"
            return pr_id
        except:
            return ""

    def auto_approve(self) -> bool:
        try:
            res = self.pr.create_review(event="APPROVE")
            if res.state == "APPROVED":
                return True
            return False
        except Exception as e:
            get_logger().exception(f"Failed to auto-approve, error: {e}")
            return False

    def calc_pr_statistics(self, pull_request_data: dict):
        return {}
