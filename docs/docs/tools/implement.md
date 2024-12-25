## Overview

The `implement` tool automatically generates implementation code based on PR review suggestions.
It combines LLM capabilities with static code analysis to help developers implement code changes quickly and with confidence.


To use the tool, manually invoke it by commenting in any PR discussion that contains code suggestions:
```
/implement
```

## Example usage

Invoke the tool manually by commenting `/implement` on any PR review discussion.
The tool will generate code implementation for the selected discussion:

![implement1](https://codium.ai/images/pr_agent/implement1.png){width=768}


**Notes** <br>
- Languages that are currently supported by the tool: Python, Java, C++, JavaScript, TypeScript, C#. <br>
- Use `/implement <discuttion comment URL>` to indirectly call the tool.