## [Unreleased]

### Added
- New feature to the PR Agent that allows it to update the changelog based on the contents of a pull request. This feature is currently implemented for the Github provider only.
- New command 'update_changelog' added to the list of supported commands in `pr_agent/cli.py`.
- New configuration file 'pr_update_changelog.toml' added to the list of settings files in `pr_agent/config_loader.py`.
- New class `PRUpdateChangelog` in `pr_agent/tools/pr_update_changelog.py` responsible for updating the changelog based on the PR's contents.
- New prompts for the changelog update feature in `pr_agent/settings/pr_update_changelog.toml`.

### Changed
- Updated `pr_agent/agent/pr_agent.py` to handle the 'update_changelog' command.
- Updated `pr_agent/cli.py` to handle the 'update_changelog' command and reflect it in the help message.
- Updated `README.md` to include the 'update_changelog' command in the usage section and feature list.
- Updated `pr_agent/settings/configuration.toml` to include settings for the new feature.

### Fixed
- No bug fixes in this PR.