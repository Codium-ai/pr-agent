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
The `improve` tool scans the PR code changes, and automatically generates committable suggestions for improving the PR code.
The tool can be triggered automatically every time a new PR is [opened](https://github.com/Codium-ai/pr-agent/blob/main/Usage.md#github-app-automatic-tools), or it can be invoked manually by commenting on any PR:
```
/improve
```

For example:

<kbd><img src=https://codium.ai/images/pr_agent/improve_comment.png width="768"></kbd>

---

<kbd><img src=https://codium.ai/images/pr_agent/improve.png width="768"></kbd>

---

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
- `include_improved_code`: if set to true, the tool will include an improved code implementation in the suggestion. Default is true.

#### params for '/improve --extended' mode
- `auto_extended_mode`: enable extended mode automatically (no need for the `--extended` option). Default is false.
- `num_code_suggestions_per_chunk`: number of code suggestions provided by the 'improve' tool, per chunk. Default is 8.
- `rank_extended_suggestions`: if set to true, the tool will rank the suggestions, based on importance. Default is true.
- `max_number_of_calls`: maximum number of chunks. Default is 5.
- `final_clip_factor`: factor to remove suggestions with low confidence. Default is 0.9.

#### Summarize mode
In this mode, instead of presenting committable suggestions, the different suggestions will be combined into a single compact comment, with significantly smaller PR footprint.

To invoke the summarize mode, use the following command:
```
/improve --pr_code_suggestions.summarize=true
```

For example:

<kbd><img src=https://codium.ai/images/pr_agent/improved_summerize_open.png width="768"></kbd>

___

## Usage Tips

### Extra instructions
Extra instructions are very important for the `imrpove` tool, since they enable you to guide the model to suggestions that are more relevant to the specific needs of the project.

Be specific, clear, and concise in the instructions. With extra instructions, you are the prompter. Specify relevant aspects that you want the model to focus on.

Examples for extra instructions:
```
[pr_code_suggestions] # /improve #
extra_instructions="""
Emphasize the following aspects:
- Does the code logic covers relevant edge cases?
- Is the code logic clear and easy to understand?
- Is the code logic efficient?
...
"""
```
Use triple quotes to write multi-line instructions. Use bullet points to make the instructions more readable.

### PR footprint - regular vs summarize mode
The default mode of the `improve` tool provides committable suggestions. This mode as a high PR footprint, since each suggestion is a separate comment you need to resolve.
If you prefer something more compact, use the [`summarize`](#summarize-mode) mode, which combines all the suggestions into a single comment.

### A note on code suggestions quality

- While the current AI for code is getting better and better (GPT-4), it's not flawless. Not all the suggestions will be perfect, and a user should not accept all of them automatically.
- Suggestions are not meant to be [simplistic](./../pr_agent/settings/pr_code_suggestions_prompts.toml#L34). Instead, they aim to give deep feedback and raise questions, ideas and thoughts to the user, who can then use his judgment, experience, and understanding of the code base.
- Recommended to use the 'extra_instructions' field to guide the model to suggestions that are more relevant to the specific needs of the project.
- Best quality will be obtained by using 'improve --extended' mode.

