import os
from pr_agent.agent.pr_agent import PRAgent
from pr_agent.config_loader import get_settings
from pr_agent.tools.pr_reviewer import PRReviewer
import asyncio

async def run_action():
    try:
        pull_request_id = os.environ.get("BITBUCKET_PR_ID", '')
        slug = os.environ.get("BITBUCKET_REPO_SLUG", '')
        workspace = os.environ.get("BITBUCKET_WORKSPACE", '')
        bearer_token = os.environ.get('BITBUCKET_BEARER_TOKEN', None)
        OPENAI_KEY = os.environ.get('OPENAI_API_KEY') or os.environ.get('OPENAI.KEY')
        OPENAI_ORG = os.environ.get('OPENAI_ORG') or os.environ.get('OPENAI.ORG')
        # Check if required environment variables are set
        if not bearer_token:
            print("BITBUCKET_BEARER_TOKEN not set")
            return
        
        if not OPENAI_KEY:
            print("OPENAI_KEY not set")
            return
        # Set the environment variables in the settings
        get_settings().set("BITBUCKET.BEARER_TOKEN", bearer_token)
        get_settings().set("OPENAI.KEY", OPENAI_KEY)
        if OPENAI_ORG:
            get_settings().set("OPENAI.ORG", OPENAI_ORG)
        if pull_request_id and slug and workspace:
            pr_url = f"https://bitbucket.org/{workspace}/{slug}/pull-requests/{pull_request_id}"
            await PRReviewer(pr_url).run()
    except Exception as e:
        print(f"An error occurred: {e}")
if __name__ == "__main__":
    asyncio.run(run_action())
