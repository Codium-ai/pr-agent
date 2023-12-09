# Review Tool

The `review` tool scans the PR code changes, and automatically generates a PR review.
It can be invoked manually by commenting on any PR:
```
/review
```
For example:

<kbd><img src=https://codium.ai/images/pr_agent/review_comment.png width="768"></kbd>
<kbd><img src=https://codium.ai/images/pr_agent/review.png width="768"></kbd>

The `review` tool can also be triggered automatically every time a new PR is opened. See examples for automatic triggers for [GitHub App](https://github.com/Codium-ai/pr-agent/blob/main/Usage.md#github-app-automatic-tools) and [GitHub Action](https://github.com/Codium-ai/pr-agent/blob/main/Usage.md#working-with-github-action)

### Configuration options

Under the section 'pr_reviewer', the [configuration file](./../pr_agent/settings/configuration.toml#L16) contains options to customize the 'review' tool:

#### enable\\disable features
- `require_focused_review`: if set to true, the tool will add a section - 'is the PR a focused one'. Default is false.
- `require_score_review`: if set to true, the tool will add a section that scores the PR. Default is false.
- `require_tests_review`: if set to true, the tool will add a section that checks if the PR contains tests. Default is true.
- `require_security_review`: if set to true, the tool will add a section that checks if the PR contains security issues. Default is true.
- `require_estimate_effort_to_review`: if set to true, the tool will add a section that estimates thed effort needed to review the PR. Default is true.
#### general options
- `num_code_suggestions`: number of code suggestions provided by the 'review' tool. Default is 4.
- `inline_code_comments`: if set to true, the tool will publish the code suggestions as comments on the code diff. Default is false.
- `automatic_review`: if set to false, no automatic reviews will be done. Default is true.
- `remove_previous_review_comment`: if set to true, the tool will remove the previous review comment before adding a new one. Default is false.
- `persistent_comment`: if set to true, the review comment will be persistent, meaning that every new review request will edit the previous one. Default is true.
- `extra_instructions`: Optional extra instructions to the tool. For example: "focus on the changes in the file X. Ignore change in ...".
#### review labels
- `enable_review_labels_security`: if set to true, the tool will publish a 'possible security issue' label if it detects a security issue. Default is true.
- `enable_review_labels_effort`: if set to true, the tool will publish a 'Review effort [1-5]: x' label. Default is false.
- To enable `custom labels`, apply the configuration changes described [here](./GENERATE_CUSTOM_LABELS.md#configuration-changes) 
####  Incremental Mode
For an incremental review, which only considers changes since the last PR-Agent review, this can be useful when working on the PR in an iterative manner, and you want to focus on the changes since the last review instead of reviewing the entire PR again, the following command can be used:
```
/review -i
```
Note that the incremental mode is only available for GitHub.

<kbd><img src=https://codium.ai/images/pr_agent/incremental_review.png width="768"></kbd>

Under the section 'pr_reviewer', the [configuration file](./../pr_agent/settings/configuration.toml#L16) contains options to customize the 'review -i' tool.  
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

#### PR Reflection
By invoking:
```
/reflect_and_review
```
The tool will first ask the author questions about the PR, and will guide the review based on his answers.

<kbd><img src=https://codium.ai/images/pr_agent/reflection_questions.png width="768"></kbd>
<kbd><img src=https://codium.ai/images/pr_agent/reflection_answers.png width="768"></kbd>
<kbd><img src=https://codium.ai/images/pr_agent/reflection_insights.png width="768"></kbd>


#### A note on code suggestions quality

- With current level of AI for code (GPT-4), mistakes can happen. Not all the suggestions will be perfect, and a user should not accept all of them automatically.

- Suggestions are not meant to be [simplistic](./../pr_agent/settings/pr_reviewer_prompts.toml#L29). Instead, they aim to give deep feedback and raise questions, ideas and thoughts to the user, who can then use his judgment, experience, and understanding of the code base.

- Recommended to use the 'extra_instructions' field to guide the model to suggestions that are more relevant to the specific needs of the project.

- Unlike the 'review' feature, which does a lot of things, the ['improve --extended'](./IMPROVE.md) feature is dedicated only to suggestions, and usually gives better results.
