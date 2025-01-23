## Overview
The `custom_prompt` tool scans the PR code changes, and automatically generates suggestions for improving the PR code.
It shares similarities with the `improve` tool, but with one main difference: the `custom_prompt` tool will **only propose suggestions that follow specific guidelines defined by the prompt** in: `pr_custom_prompt.prompt` configuration.

The tool can be triggered [automatically](../usage-guide/automations_and_usage.md#github-app-automatic-tools-when-a-new-pr-is-opened) every time a new PR is opened, or can be invoked manually by commenting on a PR.

When commenting, use the following template:

```
/custom_prompt --pr_custom_prompt.prompt="
The code suggestions should focus only on the following:
- ...
- ...

"
```

With a [configuration file](../usage-guide/automations_and_usage.md#github-app), use the following template:

```
[pr_custom_prompt]
prompt="""\
The suggestions should focus only on the following:
-...
-...

"""
```

Remember - with this tool, you are the prompter. Be specific, clear, and concise in the instructions. Specify relevant aspects that you want the model to focus on. \
You might benefit from several trial-and-error iterations, until you get the correct prompt for your use case.

## Example usage

Here is an example of a possible prompt, defined in the configuration file:
```
[pr_custom_prompt]
prompt="""\
The code suggestions should focus only on the following:
- look for edge cases when implementing a new function
- make sure every variable has a meaningful name
- make sure the code is efficient
"""
```

(The instructions above are just an example. We want to emphasize that the prompt should be specific and clear, and be tailored to the needs of your project)

Results obtained with the prompt above:

![Custom prompt results](https://codium.ai/images/pr_agent/custom_suggestions_result.png){width=768}

## Configuration options

`prompt`: the prompt for the tool. It should be a multi-line string.

`num_code_suggestions`: number of code suggestions provided by the 'custom_prompt' tool. Default is 4.

`enable_help_text`: if set to true, the tool will display a help text in the comment. Default is true.
