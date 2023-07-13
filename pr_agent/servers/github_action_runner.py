import asyncio
import json
import os

from pr_agent.config_loader import settings
from pr_agent.tools.pr_reviewer import PRReviewer


async def run_action():
    GITHUB_EVENT_NAME = os.environ.get('GITHUB_EVENT_NAME', None)
    if not GITHUB_EVENT_NAME:
        print("GITHUB_EVENT_NAME not set")
        return
    GITHUB_EVENT_PATH = os.environ.get('GITHUB_EVENT_PATH', None)
    if not GITHUB_EVENT_PATH:
        print("GITHUB_EVENT_PATH not set")
        return
    event_payload = json.load(open(GITHUB_EVENT_PATH, 'r'))
    RUNNER_DEBUG = os.environ.get('RUNNER_DEBUG', None)
    if not RUNNER_DEBUG:
        print("RUNNER_DEBUG not set")
    OPENAI_KEY = os.environ.get('OPENAI_KEY', None)
    if not OPENAI_KEY:
        print("OPENAI_KEY not set")
        return
    OPENAI_ORG = os.environ.get('OPENAI_ORG', None)
    GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', None)
    if not GITHUB_TOKEN:
        print("GITHUB_TOKEN not set")
        return
    ### DEBUG
    print(event_payload)
    print(GITHUB_EVENT_NAME)
    settings.set("OPENAI.KEY", OPENAI_KEY)
    if OPENAI_ORG:
        settings.set("OPENAI.ORG", OPENAI_ORG)
    settings.set("GITHUB.USER_TOKEN", GITHUB_TOKEN)
    settings.set("GITHUB.DEPLOYMENT_TYPE", "user")
    if GITHUB_EVENT_NAME == "pull_request":
        action = event_payload.get("action", None)
        if action in ["opened", "reopened"]:
            pr_url = event_payload.get("pull_request", {}).get("url", None)
            if pr_url:
                await PRReviewer(pr_url).review()


if __name__ == '__main__':
    asyncio.run(run_action())
