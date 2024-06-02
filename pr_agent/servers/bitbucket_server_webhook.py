import json
import os

import uvicorn
from fastapi import APIRouter, FastAPI
from fastapi.encoders import jsonable_encoder
from starlette import status
from starlette.background import BackgroundTasks
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette_context.middleware import RawContextMiddleware

from pr_agent.agent.pr_agent import PRAgent
from pr_agent.config_loader import get_settings
from pr_agent.log import LoggingFormat, get_logger, setup_logger
from pr_agent.servers.utils import verify_signature

setup_logger(fmt=LoggingFormat.JSON, level="DEBUG")
router = APIRouter()


def handle_request(
    background_tasks: BackgroundTasks, url: str, body: str, log_context: dict
):
    log_context["action"] = body
    log_context["api_url"] = url
    
    async def inner():
        try:
            with get_logger().contextualize(**log_context):
                await PRAgent().handle_request(url, body)
        except Exception as e:
            get_logger().error(f"Failed to handle webhook: {e}")

    background_tasks.add_task(inner)


@router.post("/")
async def handle_webhook(background_tasks: BackgroundTasks, request: Request):
    log_context = {"server_type": "bitbucket_server"}
    data = await request.json()
    get_logger().info(json.dumps(data))

    webhook_secret = get_settings().get("BITBUCKET_SERVER.WEBHOOK_SECRET", None)
    if webhook_secret:
        body_bytes = await request.body()
        signature_header = request.headers.get("x-hub-signature", None)
        verify_signature(body_bytes, webhook_secret, signature_header)

    pr_id = data["pullRequest"]["id"]
    repository_name = data["pullRequest"]["toRef"]["repository"]["slug"]
    project_name = data["pullRequest"]["toRef"]["repository"]["project"]["key"]
    bitbucket_server = get_settings().get("BITBUCKET_SERVER.URL")
    pr_url = f"{bitbucket_server}/projects/{project_name}/repos/{repository_name}/pull-requests/{pr_id}"

    log_context["api_url"] = pr_url
    log_context["event"] = "pull_request"

    if data["eventKey"] == "pr:opened":
        body = "review"
    elif data["eventKey"] == "pr:comment:added":
        body = data["comment"]["text"]
    else:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=json.dumps({"message": "Unsupported event"}),
        )

    handle_request(background_tasks, pr_url, body, log_context)
    return JSONResponse(
        status_code=status.HTTP_200_OK, content=jsonable_encoder({"message": "success"})
    )


@router.get("/")
async def root():
    return {"status": "ok"}


def start():
    app = FastAPI(middleware=[Middleware(RawContextMiddleware)])
    app.include_router(router)
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "3000")))


if __name__ == "__main__":
    start()
