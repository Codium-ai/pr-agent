import itertools
from collections import Counter
from typing import List, Optional

from pr_agent.algo.utils import FilePatchInfo
from pr_agent.git_providers.git_provider import GitProvider


class InMemoryProvider(GitProvider):
    def __init__(self, head_branch: str, target_branch: str, files: List[FilePatchInfo]):
        self.head_branch = head_branch
        self.target_branch = target_branch
        self.files = files

    def is_supported(self, capability: str) -> bool:
        pass

    def get_files(self) -> list[FilePatchInfo]:
        return self.files

    def get_diff_files(self) -> list[FilePatchInfo]:
        return self.get_files()

    def publish_description(self, pr_title: str, pr_body: str):
        pass

    def publish_comment(self, pr_comment: str, is_temporary: bool = False):
        pass

    def publish_inline_comment(self, body: str, relevant_file: str, relevant_line_in_file: str):
        pass

    def create_inline_comment(self, body: str, relevant_file: str, relevant_line_in_file: str):
        pass

    def publish_inline_comments(self, comments: list[dict]):
        pass

    def publish_code_suggestions(self, code_suggestions: list) -> bool:
        pass

    def publish_labels(self, labels):
        pass

    def get_labels(self):
        pass

    def remove_initial_comment(self):
        pass

    def get_languages(self):
        language_count = Counter(file.language for file in self.files)
        return dict(language_count)

    def get_pr_branch(self):
        pass

    def get_user_id(self):
        pass

    def get_pr_description_full(self) -> str:
        pass

    def get_issue_comments(self):
        pass

    def get_repo_settings(self):
        pass

    def add_eyes_reaction(self, issue_comment_id: int) -> Optional[int]:
        pass

    def remove_reaction(self, issue_comment_id: int, reaction_id: int) -> bool:
        pass

    def get_commit_messages(self):
        pass


