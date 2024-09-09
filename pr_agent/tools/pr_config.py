from dynaconf import Dynaconf

from pr_agent.config_loader import get_settings
from pr_agent.git_providers import get_git_provider
from pr_agent.log import get_logger


class PRConfig:
    """
    The PRConfig class is responsible for listing all configuration options available for the user.
    """
    def __init__(self, pr_url: str, args=None, ai_handler=None):
        """
        Initialize the PRConfig object with the necessary attributes and objects to comment on a pull request.

        Args:
            pr_url (str): The URL of the pull request to be reviewed.
            args (list, optional): List of arguments passed to the PRReviewer class. Defaults to None.
        """
        self.git_provider = get_git_provider()(pr_url)

    async def run(self):
        get_logger().info('Getting configuration settings...')
        get_logger().info('Preparing configs...')
        pr_comment = self._prepare_pr_configs()
        if get_settings().config.publish_output:
            get_logger().info('Pushing configs...')
            self.git_provider.publish_comment(pr_comment)
            self.git_provider.remove_initial_comment()
        return ""

    def _prepare_pr_configs(self) -> str:
        conf_file = get_settings().find_file("configuration.toml")
        conf_settings = Dynaconf(settings_files=[conf_file])
        configuration_headers = [header.lower() for header in conf_settings.keys()]
        relevant_configs = {
            header: configs for header, configs in get_settings().to_dict().items()
            if (header.lower().startswith("pr_") or header.lower().startswith("config")) and header.lower() in configuration_headers
        }

        skip_keys = ['ai_disclaimer', 'ai_disclaimer_title', 'ANALYTICS_FOLDER', 'secret_provider', "skip_keys",
                          'trial_prefix_message', 'no_eligible_message', 'identity_provider', 'ALLOWED_REPOS',
                          'APP_NAME']
        extra_skip_keys = get_settings().config.get('config.skip_keys', [])
        if extra_skip_keys:
            skip_keys.extend(extra_skip_keys)

        markdown_text = "<details> <summary><strong>🛠️ PR-Agent Configurations:</strong></summary> \n\n"
        markdown_text += f"\n\n```yaml\n\n"
        for header, configs in relevant_configs.items():
            if configs:
                markdown_text += "\n\n"
                markdown_text += f"==================== {header} ===================="
            for key, value in configs.items():
                if key in skip_keys:
                    continue
                markdown_text += f"\n{header.lower()}.{key.lower()} = {repr(value) if isinstance(value, str) else value}"
                markdown_text += "  "
        markdown_text += "\n```"
        markdown_text += "\n</details>\n"
        get_logger().info(f"Possible Configurations outputted to PR comment", artifact=markdown_text)
        return markdown_text
