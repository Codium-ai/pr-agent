import json
import os

import uvicorn
from fastapi import APIRouter, FastAPI, Request, Response
from starlette.middleware import Middleware
from starlette.responses import JSONResponse
from starlette_context.middleware import RawContextMiddleware

from pr_agent.config_loader import get_settings

router = APIRouter()


@router.get("/")
async def handle_manifest(request: Request, response: Response):
    manifest = open("atlassian-connect.json", "rt").read()
    manifest_obj = json.loads(manifest)
    return JSONResponse(manifest_obj)

@router.post("/webhook")
async def handle_github_webhooks(request: Request, response: Response):
    data = await request.json()
    print(data)

@router.get("/webhook")
async def handle_github_webhooks(request: Request, response: Response):
    return "Webhook server online!"

@router.post("/installed")
async def handle_installed_webhooks(request: Request, response: Response):
    data = await request.json()
    print(data)

@router.post("/uninstalled")
async def handle_uninstalled_webhooks(request: Request, response: Response):
    data = await request.json()
    print(data)


def start():
    get_settings().set("CONFIG.PUBLISH_OUTPUT_PROGRESS", False)
    middleware = [Middleware(RawContextMiddleware)]
    app = FastAPI(middleware=middleware)
    app.include_router(router)

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "3000")))


if __name__ == '__main__':
    start()
