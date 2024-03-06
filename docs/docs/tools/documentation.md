## Overview
The `add_docs` tool scans the PR code changes, and automatically suggests documentation for any code components that changed in the PR (functions, classes, etc.).

It can be invoked manually by commenting on any PR:
```
/add_docs
```
For example:

<kbd><img src=https://codium.ai/images/pr_agent/docs_command.png width="768"></kbd>

<kbd><img src=https://codium.ai/images/pr_agent/docs_components.png width="768"></kbd>

<kbd><img src=https://codium.ai/images/pr_agent/docs_single_component.png width="768"></kbd>

## Configuration options
 - `docs_style`: The exact style of the documentation (for python docstring). you can choose between: `google`, `numpy`, `sphinx`, `restructuredtext`, `plain`. Default is `sphinx`.
 - `extra_instructions`: Optional extra instructions to the tool. For example: "focus on the changes in the file X. Ignore change in ...".

**Notes**

- Language that are currently fully supported: Python, Java, C++, JavaScript, TypeScript.
- For languages that are not fully supported, the tool will suggest documentation only for new components in the PR.
- A previous version of the tool, that offered support only for new components, was deprecated.