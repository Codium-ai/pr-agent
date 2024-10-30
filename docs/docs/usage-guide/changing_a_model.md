## Changing a model

See [here](https://github.com/Codium-ai/pr-agent/blob/main/pr_agent/algo/__init__.py) for a list of available models.
To use a different model than the default (GPT-4), you need to edit in the [configuration file](https://github.com/Codium-ai/pr-agent/blob/main/pr_agent/settings/configuration.toml#L2) the fields:
```
[config]
model = "..."
model_turbo = "..."
fallback_models = ["..."]
```

For models and environments not from OpenAI, you might need to provide additional keys and other parameters.
You can give parameters via a configuration file (see below for instructions), or from environment variables. See [litellm documentation](https://litellm.vercel.app/docs/proxy/quick_start#supported-llms) for the environment variables relevant per model.

### Azure

To use Azure, set in your `.secrets.toml` (working from CLI), or in the GitHub `Settings > Secrets and variables` (working from GitHub App or GitHub Action):
```
[openai]
key = "" # your azure api key
api_type = "azure"
api_version = '2023-05-15'  # Check Azure documentation for the current API version
api_base = ""  # The base URL for your Azure OpenAI resource. e.g. "https://<your resource name>.openai.azure.com"
deployment_id = ""  # The deployment name you chose when you deployed the engine
```

and set in your configuration file:
```
[config]
model="" # the OpenAI model you've deployed on Azure (e.g. gpt-3.5-turbo)
model_turbo="" # the OpenAI model you've deployed on Azure (e.g. gpt-3.5-turbo)
fallback_models=["..."] # the OpenAI model you've deployed on Azure (e.g. gpt-3.5-turbo)
```

### Hugging Face

**Local**
You can run Hugging Face models locally through either [VLLM](https://docs.litellm.ai/docs/providers/vllm) or [Ollama](https://docs.litellm.ai/docs/providers/ollama)

E.g. to use a new Hugging Face model locally via Ollama, set:
```
[__init__.py]
MAX_TOKENS = {
    "model-name-on-ollama": <max_tokens>
}
e.g.
MAX_TOKENS={
    ...,
    "ollama/llama2": 4096
}


[config] # in configuration.toml
model = "ollama/llama2"
model_turbo = "ollama/llama2"
fallback_models=["ollama/llama2"]

[ollama] # in .secrets.toml
api_base = ... # the base url for your Hugging Face inference endpoint
# e.g. if running Ollama locally, you may use:
api_base = "http://localhost:11434/"
```

### Inference Endpoints

To use a new model with Hugging Face Inference Endpoints, for example, set:
```
[__init__.py]
MAX_TOKENS = {
    "model-name-on-huggingface": <max_tokens>
}
e.g.
MAX_TOKENS={
    ...,
    "meta-llama/Llama-2-7b-chat-hf": 4096
}
[config] # in configuration.toml
model = "huggingface/meta-llama/Llama-2-7b-chat-hf"
model_turbo = "huggingface/meta-llama/Llama-2-7b-chat-hf"
fallback_models=["huggingface/meta-llama/Llama-2-7b-chat-hf"]

[huggingface] # in .secrets.toml
key = ... # your Hugging Face api key
api_base = ... # the base url for your Hugging Face inference endpoint
```
(you can obtain a Llama2 key from [here](https://replicate.com/replicate/llama-2-70b-chat/api))

### Replicate

To use Llama2 model with Replicate, for example, set:
```
[config] # in configuration.toml
model = "replicate/llama-2-70b-chat:2c1608e18606fad2812020dc541930f2d0495ce32eee50074220b87300bc16e1"
model_turbo = "replicate/llama-2-70b-chat:2c1608e18606fad2812020dc541930f2d0495ce32eee50074220b87300bc16e1"
fallback_models=["replicate/llama-2-70b-chat:2c1608e18606fad2812020dc541930f2d0495ce32eee50074220b87300bc16e1"]
[replicate] # in .secrets.toml
key = ...
```
(you can obtain a Llama2 key from [here](https://replicate.com/replicate/llama-2-70b-chat/api))


Also, review the [AiHandler](https://github.com/Codium-ai/pr-agent/blob/main/pr_agent/algo/ai_handler.py) file for instructions on how to set keys for other models.

### Groq

To use Llama3 model with Groq, for example, set:
```
[config] # in configuration.toml
model = "llama3-70b-8192"
model_turbo = "llama3-70b-8192"
fallback_models = ["groq/llama3-70b-8192"]
[groq] # in .secrets.toml
key = ... # your Groq api key
```
(you can obtain a Groq key from [here](https://console.groq.com/keys))

### Vertex AI

To use Google's Vertex AI platform and its associated models (chat-bison/codechat-bison) set:

```
[config] # in configuration.toml
model = "vertex_ai/codechat-bison"
model_turbo = "vertex_ai/codechat-bison"
fallback_models="vertex_ai/codechat-bison"

[vertexai] # in .secrets.toml
vertex_project = "my-google-cloud-project"
vertex_location = ""
```

Your [application default credentials](https://cloud.google.com/docs/authentication/application-default-credentials) will be used for authentication so there is no need to set explicit credentials in most environments.

If you do want to set explicit credentials, then you can use the `GOOGLE_APPLICATION_CREDENTIALS` environment variable set to a path to a json credentials file.

### Google AI Studio

To use [Google AI Studio](https://aistudio.google.com/) models, set the relevant models in the configuration section of the configuration file:

```toml
[config] # in configuration.toml
model="google_ai_studio/gemini-1.5-flash"
model_turbo="google_ai_studio/gemini-1.5-flash"
fallback_models=["google_ai_studio/gemini-1.5-flash"]

[google_ai_studio] # in .secrets.toml
gemini_api_key = "..."
```

If you don't want to set the API key in the .secrets.toml file, you can set the `GOOGLE_AI_STUDIO.GEMINI_API_KEY` environment variable.

### Anthropic

To use Anthropic models, set the relevant models in the configuration section of the configuration file:

```
[config]
model="anthropic/claude-3-opus-20240229"
model_turbo="anthropic/claude-3-opus-20240229"
fallback_models=["anthropic/claude-3-opus-20240229"]
```

And also set the api key in the .secrets.toml file:
```
[anthropic]
KEY = "..."
```

### Amazon Bedrock

To use Amazon Bedrock and its foundational models, add the below configuration:

```
[config] # in configuration.toml
model="bedrock/anthropic.claude-3-sonnet-20240229-v1:0"
model_turbo="bedrock/anthropic.claude-3-sonnet-20240229-v1:0"
fallback_models=["bedrock/anthropic.claude-v2:1"]
```

Note that you have to add access to foundational models before using them. Please refer to [this document](https://docs.aws.amazon.com/bedrock/latest/userguide/setting-up.html) for more details.

If you are using the claude-3 model, please configure the following settings as there are parameters incompatible with claude-3.
```
[litellm]
drop_params = true
```

AWS session is automatically authenticated from your environment, but you can also explicitly set `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` and `AWS_REGION_NAME` environment variables. Please refer to [this document](https://litellm.vercel.app/docs/providers/bedrock) for more details.

### Custom models

If the relevant model doesn't appear [here](https://github.com/Codium-ai/pr-agent/blob/main/pr_agent/algo/__init__.py), you can still use it as a custom model:

(1) Set the model name in the configuration file:
```
[config]
model="custom_model_name"
model_turbo="custom_model_name"
fallback_models=["custom_model_name"]
```
(2) Set the maximal tokens for the model:
```
[config]
custom_model_max_tokens= ...
```
(3) Go to [litellm documentation](https://litellm.vercel.app/docs/proxy/quick_start#supported-llms), find the model you want to use, and set the relevant environment variables.
