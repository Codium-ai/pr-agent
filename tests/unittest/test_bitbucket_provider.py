from pr_agent.git_providers.bitbucket_provider import BitbucketProvider


class TestBitbucketProvider:
    def test_parse_pr_url(self):
        url = "https://bitbucket.org/WORKSPACE_XYZ/MY_TEST_REPO/pull-requests/321"
        workspace_slug, repo_slug, pr_number = BitbucketProvider._parse_pr_url(url)
        assert workspace_slug == "WORKSPACE_XYZ"
        assert repo_slug == "MY_TEST_REPO"
        assert pr_number == 321
