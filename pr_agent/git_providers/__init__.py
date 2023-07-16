from pr_agent.config_loader import settings
from pr_agent.git_providers.github_provider import GithubProvider
from pr_agent.git_providers.gitlab_provider import GitLabProvider
from pr_agent.git_providers.bitbucket_provider import BitbucketProvider

_GIT_PROVIDERS = {
    'github': GithubProvider,
    'gitlab': GitLabProvider,
    'bitbucket': BitbucketProvider,
}

def get_git_provider():
    try:
        provider_id = settings.config.git_provider
    except AttributeError as e:
        raise ValueError("git_provider is a required attribute in the configuration file") from e
    if provider_id not in _GIT_PROVIDERS:
        raise ValueError(f"Unknown git provider: {provider_id}")
    return _GIT_PROVIDERS[provider_id]
