from os import environ
from pr_agent.algo.ai_handlers.base_ai_handler import BaseAiHandler
import openai
from openai import APIError, AsyncOpenAI, RateLimitError, Timeout
from retry import retry

from pr_agent.algo.ai_handlers.base_ai_handler import BaseAiHandler
from pr_agent.config_loader import get_settings
from pr_agent.log import get_logger

OPENAI_RETRIES = 5


class OpenAIHandler(BaseAiHandler):
    def __init__(self):
        # Initialize OpenAIHandler specific attributes here
        try:
            super().__init__()
            environ["OPENAI_API_KEY"] = get_settings().openai.key
            if get_settings().get("OPENAI.ORG", None):
                openai.organization = get_settings().openai.org
            if get_settings().get("OPENAI.API_TYPE", None):
                if get_settings().openai.api_type == "azure":
                    self.azure = True
                    openai.azure_key = get_settings().openai.key
            if get_settings().get("OPENAI.API_VERSION", None):
                openai.api_version = get_settings().openai.api_version
            if get_settings().get("OPENAI.API_BASE", None):
                environ["OPENAI_BASE_URL"] = get_settings().openai.api_base

        except AttributeError as e:
            raise ValueError("OpenAI key is required") from e

    @property
    def deployment_id(self):
        """
        Returns the deployment ID for the OpenAI API.
        """
        return get_settings().get("OPENAI.DEPLOYMENT_ID", None)

    @retry(exceptions=(APIError, Timeout, AttributeError, RateLimitError),
           tries=OPENAI_RETRIES, delay=2, backoff=2, jitter=(1, 3))
    async def chat_completion(self, model: str, system: str, user: str, temperature: float = 0.2):
        try:
            get_logger().info("System: ", system)
            get_logger().info("User: ", user)
            messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
            client = AsyncOpenAI()
            chat_completion = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
            )
            resp = chat_completion.choices[0].message.content
            finish_reason = chat_completion.choices[0].finish_reason
            usage = chat_completion.usage
            get_logger().info("AI response", response=resp, messages=messages, finish_reason=finish_reason,
                              model=model, usage=usage)
            return resp, finish_reason
        except (APIError, Timeout) as e:
            get_logger().error("Error during OpenAI inference: ", e)
            raise
        except (RateLimitError) as e:
            get_logger().error("Rate limit error during OpenAI inference: ", e)
            raise
        except (Exception) as e:
            get_logger().error("Unknown error during OpenAI inference: ", e)
            raise
