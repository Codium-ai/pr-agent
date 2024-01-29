# Improve Tool

## Table of Contents
- [Overview](#overview)
  - [Configuration options](#configuration-options)
  - [Summarize mode](#summarize-mode)
- [Usage Tips](#usage-tips)
    - [Extra instructions](#extra-instructions)
    - [PR footprint - regular vs summarize mode](#pr-footprint---regular-vs-summarize-mode)
    - [A note on code suggestions quality](#a-note-on-code-suggestions-quality)

## Overview
The `improve` tool scans the PR code changes, and automatically generates suggestions for improving the PR code.
The tool can be triggered automatically every time a new PR is [opened](https://github.com/Codium-ai/pr-agent/blob/main/Usage.md#github-app-automatic-tools), or it can be invoked manually by commenting on any PR:
```
/improve
```

### Summarized vs commitable code suggestions

The code suggestions can be presented as a single comment (via `pr_code_suggestions.summarize=true`):
___
<kbd><img src=https://codium.ai/images/pr_agent/code_suggestions_as_comment.png width="768"></kbd>
___

Or as a separate commitable code comment for each suggestion:
___
<kbd><img src=https://codium.ai/images/pr_agent/improve.png width="768"></kbd>

---
Note that a single comment has a significantly smaller PR footprint. We recommend this mode for most cases.
Also note that collapsible are not supported in _Bitbucket_. Hence, the suggestions are presented there as code comments.

### Extended mode

An extended mode, which does not involve PR Compression and provides more comprehensive suggestions, can be invoked by commenting on any PR:
```
/improve --extended
```
Note that the extended mode divides the PR code changes into chunks, up to the token limits, where each chunk is handled separately (might use multiple calls to GPT-4 for large PRs).
Hence, the total number of suggestions is proportional to the number of chunks, i.e., the size of the PR.

### Configuration options

To edit [configurations](./../pr_agent/settings/configuration.toml#L66) related to the improve tool (`pr_code_suggestions` section), use the following template:
```
/improve --pr_code_suggestions.some_config1=... --pr_code_suggestions.some_config2=...
```

#### General options
- `num_code_suggestions`: number of code suggestions provided by the 'improve' tool. Default is 4.
- `extra_instructions`: Optional extra instructions to the tool. For example: "focus on the changes in the file X. Ignore change in ...".
- `rank_suggestions`: if set to true, the tool will rank the suggestions, based on importance. Default is false.
- `summarize`: if set to true, the tool will display the suggestions in a single comment. Default is false.
- `enable_help_text`: if set to true, the tool will display a help text in the comment. Default is true.
#### params for '/improve --extended' mode
- `auto_extended_mode`: enable extended mode automatically (no need for the `--extended` option). Default is false.
- `num_code_suggestions_per_chunk`: number of code suggestions provided by the 'improve' tool, per chunk. Default is 8.
- `rank_extended_suggestions`: if set to true, the tool will rank the suggestions, based on importance. Default is true.
- `max_number_of_calls`: maximum number of chunks. Default is 5.
- `final_clip_factor`: factor to remove suggestions with low confidence. Default is 0.9.


## Usage Tips

### Extra instructions
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

### A note on code suggestions quality

- While the current AI for code is getting better and better (GPT-4), it's not flawless. Not all the suggestions will be perfect, and a user should not accept all of them automatically.
- Suggestions are not meant to be [simplistic](./../pr_agent/settings/pr_code_suggestions_prompts.toml#L34). Instead, they aim to give deep feedback and raise questions, ideas and thoughts to the user, who can then use his judgment, experience, and understanding of the code base.
- Recommended to use the 'extra_instructions' field to guide the model to suggestions that are more relevant to the specific needs of the project.
- Best quality will be obtained by using 'improve --extended' mode.

