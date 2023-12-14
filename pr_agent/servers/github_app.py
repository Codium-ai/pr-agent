import copy
import os
import asyncio.locks
from typing import Any, Dict, List, Tuple

import uvicorn
from fastapi import APIRouter, FastAPI, HTTPException, Request, Response
from starlette.middleware import Middleware
from starlette_context import context
from starlette_context.middleware import RawContextMiddleware

from pr_agent.agent.pr_agent import PRAgent
from pr_agent.algo.utils import update_settings_from_args
from pr_agent.config_loader import get_settings, global_settings
from pr_agent.git_providers import get_git_provider
from pr_agent.git_providers.utils import apply_repo_settings
from pr_agent.git_providers.git_provider import IncrementalPR
from pr_agent.log import LoggingFormat, get_logger, setup_logger
from pr_agent.servers.utils import verify_signature, DefaultDictWithTimeout

setup_logger(fmt=LoggingFormat.JSON)

router = APIRouter()


@router.post("/api/v1/github_webhooks")
async def handle_github_webhooks(request: Request, response: Response):
    """
    Receives and processes incoming GitHub webhook requests.
    Verifies the request signature, parses the request body, and passes it to the handle_request function for further
    processing.
    """
    get_logger().debug("Received a GitHub webhook")

    body = await get_body(request)

    get_logger().debug(f'Request body:\n{body}')
    installation_id = body.get("installation", {}).get("id")
    context["installation_id"] = installation_id
    context["settings"] = copy.deepcopy(global_settings)

    response = await handle_request(body, event=request.headers.get("X-GitHub-Event", None))
    return response or {}


@router.post("/api/v1/marketplace_webhooks")
async def handle_marketplace_webhooks(request: Request, response: Response):
    body = await get_body(request)
    get_logger().info(f'Request body:\n{body}')


async def get_body(request):
    try:
        body = await request.json()
    except Exception as e:
        get_logger().error("Error parsing request body", e)
        raise HTTPException(status_code=400, detail="Error parsing request body") from e
    webhook_secret = getattr(get_settings().github, 'webhook_secret', None)
    if webhook_secret:
        body_bytes = await request.body()
        signature_header = request.headers.get('x-hub-signature-256', None)
        verify_signature(body_bytes, webhook_secret, signature_header)
    return body


