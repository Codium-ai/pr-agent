from pr_agent.git_providers import AzureDevopsProvider
from unittest.mock import MagicMock
from unittest.mock import patch
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

    def test_init_with_valid_pr_url(self):
        mock_client = MagicMock()
        with patch('pr_agent.git_providers.azuredevops_provider.AZURE_DEVOPS_AVAILABLE', True):
            with patch('pr_agent.git_providers.azuredevops_provider.AzureDevopsProvider._get_azure_devops_client', return_value=mock_client):
                provider = AzureDevopsProvider(pr_url="https://dev.azure.com/organization/project/_git/repo/pullrequest/1", incremental=True)
                assert provider.azure_devops_client == mock_client
                assert provider.incremental is True
                assert provider.workspace_slug == "project"
                assert provider.repo_slug == "repo"
                assert provider.pr_num == 1
                assert provider.pr is not None


    def test_init_raises_importerror_when_azuredevops_not_available(self):
        with patch('pr_agent.git_providers.azuredevops_provider.AZURE_DEVOPS_AVAILABLE', False):
            with pytest.raises(ImportError) as exc_info:
                AzureDevopsProvider(pr_url="https://dev.azure.com/organization/project/_git/repo/pullrequest/1")
            assert "Azure DevOps provider is not available" in str(exc_info.value)
