## Ignoring files from analysis

In some cases, you may want to exclude specific files or directories from the analysis performed by CodiumAI PR-Agent. This can be useful, for example, when you have files that are generated automatically or files that shouldn't be reviewed, like vendored code.

You can ignore files or folders using the following methods:
 - `IGNORE.GLOB`
 - `IGNORE.REGEX`

which you can edit to ignore files or folders based on glob or regex patterns.

### Example usage

Let's look at an example where we want to ignore all files with `.py` extension from the analysis.

To ignore Python files in a PR with online usage, comment on a PR:
`/review --ignore.glob="['*.py']"`


To ignore Python files in all PRs using `glob` pattern, set in a configuration file:
```
[ignore]
glob = ['*.py']
```

And to ignore Python files in all PRs using `regex` pattern, set in a configuration file:
```
[regex]
regex = ['.*\.py$']
```

## Extra instructions

All PR-Agent tools have a parameter called `extra_instructions`, that enables to add free-text extra instructions. Example usage:
```
/update_changelog --pr_update_changelog.extra_instructions="Make sure to update also the version ..."
```

## Working with large PRs

The default mode of CodiumAI is to have a single call per tool, using GPT-4, which has a token limit of 8000 tokens.
This mode provides a very good speed-quality-cost tradeoff, and can handle most PRs successfully.
When the PR is above the token limit, it employs a [PR Compression strategy](../core-abilities/index.md).

However, for very large PRs, or in case you want to emphasize quality over speed and cost, there are two possible solutions:
1) [Use a model](https://codium-ai.github.io/Docs-PR-Agent/usage-guide/#changing-a-model) with larger context, like GPT-32K, or claude-100K. This solution will be applicable for all the tools.
2) For the `/improve` tool, there is an ['extended' mode](https://codium-ai.github.io/Docs-PR-Agent/tools/#improve) (`/improve --extended`),
which divides the PR to chunks, and processes each chunk separately. With this mode, regardless of the model, no compression will be done (but for large PRs, multiple model calls may occur)



## Patch Extra Lines

By default, around any change in your PR, git patch provides three lines of context above and below the change.
```
@@ -12,5 +12,5 @@ def func1():
 code line that already existed in the file...
 code line that already existed in the file...
 code line that already existed in the file....
-code line that was removed in the PR
+new code line added in the PR
 code line that already existed in the file...
 code line that already existed in the file...
 code line that already existed in the file...
```

For the `review`, `describe`, `ask` and `add_docs` tools, if the token budget allows, PR-Agent tries to increase the number of lines of context, via the parameter:
```
[config]
patch_extra_lines=3
```

Increasing this number provides more context to the model, but will also increase the token budget.
If the PR is too large (see [PR Compression strategy](https://github.com/Codium-ai/pr-agent/blob/main/PR_COMPRESSION.md)), PR-Agent automatically sets this number to 0, using the original git patch.


## Editing the prompts

The prompts for the various PR-Agent tools are defined in the `pr_agent/settings` folder.
In practice, the prompts are loaded and stored as a standard setting object.
Hence, editing them is similar to editing any other configuration value - just place the relevant key in `.pr_agent.toml`file, and override the default value.

For example, if you want to edit the prompts of the [describe](https://github.com/Codium-ai/pr-agent/blob/main/pr_agent/settings/pr_description_prompts.toml) tool, you can add the following to your `.pr_agent.toml` file:
```
[pr_description_prompt]
system="""
...
"""
user="""
...
"""
```
Note that the new prompt will need to generate an output compatible with the relevant [post-process function](https://github.com/Codium-ai/pr-agent/blob/main/pr_agent/tools/pr_description.py#L137).
