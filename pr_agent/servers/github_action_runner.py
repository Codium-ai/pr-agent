import asyncio
import json
import os
import logging
import sys
import tempfile

from pr_agent.agent.pr_agent import PRAgent
from pr_agent.algo.utils import update_settings_from_args
from pr_agent.config_loader import get_settings, global_settings
from pr_agent.git_providers import get_git_provider
from pr_agent.tools.pr_reviewer import PRReviewer


async def run_action():
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    # Get environment variables
    GITHUB_EVENT_NAME = os.environ.get('GITHUB_EVENT_NAME')
    GITHUB_EVENT_PATH = os.environ.get('GITHUB_EVENT_PATH')
    OPENAI_KEY = os.environ.get('OPENAI_KEY') or os.environ.get('OPENAI.KEY')
    OPENAI_ORG = os.environ.get('OPENAI_ORG') or os.environ.get('OPENAI.ORG')
    GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
    get_settings().set("CONFIG.PUBLISH_OUTPUT_PROGRESS", False)


    # Check if required environment variables are set
    if not GITHUB_EVENT_NAME:
        print("GITHUB_EVENT_NAME not set")
        return
    if not GITHUB_EVENT_PATH:
        print("GITHUB_EVENT_PATH not set")
        return
    if not OPENAI_KEY:
        print("OPENAI_KEY not set")
        return
    if not GITHUB_TOKEN:
        print("GITHUB_TOKEN not set")
        return

    # Set the environment variables in the settings
    get_settings().set("OPENAI.KEY", OPENAI_KEY)
    if OPENAI_ORG:
        get_settings().set("OPENAI.ORG", OPENAI_ORG)
    get_settings().set("GITHUB.USER_TOKEN", GITHUB_TOKEN)
    get_settings().set("GITHUB.DEPLOYMENT_TYPE", "user")

    # Load the event payload
    try:
        with open(GITHUB_EVENT_PATH, 'r') as f:
            event_payload = json.load(f)
    except json.decoder.JSONDecodeError as e:
        print(f"Failed to parse JSON: {e}")
        return

    # Handle pull request event
    if GITHUB_EVENT_NAME == "pull_request":
        action = event_payload.get("action")
        if action in ["opened", "reopened"]:
            pr_url = event_payload.get("pull_request", {}).get("url")
            if pr_url:
                # First, apply repo specific settings if exists
                if get_settings().config.use_repo_settings_file:
                    repo_settings_file = None
                    try:
                        git_provider = get_git_provider()(pr_url)
                        repo_settings = git_provider.get_repo_settings()
                        logging.error(repo_settings)
                        if repo_settings:
                            repo_settings_file = None
                            fd, repo_settings_file = tempfile.mkstemp(suffix='.toml')
                            os.write(fd, repo_settings)
                            get_settings().load_file(repo_settings_file)
                    finally:
                        if repo_settings_file:
                            try:
                                os.remove(repo_settings_file)
                            except Exception as e:
                                logging.error(f"Failed to remove temporary settings file {repo_settings_file}", e)

                logging.error(get_settings())
                logging.error(get_settings().github_app.pr_commands)
                logging.error(get_settings().github_action)
                logging.error(get_settings().github_action.pr_commands)
                pr_commands = get_settings().github_action.pr_commands
                if not pr_commands:
                    await PRReviewer(pr_url).run()
                else:
                    for command in pr_commands:
                        split_command = command.split(" ")
                        command = split_command[0]
                        args = split_command[1:]
                        other_args = update_settings_from_args(args)
                        new_command = ' '.join([command] + other_args)
                        await PRAgent().handle_request(pr_url, new_command)

    # Handle issue comment event
    elif GITHUB_EVENT_NAME == "issue_comment":
        action = event_payload.get("action")
        if action in ["created", "edited"]:
            comment_body = event_payload.get("comment", {}).get("body")
            if comment_body:
                is_pr = False
                # check if issue is pull request
                if event_payload.get("issue", {}).get("pull_request"):
                    url = event_payload.get("issue", {}).get("pull_request", {}).get("url")
                    is_pr = True
                else:
                    url = event_payload.get("issue", {}).get("url")
                if url:
                    body = comment_body.strip().lower()
                    comment_id = event_payload.get("comment", {}).get("id")
                    provider = get_git_provider()(pr_url=url)
                    if is_pr:
                        await PRAgent().handle_request(url, body, notify=lambda: provider.add_eyes_reaction(comment_id))
                    else:
                        await PRAgent().handle_request(url, body)


if __name__ == '__main__':
    asyncio.run(run_action())
