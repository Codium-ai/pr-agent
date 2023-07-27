from typing import Dict, Any
import logging
import sys

import uvicorn
from fastapi import APIRouter, FastAPI, HTTPException, Request, Response
from starlette.middleware import Middleware
from starlette_context import context
from starlette_context.middleware import RawContextMiddleware

from pr_agent.agent.pr_agent import PRAgent
from pr_agent.config_loader import settings
from pr_agent.servers.utils import verify_signature

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
router = APIRouter()


@router.post("/api/v1/github_webhooks")
async def handle_github_webhooks(request: Request, response: Response):
    """
    Receives and processes incoming GitHub webhook requests.
    Verifies the request signature, parses the request body, and passes it to the handle_request function for further processing.
    """
    logging.debug("Received a GitHub webhook")
    
    try:
        body = await request.json()
    except Exception as e:
        logging.error("Error parsing request body", e)
        raise HTTPException(status_code=400, detail="Error parsing request body") from e
    
    body_bytes = await request.body()
    signature_header = request.headers.get('x-hub-signature-256', None)
    
    webhook_secret = getattr(settings.github, 'webhook_secret', None)
    
    if webhook_secret:
        verify_signature(body_bytes, webhook_secret, signature_header)
    
    logging.debug(f'Request body:\n{body}')
    installation_id = body.get("installation", {}).get("id")
    context["installation_id"] = installation_id

    return await handle_request(body)


async def handle_request(body: Dict[str, Any]):
    """
    Handle incoming GitHub webhook requests.

    Args:
        body: The request body.
    """
    action = body.get("action")
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
        await agent.handle_request(api_url, comment_body)

    elif action in ["opened"] or 'reopened' in action:
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
    settings.set("GITHUB.DEPLOYMENT_TYPE", "app")
    middleware = [Middleware(RawContextMiddleware)]
    app = FastAPI(middleware=middleware)
    app.include_router(router)

    uvicorn.run(app, host="0.0.0.0", port=3000)


if __name__ == '__main__':
    start()