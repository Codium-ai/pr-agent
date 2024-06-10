## Overview
The `review` tool scans the PR code changes, and generates a list of feedbacks about the PR, aiming to aid the reviewing process.
<br>
The tool can be triggered automatically every time a new PR is [opened](../usage-guide/automations_and_usage.md#github-app-automatic-tools-when-a-new-pr-is-opened), or can be invoked manually by commenting on any PR:
```
/review
```

Note that the main purpose of the `review` tool is to provide the **PR reviewer** with useful feedbacks and insights. The PR author, in contrast, may prefer to save time and focus on the output of the [improve](./improve.md) tool, which provides actionable code suggestions.

## Example usage

### Manual triggering

Invoke the tool manually by commenting `/review` on any PR:

![review comment](https://codium.ai/images/pr_agent/review_comment.png){width=512}

After ~30 seconds, the tool will generate a review for the PR:

![review](https://codium.ai/images/pr_agent/review3.png){width=512}

If you want to edit [configurations](#configuration-options), add the relevant ones to the command:
```
/review --pr_reviewer.some_config1=... --pr_reviewer.some_config2=...
```

### Automatic triggering

To run the `review` automatically when a PR is opened, define in a [configuration file](https://pr-agent-docs.codium.ai/usage-guide/configuration_options/#wiki-configuration-file):
```
[github_app]
pr_commands = [
    "/review",
    ...
]

[pr_reviewer]
num_code_suggestions = ...
...
```

- The `pr_commands` lists commands that will be executed automatically when a PR is opened.
- The `[pr_reviewer]` section contains the configurations for the `review` tool you want to edit (if any).

### Incremental Mode
Incremental review only considers changes since the last PR-Agent review. This can be useful when working on the PR in an iterative manner, and you want to focus on the changes since the last review instead of reviewing the entire PR again.
For invoking the incremental mode, the following command can be used:
```
/review -i
```
Note that the incremental mode is only available for GitHub.

![incremental review](https://codium.ai/images/pr_agent/incremental_review_2.png){width=512}

[//]: # (### PR Reflection)

[//]: # ()
[//]: # (By invoking:)

[//]: # (```)

[//]: # (/reflect_and_review)

[//]: # (```)

[//]: # (The tool will first ask the author questions about the PR, and will guide the review based on their answers.)

[//]: # ()
[//]: # (![reflection questions]&#40;https://codium.ai/images/pr_agent/reflection_questions.png&#41;{width=512})

[//]: # ()
[//]: # (![reflection answers]&#40;https://codium.ai/images/pr_agent/reflection_answers.png&#41;{width=512})

[//]: # ()
[//]: # (![reflection insights]&#40;https://codium.ai/images/pr_agent/reflection_insights.png&#41;{width=512})



## Configuration options

!!! example "General options"

<table>
  <tr>
    <td><b>num_code_suggestions</b></td>
    <td>Number of code suggestions provided by the 'review' tool. For manual comments, default is 4. For PR-Agent app auto tools, default is 0, meaning no code suggestions will be provided by the review tool, unless you manually edit pr_commands.</td>
  </tr>
  <tr>
    <td><b>inline_code_comments</b></td>
    <td>If set to true, the tool will publish the code suggestions as comments on the code diff. Default is false.</td>
  </tr>
  <tr>
    <td><b>persistent_comment</b></td>
    <td>If set to true, the review comment will be persistent, meaning that every new review request will edit the previous one. Default is true.</td>
  </tr>
  <tr>
    <td><b>extra_instructions</b></td>
    <td>Optional extra instructions to the tool. For example: "focus on the changes in the file X. Ignore change in ...".</td>
  </tr>
  <tr>
    <td><b>enable_help_text</b></td>
    <td>If set to true, the tool will display a help text in the comment. Default is true.</td>
  </tr>
</table>

!!! example "Enable\\disable specific sub-sections"

<table>
  <tr>
    <td><b>require_score_review</b></td>
    <td>If set to true, the tool will add a section that scores the PR. Default is false.</td>
  </tr>
  <tr>
    <td><b>require_tests_review</b></td>
    <td>If set to true, the tool will add a section that checks if the PR contains tests. Default is true.</td>
  </tr>
  <tr>
    <td><b>require_estimate_effort_to_review</b></td>
    <td>If set to true, the tool will add a section that estimates the effort needed to review the PR. Default is true.</td>
  </tr>
  <tr>
    <td><b>require_can_be_split_review</b></td>
    <td>If set to true, the tool will add a section that checks if the PR contains several themes, and can be split into smaller PRs. Default is false.</td>
  </tr>
  <tr>
    <td><b>require_security_review</b></td>
    <td>If set to true, the tool will add a section that checks if the PR contains a possible security or vulnerability issue. Default is true.</td>
  </tr>
</table>

!!! example "SOC2 ticket compliance 💎"

This sub-tool checks if the PR description properly contains a ticket to a project management system (e.g., Jira, Asana, Trello, etc.), as required by SOC2 compliance. If not, it will add a label to the PR: "Missing SOC2 ticket".
    
<table>
  <tr>
    <td><b>require_soc2_ticket</b></td>
    <td>If set to true, the SOC2 ticket checker sub-tool will be enabled. Default is false.</td>
  </tr>
  <tr>
    <td><b>soc2_ticket_prompt</b></td>
    <td>The prompt for the SOC2 ticket review. Default is: `Does the PR description include a link to ticket in a project management system (e.g., Jira, Asana, Trello, etc.) ?`. Edit this field if your compliance requirements are different.</td>
  </tr>
</table>

!!! example "Adding PR labels"

You can enable\disable the `review` tool to add specific labels to the PR:

<table>
  <tr>
    <td><b>enable_review_labels_security</b></td>
    <td>If set to true, the tool will publish a 'possible security issue' label if it detects a security issue. Default is true.</td>
  </tr>
  <tr>
    <td><b>enable_review_labels_effort</b></td>
    <td>If set to true, the tool will publish a 'Review effort [1-5]: x' label. Default is true.</td>
  </tr>
</table>

!!! example "Auto-approval"

If enabled, the `review` tool can approve a PR when a specific comment, `/review auto_approve`, is invoked.

<table>
  <tr>
    <td><b>enable_auto_approval</b></td>
    <td>If set to true, the tool will approve the PR when invoked with the 'auto_approve' command. Default is false. This flag can be changed only from configuration file.</td>
  </tr>
  <tr>
    <td><b>maximal_review_effort</b></td>
    <td>Maximal effort level for auto-approval. If the PR's estimated review effort is above this threshold, the auto-approval will not run. Default is 5.</td>
  </tr>
</table>

## Usage Tips

!!! tip "General guidelines"

    The `review` tool provides a collection of configurable feedbacks about a PR.
    It is recommended to review the [Configuration options](#configuration-options) section, and choose the relevant options for your use case.
    
    Some of the features that are disabled by default are quite useful, and should be considered for enabling. For example: 
    `require_score_review`, `require_soc2_ticket`, and more.
    
    On the other hand, if you find one of the enabled features to be irrelevant for your use case, disable it. No default configuration can fit all use cases.

!!! tip "Automation"
    When you first install PR-Agent app, the [default mode](../usage-guide/automations_and_usage.md#github-app-automatic-tools-when-a-new-pr-is-opened) for the `review` tool is:
    ```
    pr_commands = ["/review --pr_reviewer.num_code_suggestions=0", ...]
    ```
    Meaning the `review` tool will run automatically on every PR, without providing code suggestions.
    Edit this field to enable/disable the tool, or to change the used configurations.

!!! tip "Possible labels from the review tool"

    The `review` tool can auto-generate two specific types of labels for a PR:
    
    - a `possible security issue` label that detects if a possible [security issue](https://github.com/Codium-ai/pr-agent/blob/tr/user_description/pr_agent/settings/pr_reviewer_prompts.toml#L136) exists in the PR code (`enable_review_labels_security` flag)
    - a `Review effort [1-5]: x` label, where x is the estimated effort to review the PR (`enable_review_labels_effort` flag)
    
    Both modes are useful, and we recommended to enable them.

!!! tip "Extra instructions"

    Extra instructions are important.
    The `review` tool can be configured with extra instructions, which can be used to guide the model to a feedback tailored to the needs of your project.
    
    Be specific, clear, and concise in the instructions. With extra instructions, you are the prompter. Specify the relevant sub-tool, and the relevant aspects of the PR that you want to emphasize.
    
    Examples for extra instructions:
    ```
    [pr_reviewer]
    extra_instructions="""\
    In the code feedback section, emphasize the following:
    - Does the code logic cover relevant edge cases?
    - Is the code logic clear and easy to understand?
    - Is the code logic efficient?
    ...
    """
    ```
    Use triple quotes to write multi-line instructions. Use bullet points to make the instructions more readable.


!!! tip "Auto-approval"

    PR-Agent can approve a PR when a specific comment is invoked.
    
    To ensure safety, the auto-approval feature is disabled by default. To enable auto-approval, you need to actively set in a pre-defined configuration file the following:
    ```
    [pr_reviewer]
    enable_auto_approval = true
    ```
    (this specific flag cannot be set with a command line argument, only in the configuration file, committed to the repository)
    
    
    After enabling, by commenting on a PR:
    ```
    /review auto_approve
    ```
    PR-Agent will automatically approve the PR, and add a comment with the approval.
    
    
    You can also enable auto-approval only if the PR meets certain requirements, such as that the `estimated_review_effort` label is equal or below a certain threshold, by adjusting the flag:
    ```
    [pr_reviewer]
    maximal_review_effort = 5
    ```

[//]: # (!!! tip  "Code suggestions")

[//]: # ()
[//]: # (    If you set `num_code_suggestions`>0 , the `review` tool will also provide code suggestions.)

[//]: # (    )
[//]: # (    Notice If you are interested **only** in the code suggestions, it is recommended to use the [`improve`]&#40;./improve.md&#41; feature instead, since it is a dedicated only to code suggestions, and usually gives better results.)

[//]: # (    Use the `review` tool if you want to get more comprehensive feedback, which includes code suggestions as well.)

