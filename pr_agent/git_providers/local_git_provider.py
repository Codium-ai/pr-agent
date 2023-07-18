import logging
from typing import List

from git import Repo
from github.PullRequest import PullRequest

from pr_agent.config_loader import settings
from pr_agent.git_providers.git_provider import GitProvider, FilePatchInfo


class PullRequestMimic():
    '''
    This class mimics the PullRequest class from the PyGithub library.
    It only implements methods used by the GitHubProvider class.
    '''

    def __init__(self, title):
        self.title = title


class LocalGitProvider(GitProvider):
    '''
    This class implements the GitProvider interface for local git repositories.
    It mimics the PR functionality of the GitProvider interface, but does not require a hosted git repository.
    Instead of providing a PR url, the user provides a local branch path to generate a diff-patch.
    For the MVP it only supports the /review capability.
    '''

    def __init__(self, branch_name):
        self.repo = Repo(settings.get("local.path"))
        self.branch_name = branch_name
        self.diff_files = None
        self.pr = PullRequestMimic(self.get_pr_title())

    def is_supported(self, capability: str) -> bool:
        # TODO implement
        pass

    def get_diff_files(self) -> list[FilePatchInfo]:
        # TODO implement
        pass

    def get_files(self) -> List[str]:
        '''
        Returns a list of files with changes in the diff.
        '''
        # Assert existence of specific branch
        branch_names = [ref.name for ref in self.repo.branches]
        if self.branch_name not in branch_names:
            raise KeyError(f"Branch: {self.branch_name} does not exist")
        branch = self.repo.branches[self.branch_name]
        # Compare the two branches
        diff_index = self.repo.head.commit.diff(branch.commit)
        # Get the list of changed files
        # TODO Why only a.side is being returned? What in case of a rename? Should we zip a-b side by side to compare them later in case of different names?
        diff_files = [item.a_path for item in diff_index]
        return diff_files

    def publish_description(self, pr_title: str, pr_body: str):
        raise NotImplementedError('Publishing descriptions is not implemented for the local git provider')

    def publish_comment(self, pr_comment: str, is_temporary: bool = False):
        logging.info(pr_comment)

    def publish_inline_comment(self, body: str, relevant_file: str, relevant_line_in_file: str):
        raise NotImplementedError('Publishing inline comments is not implemented for the local git provider')

    def create_inline_comment(self, body: str, relevant_file: str, relevant_line_in_file: str):
        raise NotImplementedError('Creating inline comments is not implemented for the local git provider')

    def publish_inline_comments(self, comments: list[dict]):
        raise NotImplementedError('Publishing inline comments is not implemented for the local git provider')

    def publish_code_suggestion(self, body: str, relevant_file: str,
                                relevant_lines_start: int, relevant_lines_end: int):
        raise NotImplementedError('Publishing code suggestions is not implemented for the local git provider')

    def remove_initial_comment(self):
        raise NotImplementedError('Removing initial comments is not implemented for the local git provider')

    def get_languages(self):
        pass

    def get_pr_branch(self):
        return self.repo.head

    def get_user_id(self):
        raise NotImplementedError('Getting user id is not implemented for the local git provider')

    def get_pr_description(self):
        commits_diff = list(self.repo.iter_commits(self.branch_name + '..HEAD'))
        # Get the commit messages and concatenate
        commit_messages = " ".join([commit.message for commit in commits_diff])
        # TODO Handle the description better - maybe use gpt-3.5 summarisation here?
        return commit_messages[:200]  # Use max 200 characters

    def get_pr_title(self):
        # TODO Handle the title better - perhaps ask the user to provide it?
        return self.get_pr_description()[:50]

    def get_issue_comments(self):
        raise NotImplementedError('Getting issue comments is not implemented for the local git provider')
