## Overview - Static Code Analysis 💎

By combining static code analysis with LLM capabilities, Qodo Merge can provide a comprehensive analysis of the PR code changes on a component level.

It scans the PR code changes, finds all the code components (methods, functions, classes) that changed, and enables to interactively generate tests, docs, code suggestions and similar code search for each component.

!!! note "Language that are currently supported:"
    Python, Java, C++, JavaScript, TypeScript, C#.


## Capabilities

### Analyze PR


The [`analyze`](https://qodo-merge-docs.qodo.ai/tools/analyze/) tool enables to interactively generate tests, docs, code suggestions and similar code search for each component that changed in the PR.
It can be invoked manually by commenting on any PR:
```
/analyze
```

An example result:

![Analyze 1](https://codium.ai/images/pr_agent/analyze_1.png){width=768}

Clicking on each checkbox will trigger the relevant tool for the selected component.

### Generate Tests

The [`test`](https://qodo-merge-docs.qodo.ai/tools/test/) tool  generate tests for a selected component, based on the PR code changes.
It can be invoked manually by commenting on any PR:
```
/test component_name
```
where 'component_name' is the name of a specific component in the PR,  Or be triggered interactively by using the `analyze` tool.

![test1](https://codium.ai/images/pr_agent/test1.png){width=768}

### Generate Docs for a Component

The [`add_docs`](https://qodo-merge-docs.qodo.ai/tools/documentation/) tool scans the PR code changes, and automatically generate docstrings for any code components that changed in the PR.
It can be invoked manually by commenting on any PR:
```
/add_docs component_name
```

Or be triggered interactively by using the `analyze` tool.

![Docs single component](https://codium.ai/images/pr_agent/docs_single_component.png){width=768}

### Generate Code Suggestions for a Component
The [`improve_component`](https://qodo-merge-docs.qodo.ai/tools/improve_component/) tool generates code suggestions for a specific code component that changed in the PR.
It can be invoked manually by commenting on any PR:
```
/improve_component component_name
```

Or be triggered interactively by using the `analyze` tool.

![improve_component2](https://codium.ai/images/pr_agent/improve_component2.png){width=768}

### Find Similar Code

The [`similar code`](https://qodo-merge-docs.qodo.ai/tools/similar_code/) tool retrieves the most similar code components from inside the organization's codebase, or from open-source code.

For example:

`Global Search` for a method called `chat_completion`:

![similar code global](https://codium.ai/images/pr_agent/similar_code_global2.png){width=768}
