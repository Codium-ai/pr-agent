# Test Tool 💎
By combining LLM abilities with static code analysis, the `test` tool  generate tests for a selected component, based on the PR code changes.
Language that are currently supported by the tool: Python, Java, C++, JavaScript, TypeScript.
It can be invoked manually by commenting on any PR:
```
/test component_name
```
where component_name is the name of a specific component in the PR.
To get a list of the components that changed in the PR, use the [`analyze`](https://github.com/Codium-ai/pr-agent/blob/main/docs/Analyze.md) tool.


An example [result](https://github.com/Codium-ai/pr-agent/pull/598#issuecomment-1913679429):

<kbd><img src=https://codium.ai/images/pr_agent/test1.png width="704"></kbd>
___
<kbd><img src=https://codium.ai/images/pr_agent/test2.png width="768"></kbd>
___
<kbd><img src=https://codium.ai/images/pr_agent/test3.png width="768"></kbd>


### Configuration options
- `num_tests`: number of tests to generate. Default is 3.
- `testing_framework`: the testing framework to use. If not set, for Python it will use `pytest`, for Java it will use `JUnit`, for C++ it will use `Catch2`, and for JavaScript and TypeScript it will use `jest`.
- `avoid_mocks`: if set to true, the tool will try to avoid using mocks in the generated tests. Default is true. Note that even if this option is set to true, the tool might still use mocks if it cannot generate a test without them.
- `extra_instructions`: Optional extra instructions to the tool. For example: "use the following mock injection scheme: ...".