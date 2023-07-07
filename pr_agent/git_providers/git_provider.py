
from abc import ABC
from dataclasses import dataclass


@dataclass
class FilePatchInfo:
    base_file: str
    head_file: str
    patch: str
    filename: str
    tokens: int = -1


class GitProvider(ABC):
    def get_diff_files(self) -> list[FilePatchInfo]:
        pass

    def publish_comment(self, pr_comment: str, is_temporary: bool = False):
        pass

    def remove_initial_comment(self):
        pass

    def get_languages(self):
        pass

    def get_main_pr_language(self) -> str:
        pass

    def get_pr_branch(self):
        pass

    def get_user_id(self):
        pass

    def get_pr_description():
        pass