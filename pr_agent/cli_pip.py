from pr_agent import cli
from pr_agent.config_loader import get_settings
from pr_agent.log import setup_logger

setup_logger()


def main():
    # Fill in the following values
    provider = "github"  # GitHub provider
    user_token = "..."  # GitHub user token
    openai_key = "..."  # OpenAI key
    pr_url = "..."  # PR URL, for example 'https://github.com/Codium-ai/pr-agent/pull/809'
    command = "/review"  # Command to run (e.g. '/review', '/describe', '/ask="What is the purpose of this PR?"')

    # Setting the configurations
    get_settings().set("CONFIG.git_provider", provider)
    get_settings().set("openai.key", openai_key)
    get_settings().set("github.user_token", user_token)

    # Preparing the command
    run_command = f"--pr_url={pr_url} {command.lstrip('/')}"
    args = cli.set_parser().parse_args(run_command.split())

    # Run the command. Feedback will appear in GitHub PR comments
    cli.run(args=args)


if __name__ == '__main__':
    main()
