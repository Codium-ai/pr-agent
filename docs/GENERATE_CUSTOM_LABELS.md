# Generate Custom Labels
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

### How to enable custom labels

Note that in addition to the dedicated tool `generate_labels`, the custom labels will also be used by the `review` and `describe` tools.

#### CLI
To enable custom labels, you need to apply the [configuration changes](#configuration-changes) to the [custom_labels file](./../pr_agent/settings/custom_labels.toml):

#### GitHub Action and GitHub App
To enable custom labels, you need to apply the [configuration changes](#configuration-changes) to the local `.pr_agent.toml` file in you repository.

#### Configuration changes
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

