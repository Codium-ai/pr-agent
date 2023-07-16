## Configuration

The different tools and sub-tools used by CodiumAI pr-agent are easily configurable via the configuration file: `/pr-agent/settings/configuration.toml`.
##### Git Provider:
You can select your git_provider with the flag `git_provider` in the `config` section

##### PR Reviewer:

You can enable/disable the different PR Reviewer abilities with the following flags (`pr_reviewer` section):
```
require_focused_review=true
require_tests_review=true
require_security_review=true
```
You can contol the number of suggestions returned by the PR Reviewer with the following flag:
```inline_code_comments=3```
And enable/disable the inline code suggestions with the following flag:
```inline_code_comments=true```
