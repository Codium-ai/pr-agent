import os
import requests
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
        self.api_base = None
        self.repetition_penalty = None
        """
        get_settings().set("watsonx.url", watsonx_url)
        get_settings().set("watsonx.iam_api_key", iam_api_key)
        get_settings().set("watsonx.project_id", project_id)
        common_cloud_provider_auth_params: dict = {
          "params": ["project", "region_name", "token"],
          "providers": ["vertex_ai", "bedrock", "watsonx", "azure"],
        }
        """
        if get_settings().get("watsonx.url", None) and \
           get_settings().get("watsonx.iam_api_key", None) and \
           get_settings().get("watsonx.project_id", None):
            os.environ["WATSONX_URL"] = get_settings().watsonx.url
            os.environ["WATSONX_APIKEY"] = get_settings().watsonx.iam_api_key
            os.environ["WATSONX_PROJECT_ID"] = get_settings().watsonx.project_id

        if get_settings().get("OPENAI.KEY", None):
            openai.api_key = get_settings().openai.key
            litellm.openai_key = get_settings().openai.key
        elif 'OPENAI_API_KEY' not in os.environ:
            litellm.api_key = "dummy_key"
        if get_settings().get("aws.AWS_ACCESS_KEY_ID"):
            assert get_settings().aws.AWS_SECRET_ACCESS_KEY and get_settings().aws.AWS_REGION_NAME, "AWS credentials are incomplete"
            os.environ["AWS_ACCESS_KEY_ID"] = get_settings().aws.AWS_ACCESS_KEY_ID
            os.environ["AWS_SECRET_ACCESS_KEY"] = get_settings().aws.AWS_SECRET_ACCESS_KEY
            os.environ["AWS_REGION_NAME"] = get_settings().aws.AWS_REGION_NAME
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
        if get_settings().get("GROQ.KEY", None):
            litellm.api_key = get_settings().groq.key
        if get_settings().get("REPLICATE.KEY", None):
            litellm.replicate_key = get_settings().replicate.key
        if get_settings().get("HUGGINGFACE.KEY", None):
            litellm.huggingface_key = get_settings().huggingface.key
        if get_settings().get("HUGGINGFACE.API_BASE", None) and 'huggingface' in get_settings().config.model:
            litellm.api_base = get_settings().huggingface.api_base
            self.api_base = get_settings().huggingface.api_base
        if get_settings().get("OLLAMA.API_BASE", None):
            litellm.api_base = get_settings().ollama.api_base
            self.api_base = get_settings().ollama.api_base
        if get_settings().get("HUGGINGFACE.REPETITION_PENALTY", None):
            self.repetition_penalty = float(get_settings().huggingface.repetition_penalty)
        if get_settings().get("VERTEXAI.VERTEX_PROJECT", None):
            litellm.vertex_project = get_settings().vertexai.vertex_project
            litellm.vertex_location = get_settings().get(
                "VERTEXAI.VERTEX_LOCATION", None
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
        retry=retry_if_exception_type((openai.APIError, openai.APIConnectionError, openai.APITimeoutError)), # No retry on RateLimitError
        stop=stop_after_attempt(OPENAI_RETRIES)
    )
    async def chat_completion(self, model: str, system: str, user: str, temperature: float = 0.2, img_path: str = None):
        try:
            resp, finish_reason = None, None
            deployment_id = self.deployment_id
            if self.azure:
                model = 'azure/' + model
            messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
            if img_path:
                try:
                    # check if the image link is alive
                    r = requests.head(img_path, allow_redirects=True)
                    if r.status_code == 404:
                        error_msg = f"The image link is not [alive](img_path).\nPlease repost the original image as a comment, and send the question again with 'quote reply' (see [instructions](https://pr-agent-docs.codium.ai/tools/ask/#ask-on-images-using-the-pr-code-as-context))."
                        get_logger().error(error_msg)
                        return f"{error_msg}", "error"
                except Exception as e:
                    get_logger().error(f"Error fetching image: {img_path}", e)
                    return f"Error fetching image: {img_path}", "error"
                messages[1]["content"] = [{"type": "text", "text": messages[1]["content"]},
                                          {"type": "image_url", "image_url": {"url": img_path}}]

            kwargs = {
                "model": model,
                "deployment_id": deployment_id,
                "messages": messages,
                "temperature": temperature,
                "force_timeout": get_settings().config.ai_timeout,
                "api_base": self.api_base,
            }
            if self.repetition_penalty:
                kwargs["repetition_penalty"] = self.repetition_penalty

            get_logger().debug("Prompts", artifact={"system": system, "user": user})

            if get_settings().config.verbosity_level >= 2:
                get_logger().info(f"\nSystem prompt:\n{system}")
                get_logger().info(f"\nUser prompt:\n{user}")

            response = await acompletion(**kwargs)
        except (openai.APIError, openai.APITimeoutError) as e:
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
