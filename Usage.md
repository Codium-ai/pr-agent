## Usage Guide

### Table of Contents
- [Introduction](#introduction)
- [Working from a local repo (CLI)](#working-from-a-local-repo-cli)
- [Online usage](#online-usage)
- [Working with GitHub App](#working-with-github-app)
- [Working with GitHub Action](#working-with-github-action)
- [Changing a model](#changing-a-model)
- [Working with large PRs](#working-with-large-prs)
- [Appendix - additional configurations walkthrough](#appendix---additional-configurations-walkthrough)

### Introduction

After [installation](/INSTALL.md), there are three basic ways to invoke CodiumAI PR-Agent:
1. Locally running a CLI command
2. Online usage - by [commenting](https://github.com/Codium-ai/pr-agent/pull/229#issuecomment-1695021901) on a PR
3. Enabling PR-Agent tools to run automatically when a new PR is opened


Specifically, CLI commands can be issued by invoking a pre-built [docker image](/INSTALL.md#running-from-source), or by invoking a [locally cloned repo](INSTALL.md#method-2-run-from-source).
For online usage, you will need to setup either a [GitHub App](INSTALL.md#method-5-run-as-a-github-app), or a [GitHub Action](INSTALL.md#method-3-run-as-a-github-action).
GitHub App and GitHub Action also enable to run PR-Agent specific tool automatically when a new PR is opened.


#### The configuration file
The different tools and sub-tools used by CodiumAI PR-Agent are adjustable via the **[configuration file](pr_agent/settings/configuration.toml)**.
In addition to general configuration options, each tool has its own configurations. For example, the `review` tool will use parameters from the [pr_reviewer](/pr_agent/settings/configuration.toml#L16) section in the configuration file.

The [Tools Guide](./docs/TOOLS_GUIDE.md) provides a detailed description of the different tools and their configurations.

#### Ignoring files from analysis
In some cases, you may want to exclude specific files or directories from the analysis performed by CodiumAI PR-Agent. This can be useful, for example, when you have files that are generated automatically or files that shouldn't be reviewed, like vendored code.

To ignore files or directories, edit the **[ignore.toml](/pr_agent/settings/ignore.toml)** configuration file. This setting also exposes the following environment variables:

 - `IGNORE.GLOB`
 - `IGNORE.REGEX`

For example, to ignore python files in a PR with online usage, comment on a PR:
`/review --ignore.glob=['*.py']`

To ignore python files in all PRs, set in a configuration file:
```
[ignore]
glob = ['*.py']
```

#### git provider
The [git_provider](pr_agent/settings/configuration.toml#L4) field in the configuration file determines the GIT provider that will be used by PR-Agent. Currently, the following providers are supported:
`
"github", "gitlab", "azure", "codecommit", "local", "gerrit"
`

[//]: # (** online usage:**)

[//]: # (Options that are available in the configuration file can be specified at run time when calling actions. Two examples:)

[//]: # (```)

[//]: # (- /review --pr_reviewer.extra_instructions="focus on the file: ...")

[//]: # (- /describe --pr_description.add_original_user_description=false -pr_description.extra_instructions="make sure to mention: ...")

[//]: # (```)

### Working from a local repo (CLI)
When running from your local repo (CLI), your local configuration file will be used.
Examples of invoking the different tools via the CLI:

- **Review**:       `python -m pr_agent.cli --pr_url=<pr_url>  review`
- **Describe**:     `python -m pr_agent.cli --pr_url=<pr_url>  describe`
- **Improve**:      `python -m pr_agent.cli --pr_url=<pr_url>  improve`
- **Ask**:          `python -m pr_agent.cli --pr_url=<pr_url>  ask "Write me a poem about this PR"`
- **Reflect**:      `python -m pr_agent.cli --pr_url=<pr_url>  reflect`
- **Update Changelog**:      `python -m pr_agent.cli --pr_url=<pr_url>  update_changelog`

`<pr_url>` is the url of the relevant PR (for example: https://github.com/Codium-ai/pr-agent/pull/50).

**Notes:**

(1) in addition to editing your local configuration file, you can also change any configuration value by adding it to the command line:
```
python -m pr_agent.cli --pr_url=<pr_url>  /review --pr_reviewer.extra_instructions="focus on the file: ..."
```

(2) You can print results locally, without publishing them, by setting in `configuration.toml`:
```
[config]
publish_output=true
verbosity_level=2
```
This is useful for debugging or experimenting with different tools.


### Online usage

Online usage means invoking PR-Agent tools by [comments](https://github.com/Codium-ai/pr-agent/pull/229#issuecomment-1695021901) on a PR.
Commands for invoking the different tools via comments:

- **Review**:       `/review`
- **Describe**:     `/describe`
- **Improve**:      `/improve`
- **Ask**:          `/ask "..."`
- **Reflect**:      `/reflect`
- **Update Changelog**:      `/update_changelog`


To edit a specific configuration value, just add `--config_path=<value>` to any command.
For example, if you want to edit the `review` tool configurations, you can run:
```
/review --pr_reviewer.extra_instructions="..." --pr_reviewer.require_score_review=false
```
Any configuration value in [configuration file](pr_agent/settings/configuration.toml) file can be similarly edited. Comment `/config` to see the list of available configurations.


### Working with GitHub App
When running PR-Agent from GitHub App, the default [configuration file](pr_agent/settings/configuration.toml) from a pre-built docker will be initially loaded.

By uploading a local `.pr_agent.toml` file to the root of the repo's main branch, you can edit and customize any configuration parameter. Note that you need to upload `.pr_agent.toml` prior to creating a PR, in order for the configuration to take effect.

For example, if you set in `.pr_agent.toml`:

```
[pr_reviewer]
num_code_suggestions=1
```

Then you will overwrite the default number of code suggestions to 1.

#### GitHub app automatic tools
The [github_app](pr_agent/settings/configuration.toml#L76) section defines GitHub app-specific configurations.  
In this section you can define configurations to control the conditions for which tools will **run automatically**.  

##### GitHub app automatic tools for PR actions
The GitHub app can respond to the following actions on a PR:
1. `opened` - Opening a new PR
2. `reopened` - Reopening a closed PR
3. `ready_for_review` - Moving a PR from Draft to Open
4. `review_requested` - Specifically requesting review (in the PR reviewers list) from the `github-actions[bot]` user

The configuration parameter `handle_pr_actions` defines the list of actions for which the GitHub app will trigger the PR-Agent.  
The configuration parameter `pr_commands` defines the list of tools that will be **run automatically** when one of the above actions happens (e.g., a new PR is opened):
```
[github_app]
handle_pr_actions = ['opened', 'reopened', 'ready_for_review', 'review_requested']
pr_commands = [
    "/describe --pr_description.add_original_user_description=true --pr_description.keep_original_user_title=true",
    "/auto_review",
]
```
This means that when a new PR is opened/reopened or marked as ready for review, PR-Agent will run the `describe` and `auto_review` tools.  
For the describe tool, the `add_original_user_description` and `keep_original_user_title` parameters will be set to true.

You can override the default tool parameters by uploading a local configuration file called `.pr_agent.toml` to the root of your repo.
For example, if your local `.pr_agent.toml` file contains:
```
[pr_description]
add_original_user_description = false
keep_original_user_title = false
```
When a new PR is opened, PR-Agent will run the `describe` tool with the above parameters.

To cancel the automatic run of all the tools, set:
```
[github_app]
handle_pr_actions = []
```

##### GitHub app automatic tools for new code (PR push)
In addition to running automatic tools when a PR is opened, the GitHub app can also respond to new code that is pushed to an open PR.

The configuration toggle `handle_push_trigger` can be used to enable this feature.  
The configuration parameter `push_commands` defines the list of tools that will be **run automatically** when new code is pushed to the PR.
```
[github_app]
handle_push_trigger = true
push_commands = [
    "/describe --pr_description.add_original_user_description=true --pr_description.keep_original_user_title=true",
    "/auto_review -i --pr_reviewer.remove_previous_review_comment=true",
]
```
This means that when new code is pushed to the PR, the PR-Agent will run the `describe` and incremental `auto_review` tools.  
For the describe tool, the `add_original_user_description` and `keep_original_user_title` parameters will be set to true.  
For the `auto_review` tool, it will run in incremental mode, and the `remove_previous_review_comment` parameter will be set to true.

Much like the configurations for `pr_commands`, you can override the default tool parameters by uploading a local configuration file to the root of your repo.

#### Editing the prompts
The prompts for the various PR-Agent tools are defined in the `pr_agent/settings` folder.
In practice, the prompts are loaded and stored as a standard setting object.
Hence, editing them is similar to editing any other configuration value - just place the relevant key in `.pr_agent.toml`file, and override the default value.

For example, if you want to edit the prompts of the [describe](./pr_agent/settings/pr_description_prompts.toml) tool, you can add the following to your `.pr_agent.toml` file:
```
[pr_description_prompt]
system="""
...
"""
user="""
...
"""
```
Note that the new prompt will need to generate an output compatible with the relevant [post-process function](./pr_agent/tools/pr_description.py#L137).

### Working with GitHub Action
You can configure settings in GitHub action by adding environment variables under the env section in `.github/workflows/pr_agent.yml` file. 
Specifically, start by setting the following environment variables:
```yaml
      env:
        OPENAI_KEY: ${{ secrets.OPENAI_KEY }} # Make sure to add your OpenAI key to your repo secrets
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }} # Make sure to add your GitHub token to your repo secrets
        github_action.auto_review: "true" # enable\disable auto review
        github_action.auto_describe: "true" # enable\disable auto describe
        github_action.auto_improve: "false" # enable\disable auto improve
```
`github_action.auto_review`, `github_action.auto_describe` and `github_action.auto_improve` are used to enable/disable automatic tools that run when a new PR is opened.
If not set, the default option is that only the `review` tool will run automatically when a new PR is opened.

Note that you can give additional config parameters by adding environment variables to `.github/workflows/pr_agent.yml`, or by using a `.pr_agent.toml` file in the root of your repo, similar to the GitHub App usage.

For example, you can set an environment variable: `pr_description.add_original_user_description=false`, or add a `.pr_agent.toml` file with the following content:
```
[pr_description]
add_original_user_description = false
```


### Changing a model

See [here](pr_agent/algo/__init__.py) for the list of available models.
To use a different model than the default (GPT-4), you need to edit [configuration file](pr_agent/settings/configuration.toml#L2).
For models and environments not from OPENAI, you might need to provide additional keys and other parameters. See below for instructions.

#### Azure
To use Azure, set in your `.secrets.toml` (working from CLI), or in the GitHub `Settings > Secrets and variables` (working from GitHub App or GitHub Action):
```
api_key = "" # your azure api key
api_type = "azure"
api_version = '2023-05-15'  # Check Azure documentation for the current API version
api_base = ""  # The base URL for your Azure OpenAI resource. e.g. "https://<your resource name>.openai.azure.com"
openai.deployment_id = ""  # The deployment name you chose when you deployed the engine
```

and set in your configuration file:
```
[config]
model="" # the OpenAI model you've deployed on Azure (e.g. gpt-3.5-turbo)
```

#### Huggingface

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

**Inference Endpoints**

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

#### Replicate

To use Llama2 model with Replicate, for example, set:
```
[config] # in configuration.toml
model = "replicate/llama-2-70b-chat:2c1608e18606fad2812020dc541930f2d0495ce32eee50074220b87300bc16e1"
[replicate] # in .secrets.toml
key = ...
```
(you can obtain a Llama2 key from [here](https://replicate.com/replicate/llama-2-70b-chat/api))


Also review the [AiHandler](pr_agent/algo/ai_handler.py) file for instruction how to set keys for other models.

#### Vertex AI

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

#### Amazon Bedrock

To use Amazon Bedrock and its foundational models, add the below configuration:

``` 
[config] # in configuration.toml
model = "anthropic.claude-v2"
fallback_models="anthropic.claude-instant-v1"

[aws] # in .secrets.toml
bedrock_region = "us-east-1"
```

Note that you have to add access to foundational models before using them. Please refer to [this document](https://docs.aws.amazon.com/bedrock/latest/userguide/setting-up.html) for more details.

AWS session is automatically authenticated from your environment, but you can also explicitly set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` environment variables.

### Working with large PRs

The default mode of CodiumAI is to have a single call per tool, using GPT-4, which has a token limit of 8000 tokens.
This mode provide a very good speed-quality-cost tradeoff, and can handle most PRs successfully.
When the PR is above the token limit, it employs a [PR Compression strategy](./PR_COMPRESSION.md).

However, for very large PRs, or in case you want to emphasize quality over speed and cost, there are 2 possible solutions:
1) [Use a model](#changing-a-model) with larger context, like GPT-32K, or claude-100K. This solution will be applicable for all the tools.
2) For the `/improve` tool, there is an ['extended' mode](./docs/IMPROVE.md) (`/improve --extended`),
which divides the PR to chunks, and process each chunk separately. With this mode, regardless of the model, no compression will be done (but for large PRs, multiple model calls may occur)

### Appendix - additional configurations walkthrough


#### Extra instructions
All PR-Agent tools have a parameter called `extra_instructions`, that enables to add free-text extra instructions. Example usage:
```
/update_changelog --pr_update_changelog.extra_instructions="Make sure to update also the version ..."
```

#### Patch Extra Lines
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
If the PR is too large (see [PR Compression strategy](./PR_COMPRESSION.md)), PR-Agent automatically sets this number to 0, using the original git patch.


#### Azure DevOps provider
To use Azure DevOps provider use the following settings in configuration.toml:
```
[config]
git_provider="azure"
use_repo_settings_file=false
```

And use the following settings (you have to replace the values) in .secrets.toml:
```
[azure_devops]
org = "https://dev.azure.com/YOUR_ORGANIZATION/"
pat = "YOUR_PAT_TOKEN"
```
