## Local repo (CLI)
When running from your local repo (CLI), your local configuration file will be used.
Examples of invoking the different tools via the CLI:

- **Review**:       `python -m pr_agent.cli --pr_url=<pr_url>  review`
- **Describe**:     `python -m pr_agent.cli --pr_url=<pr_url>  describe`
- **Improve**:      `python -m pr_agent.cli --pr_url=<pr_url>  improve`
- **Ask**:          `python -m pr_agent.cli --pr_url=<pr_url>  ask "Write me a poem about this PR"`
- **Reflect**:      `python -m pr_agent.cli --pr_url=<pr_url>  reflect`
- **Update Changelog**:      `python -m pr_agent.cli --pr_url=<pr_url>  update_changelog`

`<pr_url>` is the url of the relevant PR (for example: [#50](https://github.com/Codium-ai/pr-agent/pull/50)).

**Notes:**

(1) in addition to editing your local configuration file, you can also change any configuration value by adding it to the command line:
```
python -m pr_agent.cli --pr_url=<pr_url>  /review --pr_reviewer.extra_instructions="focus on the file: ..."
```

(2) You can print results locally, without publishing them, by setting in `configuration.toml`:
```
[config]
publish_output=false
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
Any configuration value in [configuration file](https://github.com/Codium-ai/pr-agent/blob/main/pr_agent/settings/configuration.toml) file can be similarly edited. Comment `/config` to see the list of available configurations.


## GitHub App

### GitHub app automatic tools when a new PR is opened

The [github_app](https://github.com/Codium-ai/pr-agent/blob/main/pr_agent/settings/configuration.toml#L108) section defines GitHub app specific configurations.  

The configuration parameter `pr_commands` defines the list of tools that will be **run automatically** when a new PR is opened.
```
[github_app]
pr_commands = [
    "/describe --pr_description.add_original_user_description=true --pr_description.keep_original_user_title=true --pr_description.final_update_message=false",
    "/review --pr_reviewer.num_code_suggestions=0 --pr_reviewer.final_update_message=false",
    "/improve",
]
```
This means that when a new PR is opened/reopened or marked as ready for review, PR-Agent will run the `describe`, `review` and `improve` tools.  
For the `describe` tool, for example, the `add_original_user_description` and `keep_original_user_title` parameters will be set to true.

You can override the default tool parameters by using one the three options for a [configuration file](https://codium-ai.github.io/Docs-PR-Agent/usage-guide/#configuration-options): **wiki**, **local**, or **global**. 
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

You can also disable automatic runs for PRs with specific titles, by setting the `ignore_pr_titles` parameter with the relevant regex. For example:
```
[github_app]
ignore_pr_title = ["^[Auto]", ".*ignore.*"]
```
will ignore PRs with titles that start with "Auto" or contain the word "ignore".

### GitHub app automatic tools for push actions (commits to an open PR)

In addition to running automatic tools when a PR is opened, the GitHub app can also respond to new code that is pushed to an open PR.

The configuration toggle `handle_push_trigger` can be used to enable this feature.  
The configuration parameter `push_commands` defines the list of tools that will be **run automatically** when new code is pushed to the PR.
```
[github_app]
handle_push_trigger = true
push_commands = [
    "/describe --pr_description.add_original_user_description=true --pr_description.keep_original_user_title=true",
    "/review  --pr_reviewer.num_code_suggestions=0",
]
```
This means that when new code is pushed to the PR, the PR-Agent will run the `describe` and `review` tools, with the specified parameters.

## GitHub Action
`GitHub Action` is a different way to trigger PR-Agent tools, and uses a different configuration mechanism than `GitHub App`.
You can configure settings for `GitHub Action` by adding environment variables under the env section in `.github/workflows/pr_agent.yml` file. 
Specifically, start by setting the following environment variables:
```yaml
      env:
        OPENAI_KEY: ${{ secrets.OPENAI_KEY }} # Make sure to add your OpenAI key to your repo secrets
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }} # Make sure to add your GitHub token to your repo secrets
        github_action_config.auto_review: "true" # enable\disable auto review
        github_action_config.auto_describe: "true" # enable\disable auto describe
        github_action_config.auto_improve: "true" # enable\disable auto improve
