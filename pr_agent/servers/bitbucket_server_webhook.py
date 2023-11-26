import json

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
from pr_agent.log import get_logger

router = APIRouter()


def handle_request(background_tasks: BackgroundTasks, url: str, body: str, log_context: dict):
    log_context["action"] = body
    log_context["event"] = "pull_request" if body == "review" else "comment"
    log_context["api_url"] = url
    with get_logger().contextualize(**log_context):
        background_tasks.add_task(PRAgent().handle_request, url, body)


@router.post("/webhook")
async def handle_webhook(background_tasks: BackgroundTasks, request: Request):
    log_context = {"server_type": "bitbucket_server"}
    data = await request.json()
    get_logger().info(json.dumps(data))

    pr_id = data['pullRequest']['id']
    repository_name = data['pullRequest']['toRef']['repository']['slug']
    project_name = data['pullRequest']['toRef']['repository']['project']['key']
    bitbucket_server = get_settings().get("BITBUCKET_SERVER.URL")
    pr_url = f"{bitbucket_server}/projects/{project_name}/repos/{repository_name}/pull-requests/{pr_id}"

    log_context["api_url"] = pr_url
    log_context["event"] = "pull_request"

    handle_request(background_tasks, pr_url, "review", log_context)
    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder({"message": "success"}))


@router.get("/")
async def root():
    return {"status": "ok"}


def start():
    bitbucket_server_url = get_settings().get("BITBUCKET_SERVER.URL", None)
    if not bitbucket_server_url:
        raise ValueError("BITBUCKET_SERVER.URL is not set")
    get_settings().config.git_provider = "bitbucket_server"
    middleware = [Middleware(RawContextMiddleware)]
    app = FastAPI(middleware=middleware)
    app.include_router(router)
    uvicorn.run(app, host="0.0.0.0", port=3000)


if __name__ == '__main__':
    start()
