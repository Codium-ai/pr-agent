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

## Usage Tips

### Self-review
If you set in a configuration file:
```
[pr_code_suggestions]
demand_code_suggestions_self_review = true
```
The `improve` tool will add a checkbox below the suggestions, prompting user to acknowledge that they have reviewed the suggestions.
You can set the content of the checkbox text via:
```
[pr_code_suggestions]
code_suggestions_self_review_text = "... (your text here) ..."
```

![self_review_1](https://codium.ai/images/pr_agent/self_review_1.png){width=512}


💎 In addition, by setting:
```
[pr_code_suggestions]
approve_pr_on_self_review = true
```
the tool can automatically approve the PR when the user checks the self-review checkbox.

!!! tip "Tip - demanding self-review from the PR author"
    If you set the number of required reviewers for a PR to 2, this effectively means that the PR author must click the self-review checkbox before the PR can be merged (in addition to a human reviewer).

    ![self_review_2](https://codium.ai/images/pr_agent/self_review_2.png){width=512}

### `Extra instructions` and `best practices`

#### Extra instructions
You can use the `extra_instructions` configuration option to give the AI model additional instructions for the `improve` tool.
Be specific, clear, and concise in the instructions. With extra instructions, you are the prompter. Specify relevant aspects that you want the model to focus on.
    
Examples for possible instructions:
```
[pr_code_suggestions]
extra_instructions="""\
(1) Answer in japanese
(2) Don't suggest to add try-excpet block
(3) Ignore changes in toml files
...
"""
```
Use triple quotes to write multi-line instructions. Use bullet points or numbers to make the instructions more readable.

#### Best practices 💎
Another option to give additional guidance to the AI model is by creating a dedicated [**wiki page**](https://github.com/Codium-ai/pr-agent/wiki) called `best_practices.md`. 
This page can contain a list of best practices, coding standards, and guidelines that are specific to your repo/organization

The AI model will use this page as a reference, and in case the PR code violates any of the guidelines, it will suggest improvements accordingly, with a dedicated label: `Organization
best practice`. 

Example for a `best_practices.md` content can be found [here](https://github.com/Codium-ai/pr-agent/blob/main/docs/docs/usage-guide/EXAMPLE_BEST_PRACTICE.md) (adapted from Google's [pyguide](https://google.github.io/styleguide/pyguide.html)).
This file is only an example. Since it is used as a prompt for an AI model, we want to emphasize the following:

- It should be written in a clear and concise manner
- If needed, it should give short relevant code snippets as examples
- Up to 800 lines are allowed


Example results:

![best_practice](https://codium.ai/images/pr_agent/org_best_practice.png){width=512}

Note that while the `extra instructions` are more related to the way the `improve` tool behaves, the `best_practices.md` file is a general guideline for the way code should be written in the repo.
Using a combination of both can help the AI model to provide relevant and tailored suggestions.

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

## A note on code suggestions quality

- While the current AI for code is getting better and better (GPT-4), it's not flawless. Not all the suggestions will be perfect, and a user should not accept all of them automatically. Critical reading and judgment are required.
- While mistakes of the AI are rare but can happen, a real benefit from the suggestions of the `improve` (and [`review`](https://pr-agent-docs.codium.ai/tools/review/)) tool is to catch, with high probability, **mistakes or bugs done by the PR author**, when they happen. So, it's a good practice to spend the needed ~30-60 seconds to review the suggestions, even if not all of them are always relevant.
- The hierarchical structure of the suggestions is designed to help the user to _quickly_ understand them, and to decide which ones are relevant and which are not:

    - Only if the `Category` header is relevant, the user should move to the summarized suggestion description
    - Only if the summarized suggestion description is relevant, the user should click on the collapsible, to read the full suggestion description with a code preview example.

In addition, we recommend to use the `extra_instructions` field to guide the model to suggestions that are more relevant to the specific needs of the project. 
<br>
Consider also trying the [Custom Prompt Tool](./custom_prompt.md) 💎, that will **only** propose code suggestions that follow specific guidelines defined by user.
