try:
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_openai import AzureChatOpenAI, ChatOpenAI
except:  # we don't enforce langchain as a dependency, so if it's not installed, just move on
    pass

import functools

from openai import APIError, RateLimitError, Timeout
from retry import retry

from pr_agent.algo.ai_handlers.base_ai_handler import BaseAiHandler
from pr_agent.config_loader import get_settings
from pr_agent.log import get_logger

OPENAI_RETRIES = 5


class LangChainOpenAIHandler(BaseAiHandler):
    def __init__(self):
        # Initialize OpenAIHandler specific attributes here
        super().__init__()
        self.azure = get_settings().get("OPENAI.API_TYPE", "").lower() == "azure"

        # Create a default unused chat object to trigger early validation
        self._create_chat(self.deployment_id)

    def chat(self, messages: list, model: str, temperature: float):
        chat = self._create_chat(self.deployment_id)
        return chat.invoke(input=messages, model=model, temperature=temperature)

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
            messages = [SystemMessage(content=system), HumanMessage(content=user)]

            # get a chat completion from the formatted messages
            resp = self.chat(messages, model=model, temperature=temperature)
            finish_reason = "completed"
            return resp.content, finish_reason

        except (Exception) as e:
            get_logger().error("Unknown error during OpenAI inference: ", e)
            raise e

    def _create_chat(self, deployment_id=None):
        try:
            if self.azure:
                # using a partial function so we can set the deployment_id later to support fallback_deployments
                # but still need to access the other settings now so we can raise a proper exception if they're missing
                return AzureChatOpenAI(
                    openai_api_key=get_settings().openai.key,
                    openai_api_version=get_settings().openai.api_version,
                    azure_deployment=deployment_id,
                    azure_endpoint=get_settings().openai.api_base,
                )
            else:
                # for llms that compatible with openai, should use custom api base
                openai_api_base = get_settings().get("OPENAI.API_BASE", None)
                if openai_api_base is None or len(openai_api_base) == 0:
                    return ChatOpenAI(openai_api_key=get_settings().openai.key)
                else:
                    return ChatOpenAI(openai_api_key=get_settings().openai.key, openai_api_base=openai_api_base)
        except AttributeError as e:
            if getattr(e, "name"):
                raise ValueError(f"OpenAI {e.name} is required") from e
            else:
                raise e
