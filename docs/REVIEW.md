# Describe Tool

The `review` tool scans the PR code changes, and automatically generates a PR review.
It can ba invoked manually by commenting on any PR:
```
/review
```
For example:

<kbd><img src=./../pics/review_comment.png width="768"></kbd>
<kbd><img src=./../pics/describe.png width="768"><kbd>

The `review` tool can also be triggered automatically every time a new PR is opened. See examples for automatic triggers for [GitHub App](https://github.com/Codium-ai/pr-agent/blob/main/Usage.md#github-app-automatic-tools) and [GitHub Action](https://github.com/Codium-ai/pr-agent/blob/main/Usage.md#working-with-github-action)

### Configuration options

Under the section 'pr_reviewer', the [configuration file](./../pr_agent/settings/configuration.toml#L16) contains options to customize the 'review' tool:

- `require_focused_review`: if set to true, the tool will add a section - 'is the PR a focused one'. Default is false.
- `require_score_review`: if set to true, the tool will add a section that scores the PR. Default is false.
- `require_tests_review`: if set to true, the tool will add a section that checks if the PR contains tests. Default is true.
- `require_security_review`: if set to true, the tool will add a section that checks if the PR contains security issues. Default is true.
- `require_estimate_effort_to_review`: if set to true, the tool will add a section that estimates thed effort needed to review the PR. Default is true.
- `num_code_suggestions`: number of code suggestions provided by the 'review' tool. Default is 4.
- `inline_code_comments`: if set to true, the tool will publish the code suggestions as comments on the code diff. Default is false.
- `automatic_review`: if set to false, no automatic reviews will be done. Default is true.
- `extra_instructions`: Optional extra instructions to the tool. For example: "focus on the changes in the file X. Ignore change in ...".

#### PR Reflection
By invoking:
```
/reflect_and_review
```
The module will first ask the author questions about the PR, and will guide the review based on his answers.

<kbd><img src=./../pics/reflection_questions.png width="768"></kbd>
<kbd><img src=./../pics/reflection_answers.png width="768"></kbd>
<kbd><img src=./../pics/reflection_insights.png width="768"></kbd>