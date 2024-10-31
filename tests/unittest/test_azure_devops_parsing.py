from pr_agent.git_providers import AzureDevopsProvider
import pytest


class TestAzureDevOpsParsing():
    def test_regular_address(self):
        pr_url = "https://dev.azure.com/organization/project/_git/repo/pullrequest/1"

        # workspace_slug, repo_slug, pr_number
        assert AzureDevopsProvider._parse_pr_url(pr_url) == ("project", "repo", 1)

    def test_visualstudio_address(self):
        pr_url = "https://organization.visualstudio.com/project/_git/repo/pullrequest/1"

        # workspace_slug, repo_slug, pr_number
        assert AzureDevopsProvider._parse_pr_url(pr_url) == ("project", "repo", 1)

    def test_provider_init_without_dependencies(self, monkeypatch):
        monkeypatch.setattr("pr_agent.git_providers.azuredevops_provider.AZURE_DEVOPS_AVAILABLE", False)
        with pytest.raises(ImportError, match="Azure DevOps provider is not available"):
            AzureDevopsProvider()


    def test_invalid_pr_url(self):
        invalid_url = "https://dev.azure.com/organization/project/invalid/url"
        with pytest.raises(ValueError, match="The provided URL does not appear to be a Azure DevOps PR URL"):
            AzureDevopsProvider._parse_pr_url(invalid_url)
