import logging

import openai
from openai.error import APIError, Timeout, TryAgain
from retry import retry

from pr_agent.config_loader import settings

OPENAI_RETRIES=2

class AiHandler:
    def __init__(self):
        try:
            openai.api_key = settings.openai.key
            if settings.get("OPENAI.ORG", None):
                openai.organization = settings.openai.org
            self.deployment_id = settings.get("OPENAI.DEPLOYMENT_ID", None)
            if settings.get("OPENAI.API_TYPE", None):
                openai.api_type = settings.openai.api_type
            if settings.get("OPENAI.API_VERSION", None):
                openai.api_version = settings.openai.api_version
            if settings.get("OPENAI.API_BASE", None):
                openai.api_base = settings.openai.api_base
        except AttributeError as e:
            raise ValueError("OpenAI key is required") from e

    @retry(exceptions=(APIError, Timeout, TryAgain, AttributeError),
           tries=OPENAI_RETRIES, delay=2, backoff=2, jitter=(1, 3))
    async def chat_completion(self, model: str, temperature: float, system: str, user: str):
        try:
            response = await openai.ChatCompletion.acreate(
                            model=model,
                            deployment_id=self.deployment_id,
                            messages=[
                                {"role": "system", "content": system},
                                {"role": "user", "content": user}
                            ],
                            temperature=temperature,
                        )
        except (APIError, Timeout, TryAgain) as e:
            logging.error("Error during OpenAI inference: ", e)
            raise
        if response is None or len(response.choices) == 0:
            raise TryAgain
        resp = response.choices[0]['message']['content']
        finish_reason = response.choices[0].finish_reason
        return resp, finish_reason
