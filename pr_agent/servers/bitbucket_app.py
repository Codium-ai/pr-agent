import copy
import hashlib
import json
import logging
import os
import sys
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
from pr_agent.config_loader import get_settings, global_settings
from pr_agent.secret_providers import get_secret_provider

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
router = APIRouter()
secret_provider = get_secret_provider()

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
        logging.error(f"Failed to get bearer token: {e}")
        raise e

@router.get("/")
async def handle_manifest(request: Request, response: Response):
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    manifest = open(os.path.join(cur_dir, "atlassian-connect.json"), "rt").read()
    try:
        manifest = manifest.replace("app_key", get_settings().bitbucket.app_key)
        manifest = manifest.replace("base_url", get_settings().bitbucket.base_url)
    except:
        logging.error("Failed to replace api_key in Bitbucket manifest, trying to continue")
    manifest_obj = json.loads(manifest)
    return JSONResponse(manifest_obj)

@router.post("/webhook")
async def handle_github_webhooks(background_tasks: BackgroundTasks, request: Request):
    print(request.headers)
    jwt_header = request.headers.get("authorization", None)
    if jwt_header:
        input_jwt = jwt_header.split(" ")[1]
    data = await request.json()
    print(data)
    async def inner():
        try:
            owner = data["data"]["repository"]["owner"]["username"]
            secrets = json.loads(secret_provider.get_secret(owner))
            shared_secret = secrets["shared_secret"]
            client_key = secrets["client_key"]
            jwt.decode(input_jwt, shared_secret, audience=client_key, algorithms=["HS256"])
            bearer_token = await get_bearer_token(shared_secret, client_key)
            context['bitbucket_bearer_token'] = bearer_token
            context["settings"] = copy.deepcopy(global_settings)
            event = data["event"]
            agent = PRAgent()
            if event == "pullrequest:created":
                pr_url = data["data"]["pullrequest"]["links"]["html"]["href"]
                await agent.handle_request(pr_url, "review")
            elif event == "pullrequest:comment_created":
                pr_url = data["data"]["pullrequest"]["links"]["html"]["href"]
                comment_body = data["data"]["comment"]["content"]["raw"]
                await agent.handle_request(pr_url, comment_body)
        except Exception as e:
            logging.error(f"Failed to handle webhook: {e}")
    background_tasks.add_task(inner)
    return "OK"

@router.get("/webhook")
async def handle_github_webhooks(request: Request, response: Response):
    return "Webhook server online!"

@router.post("/installed")
async def handle_installed_webhooks(request: Request, response: Response):
    try:
        print(request.headers)
        data = await request.json()
        print(data)
        shared_secret = data["sharedSecret"]
        client_key = data["clientKey"]
        username = data["principal"]["username"]
        secrets = {
            "shared_secret": shared_secret,
            "client_key": client_key
        }
        secret_provider.store_secret(username, json.dumps(secrets))
    except Exception as e:
        logging.error(f"Failed to register user: {e}")
        return JSONResponse({"error": "Unable to register user"}, status_code=500)

@router.post("/uninstalled")
async def handle_uninstalled_webhooks(request: Request, response: Response):
    data = await request.json()
    print(data)


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
