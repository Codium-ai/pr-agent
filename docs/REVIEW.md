# Review Tool

## Table of Contents
- [Overview](#overview)
  - [Configuration options](#configuration-options)
  - [Incremental Mode](#incremental-mode)
  - [PR Reflection](#pr-reflection)
- [Usage Tips](#usage-tips)
  - [General guidelines](#general-guidelines)
  - [Code suggestions](#code-suggestions)
  - [Automation](#automation)
  - [Auto-labels](#auto-labels)
  - [Extra instructions](#extra-instructions)

## Overview
The `review` tool scans the PR code changes, and automatically generates a PR review.
The tool can be triggered automatically every time a new PR is [opened](https://github.com/Codium-ai/pr-agent/blob/main/Usage.md#github-app-automatic-tools), or can be invoked manually by commenting on any PR:
```
/review
```
For example:
___
<kbd><img src=https://codium.ai/images/pr_agent/review_comment.png width="768"></kbd>
___
<kbd><img src=https://codium.ai/images/pr_agent/review.png width="768"></kbd>
___

### Configuration options

To edit [configurations](./../pr_agent/settings/configuration.toml#L19)  related to the review tool (`pr_reviewer` section), use the following template:
```
/review --pr_reviewer.some_config1=... --pr_reviewer.some_config2=...
```

#### General options
- `num_code_suggestions`: number of code suggestions provided by the 'review' tool. Default is 4.
- `inline_code_comments`: if set to true, the tool will publish the code suggestions as comments on the code diff. Default is false.
- `persistent_comment`: if set to true, the review comment will be persistent, meaning that every new review request will edit the previous one. Default is true.
- `extra_instructions`: Optional extra instructions to the tool. For example: "focus on the changes in the file X. Ignore change in ...".
#### Enable\\disable features
- `require_focused_review`: if set to true, the tool will add a section - 'is the PR a focused one'. Default is false.
- `require_score_review`: if set to true, the tool will add a section that scores the PR. Default is false.
- `require_tests_review`: if set to true, the tool will add a section that checks if the PR contains tests. Default is true.
- `require_security_review`: if set to true, the tool will add a section that checks if the PR contains security issues. Default is true.
- `require_estimate_effort_to_review`: if set to true, the tool will add a section that estimates the effort needed to review the PR. Default is true.
#### SOC2 ticket compliance 💎
This sub-tool checks if the PR description properly contains a ticket to a project management system (e.g., Jira, Asana, Trello, etc.), as required by SOC2 compliance. If not, it will add a label to the PR: "Missing SOC2 ticket".
- `require_soc2_ticket`: If set to true, the SOC2 ticket checker sub-tool will be enabled. Default is false.
- `soc2_ticket_prompt`: The prompt for the SOC2 ticket review. Default is: `Does the PR description include a link to ticket in a project management system (e.g., Jira, Asana, Trello, etc.) ?`. Edit this field if your compliance requirements are different.
#### Adding PR labels
- `enable_review_labels_security`: if set to true, the tool will publish a 'possible security issue' label if it detects a security issue. Default is true.
- `enable_review_labels_effort`: if set to true, the tool will publish a 'Review effort [1-5]: x' label. Default is true.

###  Incremental Mode
Incremental review only considers changes since the last PR-Agent review. This can be useful when working on the PR in an iterative manner, and you want to focus on the changes since the last review instead of reviewing the entire PR again.
For invoking the incremental mode, the following command can be used:
```
/review -i
```
Note that the incremental mode is only available for GitHub.

<kbd><img src=https://codium.ai/images/pr_agent/incremental_review.png width="768"></kbd>

Under the section 'pr_reviewer', the [configuration file](./../pr_agent/settings/configuration.toml#L19) contains options to customize the 'review -i' tool.  
These configurations can be used to control the rate at which the incremental review tool will create new review comments when invoked automatically, to prevent making too much noise in the PR.
- `minimal_commits_for_incremental_review`: Minimal number of commits since the last review that are required to create incremental review.
If there are less than the specified number of commits since the last review, the tool will not perform any action.
Default is 0 - the tool will always run, no matter how many commits since the last review.
- `minimal_minutes_for_incremental_review`: Minimal number of minutes that need to pass since the last reviewed commit to create incremental review.
If less that the specified number of minutes have passed between the last reviewed commit and running this command, the tool will not perform any action. 
Default is 0 - the tool will always run, no matter how much time have passed since the last reviewed commit.
- `require_all_thresholds_for_incremental_review`: If set to true, all the previous thresholds must be met for incremental review to run. If false, only one is enough to run the tool.
For example, if `minimal_commits_for_incremental_review=2` and `minimal_minutes_for_incremental_review=2`, and we have 3 commits since the last review, but the last reviewed commit is from 1 minute ago:
When `require_all_thresholds_for_incremental_review=true` the incremental review __will not__ run, because only 1 out of 2 conditions were met (we have enough commits but the last review is too recent),
but when `require_all_thresholds_for_incremental_review=false` the incremental review __will__ run, because one condition is enough (we have 3 commits which is more than the configured 2).
Default is false - the tool will run as long as at least once conditions is met.
- `remove_previous_review_comment`: if set to true, the tool will remove the previous review comment before adding a new one. Default is false.

### PR Reflection
By invoking:
```
/reflect_and_review
```
The tool will first ask the author questions about the PR, and will guide the review based on their answers.

<kbd><img src=https://codium.ai/images/pr_agent/reflection_questions.png width="768"></kbd>
___
<kbd><img src=https://codium.ai/images/pr_agent/reflection_answers.png width="768"></kbd>
___
<kbd><img src=https://codium.ai/images/pr_agent/reflection_insights.png width="768"></kbd>
___


## Usage Tips
1) [General guidelines](#general-guidelines)
2) [Code suggestions](#code-suggestions)
3) [Automation](#automation)
4) [Auto-labels](#auto-labels)
5) [Extra instructions](#extra-instructions)

### General guidelines
The `review` tool provides a collection of possible feedbacks about a PR.
It is recommended to review the [Configuration options](#configuration-options) section, and choose the relevant options for your use case.

Some of the feature that are disabled by default are quite useful, and should be considered for enabling. For example: 
`require_score_review`, `require_soc2_ticket`, and more.

On the other hand, if you find one of the enabled features to be irrelevant for your use case, disable it. No default configuration can fit all use cases.

### Code suggestions
The `review` tool provides several type of feedbacks, one of them is code suggestions.
If you are interested **only** in the code suggestions, it is recommended to use the [`improve`](./IMPROVE.md) feature instead, since it dedicated only to code suggestions, and usually gives better results.
Use the `review` tool if you want to get a more comprehensive feedback, which includes code suggestions as well.

### Automation
- When you first install the app, the [default mode](https://github.com/Codium-ai/pr-agent/blob/main/Usage.md#github-app-automatic-tools) for the `review` tool is:
```
pr_commands = ["/review", ...]
```
meaning the `review` tool will run automatically on every PR, with the default configuration.
Edit this field to enable/disable the tool, or to change the used configurations

### Auto-labels
The `review` tool can auto-generate two specific types of labels for a PR:
- a `possible security issue` label that detects a possible [security issue](https://github.com/Codium-ai/pr-agent/blob/tr/user_description/pr_agent/settings/pr_reviewer_prompts.toml#L136) (`enable_review_labels_security` flag)
- a `Review effort [1-5]: x` label, where x is the estimated effort to review the PR (`enable_review_labels_effort` flag)

Both modes are useful, and we recommended to enable them.

### Extra instructions
Extra instruction are important.
The `review` tool can be configured with extra instructions, which can be used to guide the model to a feedback tailored to the needs of your project.

Be specific, clear, and concise in the instructions. With extra instructions, you are the prompter. Specify the relevant sub-tool, and the relevant aspects of the PR that you want to emphasize.

Examples for extra instructions:
```
[pr_reviewer] # /review #
extra_instructions="""
In the code feedback section, emphasize the following:
- Does the code logic cover relevant edge cases?
- Is the code logic clear and easy to understand?
- Is the code logic efficient?
...
"""
```
Use triple quotes to write multi-line instructions. Use bullet points to make the instructions more readable.

