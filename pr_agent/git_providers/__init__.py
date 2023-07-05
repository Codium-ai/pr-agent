from pr_agent.config_loader import settings
from pr_agent.git_providers.github_provider import GithubProvider

_GIT_PROVIDERS = {
    'github': GithubProvider
}

def get_git_provider():
    try:
        provider_id = settings.config.git_provider
    except AttributeError as e:
        raise ValueError("github_provider is a required attribute in the configuration file") from e
    if provider_id not in _GIT_PROVIDERS:
        raise ValueError(f"Unknown git provider: {provider_id}")
    return _GIT_PROVIDERS[provider_id]
