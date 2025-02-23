## Overview
The `review` tool scans the PR code changes, and generates a list of feedbacks about the PR, aiming to aid the reviewing process.
<br>
The tool can be triggered automatically every time a new PR is [opened](../usage-guide/automations_and_usage.md#github-app-automatic-tools-when-a-new-pr-is-opened), or can be invoked manually by commenting on any PR:
```
/review
```

Note that the main purpose of the `review` tool is to provide the **PR reviewer** with useful feedbacks and insights. The PR author, in contrast, may prefer to save time and focus on the output of the [improve](./improve.md) tool, which provides actionable code suggestions.

(Read more about the different personas in the PR process and how Qodo Merge aims to assist them in our [blog](https://www.codium.ai/blog/understanding-the-challenges-and-pain-points-of-the-pull-request-cycle/))


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

To run the `review` automatically when a PR is opened, define in a [configuration file](https://qodo-merge-docs.qodo.ai/usage-guide/configuration_options/#wiki-configuration-file):
```
[github_app]
pr_commands = [
    "/review",
    ...
]

[pr_reviewer]
extra_instructions = "..."
...
```

- The `pr_commands` lists commands that will be executed automatically when a PR is opened.
- The `[pr_reviewer]` section contains the configurations for the `review` tool you want to edit (if any).


## Configuration options

!!! example "General options"

<table>
  <tr>
    <td><b>persistent_comment</b></td>
    <td>If set to true, the review comment will be persistent, meaning that every new review request will edit the previous one. Default is true.</td>
  </tr>
  <tr>
  <td><b>final_update_message</b></td>
  <td>When set to true, updating a persistent review comment during online commenting will automatically add a short comment with a link to the updated review in the pull request .Default is true.</td>
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
  <tr>
    <td><b>require_ticket_analysis_review</b></td>
    <td>If set to true, and the PR contains a GitHub or Jira ticket link, the tool will add a section that checks if the PR in fact fulfilled the ticket requirements. Default is true.</td>
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


## Usage Tips

!!! tip "General guidelines"

    The `review` tool provides a collection of configurable feedbacks about a PR.
    It is recommended to review the [Configuration options](#configuration-options) section, and choose the relevant options for your use case.

    Some of the features that are disabled by default are quite useful, and should be considered for enabling. For example:
    `require_score_review`, and more.

    On the other hand, if you find one of the enabled features to be irrelevant for your use case, disable it. No default configuration can fit all use cases.

!!! tip "Automation"
    When you first install Qodo Merge app, the [default mode](../usage-guide/automations_and_usage.md#github-app-automatic-tools-when-a-new-pr-is-opened) for the `review` tool is:
    ```
    pr_commands = ["/review", ...]
    ```
    Meaning the `review` tool will run automatically on every PR, without any additional configurations.
    Edit this field to enable/disable the tool, or to change the configurations used.

!!! tip "Possible labels from the review tool"

    The `review` tool can auto-generate two specific types of labels for a PR:

    - a `possible security issue` label that detects if a possible [security issue](https://github.com/Codium-ai/pr-agent/blob/tr/user_description/pr_agent/settings/pr_reviewer_prompts.toml#L136) exists in the PR code (`enable_review_labels_security` flag)
    - a `Review effort [1-5]: x` label, where x is the estimated effort to review the PR (`enable_review_labels_effort` flag)

    Both modes are useful, and we recommended to enable them.

!!! tip "Extra instructions"

    Extra instructions are important.
    The `review` tool can be configured with extra instructions, which can be used to guide the model to a feedback tailored to the needs of your project.

    Be specific, clear, and concise in the instructions. With extra instructions, you are the prompter. Specify the relevant sub-tool, and the relevant aspects of the PR that you want to emphasize.

    Examples of extra instructions:
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




!!! tip  "Code suggestions"

    The `review` tool previously included a legacy feature for providing code suggestions (controlled by `--pr_reviewer.num_code_suggestion`). This functionality has been deprecated and replaced by the [`improve`](./improve.md) tool, which offers higher quality and more actionable code suggestions.

    
