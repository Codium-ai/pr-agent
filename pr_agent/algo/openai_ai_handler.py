from pr_agent.algo.base_ai_handler import BaseAiHandler
import openai
from openai.error import APIError, RateLimitError, Timeout, TryAgain
from retry import retry

from pr_agent.config_loader import get_settings

OPENAI_RETRIES = 5


class OpenAIHandler(BaseAiHandler):
    def __init__(self):
        # Initialize OpenAIHandler specific attributes here
        try:
            super().__init__()
            openai.api_key = get_settings().openai.key
            if get_settings().get("OPENAI.ORG", None):
                openai.organization = get_settings().openai.org
            if get_settings().get("OPENAI.API_TYPE", None):
                if get_settings().openai.api_type == "azure":
                    self.azure = True
                    openai.azure_key = get_settings().openai.key
            if get_settings().get("OPENAI.API_VERSION", None):
                openai.api_version = get_settings().openai.api_version
            if get_settings().get("OPENAI.API_BASE", None):
                openai.api_base = get_settings().openai.api_base

        except AttributeError as e:
            raise ValueError("OpenAI key is required") from e
    @property
    def deployment_id(self):
        """
        Returns the deployment ID for the OpenAI API.
        """
        return get_settings().get("OPENAI.DEPLOYMENT_ID", None)
    
    @retry(exceptions=(APIError, Timeout, TryAgain, AttributeError, RateLimitError),
           tries=OPENAI_RETRIES, delay=2, backoff=2, jitter=(1, 3))
    async def chat_completion(self, model: str, system: str, user: str, temperature: float = 0.2):
        chat_completion = await openai.ChatCompletion.acreate(
            model=model,
            messages=[{
                "role": "system",
                "content": system
            }, {
                "role": "user",
                "content": user            
            }],
        )
        return chat_completion.choices[0].message.content
