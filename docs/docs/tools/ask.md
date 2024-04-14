## Overview

The `ask` tool answers questions about the PR, based on the PR code changes. Make sure to be specific and clear in your questions.
It can be invoked manually by commenting on any PR:
```
/ask "..."
```
For example:

![Ask Comment](https://codium.ai/images/pr_agent/ask_comment.png){width=512}

![Ask](https://codium.ai/images/pr_agent/ask.png){width=512}

## Ask lines

You can run `/ask` on specific lines of code in the PR from the PR's diff view. The tool will answer questions based on the code changes in the selected lines.
- Click on the '+' sign next to the line number to select the line.
- To select multiple lines, click on the '+' sign of the first line and then hold and drag to select the rest of the lines. 
- write `/ask "..."` in the comment box and press `Add single comment` button.

![Ask Line](https://codium.ai/images/pr_agent/Ask_line.png){width=512}

Note that the tool does not have "memory" of previous questions, and answers each question independently.

## Ask on images (using the PR code as context)

You can also ask questions about images that appear in the comment, where the entire PR is considered as the context. The tool will answer questions based on the images in the PR.
The basic syntax is:
```
/ask "..."

[Image](https://real_link_to_image)
```

Note that GitHub has a mecahnism of pasting images in comments. However, pasted image does not provide a direct link.
To get a direct link to the image, we recommend using the following steps:
1) send a comment that contains only the image:

![Ask image1](https://codium.ai/images/pr_agent/ask_images1.png){width=512}

2) quote reply to that comment:

![Ask image2](https://codium.ai/images/pr_agent/ask_images2.png){width=512}

3) type the question below the image:

![Ask image3](https://codium.ai/images/pr_agent/ask_images3.png){width=512}
![Ask image4](https://codium.ai/images/pr_agent/ask_images3.png){width=512}

4) post the comment, and receive the answer:

![Ask image5](https://codium.ai/images/pr_agent/ask_images5.png){width=512}