# Improve Tool

The `improve` tool scans the PR code changes, and automatically generates committable suggestions for improving the PR code.
It can be invoked manually by commenting on any PR:
```
/improve
```
For example:

<kbd><img src=https://codium.ai/images/pr_agent/improve_comment.png width="768"></kbd>
<kbd><img src=https://codium.ai/images/pr_agent/improve.png width="768"></kbd>

The `improve` tool can also be triggered automatically every time a new PR is opened. See examples for automatic triggers for [GitHub App](https://github.com/Codium-ai/pr-agent/blob/main/Usage.md#github-app-automatic-tools) and [GitHub Action](https://github.com/Codium-ai/pr-agent/blob/main/Usage.md#working-with-github-action)

An extended mode, which does not involve PR Compression and provides more comprehensive suggestions, can be invoked by commenting on any PR:
```
/improve --extended
```
Note that the extended mode divides the PR code changes into chunks, up to the token limits, where each chunk is handled separately (multiple calls to GPT-4).
Hence, the total number of suggestions is proportional to the number of chunks, i.e., the size of the PR.

### Configuration options

Under the section 'pr_code_suggestions', the [configuration file](./../pr_agent/settings/configuration.toml#L40) contains options to customize the 'improve' tool:

- `num_code_suggestions`: number of code suggestions provided by the 'improve' tool. Default is 4.
- `extra_instructions`: Optional extra instructions to the tool. For example: "focus on the changes in the file X. Ignore change in ...".
- `rank_suggestions`: if set to true, the tool will rank the suggestions, based on importance. Default is false.

#### params for '/improve --extended' mode
- `num_code_suggestions_per_chunk`: number of code suggestions provided by the 'improve' tool, per chunk. Default is 8.
- `rank_extended_suggestions`: if set to true, the tool will rank the suggestions, based on importance. Default is true.
- `max_number_of_calls`: maximum number of chunks. Default is 5.
- `final_clip_factor`: factor to remove suggestions with low confidence. Default is 0.9.

#### summarize mode
- `summarize`: if set to true, the tool will present the code suggestions in a compact way. Default is false.

In this mode, instead of presenting committable suggestions, the different suggestions will be combined into a single compact comment, with significantly smaller PR footprint.

For example:

`/improve --pr_code_suggestions.summarize=true`

<kbd><img src=https://codium.ai/images/pr_agent/improved_summerize_open.png width="768"></kbd>

___

### A note on code suggestions quality

- While the current AI for code is getting better and better (GPT-4), it's not flawless. Not all the suggestions will be perfect, and a user should not accept all of them automatically.

- Suggestions are not meant to be [simplistic](./../pr_agent/settings/pr_code_suggestions_prompts.toml#L34). Instead, they aim to give deep feedback and raise questions, ideas and thoughts to the user, who can then use his judgment, experience, and understanding of the code base.

- Recommended to use the 'extra_instructions' field to guide the model to suggestions that are more relevant to the specific needs of the project.

- Best quality will be obtained by using 'improve --extended' mode.
