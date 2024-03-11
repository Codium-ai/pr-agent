import copy
import json

import uvicorn
from fastapi import APIRouter, FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from starlette.background import BackgroundTasks
from starlette.middleware import Middleware
from starlette_context import context
from starlette_context.middleware import RawContextMiddleware

from pr_agent.agent.pr_agent import PRAgent
from pr_agent.algo.utils import update_settings_from_args
from pr_agent.config_loader import get_settings, global_settings
from pr_agent.git_providers.utils import apply_repo_settings
from pr_agent.log import LoggingFormat, get_logger, setup_logger
from pr_agent.secret_providers import get_secret_provider

setup_logger(fmt=LoggingFormat.JSON, level="DEBUG")
router = APIRouter()

secret_provider = get_secret_provider() if get_settings().get("CONFIG.SECRET_PROVIDER") else None


def handle_request(background_tasks: BackgroundTasks, url: str, body: str, log_context: dict):
    log_context["action"] = body
    log_context["event"] = "pull_request" if body == "/review" else "comment"
    log_context["api_url"] = url
    with get_logger().contextualize(**log_context):
        background_tasks.add_task(PRAgent().handle_request, url, body)


async def _perform_commands_gitlab(commands_conf: str, agent: PRAgent, api_url: str, log_context: dict):
    apply_repo_settings(api_url)
    commands = get_settings().get(f"gitlab.{commands_conf}", {})
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
async def gitlab_webhook(background_tasks: BackgroundTasks, request: Request):
    log_context = {"server_type": "gitlab_app"}
    get_logger().debug("Received a GitLab webhook")

    # Check if the request is authorized
    if request.headers.get("X-Gitlab-Token") and secret_provider:
        request_token = request.headers.get("X-Gitlab-Token")
        secret = secret_provider.get_secret(request_token)
        try:
            secret_dict = json.loads(secret)
            gitlab_token = secret_dict["gitlab_token"]
            log_context["sender"] = secret_dict.get("token_name", secret_dict.get("id", "unknown"))
            context["settings"] = copy.deepcopy(global_settings)
            context["settings"].gitlab.personal_access_token = gitlab_token
        except Exception as e:
            get_logger().error(f"Failed to validate secret {request_token}: {e}")
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=jsonable_encoder({"message": "unauthorized"}))
    elif get_settings().get("GITLAB.SHARED_SECRET"):
        secret = get_settings().get("GITLAB.SHARED_SECRET")
        if not request.headers.get("X-Gitlab-Token") == secret:
            get_logger().error(f"Failed to validate secret")
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=jsonable_encoder({"message": "unauthorized"}))
    else:
        get_logger().error(f"Failed to validate secret")
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=jsonable_encoder({"message": "unauthorized"}))
    gitlab_token = get_settings().get("GITLAB.PERSONAL_ACCESS_TOKEN", None)
    if not gitlab_token:
        get_logger().error(f"No gitlab token found")
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=jsonable_encoder({"message": "unauthorized"}))

    data = await request.json()
    get_logger().info("GitLab data", artifact=data)

    if data.get('object_kind') == 'merge_request' and data['object_attributes'].get('action') in ['open', 'reopen']:
        url = data['object_attributes'].get('url')
        get_logger().info(f"New merge request: {url}")
        await _perform_commands_gitlab("pr_commands", PRAgent(), url, log_context)
    elif data.get('object_kind') == 'note' and data['event_type'] == 'note': # comment on MR
        if 'merge_request' in data:
            mr = data['merge_request']
            url = mr.get('url')
            get_logger().info(f"A comment has been added to a merge request: {url}")
            body = data.get('object_attributes', {}).get('note')
            if data.get('object_attributes', {}).get('type') == 'DiffNote' and '/ask' in body: # /ask_line
                body = handle_ask_line(body, data)

            handle_request(background_tasks, url, body, log_context)

    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder({"message": "success"}))


def handle_ask_line(body, data):
    try:
        line_range_ = data['object_attributes']['position']['line_range']
        # if line_range_['start']['type'] == 'new':
        start_line = line_range_['start']['new_line']
        end_line = line_range_['end']['new_line']
        # else:
        #     start_line = line_range_['start']['old_line']
        #     end_line = line_range_['end']['old_line']
        question = body.replace('/ask', '').strip()
        path = data['object_attributes']['position']['new_path']
        side = 'RIGHT'  # if line_range_['start']['type'] == 'new' else 'LEFT'
        comment_id = data['object_attributes']["discussion_id"]
        get_logger().info(f"Handling line comment")
        body = f"/ask_line --line_start={start_line} --line_end={end_line} --side={side} --file_name={path} --comment_id={comment_id} {question}"
    except Exception as e:
        get_logger().error(f"Failed to handle ask line comment: {e}")
    return body


@router.get("/")
async def root():
    return {"status": "ok"}

def start():
    gitlab_url = get_settings().get("GITLAB.URL", None)
    if not gitlab_url:
        raise ValueError("GITLAB.URL is not set")
    get_settings().config.git_provider = "gitlab"
    middleware = [Middleware(RawContextMiddleware)]
    app = FastAPI(middleware=middleware)
    app.include_router(router)

    uvicorn.run(app, host="0.0.0.0", port=3000)


if __name__ == '__main__':
    start()
