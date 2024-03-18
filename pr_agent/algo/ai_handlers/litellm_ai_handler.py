import os

import boto3
import litellm
import openai
from litellm import acompletion
from tenacity import retry, retry_if_exception_type, stop_after_attempt
from pr_agent.algo.ai_handlers.base_ai_handler import BaseAiHandler
from pr_agent.config_loader import get_settings
from pr_agent.log import get_logger

OPENAI_RETRIES = 5


class LiteLLMAIHandler(BaseAiHandler):
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
        self.azure = False
        self.aws_bedrock_client = None
        self.api_base = None
        self.repetition_penalty = None
        if get_settings().get("OPENAI.KEY", None):
            openai.api_key = get_settings().openai.key
            litellm.openai_key = get_settings().openai.key
        if get_settings().get("litellm.use_client"):
            litellm_token = get_settings().get("litellm.LITELLM_TOKEN")
            assert litellm_token, "LITELLM_TOKEN is required"
            os.environ["LITELLM_TOKEN"] = litellm_token
            litellm.use_client = True
        if get_settings().get("LITELLM.DROP_PARAMS", None):
            litellm.drop_params = get_settings().litellm.drop_params
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
        if get_settings().get("HUGGINGFACE.API_BASE", None) and 'huggingface' in get_settings().config.model:
            litellm.api_base = get_settings().huggingface.api_base
            self.api_base = get_settings().huggingface.api_base
        if get_settings().get("HUGGINGFACE.REPITITION_PENALTY", None):
            self.repetition_penalty = float(get_settings().huggingface.repetition_penalty)
        if get_settings().get("VERTEXAI.VERTEX_PROJECT", None):
            litellm.vertex_project = get_settings().vertexai.vertex_project
            litellm.vertex_location = get_settings().get(
                "VERTEXAI.VERTEX_LOCATION", None
            )
        if get_settings().get("AWS.BEDROCK_REGION", None):
            litellm.AmazonAnthropicConfig.max_tokens_to_sample = 2000
            litellm.AmazonAnthropicClaude3Config.max_tokens = 2000
            self.aws_bedrock_client = boto3.client(
                service_name="bedrock-runtime",
                region_name=get_settings().aws.bedrock_region,
            )

    def prepare_logs(self, response, system, user, resp, finish_reason):
        response_log = response.dict().copy()
        response_log['system'] = system
        response_log['user'] = user
        response_log['output'] = resp
        response_log['finish_reason'] = finish_reason
        if hasattr(self, 'main_pr_language'):
            response_log['main_pr_language'] = self.main_pr_language
        else:
            response_log['main_pr_language'] = 'unknown'
        return response_log

    @property
    def deployment_id(self):
        """
        Returns the deployment ID for the OpenAI API.
        """
        return get_settings().get("OPENAI.DEPLOYMENT_ID", None)

    @retry(
        retry=retry_if_exception_type((openai.APIError, openai.APIConnectionError, openai.Timeout)), # No retry on RateLimitError
        stop=stop_after_attempt(OPENAI_RETRIES)
    )
    async def chat_completion(self, model: str, system: str, user: str, temperature: float = 0.2):
        try:
            resp, finish_reason = None, None
            deployment_id = self.deployment_id
            if self.azure:
                model = 'azure/' + model
            messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
            kwargs = {
                "model": model,
                "deployment_id": deployment_id,
                "messages": messages,
                "temperature": temperature,
                "force_timeout": get_settings().config.ai_timeout,
                "api_base" : self.api_base,
            }
            if self.aws_bedrock_client:
                kwargs["aws_bedrock_client"] = self.aws_bedrock_client
            if self.repetition_penalty:
                kwargs["repetition_penalty"] = self.repetition_penalty

            get_logger().debug("Prompts", artifact={"system": system, "user": user})

            if get_settings().config.verbosity_level >= 2:
                get_logger().info(f"\nSystem prompt:\n{system}")
                get_logger().info(f"\nUser prompt:\n{user}")

            response = await acompletion(**kwargs)
        except (openai.APIError, openai.Timeout) as e:
            get_logger().error("Error during OpenAI inference: ", e)
            raise
        except (openai.RateLimitError) as e:
            get_logger().error("Rate limit error during OpenAI inference: ", e)
            raise
        except (Exception) as e:
            get_logger().error("Unknown error during OpenAI inference: ", e)
            raise openai.APIError from e
        if response is None or len(response["choices"]) == 0:
            raise openai.APIError
        else:
            resp = response["choices"][0]['message']['content']
            finish_reason = response["choices"][0]["finish_reason"]
            get_logger().debug(f"\nAI response:\n{resp}")

            # log the full response for debugging
            response_log = self.prepare_logs(response, system, user, resp, finish_reason)
            get_logger().debug("Full_response", artifact=response_log)

            # for CLI debugging
            if get_settings().config.verbosity_level >= 2:
                get_logger().info(f"\nAI response:\n{resp}")

        return resp, finish_reason