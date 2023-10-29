# Generate Custom Labels
The `generate_labels` tool scans the PR code changes, and given a list of labels and their descriptions, it automatically suggests labels that match the PR code changes.

It can be invoked manually by commenting on any PR:
```
/generate_labels
```
For example:

If we wish to add detect changes to SQL queries in a given PR, we can add the following custom label along with its description:

<kbd><img src=./../pics/custom_labels_list.png width="768"></kbd>
When running the `generate_labels` tool on a PR that includes changes in SQL queries, it will automatically suggest the custom label:
<kbd><img src=./../pics/custom_label_published.png width="768"></kbd>

### Configuration options
To enable custom labels, you need to add the following configuration to the [custom_labels file](./../pr_agent/settings/custom_labels.toml):
 - Change `enable_custom_labels` to True: This will turn off the default labels and enable the custom labels provided in the custom_labels.toml file.
 - Add the custom labels to the custom_labels.toml file. It should be formatted as follows:
 ```
[custom_labels."Custom Label Name"]
description = "Description of when AI should suggest this label"
```
 - You can add modify the list to include all the custom labels you wish to use in your repository.

#### Github Action
To use the `generate_labels` tool with Github Action:

- Add the following file to your repository under `env` section in `.github/workflows/pr_agent.yml`
- Comma separated list of custom labels and their descriptions
- The number of labels and descriptions should be the same and in the same order (empty descriptions are allowed):
```
CUSTOM_LABELS: "label1, label2, ..."
CUSTOM_LABELS_DESCRIPTION: "label1 description, label2 description, ..."
```