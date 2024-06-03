## Overview
The `improve_component` tool generates code suggestions for a specific code component that changed in the PR.
it can be invoked manually by commenting on any PR:
```
/improve_component component_name
```

To get a list of the components that changed in the PR and choose the relevant component interactively, use the [`analyze`](./analyze.md) tool.


## Example usage

Invoke the tool manually by commenting `/improve_component` on any PR:

![improve_component1](https://codium.ai/images/pr_agent/improve_component1.png){width=768}

The tool will generate code suggestions for the selected component (if no component is stated, it will generate code suggestions for the largest component):

![improve_component2](https://codium.ai/images/pr_agent/improve_component2.png){width=768}

**Notes**
- Language that are currently supported by the tool: Python, Java, C++, JavaScript, TypeScript, C#.
- This tool can also be triggered interactively by using the [`analyze`](./analyze.md) tool.

## Configuration options
- `num_code_suggestions`: number of code suggestions to provide. Default is 4
- `extra_instructions`: Optional extra instructions to the tool. For example: "focus on ...".
- `file`: in case there are several components with the same name, you can specify the relevant file.
- `class_name`: in case there are several methods with the same name in the same file, you can specify the relevant class name.