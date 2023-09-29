# Describe Tool

The `improve` tool scans the PR code changes, and automatically generate committable suggestions for improving the PR code.
It can be invoked manually by commenting on any PR:
```
/improve
```
For example:

<kbd><img src=./../pics/improve_comment.png width="768"></kbd>
<kbd><img src=./../pics/improve.png width="768"></kbd>

The `improve` tool can also be triggered automatically every time a new PR is opened. See examples for automatic triggers for [GitHub App](https://github.com/Codium-ai/pr-agent/blob/main/Usage.md#github-app-automatic-tools) and [GitHub Action](https://github.com/Codium-ai/pr-agent/blob/main/Usage.md#working-with-github-action)

An extended mode, which does not involve PR Compression and provides more comprehensive suggestions, can be invoked by commenting on any PR:
```
/improve --extended
```
Note that the extended mode divides the PR code changes into chunks, up to the token limits, where each chunk is handled separately (multiple calls to GPT-4).
Hence, the total number of suggestions is proportional to the number of chunks, i.e. the size of the PR.

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