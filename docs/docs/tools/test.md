## Overview
By combining LLM abilities with static code analysis, the `test` tool  generate tests for a selected component, based on the PR code changes.
It can be invoked manually by commenting on any PR:
```
/test component_name
```
where 'component_name' is the name of a specific component in the PR.
To get a list of the components that changed in the PR and choose the relevant component interactively, use the [`analyze`](./analyze.md) tool.

## Example usage

Invoke the tool manually by commenting `/test` on any PR:

![test1](https://codium.ai/images/pr_agent/test1.png){width=704}

The tool will generate tests for the selected component (if no component is stated, it will generate tests for largest component):

![test2](https://codium.ai/images/pr_agent/test2.png){width=768}

![test3](https://codium.ai/images/pr_agent/test3.png){width=768}

(Example taken from [here](https://github.com/Codium-ai/pr-agent/pull/598#issuecomment-1913679429)):

**Notes**
- Language that are currently supported by the tool: Python, Java, C++, JavaScript, TypeScript, C#.
- This tool can also be triggered interactively by using the [`analyze`](./analyze.md) tool.


## Configuration options
- `num_tests`: number of tests to generate. Default is 3.
- `testing_framework`: the testing framework to use. If not set, for Python it will use `pytest`, for Java it will use `JUnit`, for C++ it will use `Catch2`, and for JavaScript and TypeScript it will use `jest`.
- `avoid_mocks`: if set to true, the tool will try to avoid using mocks in the generated tests. Note that even if this option is set to true, the tool might still use mocks if it cannot generate a test without them. Default is true.
- `extra_instructions`: Optional extra instructions to the tool. For example: "use the following mock injection scheme: ...".
- `file`: in case there are several components with the same name, you can specify the relevant file.
- `class_name`: in case there are several methods with the same name in the same file, you can specify the relevant class name.
- `enable_help_text`: if set to true, the tool will add a help text to the PR comment. Default is true.