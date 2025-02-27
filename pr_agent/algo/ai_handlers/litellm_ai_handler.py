import os

import litellm
import openai
import requests
from litellm import acompletion
from tenacity import retry, retry_if_exception_type, stop_after_attempt

from pr_agent.algo import NO_SUPPORT_TEMPERATURE_MODELS, SUPPORT_REASONING_EFFORT_MODELS, USER_MESSAGE_ONLY_MODELS
from pr_agent.algo.ai_handlers.base_ai_handler import BaseAiHandler
from pr_agent.algo.utils import ReasoningEffort, get_version
from pr_agent.config_loader import get_settings
from pr_agent.log import get_logger
import json

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
        if get_settings().get("LITELLM.SUCCESS_CALLBACK", None):
            litellm.success_callback = get_settings().litellm.success_callback
        if get_settings().get("LITELLM.FAILURE_CALLBACK", None):
            litellm.failure_callback = get_settings().litellm.failure_callback
        if get_settings().get("LITELLM.SERVICE_CALLBACK", None):
            litellm.service_callback = get_settings().litellm.service_callback
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
        # Google AI Studio
        # SEE https://docs.litellm.ai/docs/providers/gemini
        if get_settings().get("GOOGLE_AI_STUDIO.GEMINI_API_KEY", None):
          os.environ["GEMINI_API_KEY"] = get_settings().google_ai_studio.gemini_api_key

        # Support deepseek models
        if get_settings().get("DEEPSEEK.KEY", None):
            os.environ['DEEPSEEK_API_KEY'] = get_settings().get("DEEPSEEK.KEY")

        # Models that only use user meessage
        self.user_message_only_models = USER_MESSAGE_ONLY_MODELS

        # Model that doesn't support temperature argument
        self.no_support_temperature_models = NO_SUPPORT_TEMPERATURE_MODELS

        # Models that support reasoning effort
        self.support_reasoning_models = SUPPORT_REASONING_EFFORT_MODELS

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

    def add_litellm_callbacks(selfs, kwargs) -> dict:
        captured_extra = []

        def capture_logs(message):
            # Parsing the log message and context
            record = message.record
            log_entry = {}
            if record.get('extra', None).get('command', None) is not None:
                log_entry.update({"command": record['extra']["command"]})
            if record.get('extra', {}).get('pr_url', None) is not None:
                log_entry.update({"pr_url": record['extra']["pr_url"]})

            # Append the log entry to the captured_logs list
            captured_extra.append(log_entry)

        # Adding the custom sink to Loguru
        handler_id = get_logger().add(capture_logs)
        get_logger().debug("Capturing logs for litellm callbacks")
        get_logger().remove(handler_id)

        context = captured_extra[0] if len(captured_extra) > 0 else None

        command = context.get("command", "unknown")
        pr_url = context.get("pr_url", "unknown")
        git_provider = get_settings().config.git_provider

        metadata = dict()
        callbacks = litellm.success_callback + litellm.failure_callback + litellm.service_callback
        if "langfuse" in callbacks:
            metadata.update({
                "trace_name": command,
                "tags": [git_provider, command, f'version:{get_version()}'],
                "trace_metadata": {
                    "command": command,
                    "pr_url": pr_url,
                },
            })
        if "langsmith" in callbacks:
            metadata.update({
                "run_name": command,
                "tags": [git_provider, command, f'version:{get_version()}'],
                "extra": {
                    "metadata": {
                        "command": command,
                        "pr_url": pr_url,
                    }
                },
            })

        # Adding the captured logs to the kwargs
        kwargs["metadata"] = metadata

        return kwargs

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
            if 'claude' in model and not system:
                system = "No system prompt provided"
                get_logger().warning(
                    "Empty system prompt for claude model. Adding a newline character to prevent OpenAI API error.")
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

            # Currently, some models do not support a separate system and user prompts
            if model in self.user_message_only_models or get_settings().config.custom_reasoning_model:
                user = f"{system}\n\n\n{user}"
                system = ""
                get_logger().info(f"Using model {model}, combining system and user prompts")
                messages = [{"role": "user", "content": user}]
                kwargs = {
                    "model": model,
                    "deployment_id": deployment_id,
                    "messages": messages,
                    "timeout": get_settings().config.ai_timeout,
                    "api_base": self.api_base,
                }
            else:
                kwargs = {
                    "model": model,
                    "deployment_id": deployment_id,
                    "messages": messages,
                    "timeout": get_settings().config.ai_timeout,
                    "api_base": self.api_base,
                }

            # Add temperature only if model supports it
            if model not in self.no_support_temperature_models and not get_settings().config.custom_reasoning_model:
                # get_logger().info(f"Adding temperature with value {temperature} to model {model}.")
                kwargs["temperature"] = temperature

            # Add reasoning_effort if model supports it
            if (model in self.support_reasoning_models):
                supported_reasoning_efforts = [ReasoningEffort.HIGH.value, ReasoningEffort.MEDIUM.value, ReasoningEffort.LOW.value]
                reasoning_effort = get_settings().config.reasoning_effort if (get_settings().config.reasoning_effort in supported_reasoning_efforts) else ReasoningEffort.MEDIUM.value
                get_logger().info(f"Adding reasoning_effort with value {reasoning_effort} to model {model}.")
                kwargs["reasoning_effort"] = reasoning_effort

            if get_settings().litellm.get("enable_callbacks", False):
                kwargs = self.add_litellm_callbacks(kwargs)

            seed = get_settings().config.get("seed", -1)
            if temperature > 0 and seed >= 0:
                raise ValueError(f"Seed ({seed}) is not supported with temperature ({temperature}) > 0")
            elif seed >= 0:
                get_logger().info(f"Using fixed seed of {seed}")
                kwargs["seed"] = seed

            if self.repetition_penalty:
                kwargs["repetition_penalty"] = self.repetition_penalty

            #Added support for extra_headers while using litellm to call underlying model, via a api management gateway, would allow for passing custom headers for security and authorization
            if get_settings().get("LITELLM.EXTRA_HEADERS", None):
                try:
                    litellm_extra_headers = json.loads(get_settings().litellm.extra_headers)
                    if not isinstance(litellm_extra_headers, dict):
                        raise ValueError("LITELLM.EXTRA_HEADERS must be a JSON object")
                except json.JSONDecodeError as e:
                    raise ValueError(f"LITELLM.EXTRA_HEADERS contains invalid JSON: {str(e)}")
                kwargs["extra_headers"] = litellm_extra_headers
            
            get_logger().debug("Prompts", artifact={"system": system, "user": user})
            
            if get_settings().config.verbosity_level >= 2:
                get_logger().info(f"\nSystem prompt:\n{system}")
                get_logger().info(f"\nUser prompt:\n{user}")
                
            response = await acompletion(**kwargs)
        except (openai.APIError, openai.APITimeoutError) as e:
            get_logger().warning(f"Error during LLM inference: {e}")
            raise
        except (openai.RateLimitError) as e:
            get_logger().error(f"Rate limit error during LLM inference: {e}")
            raise
        except (Exception) as e:
            get_logger().warning(f"Unknown error during LLM inference: {e}")
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
