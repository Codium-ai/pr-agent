## Configuration

The different tools and sub-tools used by CodiumAI PR-Agent are adjustable via the **[configuration file](pr_agent/settings/configuration.toml)**

The `git_provider` field in the configuration file determines the GIT provider that will be used by PR-Agent. Currently, the following providers are supported:
`
"github", "gitlab", "azure", "codecommit", "local"
`

Options that are available in the configuration file can be specified at run time when calling actions. Two examples:
```
- /review --pr_reviewer.extra_instructions="focus on the file: ..."
- /describe --pr_description.add_original_user_description=false -pr_description.extra_instructions="make sure to mention: ..."
```

### Working from CLI
When running from source (CLI), your local configuration file will be used.

Examples for invoking the different tools via the CLI:

- **Review**:       `python cli.py --pr_url=<pr_url>  review`
- **Describe**:     `python cli.py --pr_url=<pr_url>  describe`
- **Improve**:      `python cli.py --pr_url=<pr_url>  improve`
- **Ask**:          `python cli.py --pr_url=<pr_url>  ask "Write me a poem about this PR"`
- **Reflect**:      `python cli.py --pr_url=<pr_url>  reflect`
- **Update Changelog**:      `python cli.py --pr_url=<pr_url>  update_changelog`

`<pr_url>` is the url of the relevant PR (for example: https://github.com/Codium-ai/pr-agent/pull/50).

**Notes:**

(1) In addition to general configuration options, each tool has its own configurations. For example, the 'review' tool will use parameters from the `[pr_reviewer]` section in the [configuration file](/pr_agent/settings/configuration.toml#L16)

(2) You can print results locally, without publishing them, by setting in `configuration.toml`:
```
[config]
publish_output=true
verbosity_level=2
```
This is useful for debugging or experimenting with the different tools.

### Working from GitHub App (pre-built repo)
When running PR-Agent from GitHub App, the default configuration file (`configuration.toml`) will be initially loaded.

#### GitHub app default tools
The `[github_app]` section defines the GitHub app specific configurations. 
An important parameter is `pr_commands`, which is a list of tools that will be run automatically when a new PR is opened:
```
[github_app]
pr_commands = [
    "/describe --pr_description.add_original_user_description=true --pr_description.keep_original_user_title=true",
    "/auto_review",
]
```
This means that when a new PR is opened, PR-Agent will run the `describe` and `auto_review` tools.
For the describe tool, the `add_original_user_description` and `keep_original_user_title` parameters will be set to true.

However, you can override the default tool parameters by uploading a local configuration file called `.pr_agent.toml` to the root of your repo.
For example, if your local `.pr_agent.toml` file contains:
```
[pr_description]
add_original_user_description = false
keep_original_user_title = false
```
Then when a new PR is opened, PR-Agent will run the `describe` tool with the above parameters.

Note that a local `.pr_agent.toml` file enables you to edit and customize the default parameters of any tool, not just the ones that are run automatically.

#### Editing the prompts
The prompts for the various PR-Agent tools are defined in the `pr_agent/settings` folder.

In practice, the prompts are loaded and stored as a standard setting object. Hence,
editing them is similar to editing any other configuration value - just place the relevant key in `.pr_agent.toml`file, and override the default value.

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

#### Extra instructions
All PR-Agent tools have a parameter called `extra_instructions`, that enables to add free-text extra instructions. Example usage:
```
/update_changelog --pr_update_changelog.extra_instructions="Make sure to update also the version ..."
```

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