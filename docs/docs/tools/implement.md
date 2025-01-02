## Overview

The `implement` tool automatically generates implementation code based on PR review suggestions.
It combines LLM capabilities with PR review suggestions to help developers implement code changes quickly and with confidence.

## Usage Scenarios


### 1. For Reviewers

Reviewers can request code changes by: <br>
1. Selecting the code block to be modified. <br>
2. Adding a comment with the syntax: 
```
/implement <code-change-description>
```

![implement1](https://codium.ai/images/pr_agent/implement1.png){width=600}


### 2. For PR Authors

PR authors can implement suggested changes by replying to a review comment using either: <br>
1. Add specific implementation details as described above
```
/implement <code-change-description>
```
2. Use the original review comment as instructions
```
/implement
```

![implement2](https://codium.ai/images/pr_agent/implement2.png){width=600}

### 3. For Referencing Comments

You can reference and implement changes from any comment by:
```
/implement <link-to-review-comment>
```

![implement3](https://codium.ai/images/pr_agent/implement3.png){width=600}

Note that the implementation will occur within the review discussion thread.


**Configuration options** <br>
- Use `/implement` to implement code change within and based on the review discussion. <br>
- Use `/implement <code-change-description>` inside a review discussion to implement specific instructions. <br>
- Use `/implement <link-to-review-comment>` to indirectly call the tool from any comment. <br>
