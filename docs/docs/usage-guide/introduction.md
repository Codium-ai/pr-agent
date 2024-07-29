
After [installation](https://pr-agent-docs.codium.ai/installation/), there are three basic ways to invoke CodiumAI PR-Agent:

1. Locally running a CLI command
2. Online usage - by [commenting](https://github.com/Codium-ai/pr-agent/pull/229#issuecomment-1695021901) on a PR
3. Enabling PR-Agent tools to run automatically when a new PR is opened


Specifically, CLI commands can be issued by invoking a pre-built [docker image](https://pr-agent-docs.codium.ai/installation/locally/#using-docker-image), or by invoking a [locally cloned repo](https://pr-agent-docs.codium.ai/installation/locally/#run-from-source).

For online usage, you will need to setup either a [GitHub App](https://pr-agent-docs.codium.ai/installation/github/#run-as-a-github-app) or a [GitHub Action](https://pr-agent-docs.codium.ai/installation/github/#run-as-a-github-action) (GitHub), a [GitLab webhook](https://pr-agent-docs.codium.ai/installation/gitlab/#run-a-gitlab-webhook-server) (GitLab), or a [BitBucket App](https://pr-agent-docs.codium.ai/installation/bitbucket/#run-using-codiumai-hosted-bitbucket-app) (BitBucket).
These platforms also enable to run PR-Agent specific tools automatically when a new PR is opened, or on each push to a branch.

