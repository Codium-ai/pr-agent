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



