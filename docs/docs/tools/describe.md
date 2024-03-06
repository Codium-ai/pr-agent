## Overview
The `describe` tool scans the PR code changes, and generates a description for the PR - title, type, summary, walkthrough and labels.

The tool can be triggered automatically every time a new PR is [opened](../usage-guide/automations_and_usage.md#github-app-automatic-tools-when-a-new-pr-is-opened), or it can be invoked manually by commenting on any PR:
```
/describe
```
For example:

<kbd><img src=https://codium.ai/images/pr_agent/describe_comment.png width="768"></kbd>

<kbd><img src=https://codium.ai/images/pr_agent/describe_new.png width="768"></kbd>


  
## Configuration options
To edit [configurations](https://github.com/Codium-ai/pr-agent/blob/main/pr_agent/settings/configuration.toml#L46) related to the describe tool (`pr_description` section), use the following template:
```
/describe --pr_description.some_config1=... --pr_description.some_config2=...
```

### Possible configurations:

- `publish_labels`: if set to true, the tool will publish the labels to the PR. Default is true.

- `publish_description_as_comment`: if set to true, the tool will publish the description as a comment to the PR. If false, it will overwrite the origianl description. Default is false.

- `add_original_user_description`: if set to true, the tool will add the original user description to the generated description. Default is true.

- `keep_original_user_title`: if set to true, the tool will keep the original PR title, and won't change it. Default is true.

- `extra_instructions`: Optional extra instructions to the tool. For example: "focus on the changes in the file X. Ignore change in ...".

- To enable `custom labels`, apply the configuration changes described [here](./custom_labels.md#configuration-options)

- `enable_pr_type`: if set to false, it will not show the `PR type` as a text value in the description content. Default is true.

- `final_update_message`: if set to true, it will add a comment message [`PR Description updated to latest commit...`](https://github.com/Codium-ai/pr-agent/pull/499#issuecomment-1837412176) after finishing calling `/describe`. Default is true.

- `enable_semantic_files_types`: if set to true, "Changes walkthrough" section will be generated. Default is true.
- `collapsible_file_list`: if set to true, the file list in the "Changes walkthrough" section will be collapsible. If set to "adaptive", the file list will be collapsible only if there are more than 8 files. Default is "adaptive".
  
### Inline file summary 💎
> This feature is available only in PR-Agent Pro

This feature will enable you to quickly understand the changes in each file while reviewing the code changes (diff view).

To add the walkthrough table to the "Files changed" tab, you can click on the checkbox that appears PR Description status message below the main PR Description:

<kbd><img src=https://codium.ai/images/pr_agent/add_table_checkbox.png width="512"></kbd>

If you prefer to have the file summaries appear in the "Files changed" tab on every PR, change the `pr_description.inline_file_summary` parameter in the configuration file, possible values are:

- `'table'`: File changes walkthrough table will be displayed on the top of the "Files changed" tab, in addition to the "Conversation" tab.
<kbd><img src=https://codium.ai/images/pr_agent/diffview-table.png width="768"></kbd>

- `true`: A collapsable file comment with changes title and a changes summary for each file in the PR.
<kbd><img src=https://codium.ai/images/pr_agent/diffview_changes.png width="768"></kbd>

- `false` (`default`): File changes walkthrough will be added only to the "Conversation" tab.

**Note** that this feature is currently available only for GitHub.


### Handle custom labels from the Repo's labels page 💎
> This feature is available only in PR-Agent Pro 

You can control  the custom labels that will be suggested by the `describe` tool, from the repo's labels page:

* GitHub : go to `https://github.com/{owner}/{repo}/labels` (or click on the "Labels" tab in the issues or PRs page)
* GitLab : go to `https://gitlab.com/{owner}/{repo}/-/labels` (or click on "Manage" -> "Labels" on the left menu)

Now add/edit the custom labels. they should be formatted as follows:
* Label name: The name of the custom label.
* Description: Start the description of with prefix `pr_agent:`, for example: `pr_agent: Description of when AI should suggest this label`.<br>

The description should be comprehensive and detailed, indicating when to add the desired label. For example:
<kbd><img src=https://codium.ai/images/pr_agent/add_native_custom_labels.png width="880"></kbd>


### Markers template

To enable markers, set `pr_description.use_description_markers=true`.
Markers enable to easily integrate user's content and auto-generated content, with a template-like mechanism.

For example, if the PR original description was:
```
User content...

## PR Type:
pr_agent:type

## PR Description:
pr_agent:summary

## PR Walkthrough:
pr_agent:walkthrough
```
The marker `pr_agent:type` will be replaced with the PR type, `pr_agent:summary` will be replaced with the PR summary, and `pr_agent:walkthrough` will be replaced with the PR walkthrough.

<kbd><img src=https://codium.ai/images/pr_agent/describe_markers_before.png width="768"></kbd>
&rarr;
<kbd><img src=https://codium.ai/images/pr_agent/describe_markers_after.png width="768"></kbd>

### Configuration params:

- `use_description_markers`: if set to true, the tool will use markers template. It replaces every marker of the form `pr_agent:marker_name` with the relevant content. Default is false.
- `include_generated_by_header`: if set to true, the tool will add a dedicated header: 'Generated by PR Agent at ...' to any automatic content. Default is true.


## Usage Tips

### Automation
- When you first install the app, the [default mode](../usage-guide/automations_and_usage.md#github-app) for the describe tool is:
```
pr_commands = ["/describe --pr_description.add_original_user_description=true" 
                         "--pr_description.keep_original_user_title=true", ...]
```
meaning the `describe` tool will run automatically on every PR, will keep the original title, and will add the original user description above the generated description. 
<br> This default settings aim to strike a good balance between automation and control:
If you want more automation, just give the PR a title, and the tool will auto-write a full description; If you want more control, you can add a detailed description, and the tool will add the complementary description below it.
- For maximal automation, you can change the default mode to:
```
pr_commands = ["/describe --pr_description.add_original_user_description=false" 
                         "--pr_description.keep_original_user_title=true", ...]
```
so the title will be auto-generated as well.
- Markers are an alternative way to control the generated description, to give maximal control to the user. If you set:
```
pr_commands = ["/describe --pr_description.use_description_markers=true", ...]
```
the tool will replace every marker of the form `pr_agent:marker_name` in the PR description with the relevant content, where `marker_name` is one of the following:
  - `type`: the PR type.
  - `summary`: the PR summary.
  - `walkthrough`: the PR walkthrough.

Note that when markers are enabled, if the original PR description does not contain any markers, the tool will not alter the description at all.

### Custom labels

The default labels of the describe tool are quite generic, since they are meant to be used in any repo: [`Bug fix`, `Tests`, `Enhancement`, `Documentation`, `Other`].

If you specify [custom labels](#handle-custom-labels-from-the-repos-labels-page) in the repo's labels page, you can get tailored labels for your use cases.
Examples for custom labels:
- `Main topic:performance` -  pr_agent:The main topic of this PR is performance
- `New endpoint` -  pr_agent:A new endpoint was added in this PR
- `SQL query` -  pr_agent:A new SQL query was added in this PR
- `Dockerfile changes` - pr_agent:The PR contains changes in the Dockerfile
- ...

The list above is eclectic, and aims to give an idea of different possibilities. Define custom labels that are relevant for your repo and use cases.
Note that Labels are not mutually exclusive, so you can add multiple label categories.
<br>Make sure to provide proper title, and a detailed and well-phrased description for each label, so the tool will know when to suggest it.