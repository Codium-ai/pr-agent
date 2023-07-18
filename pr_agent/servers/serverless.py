import logging

from fastapi import FastAPI
from mangum import Mangum

from pr_agent.servers.github_app import router

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

app = FastAPI()
app.include_router(router)

handler = Mangum(app, lifespan="off")


def serverless(event, context):
    return handler(event, context)
