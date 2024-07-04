
from dotenv import load_dotenv
load_dotenv()
import os

from pr_agent import cli
from pr_agent.config_loader import get_settings


def main():
    # Fill in the following values
    provider = "github"  # GitHub provider
    pr_url = "https://github.com/multicloudlab/pr-agent-test/pull/1"  # PR URL, for example 'https://github.com/Codium-ai/pr-agent/pull/809'
    command = "/improve"  # Command to run (e.g. '/review', '/describe', '/ask="What is the purpose of this PR?"')


    # Setting the configurations
    get_settings().set("CONFIG.git_provider", provider)
    # get_settings().set("openai.key", os.getnenv("openai_key"))
    get_settings().set("watsonx.url", os.getenv("watsonx_url"))
    get_settings().set("watsonx.iam_api_key", os.getenv("iam_api_key"))
    get_settings().set("watsonx.project_id", os.getenv("project_id"))
    get_settings().set("github.user_token", os.getenv("user_token"))

    # Run the command. Feedback will appear in GitHub PR comments
    cli.run_command(pr_url, command)


if __name__ == '__main__':
    main()
