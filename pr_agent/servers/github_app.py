import copy
import logging
import sys
import os
import time
from typing import Any, Dict

import uvicorn
from fastapi import APIRouter, FastAPI, HTTPException, Request, Response
from starlette.middleware import Middleware
from starlette_context import context
from starlette_context.middleware import RawContextMiddleware

from pr_agent.agent.pr_agent import PRAgent
from pr_agent.algo.utils import update_settings_from_args
from pr_agent.config_loader import get_settings, global_settings
from pr_agent.git_providers import get_git_provider
from pr_agent.servers.utils import verify_signature

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
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

    response = await handle_request(body, event=request.headers.get("X-GitHub-Event", None))
    return response or {}


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
    webhook_secret = getattr(get_settings().github, 'webhook_secret', None)
    if webhook_secret:
        body_bytes = await request.body()
        signature_header = request.headers.get('x-hub-signature-256', None)
        verify_signature(body_bytes, webhook_secret, signature_header)
    return body


_duplicate_requests_cache = {}


async def handle_request(body: Dict[str, Any], event: str):
    """
    Handle incoming GitHub webhook requests.

    Args:
        body: The request body.
        event: The GitHub event type.
    """
    action = body.get("action")
    if not action:
        return {}
    agent = PRAgent()
    bot_user = get_settings().github_app.bot_user
    logging.info(f"action: '{action}'")
    logging.info(f"event: '{event}'")

    if get_settings().github_app.duplicate_requests_cache and _is_duplicate_request(body):
        return {}

    # handle all sorts of comment events (e.g. issue_comment)
    if action == 'created':
        if "comment" not in body:
            return {}
        comment_body = body.get("comment", {}).get("body")
        sender = body.get("sender", {}).get("login")
        if sender and bot_user in sender:
            logging.info(f"Ignoring comment from {bot_user} user")
            return {}
        logging.info(f"Processing comment from {sender} user")
        if "issue" in body and "pull_request" in body["issue"] and "url" in body["issue"]["pull_request"]:
            api_url = body["issue"]["pull_request"]["url"]
        elif "comment" in body and "pull_request_url" in body["comment"]:
            api_url = body["comment"]["pull_request_url"]
        else:
            return {}
        logging.info(body)
        logging.info(f"Handling comment because of event={event} and action={action}")
        comment_id = body.get("comment", {}).get("id")
        provider = get_git_provider()(pr_url=api_url)
        await agent.handle_request(api_url, comment_body, notify=lambda: provider.add_eyes_reaction(comment_id))

    # handle pull_request event:
    #   automatically review opened/reopened/ready_for_review PRs as long as they're not in draft,
    #   as well as direct review requests from the bot
    elif event == 'pull_request':
        pull_request = body.get("pull_request")
        if not pull_request:
            return {}
        api_url = pull_request.get("url")
        if not api_url:
            return {}
        if pull_request.get("draft", True) or pull_request.get("state") != "open" or pull_request.get("user", {}).get("login", "") == bot_user:
            return {}
        if action in get_settings().github_app.handle_pr_actions:
            if action == "review_requested":
                if body.get("requested_reviewer", {}).get("login", "") != bot_user:
                    return {}
                if pull_request.get("created_at") == pull_request.get("updated_at"):
                    # avoid double reviews when opening a PR for the first time
                    return {}
            logging.info(f"Performing review because of event={event} and action={action}")
            for command in get_settings().github_app.pr_commands:
                split_command = command.split(" ")
                command = split_command[0]
                args = split_command[1:]
                other_args = update_settings_from_args(args)
                new_command = ' '.join([command] + other_args)
                logging.info(body)
                logging.info(f"Performing command: {new_command}")
                await agent.handle_request(api_url, new_command)

    logging.info("event or action does not require handling")
    return {}


def _is_duplicate_request(body: Dict[str, Any]) -> bool:
    """
    In some deployments its possible to get duplicate requests if the handling is long,
    This function checks if the request is duplicate and if so - ignores it.
    """
    request_hash = hash(str(body))
    logging.info(f"request_hash: {request_hash}")
    request_time = time.monotonic()
    ttl = get_settings().github_app.duplicate_requests_cache_ttl  # in seconds
    to_delete = [key for key, key_time in _duplicate_requests_cache.items() if request_time - key_time > ttl]
    for key in to_delete:
        del _duplicate_requests_cache[key]
    is_duplicate = request_hash in _duplicate_requests_cache
    _duplicate_requests_cache[request_hash] = request_time
    if is_duplicate:
        logging.info(f"Ignoring duplicate request {request_hash}")
    return is_duplicate


@router.get("/")
async def root():
    return {"status": "ok"}


def start():
    if get_settings().github_app.override_deployment_type:
        # Override the deployment type to app
        get_settings().set("GITHUB.DEPLOYMENT_TYPE", "app")
    get_settings().set("CONFIG.PUBLISH_OUTPUT_PROGRESS", False)
    middleware = [Middleware(RawContextMiddleware)]
    app = FastAPI(middleware=middleware)
    app.include_router(router)

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "3000")))


if __name__ == '__main__':
    start()
