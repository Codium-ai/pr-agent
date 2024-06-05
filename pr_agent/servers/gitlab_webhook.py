import copy
import json
from datetime import datetime

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


async def get_mr_url_from_commit_sha(commit_sha, gitlab_token, project_id):
    try:
        import requests
        headers = {
            'Private-Token': f'{gitlab_token}'
        }
        # API endpoint to find MRs containing the commit
        gitlab_url = get_settings().get("GITLAB.URL", 'https://gitlab.com')
        response = requests.get(
            f'{gitlab_url}/api/v4/projects/{project_id}/repository/commits/{commit_sha}/merge_requests',
            headers=headers
        )
        merge_requests = response.json()
        if merge_requests and response.status_code == 200:
            pr_url = merge_requests[0]['web_url']
            return pr_url
        else:
            get_logger().info(f"No merge requests found for commit: {commit_sha}")
            return None
    except Exception as e:
        get_logger().error(f"Failed to get MR url from commit sha: {e}")
        return None

async def handle_request(api_url: str, body: str, log_context: dict, sender_id: str):
    log_context["action"] = body
    log_context["event"] = "pull_request" if body == "/review" else "comment"
    log_context["api_url"] = api_url

    with get_logger().contextualize(**log_context):
        await PRAgent().handle_request(api_url, body)


async def _perform_commands_gitlab(commands_conf: str, agent: PRAgent, api_url: str,
                                   log_context: dict):
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
    start_time = datetime.now()
    request_json = await request.json()

    async def inner(data: dict):
        log_context = {"server_type": "gitlab_app"}
        get_logger().debug("Received a GitLab webhook")
        if request.headers.get("X-Gitlab-Token") and secret_provider:
            request_token = request.headers.get("X-Gitlab-Token")
            secret = secret_provider.get_secret(request_token)
            try:
                secret_dict = json.loads(secret)
                gitlab_token = secret_dict["gitlab_token"]
                log_context["token_id"] = secret_dict.get("token_name", secret_dict.get("id", "unknown"))
                context["settings"] = copy.deepcopy(global_settings)
                context["settings"].gitlab.personal_access_token = gitlab_token
            except Exception as e:
                get_logger().error(f"Failed to validate secret {request_token}: {e}")
                return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=jsonable_encoder({"message": "unauthorized"}))
        elif get_settings().get("GITLAB.SHARED_SECRET"):
            secret = get_settings().get("GITLAB.SHARED_SECRET")
            if not request.headers.get("X-Gitlab-Token") == secret:
                get_logger().error("Failed to validate secret")
                return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=jsonable_encoder({"message": "unauthorized"}))
        else:
            get_logger().error("Failed to validate secret")
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=jsonable_encoder({"message": "unauthorized"}))
        gitlab_token = get_settings().get("GITLAB.PERSONAL_ACCESS_TOKEN", None)
        if not gitlab_token:
            get_logger().error("No gitlab token found")
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=jsonable_encoder({"message": "unauthorized"}))

        get_logger().info("GitLab data", artifact=data)
        sender = data.get("user", {}).get("username", "unknown")
        sender_id = data.get("user", {}).get("id", "unknown")

        # logic to ignore bot users (unlike Github, no direct flag for bot users in gitlab)
        sender_name = data.get("user", {}).get("name", "unknown").lower()
        if 'codium' in sender_name or 'bot_' in sender_name or 'bot-' in sender_name or '_bot' in sender_name or '-bot' in sender_name:
            get_logger().info(f"Skipping bot user: {sender_name}")
            return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder({"message": "success"}))

        log_context["sender"] = sender
        if data.get('object_kind') == 'merge_request' and data['object_attributes'].get('action') in ['open', 'reopen']:
            url = data['object_attributes'].get('url')
            get_logger().info(f"New merge request: {url}")
            await _perform_commands_gitlab("pr_commands", PRAgent(), url, log_context)
        elif data.get('object_kind') == 'note' and data.get('event_type') == 'note': # comment on MR
            if 'merge_request' in data:
                mr = data['merge_request']
                url = mr.get('url')
                get_logger().info(f"A comment has been added to a merge request: {url}")
                body = data.get('object_attributes', {}).get('note')
                if data.get('object_attributes', {}).get('type') == 'DiffNote' and '/ask' in body: # /ask_line
                    body = handle_ask_line(body, data)

                await handle_request(url, body, log_context, sender_id)
        elif data.get('object_kind') == 'push' and data.get('event_name') == 'push':
            try:
                project_id = data['project_id']
                commit_sha = data['checkout_sha']
                url = await get_mr_url_from_commit_sha(commit_sha, gitlab_token, project_id)
                if not url:
                    get_logger().info(f"No MR found for commit: {commit_sha}")
                    return JSONResponse(status_code=status.HTTP_200_OK,
                                        content=jsonable_encoder({"message": "success"}))

                # we need first to apply_repo_settings
                apply_repo_settings(url)
                commands_on_push = get_settings().get(f"gitlab.push_commands", {})
                handle_push_trigger = get_settings().get(f"gitlab.handle_push_trigger", False)
                if not commands_on_push or not handle_push_trigger:
                    get_logger().info("Push event, but no push commands found or push trigger is disabled")
                    return JSONResponse(status_code=status.HTTP_200_OK,
                                        content=jsonable_encoder({"message": "success"}))

                get_logger().debug(f'A push event has been received: {url}')
                await _perform_commands_gitlab("push_commands", PRAgent(), url, log_context)
            except Exception as e:
                get_logger().error(f"Failed to handle push event: {e}")

    background_tasks.add_task(inner, request_json)
    end_time = datetime.now()
    get_logger().info(f"Processing time: {end_time - start_time}", request=request_json)
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
        get_logger().info("Handling line comment")
        body = f"/ask_line --line_start={start_line} --line_end={end_line} --side={side} --file_name={path} --comment_id={comment_id} {question}"
    except Exception as e:
        get_logger().error(f"Failed to handle ask line comment: {e}")
    return body


@router.get("/")
async def root():
    return {"status": "ok"}

gitlab_url = get_settings().get("GITLAB.URL", None)
if not gitlab_url:
    raise ValueError("GITLAB.URL is not set")
get_settings().config.git_provider = "gitlab"
middleware = [Middleware(RawContextMiddleware)]
app = FastAPI(middleware=middleware)
app.include_router(router)


def start():
    uvicorn.run(app, host="0.0.0.0", port=3000)


if __name__ == '__main__':
    start()