```
`github_action_config.auto_review`, `github_action_config.auto_describe` and `github_action_config.auto_improve` are used to enable/disable automatic tools that run when a new PR is opened.
If not set, the default configuration is for all three tools to run automatically when a new PR is opened.

Note that you can give additional config parameters by adding environment variables to `.github/workflows/pr_agent.yml`, or by using a `.pr_agent.toml` file in the root of your repo, similar to the GitHub App usage.

For example, you can set an environment variable: `pr_description.add_original_user_description=false`, or add a `.pr_agent.toml` file with the following content:
```
[pr_description]
add_original_user_description = false
```

## GitLab Webhook
After setting up a GitLab webhook, to control which commands will run automatically when a new PR is opened, you can set the `pr_commands` parameter in the configuration file, similar to the GitHub App:
```
[gitlab]
pr_commands = [
    "/describe --pr_description.add_original_user_description=true --pr_description.keep_original_user_title=true",
    "/review --pr_reviewer.num_code_suggestions=0",
    "/improve",
]
```

## BitBucket App
Similar to GitHub app, when running PR-Agent from BitBucket App, the default [configuration file](https://github.com/Codium-ai/pr-agent/blob/main/pr_agent/settings/configuration.toml) from a pre-built docker will be initially loaded.

By uploading a local `.pr_agent.toml` file to the root of the repo's main branch, you can edit and customize any configuration parameter. Note that you need to upload `.pr_agent.toml` prior to creating a PR, in order for the configuration to take effect.

For example, if your local `.pr_agent.toml` file contains:
```
[pr_reviewer]
inline_code_comments = true
```

Each time you invoke a `/review` tool, it will use inline code comments.

### BitBucket Self-Hosted App automatic tools

to control which commands will run automatically when a new PR is opened, you can set the `pr_commands` parameter in the configuration file:
Specifically, set the following values:

[bitbucket_app]
```
pr_commands = [
    "/review --pr_reviewer.num_code_suggestions=0",
    "/improve --pr_code_suggestions.summarize=false",
]
```

## Azure DevOps provider

To use Azure DevOps provider use the following settings in configuration.toml:
```
[config]
git_provider="azure"
use_repo_settings_file=false
```

Azure DevOps provider supports [PAT token](https://learn.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate?view=azure-devops&tabs=Windows) or [DefaultAzureCredential](https://learn.microsoft.com/en-us/azure/developer/python/sdk/authentication-overview#authentication-in-server-environments) authentication.
PAT is faster to create, but has build in experation date, and will use the user identity for API calls. 
Using DefaultAzureCredential you can use managed identity or Service principle, which are more secure and will create seperate ADO user identity (via AAD) to the agent.

If PAT was choosen, you can assign the value in .secrets.toml. 
If DefaultAzureCredential was choosen, you can assigned the additional env vars like AZURE_CLIENT_SECRET directly, 
or use managed identity/az cli (for local develpment) without any additional configuration.
in any case, 'org' value must be assigned in .secrets.toml:
```
[azure_devops]
org = "https://dev.azure.com/YOUR_ORGANIZATION/"
# pat = "YOUR_PAT_TOKEN" needed only if using PAT for authentication
```

### Azure DevOps Webhook

To control which commands will run automatically when a new PR is opened, you can set the `pr_commands` parameter in the configuration file, similar to the GitHub App:
```
[azure_devops_server]
pr_commands = [
    "/describe --pr_description.add_original_user_description=true --pr_description.keep_original_user_title=true",
    "/review --pr_reviewer.num_code_suggestions=0",
    "/improve",
]
```