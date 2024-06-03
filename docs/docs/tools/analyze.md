## Overview
The `analyze` tool combines advanced static code analysis with LLM capabilities to provide a comprehensive analysis of the PR code changes.

The tool scans the PR code changes, find the code components (methods, functions, classes) that changed, and enables to interactively generate tests, docs, code suggestions and similar code search for each component.

It can be invoked manually by commenting on any PR:
```
/analyze
```

## Example usage

An example result:

![Analyze 1](https://codium.ai/images/pr_agent/analyze_1.png){width=750}

**Notes**

- Language that are currently supported: Python, Java, C++, JavaScript, TypeScript, C#.