_duplicate_requests_cache = DefaultDictWithTimeout(ttl=get_settings().github_app.duplicate_requests_cache_ttl)
_duplicate_push_triggers = DefaultDictWithTimeout(ttl=get_settings().github_app.push_trigger_pending_tasks_ttl)
_pending_task_duplicate_push_conditions = DefaultDictWithTimeout(asyncio.locks.Condition, ttl=get_settings().github_app.push_trigger_pending_tasks_ttl)


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
    sender = body.get("sender", {}).get("login")
    log_context = {"action": action, "event": event, "sender": sender, "server_type": "github_app"}

    if get_settings().github_app.duplicate_requests_cache and _is_duplicate_request(body):
        return {}

    # handle all sorts of comment events (e.g. issue_comment)
    if action == 'created':
        if "comment" not in body:
            return {}
        comment_body = body.get("comment", {}).get("body")
        if sender and bot_user in sender:
            get_logger().info(f"Ignoring comment from {bot_user} user")
            return {}
        get_logger().info(f"Processing comment from {sender} user")
        if "issue" in body and "pull_request" in body["issue"] and "url" in body["issue"]["pull_request"]:
            api_url = body["issue"]["pull_request"]["url"]
        elif "comment" in body and "pull_request_url" in body["comment"]:
            api_url = body["comment"]["pull_request_url"]
        else:
            return {}
        log_context["api_url"] = api_url
        get_logger().info(body)
        get_logger().info(f"Handling comment because of event={event} and action={action}")
        comment_id = body.get("comment", {}).get("id")
        provider = get_git_provider()(pr_url=api_url)
        with get_logger().contextualize(**log_context):
            await agent.handle_request(api_url, comment_body, notify=lambda: provider.add_eyes_reaction(comment_id))

    # handle pull_request event:
    #   automatically review opened/reopened/ready_for_review PRs as long as they're not in draft,
    #   as well as direct review requests from the bot
    elif event == 'pull_request' and action != 'synchronize':
        pull_request, api_url = _check_pull_request_event(action, body, log_context, bot_user)
        if not (pull_request and api_url):
            return {}
        if action in get_settings().github_app.handle_pr_actions:
            if action == "review_requested":
                if body.get("requested_reviewer", {}).get("login", "") != bot_user:
                    return {}
            get_logger().info(f"Performing review for {api_url=} because of {event=} and {action=}")
            await _perform_commands("pr_commands", agent, body, api_url, log_context)

    # handle pull_request event with synchronize action - "push trigger" for new commits
    elif event == 'pull_request' and action == 'synchronize':
        pull_request, api_url = _check_pull_request_event(action, body, log_context, bot_user)
        if not (pull_request and api_url):
            return {}

        apply_repo_settings(api_url)
        if not get_settings().github_app.handle_push_trigger:
            return {}

        # TODO: do we still want to get the list of commits to filter bot/merge commits?
        before_sha = body.get("before")
        after_sha = body.get("after")
        merge_commit_sha = pull_request.get("merge_commit_sha")
        if before_sha == after_sha:
            return {}
        if get_settings().github_app.push_trigger_ignore_merge_commits and after_sha == merge_commit_sha:
            return {}
        if get_settings().github_app.push_trigger_ignore_bot_commits and body.get("sender", {}).get("login", "") == bot_user:
            return {}

        # Prevent triggering multiple times for subsequent push triggers when one is enough:
        # The first push will trigger the processing, and if there's a second push in the meanwhile it will wait.
        # Any more events will be discarded, because they will all trigger the exact same processing on the PR.
        # We let the second event wait instead of discarding it because while the first event was being processed,
        # more commits may have been pushed that led to the subsequent events,
        # so we keep just one waiting as a delegate to trigger the processing for the new commits when done waiting.
        current_active_tasks = _duplicate_push_triggers.setdefault(api_url, 0)
        max_active_tasks = 2 if get_settings().github_app.push_trigger_pending_tasks_backlog else 1
        if current_active_tasks < max_active_tasks:
            # first task can enter, and second tasks too if backlog is enabled
            get_logger().info(
                f"Continue processing push trigger for {api_url=} because there are {current_active_tasks} active tasks"
            )
            _duplicate_push_triggers[api_url] += 1
        else:
            get_logger().info(
                f"Skipping push trigger for {api_url=} because another event already triggered the same processing"
            )
            return {}
        async with _pending_task_duplicate_push_conditions[api_url]:
            if current_active_tasks == 1:
                # second task waits
                get_logger().info(
                    f"Waiting to process push trigger for {api_url=} because the first task is still in progress"
                )
                await _pending_task_duplicate_push_conditions[api_url].wait()
                get_logger().info(f"Finished waiting to process push trigger for {api_url=} - continue with flow")

        try:
            if get_settings().github_app.push_trigger_wait_for_initial_review and not get_git_provider()(api_url, incremental=IncrementalPR(True)).previous_review:
                get_logger().info(f"Skipping incremental review because there was no initial review for {api_url=} yet")
                return {}
            get_logger().info(f"Performing incremental review for {api_url=} because of {event=} and {action=}")
            await _perform_commands("push_commands", agent, body, api_url, log_context)

        finally:
            # release the waiting task block
            async with _pending_task_duplicate_push_conditions[api_url]:
                _pending_task_duplicate_push_conditions[api_url].notify(1)
                _duplicate_push_triggers[api_url] -= 1

    get_logger().info("event or action does not require handling")
    return {}


def _check_pull_request_event(action: str, body: dict, log_context: dict, bot_user: str) -> Tuple[Dict[str, Any], str]:
    invalid_result = {}, ""
    pull_request = body.get("pull_request")
    if not pull_request:
        return invalid_result
    api_url = pull_request.get("url")
    if not api_url:
        return invalid_result
    log_context["api_url"] = api_url
    if pull_request.get("draft", True) or pull_request.get("state") != "open" or pull_request.get("user", {}).get("login", "") == bot_user:
        return invalid_result
    if action in ("review_requested", "synchronize") and pull_request.get("created_at") == pull_request.get("updated_at"):
        # avoid double reviews when opening a PR for the first time
        return invalid_result
    return pull_request, api_url


async def _perform_commands(commands_conf: str, agent: PRAgent, body: dict, api_url: str, log_context: dict):
    apply_repo_settings(api_url)
    commands = get_settings().get(f"github_app.{commands_conf}")
    for command in commands:
        split_command = command.split(" ")
        command = split_command[0]
        args = split_command[1:]
        other_args = update_settings_from_args(args)
        new_command = ' '.join([command] + other_args)
        get_logger().info(body)
        get_logger().info(f"Performing command: {new_command}")
        with get_logger().contextualize(**log_context):
            await agent.handle_request(api_url, new_command)


def _is_duplicate_request(body: Dict[str, Any]) -> bool:
    """
    In some deployments its possible to get duplicate requests if the handling is long,
    This function checks if the request is duplicate and if so - ignores it.
    """
    request_hash = hash(str(body))
    get_logger().info(f"request_hash: {request_hash}")
    is_duplicate = _duplicate_requests_cache.get(request_hash, False)
    _duplicate_requests_cache[request_hash] = True
    if is_duplicate:
        get_logger().info(f"Ignoring duplicate request {request_hash}")
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
