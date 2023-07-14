from abc import ABC, abstractmethod
from dataclasses import dataclass

# enum EDIT_TYPE (ADDED, DELETED, MODIFIED, RENAMED)
from enum import Enum
class EDIT_TYPE(Enum):
    ADDED = 1
    DELETED = 2
    MODIFIED = 3
    RENAMED = 4

@dataclass
class FilePatchInfo:
    base_file: str
    head_file: str
    patch: str
    filename: str
    tokens: int = -1
    edit_type: EDIT_TYPE = EDIT_TYPE.MODIFIED
    old_filename: str = None


class GitProvider(ABC):
    @abstractmethod
    def get_diff_files(self) -> list[FilePatchInfo]:
        pass

    @abstractmethod
    def publish_description(self, pr_title: str, pr_body: str):
        pass

    @abstractmethod
    def publish_comment(self, pr_comment: str, is_temporary: bool = False):
        pass

    @abstractmethod
    def publish_inline_comment(self, body: str, relevant_file: str, relevant_line_in_file: str):
        pass

    @abstractmethod
    def remove_initial_comment(self):
        pass

    @abstractmethod
    def get_languages(self):
        pass

    @abstractmethod
    def get_pr_branch(self):
        pass

    @abstractmethod
    def get_user_id(self):
        pass

    @abstractmethod
    def get_pr_description(self):
        pass


def get_main_pr_language(languages, files) -> str:
    """
    Get the main language of the commit. Return an empty string if cannot determine.
    """
    main_language_str = ""
    try:
        top_language = max(languages, key=languages.get).lower()

        # validate that the specific commit uses the main language
        extension_list = []
        for file in files:
            extension_list.append(file.filename.rsplit('.')[-1])

        # get the most common extension
        most_common_extension = max(set(extension_list), key=extension_list.count)

        # look for a match. TBD: add more languages, do this systematically
        if most_common_extension == 'py' and top_language == 'python' or \
                most_common_extension == 'js' and top_language == 'javascript' or \
                most_common_extension == 'ts' and top_language == 'typescript' or \
                most_common_extension == 'go' and top_language == 'go' or \
                most_common_extension == 'java' and top_language == 'java' or \
                most_common_extension == 'c' and top_language == 'c' or \
                most_common_extension == 'cpp' and top_language == 'c++' or \
                most_common_extension == 'cs' and top_language == 'c#' or \
                most_common_extension == 'swift' and top_language == 'swift' or \
                most_common_extension == 'php' and top_language == 'php' or \
                most_common_extension == 'rb' and top_language == 'ruby' or \
                most_common_extension == 'rs' and top_language == 'rust' or \
                most_common_extension == 'scala' and top_language == 'scala' or \
                most_common_extension == 'kt' and top_language == 'kotlin' or \
                most_common_extension == 'pl' and top_language == 'perl' or \
                most_common_extension == 'swift' and top_language == 'swift':
            main_language_str = top_language

    except Exception:
        pass

    return main_language_str
