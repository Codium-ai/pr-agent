## Overview

The `ask` tool answers questions about the PR, based on the PR code changes. Make sure to be specific and clear in your questions.
It can be invoked manually by commenting on any PR:
```
/ask "..."
```
For example:

![Ask Comment](https://codium.ai/images/pr_agent/ask_comment.png){width=768}

![Ask](https://codium.ai/images/pr_agent/ask.png){width=768}

## Ask lines

You can run `/ask` on specific lines of code in the PR from the PR's diff view. The tool will answer questions based on the code changes in the selected lines.
- Click on the '+' sign next to the line number to select the line.
- To select multiple lines, click on the '+' sign of the first line and then hold and drag to select the rest of the lines. 
- write `/ask "..."` in the comment box and press `Add single comment` button.

![Ask Line](https://codium.ai/images/pr_agent/Ask_line.png){width=768}

Note that the tool does not have "memory" of previous questions, and answers each question independently.
