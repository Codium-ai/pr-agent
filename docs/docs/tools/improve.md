## Overview
The `improve` tool scans the PR code changes, and automatically generates suggestions for improving the PR code.
The tool can be triggered automatically every time a new PR is [opened](../usage-guide/automations_and_usage.md#github-app-automatic-tools-when-a-new-pr-is-opened), or it can be invoked manually by commenting on any PR:
```
/improve
```

### Summarized vs committable code suggestions

The code suggestions can be presented as a single comment (via `pr_code_suggestions.summarize=true`):

<kbd>
<a href="https://codium.ai/images/pr_agent/code_suggestions_as_comment.png" target="_blank">
<img src="https://codium.ai/images/pr_agent/code_suggestions_as_comment.png" width="512">
</a>
</kbd>


Or as a separate commitable code comment for each suggestion:

<kbd>
<a href="https://codium.ai/images/pr_agent/improve.png" target="_blank">
<img src="https://codium.ai/images/pr_agent/improve.png" width="512">
</a>
</kbd>

Note that a single comment has a significantly smaller PR footprint. We recommend this mode for most cases.
Also note that collapsible are not supported in _Bitbucket_. Hence, the suggestions are presented there as code comments.

### Extended mode

An extended mode, which does not involve PR Compression and provides more comprehensive suggestions, can be invoked by commenting on any PR:
```
/improve --extended
```

or by setting:
```
[pr_code_suggestions]
auto_extended_mode=true
```
(True by default).

Note that the extended mode divides the PR code changes into chunks, up to the token limits, where each chunk is handled separately (might use multiple calls to GPT-4 for large PRs).
Hence, the total number of suggestions is proportional to the number of chunks, i.e., the size of the PR.

### Configuration options

To edit [configurations](https://github.com/Codium-ai/pr-agent/blob/main/pr_agent/settings/configuration.toml#L66) related to the improve tool (`pr_code_suggestions` section), use the following template:
```
/improve --pr_code_suggestions.some_config1=... --pr_code_suggestions.some_config2=...
```

!!! example "General options"

    - `num_code_suggestions`: number of code suggestions provided by the 'improve' tool. Default is 4 for CLI, 0 for auto tools.
    - `extra_instructions`: Optional extra instructions to the tool. For example: "focus on the changes in the file X. Ignore change in ...".
    - `rank_suggestions`: if set to true, the tool will rank the suggestions, based on importance. Default is false.
    - `summarize`: if set to true, the tool will display the suggestions in a single comment. Default is true.
    - `persistent_comment`: if set to true, the improve comment will be persistent, meaning that every new improve request will edit the previous one. Default is false.
    - `enable_help_text`: if set to true, the tool will display a help text in the comment. Default is true.

!!! example "params for '/improve --extended' mode"

    - `auto_extended_mode`: enable extended mode automatically (no need for the `--extended` option). Default is true.
    - `num_code_suggestions_per_chunk`: number of code suggestions provided by the 'improve' tool, per chunk. Default is 5.
    - `rank_extended_suggestions`: if set to true, the tool will rank the suggestions, based on importance. Default is true.
    - `max_number_of_calls`: maximum number of chunks. Default is 5.
    - `final_clip_factor`: factor to remove suggestions with low confidence. Default is 0.9.


## Usage Tips

!!! tip "Extra instructions"

    Extra instructions are very important for the `imrpove` tool, since they enable you to guide the model to suggestions that are more relevant to the specific needs of the project.
    
    Be specific, clear, and concise in the instructions. With extra instructions, you are the prompter. Specify relevant aspects that you want the model to focus on.
    
    Examples for extra instructions:
    ```
    [pr_code_suggestions] # /improve #
    extra_instructions="""
    Emphasize the following aspects:
    - Does the code logic cover relevant edge cases?
    - Is the code logic clear and easy to understand?
    - Is the code logic efficient?
    ...
    """
    ```
    Use triple quotes to write multi-line instructions. Use bullet points to make the instructions more readable.

!!! tip "Review vs. Improve tools comparison"

    - The [`review`](https://pr-agent-docs.codium.ai/tools/review/) tool includes a section called 'Possible issues', that also provide feedback on the PR Code.
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
Consider also trying the [Custom Suggestions Tool](./custom_suggestions.md) 💎, that will **only** propose suggestions that follow specific guidelines defined by user.
