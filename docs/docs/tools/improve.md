## Overview
The `improve` tool scans the PR code changes, and automatically generates suggestions for improving the PR code.
The tool can be triggered automatically every time a new PR is [opened](../usage-guide/automations_and_usage.md#github-app-automatic-tools-when-a-new-pr-is-opened), or it can be invoked manually by commenting on any PR:
```
/improve
```

## Example usage

### Manual triggering

Invoke the tool manually by commenting `/improve` on any PR. The code suggestions by default are presented as a single comment:

![code suggestions as comment](https://codium.ai/images/pr_agent/code_suggestions_as_comment.png){width=512}

To edit [configurations](#configuration-options) related to the improve tool, use the following template:
```
/improve --pr_code_suggestions.some_config1=... --pr_code_suggestions.some_config2=...
```

For example, you can choose to present the suggestions as commitable code comments, by running the following command:
```
/improve --pr_code_suggestions.commitable_code_suggestions=true
```

![improve](https://codium.ai/images/pr_agent/improve.png){width=512}


Note that a single comment has a significantly smaller PR footprint. We recommend this mode for most cases.
Also note that collapsible are not supported in _Bitbucket_. Hence, the suggestions are presented there as code comments.

### Automatic triggering

To run the `improve` automatically when a PR is opened, define in a [configuration file](https://pr-agent-docs.codium.ai/usage-guide/configuration_options/#wiki-configuration-file):
```
[github_app]
pr_commands = [
    "/improve",
    ...
]

[pr_code_suggestions]
num_code_suggestions_per_chunk = ...
...
```

- The `pr_commands` lists commands that will be executed automatically when a PR is opened.
- The `[pr_code_suggestions]` section contains the configurations for the `improve` tool you want to edit (if any)

### Extended mode

An extended mode, which does not involve PR Compression and provides more comprehensive suggestions, can be invoked by commenting on any PR by setting:
```
[pr_code_suggestions]
auto_extended_mode=true
```
(This mode is true by default).

Note that the extended mode divides the PR code changes into chunks, up to the token limits, where each chunk is handled separately (might use multiple calls to GPT-4 for large PRs).
Hence, the total number of suggestions is proportional to the number of chunks, i.e., the size of the PR.



## Configuration options

!!! example "General options"

<table>
  <tr>
    <td><b>num_code_suggestions</b></td>
    <td>Number of code suggestions provided by the 'improve' tool. Default is 4 for CLI, 0 for auto tools.</td>
  </tr>
  <tr>
    <td><b>extra_instructions</b></td>
    <td>Optional extra instructions to the tool. For example: "focus on the changes in the file X. Ignore change in ...".</td>
  </tr>
  <tr>
    <td><b>rank_suggestions</b></td>
    <td>If set to true, the tool will rank the suggestions, based on importance. Default is false.</td>
  </tr>
  <tr>
    <td><b>commitable_code_suggestions</b></td>
    <td>If set to true, the tool will display the suggestions as commitable code comments. Default is false.</td>
  </tr>
  <tr>
    <td><b>persistent_comment</b></td>
    <td>If set to true, the improve comment will be persistent, meaning that every new improve request will edit the previous one. Default is false.</td>
  </tr>
  <tr>
    <td><b>self_reflect_on_suggestions</b></td>
    <td>If set to true, the improve tool will calculate an importance score for each suggestion [1-10], and sort the suggestion labels group based on this score. Default is true.</td>
  </tr>
  <tr>
    <td><b>suggestions_score_threshold</b></td>
    <td> Any suggestion with importance score less than this threshold will be removed. Default is 0. Highly recommend not to set this value above 7-8, since above it may clip relevant suggestions that can be useful. </td>
  </tr>
  <tr>
    <td><b>apply_suggestions_checkbox</b></td>
    <td> Enable the checkbox to create a committable suggestion. Default is true.</td>
  </tr>
  <tr>
    <td><b>enable_help_text</b></td>
    <td>If set to true, the tool will display a help text in the comment. Default is true.</td>
  </tr>
</table>

!!! example "params for 'extended' mode"

<table>
  <tr>
    <td><b>auto_extended_mode</b></td>
    <td>Enable extended mode automatically (no need for the --extended option). Default is true.</td>
  </tr>
  <tr>
    <td><b>num_code_suggestions_per_chunk</b></td>
    <td>Number of code suggestions provided by the 'improve' tool, per chunk. Default is 5.</td>
  </tr>
  <tr>
    <td><b>rank_extended_suggestions</b></td>
    <td>If set to true, the tool will rank the suggestions, based on importance. Default is true.</td>
  </tr>
  <tr>
    <td><b>max_number_of_calls</b></td>
    <td>Maximum number of chunks. Default is 5.</td>
  </tr>
  <tr>
    <td><b>final_clip_factor</b></td>
    <td>Factor to remove suggestions with low confidence. Default is 0.9.</td>
  </tr>
</table>

## Usage Tips

!!! tip "Extra instructions"

    Extra instructions are very important for the `imrpove` tool, since they enable you to guide the model to suggestions that are more relevant to the specific needs of the project.
    
    Be specific, clear, and concise in the instructions. With extra instructions, you are the prompter. Specify relevant aspects that you want the model to focus on.
    
    Examples for extra instructions:
    ```
    [pr_code_suggestions] # /improve #
    extra_instructions="""\
    Emphasize the following aspects:
    - Does the code logic cover relevant edge cases?
    - Is the code logic clear and easy to understand?
    - Is the code logic efficient?
    ...
    """
    ```
    Use triple quotes to write multi-line instructions. Use bullet points to make the instructions more readable.

!!! tip "Review vs. Improve tools comparison"

    - The [review](https://pr-agent-docs.codium.ai/tools/review/) tool includes a section called 'Possible issues', that also provide feedback on the PR Code.
    In this section, the model is instructed to focus **only** on [major bugs and issues](https://github.com/Codium-ai/pr-agent/blob/main/pr_agent/settings/pr_reviewer_prompts.toml#L71).
    - The `improve` tool, on the other hand, has a broader mandate, and in addition to bugs and issues, it can also give suggestions for improving code quality and making the code more efficient, readable, and maintainable (see [here](https://github.com/Codium-ai/pr-agent/blob/main/pr_agent/settings/pr_code_suggestions_prompts.toml#L34)).
    - Hence, if you are interested only in feedback about clear bugs, the `review` tool might suffice. If you want a more detailed feedback, including broader suggestions for improving the PR code, also enable the `improve` tool to run on each PR.

## A note on code suggestions quality

- While the current AI for code is getting better and better (GPT-4), it's not flawless. Not all the suggestions will be perfect, and a user should not accept all of them automatically. Critical reading and judgment are required.
- While mistakes of the AI are rare but can happen, a real benefit from the suggestions of the `improve` (and [`review`](https://pr-agent-docs.codium.ai/tools/review/)) tool is to catch, with high probability, **mistakes or bugs done by the PR author**, when they happen. So, it's a good practice to spend the needed ~30-60 seconds to review the suggestions, even if not all of them are always relevant.
- The hierarchical structure of the suggestions is designed to help the user to _quickly_ understand them, and to decide which ones are relevant and which are not:

    - Only if the `Category` header is relevant, the user should move to the summarized suggestion description
    - Only if the summarized suggestion description is relevant, the user should click on the collapsible, to read the full suggestion description with a code preview example.

In addition, we recommend to use the `exra_instructions` field to guide the model to suggestions that are more relevant to the specific needs of the project. 
<br>
Consider also trying the [Custom Prompt Tool](./custom_prompt.md) 💎, that will **only** propose code suggestions that follow specific guidelines defined by user.
