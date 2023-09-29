# Update Changelog Tool

The `update_changelog` tool automatically updates the CHANGELOG.md file with the PR changes.
It can be invoked manually by commenting on any PR:
```
/update_changelog
```
For example:

<kbd><img src=./../pics/update_changelog_comment.png width="768"></kbd>
<kbd><img src=./../pics/update_changelog.png width="768"></kbd>


### Configuration options

Under the section 'pr_update_changelog', the [configuration file](./../pr_agent/settings/configuration.toml#L50) contains options to customize the 'update changelog' tool:

- `push_changelog_changes`: whether to push the changes to CHANGELOG.md, or just print them. Default is false (print only).
- `extra_instructions`: Optional extra instructions to the tool. For example: "focus on the changes in the file X. Ignore change in ...