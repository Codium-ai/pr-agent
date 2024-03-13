## Ignoring files from analysis

In some cases, you may want to exclude specific files or directories from the analysis performed by CodiumAI PR-Agent. This can be useful, for example, when you have files that are generated automatically or files that shouldn't be reviewed, like vendored code.

To ignore files or directories, edit the **[ignore.toml](https://github.com/Codium-ai/pr-agent/blob/main/pr_agent/settings/ignore.toml)** configuration file. This setting also exposes the following environment variables:

 - `IGNORE.GLOB`
 - `IGNORE.REGEX`

For example, to ignore python files in a PR with online usage, comment on a PR:
`/review --ignore.glob=['*.py']`

To ignore python files in all PRs, set in a configuration file:
```
[ignore]
glob = ['*.py']
```

## Extra instructions

All PR-Agent tools have a parameter called `extra_instructions`, that enables to add free-text extra instructions. Example usage:
```
/update_changelog --pr_update_changelog.extra_instructions="Make sure to update also the version ..."
```

## Working with large PRs

The default mode of CodiumAI is to have a single call per tool, using GPT-4, which has a token limit of 8000 tokens.
This mode provide a very good speed-quality-cost tradeoff, and can handle most PRs successfully.
When the PR is above the token limit, it employs a [PR Compression strategy](../core-abilities/index.md).

However, for very large PRs, or in case you want to emphasize quality over speed and cost, there are 2 possible solutions:
1) [Use a model](https://codium-ai.github.io/Docs-PR-Agent/usage-guide/#changing-a-model) with larger context, like GPT-32K, or claude-100K. This solution will be applicable for all the tools.
2) For the `/improve` tool, there is an ['extended' mode](https://codium-ai.github.io/Docs-PR-Agent/tools/#improve) (`/improve --extended`),
which divides the PR to chunks, and process each chunk separately. With this mode, regardless of the model, no compression will be done (but for large PRs, multiple model calls may occur)


## Changing a model

See [here](https://github.com/Codium-ai/pr-agent/blob/main/pr_agent/algo/__init__.py) for the list of available models.
To use a different model than the default (GPT-4), you need to edit [configuration file](https://github.com/Codium-ai/pr-agent/blob/main/pr_agent/settings/configuration.toml#L2).
For models and environments not from OPENAI, you might need to provide additional keys and other parameters. See below for instructions.

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
```

### Huggingface

**Local**
You can run Huggingface models locally through either [VLLM](https://docs.litellm.ai/docs/providers/vllm) or [Ollama](https://docs.litellm.ai/docs/providers/ollama)

E.g. to use a new Huggingface model locally via Ollama, set:
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

[ollama] # in .secrets.toml
api_base = ... # the base url for your huggingface inference endpoint
# e.g. if running Ollama locally, you may use:
api_base = "http://localhost:11434/"
```

### Inference Endpoints

To use a new model with Huggingface Inference Endpoints, for example, set:
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

[huggingface] # in .secrets.toml
key = ... # your huggingface api key
api_base = ... # the base url for your huggingface inference endpoint
```
(you can obtain a Llama2 key from [here](https://replicate.com/replicate/llama-2-70b-chat/api))

### Replicate

To use Llama2 model with Replicate, for example, set:
```
[config] # in configuration.toml
model = "replicate/llama-2-70b-chat:2c1608e18606fad2812020dc541930f2d0495ce32eee50074220b87300bc16e1"
[replicate] # in .secrets.toml
key = ...
```
(you can obtain a Llama2 key from [here](https://replicate.com/replicate/llama-2-70b-chat/api))


Also review the [AiHandler](https://github.com/Codium-ai/pr-agent/blob/main/pr_agent/algo/ai_handler.py) file for instruction how to set keys for other models.

### Vertex AI

To use Google's Vertex AI platform and its associated models (chat-bison/codechat-bison) set:

``` 
[config] # in configuration.toml
model = "vertex_ai/codechat-bison"
fallback_models="vertex_ai/codechat-bison"

[vertexai] # in .secrets.toml
vertex_project = "my-google-cloud-project"
vertex_location = ""
```

Your [application default credentials](https://cloud.google.com/docs/authentication/application-default-credentials) will be used for authentication so there is no need to set explicit credentials in most environments.

If you do want to set explicit credentials then you can use the `GOOGLE_APPLICATION_CREDENTIALS` environment variable set to a path to a json credentials file.

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

[aws] # in .secrets.toml
bedrock_region = "us-east-1"
```

Note that you have to add access to foundational models before using them. Please refer to [this document](https://docs.aws.amazon.com/bedrock/latest/userguide/setting-up.html) for more details.

If you are using the claude-3 model, please configure the following settings as there are parameters incompatible with claude-3.
```
[litellm]
drop_params = true
```

AWS session is automatically authenticated from your environment, but you can also explicitly set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` environment variables.


## Patch Extra Lines

By default, around any change in your PR, git patch provides 3 lines of context above and below the change.
```
@@ -12,5 +12,5 @@ def func1():
 code line that already existed in the file...
 code line that already existed in the file...
 code line that already existed in the file....
-code line that was removed in the PR
+new code line added in the PR
 code line that already existed in the file...
 code line that already existed in the file...
 code line that already existed in the file...
```

For the `review`, `describe`, `ask` and `add_docs` tools, if the token budget allows, PR-Agent tries to increase the number of lines of context, via the parameter:
```
[config]
patch_extra_lines=3
```

Increasing this number provides more context to the model, but will also increase the token budget.
If the PR is too large (see [PR Compression strategy](https://github.com/Codium-ai/pr-agent/blob/main/PR_COMPRESSION.md)), PR-Agent automatically sets this number to 0, using the original git patch.


## Editing the prompts

The prompts for the various PR-Agent tools are defined in the `pr_agent/settings` folder.
In practice, the prompts are loaded and stored as a standard setting object.
Hence, editing them is similar to editing any other configuration value - just place the relevant key in `.pr_agent.toml`file, and override the default value.

For example, if you want to edit the prompts of the [describe](https://github.com/Codium-ai/pr-agent/blob/main/pr_agent/settings/pr_description_prompts.toml) tool, you can add the following to your `.pr_agent.toml` file:
```
[pr_description_prompt]
system="""
...
"""
user="""
...
"""
```
Note that the new prompt will need to generate an output compatible with the relevant [post-process function](https://github.com/Codium-ai/pr-agent/blob/main/pr_agent/tools/pr_description.py#L137).
