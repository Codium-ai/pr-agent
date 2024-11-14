import base64
import copy
import hashlib
import json
import os
import re
import time

import jwt
import requests
import uvicorn
from fastapi import APIRouter, FastAPI, Request, Response
from starlette.background import BackgroundTasks
from starlette.middleware import Middleware
from starlette.responses import JSONResponse
from starlette_context import context
from starlette_context.middleware import RawContextMiddleware

from pr_agent.agent.pr_agent import PRAgent
from pr_agent.algo.utils import update_settings_from_args
from pr_agent.config_loader import get_settings, global_settings
from pr_agent.git_providers.utils import apply_repo_settings
from pr_agent.identity_providers import get_identity_provider
from pr_agent.identity_providers.identity_provider import Eligibility
from pr_agent.log import LoggingFormat, get_logger, setup_logger
from pr_agent.secret_providers import get_secret_provider
from pr_agent.servers.github_action_runner import get_setting_or_env, is_true
from pr_agent.tools.pr_code_suggestions import PRCodeSuggestions
from pr_agent.tools.pr_description import PRDescription
from pr_agent.tools.pr_reviewer import PRReviewer

setup_logger(fmt=LoggingFormat.JSON, level="DEBUG")
router = APIRouter()
secret_provider = get_secret_provider() if get_settings().get("CONFIG.SECRET_PROVIDER") else None


