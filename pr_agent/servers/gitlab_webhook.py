import logging

import uvicorn
from fastapi import APIRouter, FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from starlette.background import BackgroundTasks

from pr_agent.agent.pr_agent import PRAgent
from pr_agent.config_loader import get_settings
from pr_agent.secret_providers import get_secret_provider

app = FastAPI()
router = APIRouter()

if get_settings().config.secret_provider:
    secret_provider = get_secret_provider()

@router.post("/webhook")
async def gitlab_webhook(background_tasks: BackgroundTasks, request: Request):
    if get_settings().get("GITLAB.SHARED_SECRET"):
        secret = get_settings().get("GITLAB.SHARED_SECRET")
        if not request.headers.get("X-Gitlab-Token") == secret:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=jsonable_encoder({"message": "unauthorized"}))
    gitlab_token = get_settings().get("GITLAB.PERSONAL_ACCESS_TOKEN", None)
    if not gitlab_token:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=jsonable_encoder({"message": "unauthorized"}))
    data = await request.json()
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

def start():
    gitlab_url = get_settings().get("GITLAB.URL", None)
    if not gitlab_url:
        raise ValueError("GITLAB.URL is not set")
    get_settings().config.git_provider = "gitlab"

    app = FastAPI()
    app.include_router(router)

    uvicorn.run(app, host="0.0.0.0", port=3000)


if __name__ == '__main__':
    start()
