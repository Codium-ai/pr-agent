from typing import Optional

from git import Repo
from github.PullRequest import PullRequest

from pr_agent.config_loader import settings
from pr_agent.git_providers.git_provider import GitProvider, FilePatchInfo

class PullRequestMimic(PullRequest):
    '''
    This class mimics the PullRequest class from the PyGithub library.
    It only implements methods used by the GitHubProvider class.
    '''
    pass


class LocalGitProvider(GitProvider):
    '''
    This class implements the GitProvider interface for local git repositories.
    It mimics the PR functionality of the GitProvider interface, but does not require a hosted git repository.
    Instead of providing a PR url, the user provides a local branch path to generate a diff-patch.
    For the MVP it only supports the /review capability.
    '''

    def __init__(self, branch_name: Optional[str] = None):
        self.repo = Repo(settings.get("local.path"))
        compare_with = self.repo.head.commit
        if branch_name is not None:
            compare_with = self.repo.heads[branch_name].commit
        self.diff_files = None


    def is_supported(self, capability: str) -> bool:
        # TODO implement
        pass

    def get_diff_files(self) -> list[FilePatchInfo]:
        # TODO implement
        pass

    def get_files(self):
        return [change['new_path'] for change in self.mr.changes()['changes']]

    def publish_description(self, pr_title: str, pr_body: str):
        raise NotImplementedError('Publishing descriptions is not implemented for the local git provider')

    def publish_comment(self, pr_comment: str, is_temporary: bool = False):
        raise NotImplementedError('Publishing comments is not implemented for the local git provider')

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
        raise NotImplementedError('Getting PR branch is not implemented for the local git provider')

    def get_user_id(self):
        raise NotImplementedError('Getting user id is not implemented for the local git provider')

    def get_pr_description(self):
        # TODO concat an artificial PR description based on commit messages
        pass

    def get_issue_comments(self):
        raise NotImplementedError('Getting issue comments is not implemented for the local git provider')