async def get_bearer_token(shared_secret: str, client_key: str):
    try:
        now = int(time.time())
        url = "https://bitbucket.org/site/oauth2/access_token"
        canonical_url = "GET&/site/oauth2/access_token&"
        qsh = hashlib.sha256(canonical_url.encode("utf-8")).hexdigest()
        app_key = get_settings().bitbucket.app_key

        payload = {
            "iss": app_key,
            "iat": now,
            "exp": now + 240,
            "qsh": qsh,
            "sub": client_key,
            }
        token = jwt.encode(payload, shared_secret, algorithm="HS256")
        payload = 'grant_type=urn%3Abitbucket%3Aoauth2%3Ajwt'
        headers = {
            'Authorization': f'JWT {token}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        bearer_token = response.json()["access_token"]
        return bearer_token
    except Exception as e:
        get_logger().error(f"Failed to get bearer token: {e}")
        raise e

@router.get("/")
async def handle_manifest(request: Request, response: Response):
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    manifest = open(os.path.join(cur_dir, "atlassian-connect.json"), "rt").read()
    try:
        manifest = manifest.replace("app_key", get_settings().bitbucket.app_key)
        manifest = manifest.replace("base_url", get_settings().bitbucket.base_url)
    except:
        get_logger().error("Failed to replace api_key in Bitbucket manifest, trying to continue")
    manifest_obj = json.loads(manifest)
    return JSONResponse(manifest_obj)


async def _perform_commands_bitbucket(commands_conf: str, agent: PRAgent, api_url: str, log_context: dict, data: dict):
    apply_repo_settings(api_url)
    if data.get("event", "") == "pullrequest:created":
        if not should_process_pr_logic(data):
            return
    commands = get_settings().get(f"bitbucket_app.{commands_conf}", {})
    get_settings().set("config.is_auto_command", True)
    for command in commands:
        try:
            split_command = command.split(" ")
            command = split_command[0]
            args = split_command[1:]
            other_args = update_settings_from_args(args)
            new_command = ' '.join([command] + other_args)
            get_logger().info(f"Performing command: {new_command}")
            with get_logger().contextualize(**log_context):
                await agent.handle_request(api_url, new_command)
        except Exception as e:
            get_logger().error(f"Failed to perform command {command}: {e}")


def is_bot_user(data) -> bool:
    try:
        actor = data.get("data", {}).get("actor", {})
        # allow actor type: user . if it's "AppUser" or "team" then it is a bot user
        allowed_actor_types = {"user"}
        if actor and actor["type"].lower() not in allowed_actor_types:
            get_logger().info(f"BitBucket actor type is not 'user', skipping: {actor}")
            return True
    except Exception as e:
        get_logger().error(f"Failed 'is_bot_user' logic: {e}")
    return False


def should_process_pr_logic(data) -> bool:
    try:
        pr_data = data.get("data", {}).get("pullrequest", {})
        title = pr_data.get("title", "")
        source_branch = pr_data.get("source", {}).get("branch", {}).get("name", "")
        target_branch = pr_data.get("destination", {}).get("branch", {}).get("name", "")

        # logic to ignore PRs with specific titles
        if title:
            ignore_pr_title_re = get_settings().get("CONFIG.IGNORE_PR_TITLE", [])
            if not isinstance(ignore_pr_title_re, list):
                ignore_pr_title_re = [ignore_pr_title_re]
            if ignore_pr_title_re and any(re.search(regex, title) for regex in ignore_pr_title_re):
                get_logger().info(f"Ignoring PR with title '{title}' due to config.ignore_pr_title setting")
                return False

        ignore_pr_source_branches = get_settings().get("CONFIG.IGNORE_PR_SOURCE_BRANCHES", [])
        ignore_pr_target_branches = get_settings().get("CONFIG.IGNORE_PR_TARGET_BRANCHES", [])
        if (ignore_pr_source_branches or ignore_pr_target_branches):
            if any(re.search(regex, source_branch) for regex in ignore_pr_source_branches):
                get_logger().info(
                    f"Ignoring PR with source branch '{source_branch}' due to config.ignore_pr_source_branches settings")
                return False
            if any(re.search(regex, target_branch) for regex in ignore_pr_target_branches):
                get_logger().info(
                    f"Ignoring PR with target branch '{target_branch}' due to config.ignore_pr_target_branches settings")
                return False
    except Exception as e:
        get_logger().error(f"Failed 'should_process_pr_logic': {e}")
    return True


@router.post("/webhook")
async def handle_github_webhooks(background_tasks: BackgroundTasks, request: Request):
    app_name = get_settings().get("CONFIG.APP_NAME", "Unknown")
    log_context = {"server_type": "bitbucket_app", "app_name": app_name}
    get_logger().debug(request.headers)
    jwt_header = request.headers.get("authorization", None)
    if jwt_header:
        input_jwt = jwt_header.split(" ")[1]
    data = await request.json()
    get_logger().debug(data)

    async def inner():
        try:
            # ignore bot users
            if is_bot_user(data):
                return "OK"

            # Check if the PR should be processed
            if data.get("event", "") == "pullrequest:created":
                if not should_process_pr_logic(data):
                    return "OK"

            # Get the username of the sender
            actor = data.get("data", {}).get("actor", {})
            if actor:
                try:
                    username = actor["username"]
                except KeyError:
                    try:
                        username = actor["display_name"]
                    except KeyError:
                        username = actor["nickname"]
                log_context["sender"] = username

            sender_id = data.get("data", {}).get("actor", {}).get("account_id", "")
            log_context["sender_id"] = sender_id
            jwt_parts = input_jwt.split(".")
            claim_part = jwt_parts[1]
            claim_part += "=" * (-len(claim_part) % 4)
            decoded_claims = base64.urlsafe_b64decode(claim_part)
            claims = json.loads(decoded_claims)
            client_key = claims["iss"]
            secrets = json.loads(secret_provider.get_secret(client_key))
            shared_secret = secrets["shared_secret"]
            jwt.decode(input_jwt, shared_secret, audience=client_key, algorithms=["HS256"])
            bearer_token = await get_bearer_token(shared_secret, client_key)
            context['bitbucket_bearer_token'] = bearer_token
            context["settings"] = copy.deepcopy(global_settings)
            event = data["event"]
            agent = PRAgent()
            if event == "pullrequest:created":
                pr_url = data["data"]["pullrequest"]["links"]["html"]["href"]
                log_context["api_url"] = pr_url
                log_context["event"] = "pull_request"
                if pr_url:
                    with get_logger().contextualize(**log_context):
                        apply_repo_settings(pr_url)
                        if get_identity_provider().verify_eligibility("bitbucket",
                                                        sender_id, pr_url) is not Eligibility.NOT_ELIGIBLE:
                            if get_settings().get("bitbucket_app.pr_commands"):
                                await _perform_commands_bitbucket("pr_commands", PRAgent(), pr_url, log_context, data)
            elif event == "pullrequest:comment_created":
                pr_url = data["data"]["pullrequest"]["links"]["html"]["href"]
                log_context["api_url"] = pr_url
                log_context["event"] = "comment"
                comment_body = data["data"]["comment"]["content"]["raw"]
                with get_logger().contextualize(**log_context):
                    if get_identity_provider().verify_eligibility("bitbucket",
                                                                     sender_id, pr_url) is not Eligibility.NOT_ELIGIBLE:
                        await agent.handle_request(pr_url, comment_body)
        except Exception as e:
            get_logger().error(f"Failed to handle webhook: {e}")
    background_tasks.add_task(inner)
    return "OK"

@router.get("/webhook")
async def handle_github_webhooks(request: Request, response: Response):
    return "Webhook server online!"

@router.post("/installed")
async def handle_installed_webhooks(request: Request, response: Response):
    try:
        get_logger().info("handle_installed_webhooks")
        get_logger().info(request.headers)
        data = await request.json()
        get_logger().info(data)
        shared_secret = data["sharedSecret"]
        client_key = data["clientKey"]
        username = data["principal"]["username"]
        secrets = {
            "shared_secret": shared_secret,
            "client_key": client_key
        }
        secret_provider.store_secret(username, json.dumps(secrets))
    except Exception as e:
        get_logger().error(f"Failed to register user: {e}")
        return JSONResponse({"error": "Unable to register user"}, status_code=500)

@router.post("/uninstalled")
async def handle_uninstalled_webhooks(request: Request, response: Response):
    get_logger().info("handle_uninstalled_webhooks")

    data = await request.json()
    get_logger().info(data)


def start():
    get_settings().set("CONFIG.PUBLISH_OUTPUT_PROGRESS", False)
    get_settings().set("CONFIG.GIT_PROVIDER", "bitbucket")
    get_settings().set("PR_DESCRIPTION.PUBLISH_DESCRIPTION_AS_COMMENT", True)
    middleware = [Middleware(RawContextMiddleware)]
    app = FastAPI(middleware=middleware)
    app.include_router(router)

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "3000")))


if __name__ == '__main__':
    start()
