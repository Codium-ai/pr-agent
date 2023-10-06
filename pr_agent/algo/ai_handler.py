import logging
import os

import litellm
import openai
from litellm import acompletion
from openai.error import APIError, RateLimitError, Timeout, TryAgain
from retry import retry
from pr_agent.config_loader import get_settings
OPENAI_RETRIES = 5


class AiHandler:
    """
    This class handles interactions with the OpenAI API for chat completions.
    It initializes the API key and other settings from a configuration file,
    and provides a method for performing chat completions using the OpenAI ChatCompletion API.
    """

    def __init__(self):
        """
        Initializes the OpenAI API key and other settings from a configuration file.
        Raises a ValueError if the OpenAI key is missing.
        """
        try:
            openai.api_key = get_settings().openai.key
            litellm.openai_key = get_settings().openai.key
            if get_settings().get("litellm.use_client"):
                litellm_token = get_settings().get("litellm.LITELLM_TOKEN")
                assert litellm_token, "LITELLM_TOKEN is required"
                os.environ["LITELLM_TOKEN"] = litellm_token
                litellm.use_client = True
            self.azure = False
            if get_settings().get("OPENAI.ORG", None):
                litellm.organization = get_settings().openai.org
            if get_settings().get("OPENAI.API_TYPE", None):
                if get_settings().openai.api_type == "azure":
                    self.azure = True
                    litellm.azure_key = get_settings().openai.key
            if get_settings().get("OPENAI.API_VERSION", None):
                litellm.api_version = get_settings().openai.api_version
            if get_settings().get("OPENAI.API_BASE", None):
                litellm.api_base = get_settings().openai.api_base
            if get_settings().get("ANTHROPIC.KEY", None):
                litellm.anthropic_key = get_settings().anthropic.key
            if get_settings().get("COHERE.KEY", None):
                litellm.cohere_key = get_settings().cohere.key
            if get_settings().get("REPLICATE.KEY", None):
                litellm.replicate_key = get_settings().replicate.key
            if get_settings().get("REPLICATE.KEY", None):
                litellm.replicate_key = get_settings().replicate.key
            if get_settings().get("HUGGINGFACE.KEY", None):
                litellm.huggingface_key = get_settings().huggingface.key
                if get_settings().get("HUGGINGFACE.API_BASE", None):
                    litellm.api_base = get_settings().huggingface.api_base
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
        """
        Performs a chat completion using the OpenAI ChatCompletion API.
        Retries in case of API errors or timeouts.
        
        Args:
            model (str): The model to use for chat completion.
            temperature (float): The temperature parameter for chat completion.
            system (str): The system message for chat completion.
            user (str): The user message for chat completion.
        
        Returns:
            tuple: A tuple containing the response and finish reason from the API.
        
        Raises:
            TryAgain: If the API response is empty or there are no choices in the response.
            APIError: If there is an error during OpenAI inference.
            Timeout: If there is a timeout during OpenAI inference.
            TryAgain: If there is an attribute error during OpenAI inference.
        """
        try:
            deployment_id = self.deployment_id
            if get_settings().config.verbosity_level >= 2:
                logging.debug(
                    f"Generating completion with {model}"
                    f"{(' from deployment ' + deployment_id) if deployment_id else ''}"
                )
            if self.azure:
                model = 'azure/' + model
            response = await acompletion(
                model=model,
                deployment_id=deployment_id,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ],
                temperature=temperature,
                force_timeout=get_settings().config.ai_timeout
            )
        except (APIError, Timeout, TryAgain) as e:
            logging.error("Error during OpenAI inference: ", e)
            raise
        except (RateLimitError) as e:
            logging.error("Rate limit error during OpenAI inference: ", e)
            raise
        except (Exception) as e:
            logging.error("Unknown error during OpenAI inference: ", e)
            raise TryAgain from e
        if response is None or len(response["choices"]) == 0:
            raise TryAgain
        resp = response["choices"][0]['message']['content']
        finish_reason = response["choices"][0]["finish_reason"]
        print(resp, finish_reason)
        return resp, finish_reason
