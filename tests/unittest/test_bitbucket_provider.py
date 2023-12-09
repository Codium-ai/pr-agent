from pr_agent.git_providers import BitbucketServerProvider
from pr_agent.git_providers.bitbucket_provider import BitbucketProvider


class TestBitbucketProvider:
    def test_parse_pr_url(self):
        url = "https://bitbucket.org/WORKSPACE_XYZ/MY_TEST_REPO/pull-requests/321"
        workspace_slug, repo_slug, pr_number = BitbucketProvider._parse_pr_url(url)
        assert workspace_slug == "WORKSPACE_XYZ"
        assert repo_slug == "MY_TEST_REPO"
        assert pr_number == 321

    def test_bitbucket_server_pr_url(self):
        url = "https://git.onpreminstance.com/projects/AAA/repos/my-repo/pull-requests/1"
        workspace_slug, repo_slug, pr_number = BitbucketServerProvider._parse_pr_url(url)
        assert workspace_slug == "AAA"
        assert repo_slug == "my-repo"
        assert pr_number == 1
