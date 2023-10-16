from fastapi import FastAPI
from mangum import Mangum

from pr_agent.log import setup_logger
from pr_agent.servers.github_app import router

setup_logger()

app = FastAPI()
app.include_router(router)

handler = Mangum(app, lifespan="off")


def serverless(event, context):
    return handler(event, context)
