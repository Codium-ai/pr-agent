import hashlib
import json
import logging
import os
import time

import jwt
import requests
import uvicorn
from fastapi import APIRouter, FastAPI, Request, Response
from starlette.middleware import Middleware
from starlette.responses import JSONResponse
from starlette_context import context
from starlette_context.middleware import RawContextMiddleware

from pr_agent.agent.pr_agent import PRAgent
from pr_agent.config_loader import get_settings
from pr_agent.secret_providers import get_secret_provider

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
    manifest = open("atlassian-connect.json", "rt").read()
    manifest_obj = json.loads(manifest)
    return JSONResponse(manifest_obj)

@router.post("/webhook")
async def handle_github_webhooks(request: Request, response: Response):
    try:
        print(request.headers)
        data = await request.json()
        print(data)
        owner = data["data"]["repository"]["owner"]["username"]
        secrets = json.loads(secret_provider.get_secret(owner))
        shared_secret = secrets["shared_secret"]
        client_key = secrets["client_key"]
        bearer_token = await get_bearer_token(shared_secret, client_key)
        context['bitbucket_bearer_token'] = bearer_token
        event = data["event"]
        agent = PRAgent()
        if event == "pullrequest:created":
            pr_url = data["data"]["pullrequest"]["links"]["html"]["href"]
            await agent.handle_request(pr_url, "review")
    except Exception as e:
        logging.error(f"Failed to handle webhook: {e}")
        return JSONResponse({"error": "Unable to handle webhook"}, status_code=500)

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
    middleware = [Middleware(RawContextMiddleware)]
    app = FastAPI(middleware=middleware)
    app.include_router(router)

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "3000")))


if __name__ == '__main__':
    start()
