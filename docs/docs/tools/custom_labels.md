## Overview
The `generate_labels` tool scans the PR code changes, and given a list of labels and their descriptions, it automatically suggests labels that match the PR code changes.

It can be invoked manually by commenting on any PR:
```
/generate_labels
```
For example:

If we wish to add detect changes to SQL queries in a given PR, we can add the following custom label along with its description:

<kbd><img src=https://codium.ai/images/pr_agent/custom_labels_list.png width="768"></kbd>

When running the `generate_labels` tool on a PR that includes changes in SQL queries, it will automatically suggest the custom label:

<kbd><img src=https://codium.ai/images/pr_agent/custom_label_published.png width="768"></kbd>

Note that in addition to the dedicated tool `generate_labels`, the custom labels will also be used by the `describe` tool.

### How to enable custom labels
There are 3 ways to enable custom labels:

#### 1. CLI (local configuration file)
When working from CLI, you need to apply the [configuration changes](#configuration-options) to the [custom_labels file](https://github.com/Codium-ai/pr-agent/blob/main/pr_agent/settings/custom_labels.toml):

#### 2. Repo configuration file
To enable custom labels, you need to apply the [configuration changes](#configuration-options) to the local `.pr_agent.toml` file in you repository.

#### 3. Handle custom labels from the Repo's labels page 💎
> This feature is available only in PR-Agent Pro 

* GitHub : `https://github.com/{owner}/{repo}/labels`, or click on the "Labels" tab in the issues or PRs page.
* GitLab : `https://gitlab.com/{owner}/{repo}/-/labels`, or click on "Manage" -> "Labels" on the left menu.

b. Add/edit the custom labels. It should be formatted as follows:
* Label name: The name of the custom label.
* Description: Start the description of with prefix `pr_agent:`, for example: `pr_agent: Description of when AI should suggest this label`.<br>
The description should be comprehensive and detailed, indicating when to add the desired label.
<kbd><img src=https://codium.ai/images/pr_agent/add_native_custom_labels.png width="880"></kbd>

c. Now the custom labels will be included in the `generate_labels` tool.

> This feature is supported in GitHub and GitLab.

## Configuration options
 - Change `enable_custom_labels` to True: This will turn off the default labels and enable the custom labels provided in the custom_labels.toml file.
 - Add the custom labels. It should be formatted as follows:

```
[config]
enable_custom_labels=true

[custom_labels."Custom Label Name"]
description = "Description of when AI should suggest this label"

[custom_labels."Custom Label 2"]
description = "Description of when AI should suggest this label 2"
```