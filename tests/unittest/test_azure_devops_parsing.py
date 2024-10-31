from pr_agent.git_providers import AzureDevopsProvider


class TestAzureDevOpsParsing():
    def test_regular_address(self):
        pr_url = "https://dev.azure.com/organization/project/_git/repo/pullrequest/1"

        # workspace_slug, repo_slug, pr_number
        assert AzureDevopsProvider._parse_pr_url(pr_url) == ("project", "repo", 1)

    def test_visualstudio_address(self):
        pr_url = "https://organization.visualstudio.com/project/_git/repo/pullrequest/1"

        # workspace_slug, repo_slug, pr_number
        assert AzureDevopsProvider._parse_pr_url(pr_url) == ("project", "repo", 1)

    def test_parse_pr_url_no_pullrequest(self):
        invalid_url = "https://dev.azure.com/organization/project/_git/repo/branch/1"
        try:
            AzureDevopsProvider._parse_pr_url(invalid_url)
        except ValueError as e:
            assert str(e) == "The provided URL does not appear to be a Azure DevOps PR URL"
