import base64
import copy
import hashlib
import json
import os
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


async def _perform_commands_bitbucket(commands_conf: str, agent: PRAgent, api_url: str, log_context: dict):
    apply_repo_settings(api_url)
    commands = get_settings().get(f"bitbucket_app.{commands_conf}", {})
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


@router.post("/webhook")
async def handle_github_webhooks(background_tasks: BackgroundTasks, request: Request):
    log_context = {"server_type": "bitbucket_app"}
    get_logger().debug(request.headers)
    jwt_header = request.headers.get("authorization", None)
    if jwt_header:
        input_jwt = jwt_header.split(" ")[1]
    data = await request.json()
    get_logger().debug(data)
    async def inner():
        try:
            try:
                if data["data"]["actor"]["type"] != "user":
                    return "OK"
            except KeyError:
                get_logger().error("Failed to get actor type, check previous logs, this shouldn't happen.")
            try:
                owner = data["data"]["repository"]["owner"]["username"]
            except Exception as e:
                get_logger().error(f"Failed to get owner, will continue: {e}")
                owner = "unknown"
            sender_id = data["data"]["actor"]["account_id"]
            log_context["sender"] = owner
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
                                await _perform_commands_bitbucket("pr_commands", PRAgent(), pr_url, log_context)
                            else: # backwards compatibility
                                auto_review = get_setting_or_env("BITBUCKET_APP.AUTO_REVIEW", None)
                                if is_true(auto_review):  # by default, auto review is disabled
                                    await PRReviewer(pr_url).run()
                                auto_improve = get_setting_or_env("BITBUCKET_APP.AUTO_IMPROVE", None)
                                if is_true(auto_improve):  # by default, auto improve is disabled
                                    await PRCodeSuggestions(pr_url).run()
                                auto_describe = get_setting_or_env("BITBUCKET_APP.AUTO_DESCRIBE", None)
                                if is_true(auto_describe):  # by default, auto describe is disabled
                                    await PRDescription(pr_url).run()
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
