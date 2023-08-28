from pr_agent.config_loader import get_settings


def get_secret_provider():
    try:
        provider_id = get_settings().config.secret_provider
    except AttributeError as e:
        raise ValueError("secret_provider is a required attribute in the configuration file") from e
    try:
        if provider_id == 'google_cloud_storage':
            from pr_agent.secret_providers.google_cloud_storage_secret_provider import GoogleCloudStorageSecretProvider
            return GoogleCloudStorageSecretProvider()
        else:
            raise ValueError(f"Unknown secret provider: {provider_id}")
    except Exception as e:
        raise ValueError(f"Failed to initialize secret provider {provider_id}") from e
