# Add Documentation Tool
The `add_docs` tool scans the PR code changes, and automatically suggests documentation for the undocumented code components (functions, classes, etc.).

It can be invoked manually by commenting on any PR:
```
/add_docs
```
For example:

<kbd><img src=./../pics/add_docs_comment.png width="768"></kbd>
<kbd><img src=./../pics/add_docs.png width="768"></kbd>

### Configuration options
 - `docs_style`: The exact style of the documentation (for python docstring). you can choose between: `google`, `numpy`, `sphinx`, `restructuredtext`, `plain`. Default is `sphinx`.
 - `extra_instructions`: Optional extra instructions to the tool. For example: "focus on the changes in the file X. Ignore change in ...".