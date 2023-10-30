## [Version 0.9] - 2023-10-29
- codiumai/pr-agent:0.9
- codiumai/pr-agent:0.9-github_app
- codiumai/pr-agent:0.9-bitbucket-app
- codiumai/pr-agent:0.9-gitlab_webhook
- codiumai/pr-agent:0.9-github_polling
- codiumai/pr-agent:0.9-github_action

### Added::Algo
- New tool - [generate_labels](https://github.com/Codium-ai/pr-agent/blob/main/docs/GENERATE_CUSTOM_LABELS.md)
- New ability to use [customize labels](https://github.com/Codium-ai/pr-agent/blob/main/docs/GENERATE_CUSTOM_LABELS.md#how-to-enable-custom-labels) on the `review` and `describe` tools.
- New tool - [add_docs](https://github.com/Codium-ai/pr-agent/blob/main/docs/ADD_DOCUMENTATION.md)
- GitHub Action: Can now use a `.pr_agent.toml` file to control configuration parameters (see [Usage Guide](./Usage.md#working-with-github-action)).
- GitHub App: Added ability to trigger tools on [push events](https://github.com/Codium-ai/pr-agent/blob/main/Usage.md#github-app-automatic-tools-for-new-code-pr-push)
- Support custom domain URLs for Azure devops integration (see [link](https://github.com/Codium-ai/pr-agent/pull/381)).
- PR Description default mode is now in [bullet points](https://github.com/Codium-ai/pr-agent/blob/main/pr_agent/settings/configuration.toml#L35).

### Added::Documentation
Significant documentation updates (see [Installation Guide](https://github.com/Codium-ai/pr-agent/blob/main/INSTALL.md), [Usage Guide](https://github.com/Codium-ai/pr-agent/blob/main/Usage.md), and [Tools Guide](https://github.com/Codium-ai/pr-agent/blob/main/docs/TOOLS_GUIDE.md))

### Fixed
- Fixed support for BitBucket pipeline (see [link](https://github.com/Codium-ai/pr-agent/pull/386))
- Fixed a bug in `review -i` tool
- Added blacklist for specific file extensions in `add_docs` tool (see [link](https://github.com/Codium-ai/pr-agent/pull/385/))

## [Version 0.8] - 2023-09-27
- codiumai/pr-agent:0.8
- codiumai/pr-agent:0.8-github_app
- codiumai/pr-agent:0.8-bitbucket-app
- codiumai/pr-agent:0.8-gitlab_webhook
- codiumai/pr-agent:0.8-github_polling
- codiumai/pr-agent:0.8-github_action

### Added::Algo
- GitHub Action: Can control which tools will run automatically when a new PR is created. (see usage guide: https://github.com/Codium-ai/pr-agent/blob/main/Usage.md#working-with-github-action)
- Code suggestion tool: Will try to avoid an 'add comments' suggestion  (see https://github.com/Codium-ai/pr-agent/pull/327)

### Fixed
- Gitlab: Fixed a bug of improper usage of pr_id


## [Version 0.7] - 2023-09-20

### Docker Tags
- codiumai/pr-agent:0.7
- codiumai/pr-agent:0.7-github_app
- codiumai/pr-agent:0.7-bitbucket-app
- codiumai/pr-agent:0.7-gitlab_webhook
- codiumai/pr-agent:0.7-github_polling
- codiumai/pr-agent:0.7-github_action
 
### Added::Algo
- New tool /similar_issue - Currently on GitHub app and CLI: indexes the issues in the repo, find the most similar issues to the target issue.
- Describe markers: Empower the /describe tool with a templating capability (see more details in https://github.com/Codium-ai/pr-agent/pull/273).
- New feature in the /review tool - added an estimated effort estimation to the review (https://github.com/Codium-ai/pr-agent/pull/306).

### Added::Infrastructure
- Implementation of a GitLab webhook.
- Implementation of a BitBucket app.

### Fixed
- Protection against no code suggestions generated.
- Resilience to repositories where the languages cannot be automatically detected.
