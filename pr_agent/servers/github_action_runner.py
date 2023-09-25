import asyncio
import json
import os

from pr_agent.agent.pr_agent import PRAgent
from pr_agent.config_loader import get_settings
from pr_agent.git_providers import get_git_provider
from pr_agent.tools.pr_code_suggestions import PRCodeSuggestions
from pr_agent.tools.pr_description import PRDescription
from pr_agent.tools.pr_reviewer import PRReviewer


async def run_action():
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
                auto_review = os.environ.get('github_action.auto_review', None)
                if auto_review is None or (isinstance(auto_review, str) and auto_review.lower() == 'true'):
                    await PRReviewer(pr_url).run()
                auto_describe = os.environ.get('github_action.auto_describe', None)
                if isinstance(auto_describe, str) and auto_describe.lower() == 'true':
                    await PRDescription(pr_url).run()
                auto_improve = os.environ.get('github_action.auto_improve', None)
                if isinstance(auto_improve, str) and auto_improve.lower() == 'true':
                    await PRCodeSuggestions(pr_url).run()

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