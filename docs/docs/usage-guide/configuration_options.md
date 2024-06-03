The different tools and sub-tools used by CodiumAI PR-Agent are adjustable via the **[configuration file](https://github.com/Codium-ai/pr-agent/blob/main/pr_agent/settings/configuration.toml)**.

In addition to general configuration options, each tool has its own configurations. For example, the `review` tool will use parameters from the [pr_reviewer](https://github.com/Codium-ai/pr-agent/blob/main/pr_agent/settings/configuration.toml#L16) section in the configuration file.
See the [Tools Guide](https://codium-ai.github.io/Docs-PR-Agent/tools/) for a detailed description of the different tools and their configurations.

There are three ways to set persistent configurations:

1. Wiki configuration page 💎
2. Local configuration file
3. Global configuration file 💎

In terms of precedence, wiki configurations will override local configurations, and local configurations will override global configurations.

!!! tip "Tip1: edit only what you need"
    Your configuration file should be minimal, and edit only the relevant values. Don't copy the entire configuration options, since it can lead to legacy problems when something changes.
!!! tip "Tip2: show relevant configurations"
    If you set `config.output_relevant_configurations=true`, each tool will also output in a collapsible section its relevant configurations. This can be useful for debugging, or getting to know the configurations better.

## Wiki configuration file 💎

Specifically for GitHub, with PR-Agent-Pro you can set configurations by creating a page called `.pr_agent.toml` in the [wiki](https://github.com/Codium-ai/pr-agent/wiki/pr_agent.toml) of the repo. 
The advantage of this method is that it allows to set configurations without needing to commit new content to the repo - just edit the wiki page and **save**.

![wiki_configuration](https://codium.ai/images/pr_agent/wiki_configuration.png){width=512}

Click [here](https://codium.ai/images/pr_agent/wiki_configuration_pr_agent.mp4) to see a short instructional video. We recommend surrounding the configuration content with triple-quotes, to allow better presentation when displayed in the wiki as markdown.
An example content:

```
[pr_description]
generate_ai_title=true
```

PR-Agent will know to remove the triple-quotes when reading the configuration content.

## Local configuration file

By uploading a local `.pr_agent.toml` file to the root of the repo's main branch, you can edit and customize any configuration parameter. Note that you need to upload `.pr_agent.toml` prior to creating a PR, in order for the configuration to take effect.

For example, if you set in `.pr_agent.toml`:

```
[pr_reviewer]
extra_instructions="""\
- instruction a
- instruction b
...
"""
```

Then you can give a list of extra instructions to the `review` tool.


## Global configuration file 💎

If you create a repo called `pr-agent-settings` in your **organization**, it's configuration file `.pr_agent.toml` will be used as a global configuration file for any other repo that belongs to the same organization.
Parameters from a local `.pr_agent.toml` file, in a specific repo, will override the global configuration parameters.

For example, in the GitHub organization `Codium-ai`:
- The repo [`https://github.com/Codium-ai/pr-agent-settings`](https://github.com/Codium-ai/pr-agent-settings/blob/main/.pr_agent.toml) contains a `.pr_agent.toml` file that serves as a global configuration file for all the repos in the GitHub organization `Codium-ai`.
- The repo [`https://github.com/Codium-ai/pr-agent`](https://github.com/Codium-ai/pr-agent/blob/main/.pr_agent.toml) inherits the global configuration file from `pr-agent-settings`.
