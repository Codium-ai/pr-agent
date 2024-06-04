
After [installation](https://pr-agent-docs.codium.ai/installation/), there are three basic ways to invoke CodiumAI PR-Agent:

1. Locally running a CLI command
2. Online usage - by [commenting](https://github.com/Codium-ai/pr-agent/pull/229#issuecomment-1695021901) on a PR
3. Enabling PR-Agent tools to run automatically when a new PR is opened


Specifically, CLI commands can be issued by invoking a pre-built [docker image](https://pr-agent-docs.codium.ai/installation/locally/#using-docker-image), or by invoking a [locally cloned repo](https://pr-agent-docs.codium.ai/installation/locally/#run-from-source).
For online usage, you will need to setup either a [GitHub App](https://pr-agent-docs.codium.ai/installation/github/#run-as-a-github-app), or a [GitHub Action](https://pr-agent-docs.codium.ai/installation/github/#run-as-a-github-action).
GitHub App and GitHub Action also enable to run PR-Agent specific tool automatically when a new PR is opened.


**git provider**: The [git_provider](https://github.com/Codium-ai/pr-agent/blob/main/pr_agent/settings/configuration.toml#L5) field in the configuration file determines the GIT provider that will be used by PR-Agent. Currently, the following providers are supported:
`
"github", "gitlab", "bitbucket", "azure", "codecommit", "local", "gerrit"
`

