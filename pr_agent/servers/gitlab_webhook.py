import copy
import json
import logging
import sys

import uvicorn
from fastapi import APIRouter, FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from starlette.background import BackgroundTasks
from starlette.middleware import Middleware
from starlette_context import context
from starlette_context.middleware import RawContextMiddleware

from pr_agent.agent.pr_agent import PRAgent
from pr_agent.config_loader import get_settings, global_settings
from pr_agent.secret_providers import get_secret_provider

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
router = APIRouter()

secret_provider = get_secret_provider() if get_settings().get("CONFIG.SECRET_PROVIDER") else None


@router.post("/webhook")
async def gitlab_webhook(background_tasks: BackgroundTasks, request: Request):
    if request.headers.get("X-Gitlab-Token") and secret_provider:
        request_token = request.headers.get("X-Gitlab-Token")
        secret = secret_provider.get_secret(request_token)
        try:
            secret_dict = json.loads(secret)
            gitlab_token = secret_dict["gitlab_token"]
            context["settings"] = copy.deepcopy(global_settings)
            context["settings"].gitlab.personal_access_token = gitlab_token
        except Exception as e:
            logging.error(f"Failed to validate secret {request_token}: {e}")
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=jsonable_encoder({"message": "unauthorized"}))
    elif get_settings().get("GITLAB.SHARED_SECRET"):
        secret = get_settings().get("GITLAB.SHARED_SECRET")
        if not request.headers.get("X-Gitlab-Token") == secret:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=jsonable_encoder({"message": "unauthorized"}))
    else:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=jsonable_encoder({"message": "unauthorized"}))
    gitlab_token = get_settings().get("GITLAB.PERSONAL_ACCESS_TOKEN", None)
    if not gitlab_token:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=jsonable_encoder({"message": "unauthorized"}))
    data = await request.json()
    logging.info(json.dumps(data))
    if data.get('object_kind') == 'merge_request' and data['object_attributes'].get('action') in ['open', 'reopen']:
        logging.info(f"A merge request has been opened: {data['object_attributes'].get('title')}")
        url = data['object_attributes'].get('url')
        background_tasks.add_task(PRAgent().handle_request, url, "/review")
    elif data.get('object_kind') == 'note' and data['event_type'] == 'note':
        if 'merge_request' in data:
            mr = data['merge_request']
            url = mr.get('url')
            body = data.get('object_attributes', {}).get('note')
            background_tasks.add_task(PRAgent().handle_request, url, body)
    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder({"message": "success"}))


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
