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
        import tomli
        with open(get_settings().find_file("configuration.toml"), "rb") as conf_file:
            configuration_headers = [header.lower() for header in tomli.load(conf_file).keys()]
        relevant_configs = {
            header: configs for header, configs in get_settings().to_dict().items()
            if header.lower().startswith("pr_") and header.lower() in configuration_headers
        }
        comment_str = "Possible Configurations:"
        for header, configs in relevant_configs.items():
            if configs:
                comment_str += "\n"
            for key, value in configs.items():
                comment_str += f"\n{header.lower()}.{key.lower()} = {repr(value) if isinstance(value, str) else value}"
                comment_str += "  "
        if get_settings().config.verbosity_level >= 2:
            get_logger().info(f"comment_str:\n{comment_str}")
        return comment_str
