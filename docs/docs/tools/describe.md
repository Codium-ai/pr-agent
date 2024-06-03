## Overview
The `describe` tool scans the PR code changes, and generates a description for the PR - title, type, summary, walkthrough and labels.

The tool can be triggered automatically every time a new PR is [opened](../usage-guide/automations_and_usage.md#github-app-automatic-tools-when-a-new-pr-is-opened), or it can be invoked manually by commenting on any PR:
```
/describe
```

## Example usage

### Manual triggering

Invoke the tool manually by commenting `/describe` on any PR:

![Describe comment](https://codium.ai/images/pr_agent/describe_comment.png){width=512}

After ~30 seconds, the tool will generate a description for the PR:

![Describe New](https://codium.ai/images/pr_agent/describe_new.png){width=512}

If you want to edit [configurations](#configuration-options), add the relevant ones to the command:
```
/describe --pr_description.some_config1=... --pr_description.some_config2=...
```

### Automatic triggering

To run the `describe` automatically when a PR is opened, define in a [configuration file](https://pr-agent-docs.codium.ai/usage-guide/configuration_options/#wiki-configuration-file):
```
[github_app]
pr_commands = [
    "/describe",
    ...
]

[pr_description]
publish_labels = ...
...
```

- The `pr_commands` lists commands that will be executed automatically when a PR is opened.
- The `[pr_description]` section contains the configurations for the `describe` tool you want to edit (if any).


## Configuration options

!!! example "Possible configurations"

<table>
  <tr>
    <td><b>publish_labels</b></td>
    <td>If set to true, the tool will publish the labels to the PR. Default is true.</td>
  </tr>
  <tr>
    <td><b>publish_description_as_comment</b></td>
    <td>If set to true, the tool will publish the description as a comment to the PR. If false, it will overwrite the original description. Default is false.</td>
  </tr>
  <tr>
    <td><b>publish_description_as_comment_persistent</b></td>
    <td>If set to true and `publish_description_as_comment` is true, the tool will publish the description as a persistent comment to the PR. Default is true.</td>
  </tr>
  <tr>
    <td><b>add_original_user_description</b></td>
    <td>If set to true, the tool will add the original user description to the generated description. Default is true.</td>
  </tr>
  <tr>
    <td><b>generate_ai_title</b></td>
    <td>If set to true, the tool will also generate an AI title for the PR. Default is false.</td>
  </tr>
  <tr>
    <td><b>extra_instructions</b></td>
    <td>Optional extra instructions to the tool. For example: "focus on the changes in the file X. Ignore change in ..."</td>
  </tr>
  <tr>
    <td><b>enable_pr_type</b></td>
    <td>If set to false, it will not show the `PR type` as a text value in the description content. Default is true.</td>
  </tr>
  <tr>
    <td><b>final_update_message</b></td>
    <td>If set to true, it will add a comment message [`PR Description updated to latest commit...`](https://github.com/Codium-ai/pr-agent/pull/499#issuecomment-1837412176) after finishing calling `/describe`. Default is false.</td>
  </tr>
  <tr>
    <td><b>enable_semantic_files_types</b></td>
    <td>If set to true, "Changes walkthrough" section will be generated. Default is true.</td>
  </tr>
  <tr>
    <td><b>collapsible_file_list</b></td>
    <td>If set to true, the file list in the "Changes walkthrough" section will be collapsible. If set to "adaptive", the file list will be collapsible only if there are more than 8 files. Default is "adaptive".</td>
  </tr>
  <tr>
    <td><b>enable_help_text</b></td>
    <td>If set to true, the tool will display a help text in the comment. Default is false.</td>
  </tr>
</table>


## Inline file summary 💎

This feature enables you to copy the `changes walkthrough` table to the "Files changed" tab, so you can quickly understand the changes in each file while reviewing the code changes (diff view).

To copy the `changes walkthrough` table to the "Files changed" tab, you can click on the checkbox that appears PR Description status message below the main PR Description:

![Add table checkbox](https://codium.ai/images/pr_agent/add_table_checkbox.png){width=512}

If you prefer to have the file summaries appear in the "Files changed" tab on every PR, change the `pr_description.inline_file_summary` parameter in the configuration file, possible values are:

- `'table'`: File changes walkthrough table will be displayed on the top of the "Files changed" tab, in addition to the "Conversation" tab.

![Diffview table](https://codium.ai/images/pr_agent/diffview-table.png){width=512}

- `true`: A collapsable file comment with changes title and a changes summary for each file in the PR.

![Diffview changes](https://codium.ai/images/pr_agent/diffview_changes.png){width=512}

- `false` (`default`): File changes walkthrough will be added only to the "Conversation" tab.

**Note**: that this feature is currently available only for GitHub.


## Markers template

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

![Describe markers before](https://codium.ai/images/pr_agent/describe_markers_before.png){width=512}

&rarr;

![Describe markers after](https://codium.ai/images/pr_agent/describe_markers_after.png){width=512}


**Configuration params**:

- `use_description_markers`: if set to true, the tool will use markers template. It replaces every marker of the form `pr_agent:marker_name` with the relevant content. Default is false.
- `include_generated_by_header`: if set to true, the tool will add a dedicated header: 'Generated by PR Agent at ...' to any automatic content. Default is true.

## Custom labels

The default labels of the describe tool are quite generic, since they are meant to be used in any repo: [`Bug fix`, `Tests`, `Enhancement`, `Documentation`, `Other`].

You can define custom labels that are relevant for your repo and use cases.
Custom labels can be defined in a [configuration file](https://pr-agent-docs.codium.ai/tools/custom_labels/#configuration-options), or directly in the repo's [labels page](#handle-custom-labels-from-the-repos-labels-page).

Examples for custom labels:

  - `Main topic:performance` -  pr_agent:The main topic of this PR is performance
  - `New endpoint` -  pr_agent:A new endpoint was added in this PR
  - `SQL query` -  pr_agent:A new SQL query was added in this PR
  - `Dockerfile changes` - pr_agent:The PR contains changes in the Dockerfile
  - ...

The list above is eclectic, and aims to give an idea of different possibilities. Define custom labels that are relevant for your repo and use cases.
Note that Labels are not mutually exclusive, so you can add multiple label categories.
<br>
Make sure to provide proper title, and a detailed and well-phrased description for each label, so the tool will know when to suggest it.
Each label description should be a **conditional statement**, that indicates if to add the label to the PR or not, according to the PR content.


### Handle custom labels from the Repo's labels page 💎

You can control  the custom labels that will be suggested by the `describe` tool, from the repo's labels page:

* GitHub : go to `https://github.com/{owner}/{repo}/labels` (or click on the "Labels" tab in the issues or PRs page)
* GitLab : go to `https://gitlab.com/{owner}/{repo}/-/labels` (or click on "Manage" -> "Labels" on the left menu)

Now add/edit the custom labels. they should be formatted as follows:

* Label name: The name of the custom label.
* Description: Start the description of with prefix `pr_agent:`, for example: `pr_agent: Description of when AI should suggest this label`.<br>

The description should be comprehensive and detailed, indicating when to add the desired label. For example:
![Add native custom labels](https://codium.ai/images/pr_agent/add_native_custom_labels.png){width=768}


## Usage Tips

!!! tip "Automation"
    - When you first install PR-Agent app, the [default mode](../usage-guide/automations_and_usage.md#github-app) for the describe tool is:
    ```
    pr_commands = ["/describe", ...]
    ```
    meaning the `describe` tool will run automatically on every PR, with the default configurations. 


   - Markers are an alternative way to control the generated description, to give maximal control to the user. If you set:
   ```
   pr_commands = ["/describe --pr_description.use_description_markers=true", ...]
   ```
   the tool will replace every marker of the form `pr_agent:marker_name` in the PR description with the relevant content, where `marker_name` is one of the following:
         * `type`: the PR type.
         * `summary`: the PR summary.
         * `walkthrough`: the PR walkthrough.

   - Note that when markers are enabled, if the original PR description does not contain any markers, the tool will not alter the description at all.
