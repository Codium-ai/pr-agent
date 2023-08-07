import copy
import logging
import sys
from typing import Any, Dict

import uvicorn
from fastapi import APIRouter, FastAPI, HTTPException, Request, Response
from starlette.middleware import Middleware
from starlette_context import context
from starlette_context.middleware import RawContextMiddleware

from pr_agent.agent.pr_agent import PRAgent
from pr_agent.config_loader import get_settings, global_settings
from pr_agent.git_providers import get_git_provider
from pr_agent.servers.utils import verify_signature

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
router = APIRouter()


@router.post("/api/v1/github_webhooks")
async def handle_github_webhooks(request: Request, response: Response):
    """
    Receives and processes incoming GitHub webhook requests.
    Verifies the request signature, parses the request body, and passes it to the handle_request function for further
    processing.
    """
    logging.debug("Received a GitHub webhook")

    body = await get_body(request)

    logging.debug(f'Request body:\n{body}')
    installation_id = body.get("installation", {}).get("id")
    context["installation_id"] = installation_id
    context["settings"] = copy.deepcopy(global_settings)

    return await handle_request(body)


@router.post("/api/v1/marketplace_webhooks")
async def handle_marketplace_webhooks(request: Request, response: Response):
    body = await get_body(request)
    logging.info(f'Request body:\n{body}')

async def get_body(request):
    try:
        body = await request.json()
    except Exception as e:
        logging.error("Error parsing request body", e)
        raise HTTPException(status_code=400, detail="Error parsing request body") from e
    body_bytes = await request.body()
    signature_header = request.headers.get('x-hub-signature-256', None)
    webhook_secret = getattr(get_settings().github, 'webhook_secret', None)
    if webhook_secret:
        verify_signature(body_bytes, webhook_secret, signature_header)
    return body




async def handle_request(body: Dict[str, Any]):
    """
    Handle incoming GitHub webhook requests.

    Args:
        body: The request body.
    """
    action = body.get("action")
    if not action:
        return {}
    agent = PRAgent()

    if action == 'created':
        if "comment" not in body:
            return {}
        comment_body = body.get("comment", {}).get("body")
        sender = body.get("sender", {}).get("login")
        if sender and 'bot' in sender:
            return {}
        if "issue" not in body or "pull_request" not in body["issue"]:
            return {}
        pull_request = body["issue"]["pull_request"]
        api_url = pull_request.get("url")
        comment_id = body.get("comment", {}).get("id")
        provider = get_git_provider()(pr_url=api_url)
        provider.add_eyes_reaction(comment_id)
        await agent.handle_request(api_url, comment_body)


    elif action == "opened" or 'reopened' in action:
        pull_request = body.get("pull_request")
        if not pull_request:
            return {}
        api_url = pull_request.get("url")
        if not api_url:
            return {}
        await agent.handle_request(api_url, "/review")

    return {}


@router.get("/")
async def root():
    return {"status": "ok"}


def start():
    # Override the deployment type to app
    get_settings().set("GITHUB.DEPLOYMENT_TYPE", "app")
    get_settings().set("CONFIG.PUBLISH_OUTPUT_PROGRESS", False)
    middleware = [Middleware(RawContextMiddleware)]
    app = FastAPI(middleware=middleware)
    app.include_router(router)

    uvicorn.run(app, host="0.0.0.0", port=3000)


if __name__ == '__main__':
    start()