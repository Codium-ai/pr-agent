`Platforms supported: GitHub, GitLab, Bitbucket`

## Overview

The `implement` tool converts human code review discussions and feedback into ready-to-commit code changes.
It leverages LLM technology to transform PR comments and review suggestions into concrete implementation code, helping developers quickly turn feedback into working solutions.

## Usage Scenarios


### For Reviewers

Reviewers can request code changes by:

1. Selecting the code block to be modified.
2. Adding a comment with the syntax: 
```
/implement <code-change-description>
```

![implement1](https://codium.ai/images/pr_agent/implement1.png){width=640}


### For PR Authors

PR authors can implement suggested changes by replying to a review comment using either: <br>
1. Add specific implementation details as described above
```
/implement <code-change-description>
```
2. Use the original review comment as instructions
```
/implement
```

![implement2](https://codium.ai/images/pr_agent/implement2.png){width=640}

### For Referencing Comments

You can reference and implement changes from any comment by:
```
/implement <link-to-review-comment>
```

![implement3](https://codium.ai/images/pr_agent/implement3.png){width=640}

Note that the implementation will occur within the review discussion thread.


**Configuration options**

- Use `/implement` to implement code change within and based on the review discussion.
- Use `/implement <code-change-description>` inside a review discussion to implement specific instructions.
- Use `/implement <link-to-review-comment>` to indirectly call the tool from any comment.
