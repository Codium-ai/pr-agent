## Overview
The `improve` tool scans the PR code changes, and automatically generates [meaningful](https://github.com/Codium-ai/pr-agent/blob/main/pr_agent/settings/pr_code_suggestions_prompts.toml#L41) suggestions for improving the PR code.
The tool can be triggered automatically every time a new PR is [opened](../usage-guide/automations_and_usage.md#github-app-automatic-tools-when-a-new-pr-is-opened), or it can be invoked manually by commenting on any PR:
```toml
/improve
```

![code_suggestions_as_comment_closed.png](https://codium.ai/images/pr_agent/code_suggestions_as_comment_closed.png){width=512}

![code_suggestions_as_comment_open.png](https://codium.ai/images/pr_agent/code_suggestions_as_comment_open.png){width=512}

Note that the `Apply this suggestion` checkbox, which interactively converts a suggestion into a commitable code comment, is available only for Qodo Merge Pro 💎 users.


## Example usage

### Manual triggering

Invoke the tool manually by commenting `/improve` on any PR. The code suggestions by default are presented as a single comment:

To edit [configurations](#configuration-options) related to the improve tool, use the following template:
```toml
/improve --pr_code_suggestions.some_config1=... --pr_code_suggestions.some_config2=...
```

For example, you can choose to present all the suggestions as commitable code comments, by running the following command:
```toml
/improve --pr_code_suggestions.commitable_code_suggestions=true
```

![improve](https://codium.ai/images/pr_agent/improve.png){width=512}


As can be seen, a single table comment has a significantly smaller PR footprint. We recommend this mode for most cases.
Also note that collapsible are not supported in _Bitbucket_. Hence, the suggestions can only be presented in Bitbucket as code comments.

### Automatic triggering

To run the `improve` automatically when a PR is opened, define in a [configuration file](https://qodo-merge-docs.qodo.ai/usage-guide/configuration_options/#wiki-configuration-file):
```toml
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

### Assessing Impact 💎

Note that Qodo Merge pro tracks two types of implementations:

- Direct implementation - when the user directly applies the suggestion by clicking the `Apply` checkbox.
- Indirect implementation - when the user implements the suggestion in their IDE environment. In this case, Qodo Merge will utilize, after each commit, a dedicated logic to identify if a suggestion was implemented, and will mark it as implemented.

![code_suggestions_asses_impact](https://codium.ai/images/pr_agent/code_suggestions_asses_impact.png){width=512}

In post-process, Qodo Merge counts the number of suggestions that were implemented, and provides general statistics and insights about the suggestions' impact on the PR process.

![code_suggestions_asses_impact_stats_1](https://codium.ai/images/pr_agent/code_suggestions_asses_impact_stats_1.png){width=512}

![code_suggestions_asses_impact_stats_2](https://codium.ai/images/pr_agent/code_suggestions_asses_impact_stats_2.png){width=512}

## Suggestion tracking 💎
`Platforms supported: GitHub, GitLab`

Qodo Merge employs an novel detection system to automatically [identify](https://qodo-merge-docs.qodo.ai/core-abilities/impact_evaluation/) AI code suggestions that PR authors have accepted and implemented.

Accepted suggestions are also automatically documented in a dedicated wiki page called `.pr_agent_accepted_suggestions`, allowing users to track historical changes, assess the tool's effectiveness, and learn from previously implemented recommendations in the repository.
An example [result](https://github.com/Codium-ai/pr-agent/wiki/.pr_agent_accepted_suggestions):

[![pr_agent_accepted_suggestions1.png](https://qodo.ai/images/pr_agent/pr_agent_accepted_suggestions1.png){width=768}](https://github.com/Codium-ai/pr-agent/wiki/.pr_agent_accepted_suggestions)

This dedicated wiki page will also serve as a foundation for future AI model improvements, allowing it to learn from historically implemented suggestions and generate more targeted, contextually relevant recommendations.

This feature is controlled by a boolean configuration parameter: `pr_code_suggestions.wiki_page_accepted_suggestions` (default is true).

!!! note "Wiki must be enabled"
    While the aggregation process is automatic, GitHub repositories require a one-time manual wiki setup.

    To initialize the wiki: navigate to `Wiki`, select `Create the first page`, then click `Save page`.

    ![pr_agent_accepted_suggestions_create_first_page.png](https://qodo.ai/images/pr_agent/pr_agent_accepted_suggestions_create_first_page.png){width=768}

    Once a wiki repo is created, the tool will automatically use this wiki for tracking suggestions.

!!! note "Why a wiki page?"
    Your code belongs to you, and we respect your privacy. Hence, we won't store any code suggestions in an external database.

    Instead, we leverage a dedicated private page, within your repository wiki, to track suggestions. This approach offers convenient secure suggestion tracking while avoiding pull requests or any noise to the main repository.

## Usage Tips

### Implementing the proposed code suggestions
Each generated suggestion consists of three key elements:

1. A single-line summary of the proposed change
2. An expandable section containing a comprehensive description of the suggestion
3. A diff snippet showing the recommended code modification (before and after)

We advise users to apply critical analysis and judgment when implementing the proposed suggestions.
In addition to mistakes (which may happen, but are rare), sometimes the presented code modification may serve more as an _illustrative example_ than a direct applicable solution.
In such cases, we recommend prioritizing the suggestion's detailed description, using the diff snippet primarily as a supporting reference.

### Dual publishing mode
Our recommended approach for presenting code suggestions is through a [table](https://qodo-merge-docs.qodo.ai/tools/improve/#overview) (`--pr_code_suggestions.commitable_code_suggestions=false`).
This method significantly reduces the PR footprint and allows for quick and easy digestion of multiple suggestions.

We also offer a complementary **dual publishing mode**. When enabled, suggestions exceeding a certain score threshold are not only displayed in the table, but also presented as commitable PR comments.
This mode helps highlight suggestions deemed more critical.

To activate dual publishing mode, use the following setting:

```toml
[pr_code_suggestions]
dual_publishing_score_threshold = x
```

Where x represents the minimum score threshold (>=) for suggestions to be presented as commitable PR comments in addition to the table. Default is -1 (disabled).

### Self-review
If you set in a configuration file:
```toml
[pr_code_suggestions]
demand_code_suggestions_self_review = true
```

The `improve` tool will add a checkbox below the suggestions, prompting user to acknowledge that they have reviewed the suggestions.
You can set the content of the checkbox text via:
```toml
[pr_code_suggestions]
code_suggestions_self_review_text = "... (your text here) ..."
```

![self_review_1](https://codium.ai/images/pr_agent/self_review_1.png){width=512}


!!! tip "Tip - Reducing visual footprint after self-review 💎"

    The configuration parameter `pr_code_suggestions.fold_suggestions_on_self_review` (default is True)
    can be used to automatically fold the suggestions after the user clicks the self-review checkbox.

    This reduces the visual footprint of the suggestions, and also indicates to the PR reviewer that the suggestions have been reviewed by the PR author, and don't require further attention.



!!! tip "Tip - Demanding self-review from the PR author 💎"

    By setting:
    ```toml
    [pr_code_suggestions]
    approve_pr_on_self_review = true
    ```
    the tool can automatically add an approval when the PR author clicks the self-review checkbox.


    - If you set the number of required reviewers for a PR to 2, this effectively means that the PR author must click the self-review checkbox before the PR can be merged (in addition to a human reviewer).

    ![self_review_2](https://codium.ai/images/pr_agent/self_review_2.png){width=512}

    - If you keep the number of required reviewers for a PR to 1 and enable this configuration, this effectively means that the PR author can approve the PR by actively clicking the self-review checkbox.

        To prevent unauthorized approvals, this configuration defaults to false, and cannot be altered through online comments; enabling requires a direct update to the configuration file and a commit to the repository. This ensures that utilizing the feature demands a deliberate documented decision by the repository owner.


### How many code suggestions are generated?
Qodo Merge uses a dynamic strategy to generate code suggestions based on the size of the pull request (PR). Here's how it works:

1) Chunking large PRs:

- Qodo Merge divides large PRs into 'chunks'.
- Each chunk contains up to `pr_code_suggestions.max_context_tokens` tokens (default: 14,000).


2) Generating suggestions:

- For each chunk, Qodo Merge generates up to `pr_code_suggestions.num_code_suggestions_per_chunk` suggestions (default: 4).


This approach has two main benefits:

- Scalability: The number of suggestions scales with the PR size, rather than being fixed.
- Quality: By processing smaller chunks, the AI can maintain higher quality suggestions, as larger contexts tend to decrease AI performance.

Note: Chunking is primarily relevant for large PRs. For most PRs (up to 500 lines of code), Qodo Merge will be able to process the entire code in a single call.


### 'Extra instructions' and 'best practices'

#### Extra instructions

>`Platforms supported: GitHub, GitLab, Bitbucket`

You can use the `extra_instructions` configuration option to give the AI model additional instructions for the `improve` tool.
Be specific, clear, and concise in the instructions. With extra instructions, you are the prompter. Specify relevant aspects that you want the model to focus on.

Examples for possible instructions:
```toml
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

>`Platforms supported: GitHub, GitLab`

Another option to give additional guidance to the AI model is by creating a dedicated [**wiki page**](https://github.com/Codium-ai/pr-agent/wiki) called `best_practices.md`.
This page can contain a list of best practices, coding standards, and guidelines that are specific to your repo/organization.

The AI model will use this wiki page as a reference, and in case the PR code violates any of the guidelines, it will suggest improvements accordingly, with a dedicated label: `Organization
best practice`.

Example for a `best_practices.md` content can be found [here](https://github.com/Codium-ai/pr-agent/blob/main/docs/docs/usage-guide/EXAMPLE_BEST_PRACTICE.md) (adapted from Google's [pyguide](https://google.github.io/styleguide/pyguide.html)).
This file is only an example. Since it is used as a prompt for an AI model, we want to emphasize the following:

- It should be written in a clear and concise manner
- If needed, it should give short relevant code snippets as examples
- Recommended to limit the text to 800 lines or fewer. Here’s why:

     1) Extremely long best practices documents may not be fully processed by the AI model.

     2) A lengthy file probably represent a more "**generic**" set of guidelines, which the AI model is already familiar with. The objective is to focus on a more targeted set of guidelines tailored to the specific needs of this project.

##### Local and global best practices
By default, Qodo Merge will look for a local `best_practices.md` wiki file in the root of the relevant local repo.

If you want to enable also a global `best_practices.md` wiki file, set first in the global configuration file:

```toml
[best_practices]
enable_global_best_practices = true
```

Then, create a `best_practices.md` wiki file in the root of [global](https://qodo-merge-docs.qodo.ai/usage-guide/configuration_options/#global-configuration-file) configuration repository,  `pr-agent-settings`.

##### Best practices for multiple languages
For a git organization working with multiple programming languages, you can maintain a centralized global `best_practices.md` file containing language-specific guidelines. 
When reviewing pull requests, Qodo Merge automatically identifies the programming language and applies the relevant best practices from this file.
Structure your `best_practices.md` file using the following format:

```
# [Python]
...
# [Java]
...
# [JavaScript]
...
```

##### Dedicated label for best practices suggestions
Best practice suggestions are labeled as `Organization best practice` by default. 
To customize this label, modify it in your configuration file:

```toml
[best_practices]
organization_name = ""
```

And the label will be: `{organization_name} best practice`.


##### Example results

![best_practice](https://codium.ai/images/pr_agent/org_best_practice.png){width=512}


#### How to combine `extra instructions` and `best practices`

The `extra instructions` configuration is more related to the `improve` tool prompt. It can be used, for example, to avoid specific suggestions ("Don't suggest to add try-except block", "Ignore changes in toml files", ...) or to emphasize specific aspects or formats ("Answer in Japanese", "Give only short suggestions", ...)

In contrast, the `best_practices.md` file is a general guideline for the way code should be written in the repo.

Using a combination of both can help the AI model to provide relevant and tailored suggestions.

## Configuration options

??? example "General options"

    <table>
      <tr>
        <td><b>extra_instructions</b></td>
        <td>Optional extra instructions to the tool. For example: "focus on the changes in the file X. Ignore change in ...".</td>
      </tr>
      <tr>
        <td><b>commitable_code_suggestions</b></td>
        <td>If set to true, the tool will display the suggestions as commitable code comments. Default is false.</td>
      </tr>
      <tr>
        <td><b>dual_publishing_score_threshold</b></td>
        <td>Minimum score threshold for suggestions to be presented as commitable PR comments in addition to the table. Default is -1 (disabled).</td>
      </tr>
      <tr>
        <td><b>focus_only_on_problems</b></td>
        <td>If set to true, suggestions will focus primarily on identifying and fixing code problems, and less on style considerations like best practices, maintainability, or readability. Default is true.</td> 
      </tr>
      <tr>
        <td><b>persistent_comment</b></td>
        <td>If set to true, the improve comment will be persistent, meaning that every new improve request will edit the previous one. Default is false.</td>
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
      <tr>
        <td><b>enable_chat_text</b></td>
        <td>If set to true, the tool will display a reference to the PR chat in the comment. Default is true.</td>
      </tr>
      <tr>
        <td><b>wiki_page_accepted_suggestions</b></td>
        <td>If set to true, the tool will automatically track accepted suggestions in a dedicated wiki page called `.pr_agent_accepted_suggestions`. Default is true.</td>
      </tr>
    </table>

??? example "Params for number of suggestions and AI calls"

    <table>
      <tr>
        <td><b>auto_extended_mode</b></td>
        <td>Enable chunking the PR code and running the tool on each chunk. Default is true.</td>
      </tr>
      <tr>
        <td><b>num_code_suggestions_per_chunk</b></td>
        <td>Number of code suggestions provided by the 'improve' tool, per chunk. Default is 4.</td>
      </tr>
      <tr>
        <td><b>max_number_of_calls</b></td>
        <td>Maximum number of chunks. Default is 3.</td>
      </tr>
      <tr>
        <td><b>rank_extended_suggestions</b></td>
        <td>If set to true, the tool will rank the suggestions, based on importance. Default is true.</td>
      </tr>
    </table>

## A note on code suggestions quality

- AI models for code are getting better and better (Sonnet-3.5 and GPT-4), but they are not flawless. Not all the suggestions will be perfect, and a user should not accept all of them automatically. Critical reading and judgment are required.
- While mistakes of the AI are rare but can happen, a real benefit from the suggestions of the `improve` (and [`review`](https://qodo-merge-docs.qodo.ai/tools/review/)) tool is to catch, with high probability, **mistakes or bugs done by the PR author**, when they happen. So, it's a good practice to spend the needed ~30-60 seconds to review the suggestions, even if not all of them are always relevant.
- The hierarchical structure of the suggestions is designed to help the user to _quickly_ understand them, and to decide which ones are relevant and which are not:

    - Only if the `Category` header is relevant, the user should move to the summarized suggestion description
    - Only if the summarized suggestion description is relevant, the user should click on the collapsible, to read the full suggestion description with a code preview example.

- In addition, we recommend to use the [`extra_instructions`](https://qodo-merge-docs.qodo.ai/tools/improve/#extra-instructions-and-best-practices) field to guide the model to suggestions that are more relevant to the specific needs of the project.
- The interactive [PR chat](https://qodo-merge-docs.qodo.ai/chrome-extension/) also provides an easy way to get more tailored suggestions and feedback from the AI model.
