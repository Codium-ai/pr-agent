## Overview

The CI feedback tool (`/checks)` automatically triggers when a PR has a failed check.
The tool analyzes the failed checks and provides several feedbacks:

- Failed stage
- Failed test name
- Failure summary
- Relevant error logs

## Example usage

![Failed Check 1](https://www.codium.ai/images/pr_agent/failed_check1.png){width=768}

&rarr;
![Failed Check 2](https://www.codium.ai/images/pr_agent/failed_check2.png){width=768}

___

In addition to being automatically triggered, the tool can also be invoked manually by commenting on a PR:
```
/checks "https://github.com/{repo_name}/actions/runs/{run_number}/job/{job_number}"
```
where `{repo_name}` is the name of the repository, `{run_number}` is the run number of the failed check, and `{job_number}` is the job number of the failed check.

## Disabling the tool from running automatically

If you wish to disable the tool from running automatically, you can do so by adding the following configuration to the configuration file:
```
[checks]
enable_auto_checks_feedback = false
```

## Configuration options
- `enable_auto_checks_feedback` - if set to true, the tool will automatically provide feedback when a check is failed. Default is true.
- `excluded_checks_list` - a list of checks to exclude from the feedback, for example: ["check1", "check2"]. Default is an empty list.
- `persistent_comment` - if set to true, the tool will overwrite a previous checks comment with the new feedback. Default is true.
- `enable_help_text=true` - if set to true, the tool will provide a help message when a user comments "/checks" on a PR. Default is true.
- `final_update_message` - if `persistent_comment` is true and updating a previous checks message, the tool will also create a new message: "Persistent checks updated to latest commit". Default is true.
