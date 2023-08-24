import logging
import os
from collections import Counter
from typing import List, Optional, Tuple
from urllib.parse import urlparse

from ..algo.language_handler import is_valid_file, language_extension_map
from ..algo.pr_processing import clip_tokens
from ..algo.utils import load_large_diff
from ..config_loader import get_settings
from .git_provider import EDIT_TYPE, FilePatchInfo, GitProvider, IncrementalPR
from pr_agent.git_providers.codecommit_client import CodeCommitClient


class PullRequestCCMimic:
    """
    This class mimics the PullRequest class from the PyGithub library for the CodeCommitProvider.
    """

    def __init__(self, title: str, diff_files: List[FilePatchInfo]):
        self.title = title
        self.diff_files = diff_files
        self.description = None
        self.source_commit = None
        self.source_branch = None  # the branch containing your new code changes
        self.destination_commit = None
        self.destination_branch = None  # the branch you are going to merge into


class CodeCommitFile:
    """
    This class represents a file in a pull request in CodeCommit.
    """

    def __init__(
        self,
        a_path: str,
        a_blob_id: str,
        b_path: str,
        b_blob_id: str,
        edit_type: EDIT_TYPE,
    ):
        self.a_path = a_path
        self.a_blob_id = a_blob_id
        self.b_path = b_path
        self.b_blob_id = b_blob_id
        self.edit_type: EDIT_TYPE = edit_type
        self.filename = b_path if b_path else a_path


