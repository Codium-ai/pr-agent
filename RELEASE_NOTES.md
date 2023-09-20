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



