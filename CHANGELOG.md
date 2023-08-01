## 2023-08-01
2023-08-01

### Enhanced
- Introduced the ability to retrieve commit messages from pull requests across different git providers.
- Implemented commit messages retrieval for GitHub and GitLab providers.
- Updated the PR description template to include a section for commit messages if they exist.
- Added support for repository-specific configuration files (.pr_agent.yaml) for the PR Agent.
- Implemented this feature for both GitHub and GitLab providers.
- Added a new configuration option 'use_repo_settings_file' to enable or disable the use of a repo-specific settings file.


## 2023-07-30

### Enhanced
- Added the ability to modify any configuration parameter from 'configuration.toml' on-the-fly.
- Updated the command line interface and bot commands to accept configuration changes as arguments.
- Improved the PR agent to handle additional arguments for each action.

## 2023-07-28

### Improved
- Enhanced error handling and logging in the GitLab provider.
- Improved handling of inline comments and code suggestions in GitLab.
- Fixed a bug where an additional unneeded line was added to code suggestions in GitLab.

## 2023-07-26

### Added
- New feature for updating the CHANGELOG.md based on the contents of a PR.
- Added support for this feature for the Github provider.
- New configuration settings and prompts for the changelog update feature.