class CodeCommitProvider(GitProvider):
    """
    This class implements the GitProvider interface for AWS CodeCommit repositories.
    """

    def __init__(self, pr_url: Optional[str] = None, incremental: Optional[bool] = False):
        self.codecommit_client = CodeCommitClient()
        self.aws_client = None
        self.repo_name = None
        self.pr_num = None
        self.pr = None
        self.diff_files = None
        self.git_files = None
        if pr_url:
            self.set_pr(pr_url)

    def provider_name(self):
        return "CodeCommit"

    def is_supported(self, capability: str) -> bool:
        if capability in [
            "get_issue_comments",
            "create_inline_comment",
            "publish_inline_comments",
            "get_labels",
        ]:
            return False
        return True

    def set_pr(self, pr_url: str):
        self.repo_name, self.pr_num = self._parse_pr_url(pr_url)
        self.pr = self._get_pr()

    def get_files(self) -> list[CodeCommitFile]:
        # bring files from CodeCommit only once
        if self.git_files:
            return self.git_files

        self.git_files = []
        differences = self.codecommit_client.get_differences(self.repo_name, self.pr.destination_commit, self.pr.source_commit)
        for item in differences:
            self.git_files.append(CodeCommitFile(item.before_blob_path,
                                                 item.before_blob_id,
                                                 item.after_blob_path,
                                                 item.after_blob_id,
                                                 CodeCommitProvider._get_edit_type(item.change_type)))
        return self.git_files

    def get_diff_files(self) -> list[FilePatchInfo]:
        """
        Retrieves the list of files that have been modified, added, deleted, or renamed in a pull request in CodeCommit,
        along with their content and patch information.

        Returns:
            diff_files (List[FilePatchInfo]): List of FilePatchInfo objects representing the modified, added, deleted,
            or renamed files in the merge request.
        """
        # bring files from CodeCommit only once
        if self.diff_files:
            return self.diff_files

        self.diff_files = []

        files = self.get_files()
        for diff_item in files:
            patch_filename = ""
            if diff_item.a_blob_id is not None:
                patch_filename = diff_item.a_path
                original_file_content_str = self.codecommit_client.get_file(
                    self.repo_name, diff_item.a_path, self.pr.destination_commit)
                if isinstance(original_file_content_str, (bytes, bytearray)):
                    original_file_content_str = original_file_content_str.decode("utf-8")
            else:
                original_file_content_str = ""

            if diff_item.b_blob_id is not None:
                patch_filename = diff_item.b_path
                new_file_content_str = self.codecommit_client.get_file(self.repo_name, diff_item.b_path, self.pr.source_commit)
                if isinstance(new_file_content_str, (bytes, bytearray)):
                    new_file_content_str = new_file_content_str.decode("utf-8")
            else:
                new_file_content_str = ""

            patch = load_large_diff(patch_filename, new_file_content_str, original_file_content_str)

            # Store the diffs as a list of FilePatchInfo objects
            info = FilePatchInfo(
                original_file_content_str,
                new_file_content_str,
                patch,
                diff_item.b_path,
                edit_type=diff_item.edit_type,
                old_filename=None
                if diff_item.a_path == diff_item.b_path
                else diff_item.a_path,
            )
            # Only add valid files to the diff list
            # "bad extensions" are set in the language_extensions.toml file
            # a "valid file" is one that is not in the "bad extensions" list
            if is_valid_file(info.filename):
                self.diff_files.append(info)

        return self.diff_files

    def publish_description(self, pr_title: str, pr_body: str):
        return ""  # not implemented yet

    def publish_comment(self, pr_comment: str, is_temporary: bool = False):
        if is_temporary:
            logging.info(pr_comment)
            return

        try:
            self.codecommit_client.publish_comment(
                repo_name=self.repo_name,
                pr_number=str(self.pr_num),
                destination_commit=self.pr.destination_commit,
                source_commit=self.pr.source_commit,
                comment=pr_comment,
            )
        except Exception as e:
            raise ValueError(f"CodeCommit Cannot post comment for PR: {self.pr_num}") from e

    def publish_code_suggestions(self, code_suggestions: list) -> bool:
        return [""]  # not implemented yet

    def publish_labels(self, labels):
        return [""]  # not implemented yet

    def get_labels(self):
        return [""]  # not implemented yet

    def remove_initial_comment(self):
        return ""  # not implemented yet

    def publish_inline_comment(self, body: str, relevant_file: str, relevant_line_in_file: str):
        raise NotImplementedError("CodeCommit provider does not support publishing inline comments yet")

    def create_inline_comment(self, body: str, relevant_file: str, relevant_line_in_file: str):
        raise NotImplementedError("CodeCommit provider does not support creating inline comments yet")

    def publish_inline_comments(self, comments: list[dict]):
        raise NotImplementedError("CodeCommit provider does not support publishing inline comments yet")

    def get_title(self):
        return self.pr.get("title", "")

    def get_languages(self):
        """
        Returns a dictionary of languages, containing the percentage of each language used in the PR.

        Returns:
            dict: A dictionary where each key is a language name and the corresponding value is the percentage of that language in the PR.
        """
        commit_files = self.get_files()
        filenames = [ item.filename for item in commit_files ]
        extensions = CodeCommitProvider._get_file_extensions(filenames)

        # Calculate the percentage of each file extension in the PR
        percentages = CodeCommitProvider._get_language_percentages(extensions)

        # The global language_extension_map is a dictionary of languages,
        # where each dictionary item is a BoxList of extensions.
        # We want a dictionary of extensions,
        # where each dictionary item is a language name.
        # We build that language->extension dictionary here in main_extensions_flat.
        main_extensions_flat = {}
        for language, extensions in language_extension_map.items():
            for ext in extensions:
                main_extensions_flat[ext] = language

        # Map the file extension/languages to percentages
        languages = {}
        for ext, pct in percentages.items():
            languages[main_extensions_flat.get(ext, "")] = pct

        return languages

    def get_pr_branch(self):
        return self.pr.source_branch

    def get_pr_description_full(self) -> str:
        return self.pr.description

    def get_user_id(self):
        return -1  # not implemented yet

    def get_issue_comments(self):
        raise NotImplementedError("CodeCommit provider does not support issue comments yet")

    def get_repo_settings(self):
        # a local ".pr_agent.toml" settings file is optional
        settings_filename = ".pr_agent.toml"
        return self.codecommit_client.get_file(self.repo_name, settings_filename, self.pr.source_commit, optional=True)

    def add_eyes_reaction(self, issue_comment_id: int) -> Optional[int]:
        return True

    def remove_reaction(self, issue_comment_id: int, reaction_id: int) -> bool:
        return True

    @staticmethod
    def _parse_pr_url(pr_url: str) -> Tuple[str, int]:
        # Example PR URL:
        # https://us-east-1.console.aws.amazon.com/codesuite/codecommit/repositories/__MY_REPO__/pull-requests/123456"
        parsed_url = urlparse(pr_url)

        if "us-east-1.console.aws.amazon.com" not in parsed_url.netloc:
            raise ValueError(f"The provided URL is not a valid CodeCommit URL: {pr_url}")

        path_parts = parsed_url.path.strip("/").split("/")

        if (
            len(path_parts) < 6
            or path_parts[0] != "codesuite"
            or path_parts[1] != "codecommit"
            or path_parts[2] != "repositories"
            or path_parts[4] != "pull-requests"
        ):
            raise ValueError(f"The provided URL does not appear to be a CodeCommit PR URL: {pr_url}")

        repo_name = path_parts[3]

        try:
            pr_number = int(path_parts[5])
        except ValueError as e:
            raise ValueError(f"Unable to convert PR number to integer: '{path_parts[5]}'") from e

        return repo_name, pr_number

    def _get_pr(self):
        response = self.codecommit_client.get_pr(self.pr_num)

        if len(response.targets) == 0:
            raise ValueError(f"No files found in CodeCommit PR: {self.pr_num}")

        # TODO: implement support for multiple commits in one CodeCommit PR
        #       for now, we are only using the first commit in the PR
        if len(response.targets) > 1:
            logging.warning(
                "Multiple commits in one PR is not supported for CodeCommit yet. Continuing, using the first commit only..."
            )

        # Return our object that mimics PullRequest class from the PyGithub library
        # (This strategy was copied from the LocalGitProvider)
        mimic = PullRequestCCMimic(response.title, self.diff_files)
        mimic.description = response.description
        mimic.source_commit = response.targets[0].source_commit
        mimic.source_branch = response.targets[0].source_branch
        mimic.destination_commit = response.targets[0].destination_commit
        mimic.destination_branch = response.targets[0].destination_branch

        return mimic

    def get_commit_messages(self):
        return ""  # not implemented yet

    @staticmethod
    def _get_edit_type(codecommit_change_type):
        """
        Convert the CodeCommit change type string to the EDIT_TYPE enum.
        The CodeCommit change type string is returned from the get_differences SDK method.

        Returns:
            An EDIT_TYPE enum representing the modified, added, deleted, or renamed file in the PR diff.
        """
        t = codecommit_change_type.upper()
        edit_type = None
        if t == "A":
            edit_type = EDIT_TYPE.ADDED
        elif t == "D":
            edit_type = EDIT_TYPE.DELETED
        elif t == "M":
            edit_type = EDIT_TYPE.MODIFIED
        elif t == "R":
            edit_type = EDIT_TYPE.RENAMED
        return edit_type

    @staticmethod
    def _get_file_extensions(filenames):
        """
        Return a list of file extensions from a list of filenames.
        The returned extensions will include the dot "." prefix,
        to accommodate for the dots in the existing language_extension_map settings.
        Filenames with no extension will return an empty string for the extension.
        """
        extensions = []
        for filename in filenames:
            filename, ext = os.path.splitext(filename)
            if ext:
                extensions.append(ext.lower())
            else:
                extensions.append("")
        return extensions

    @staticmethod
    def _get_language_percentages(extensions):
        """
        Return a dictionary containing the programming language name (as the key),
        and the percentage that language is used (as the value),
        given a list of file extensions.
        """
        total_files = len(extensions)
        if total_files == 0:
            return {}

        # Identify language by file extension and count
        lang_count = Counter(extensions)
        # Convert counts to percentages
        lang_percentage = {
            lang: round(count / total_files * 100) for lang, count in lang_count.items()
        }
        return lang_percentage
