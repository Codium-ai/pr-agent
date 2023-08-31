## Configuration

The different tools and sub-tools used by CodiumAI PR-Agent are adjustable via the **[configuration file](pr_agent/settings/configuration.toml)**

### Working from CLI
When running from source (CLI), your local configuration file will be initially used.

Example for invoking the 'review' tools via the CLI: 

```
python cli.py --pr-url=<pr_url>  review
```
In addition to general configurations, the 'review' tool will use parameters from the `[pr_reviewer]` section (every tool has a dedicated section in the configuration file).

Note that you can print results locally, without publishing them, by setting in `configuration.toml`:

```
[config]
publish_output=true
verbosity_level=2
```
This is useful for debugging or experimenting with the different tools.

### Working from GitHub App (pre-built repo)
When running PR-Agent from GitHub App, the default configuration file (`configuration.toml`) will be loaded.

#### GitHub app default tools
The `[github_app]` section of the configuration file defines GitHub app specific configurations. 
The important parameter is `pr_commands`, which is a list of tools that will be run automatically when a new PR is opened:
```
[github_app]
pr_commands = [
    "/describe --pr_description.add_original_user_description=true --pr_description.keep_original_user_title=true",
    "/auto_review",
]
```
This means that when a new PR is opened, PR-Agent will run the `describe` and `auto_review` tools.
For the describe tool, the `add_original_user_description` and `keep_original_user_title` parameters will be set to `true`.

However, you can override the default tool parameters by uploading a local configuration file called `.pr_agent.toml` to the root of your repo.
For example, if your local `.pr_agent.toml` file contains:
```
[pr_description]
add_original_user_description = false
keep_original_user_title = false
```
Then when a new PR is opened, PR-Agent will run the `describe` tool with the above parameters.

Note that a local `.pr_agent.toml` file enables you to edit and customize the default parameters of any tool, not just the ones that are run automatically.

#### Online usage
For online usage (calling tools by comments on a PR like `/ask ...`), just add `--config_path=<value>` to any command, to edit a specific configuration value.
For example if you want to edit `pr_reviewer` configurations, you can run:
```
/review --pr_reviewer.extra_instructions="..." --pr_reviewer.require_score_review=false ...
```
Any configuration value in `configuration.toml` file can be similarly edited.


### General configuration walkthrough

#### Changing a model
See [here](pr_agent/algo/__init__.py) for the list of available models.

To use Llama2 model, for example, set:
```
[config]
model = "replicate/llama-2-70b-chat:2c1608e18606fad2812020dc541930f2d0495ce32eee50074220b87300bc16e1"
[replicate]
key = ...
```
(you can obtain a Llama2 key from [here](https://replicate.com/replicate/llama-2-70b-chat/api))

Also review the [AiHandler](pr_agent/algo/ai_handler.py) file for instruction how to set keys for other models.

#### Changing a GIT provider
See [here](pr_agent/git_providers/__init__.py) for the list of GIT providers.

To use GitHub, for example, set:
```
[config]
git_provider="github"
```

#### Extra instructions
##### General
All PR-Agent tools have a parameter called `extra_instructions`, that enables to add free-text extra instructions. Example usage:
```
/update_changelog --pr_update_changelog.extra_instructions="Make sure to update also the version ..."
```

##### Azure DevOps provider
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