# Overview

Qodo Merge is an open-source tool to help efficiently review and handle pull requests.

- See the [Installation Guide](./installation/index.md) for instructions on installing and running the tool on different git platforms.

- See the [Usage Guide](./usage-guide/index.md) for instructions on running the Qodo Merge commands via different interfaces, including _CLI_, _online usage_, or by _automatically triggering_ them when a new PR is opened.

- See the [Tools Guide](./tools/index.md) for a detailed description of the different tools.


## Qodo Merge Docs Smart Search

To search the documentation site using natural language:

1) Comment `/help "your question"` in either:

   - A pull request where Qodo Merge is installed
   - A [PR Chat](https://qodo-merge-docs.qodo.ai/chrome-extension/features/#pr-chat)

2) Qodo Merge will respond with an [answer](https://github.com/Codium-ai/pr-agent/pull/1241#issuecomment-2365259334) that includes relevant documentation links.


## Qodo Merge Features

Qodo Merge offers extensive pull request functionalities across various git providers.

|       |                                                                                                         | GitHub             | GitLab             | Bitbucket          | Azure DevOps |
|-------|---------------------------------------------------------------------------------------------------------|:--------------------:|:--------------------:|:--------------------:|:------------:|
| TOOLS | [Review](https://qodo-merge-docs.qodo.ai/tools/review/)                                                                                                  | ✅ | ✅ | ✅ |      ✅       |
|       | [Describe](https://qodo-merge-docs.qodo.ai/tools/describe/)                                                                                                | ✅ | ✅ | ✅ |      ✅       |
|       | [Improve](https://qodo-merge-docs.qodo.ai/tools/improve/)                                                                                                 | ✅ | ✅ | ✅ |      ✅       |
|       | [Ask](https://qodo-merge-docs.qodo.ai/tools/ask/)                                                                                                     | ✅ | ✅ | ✅ |      ✅       |
|       | ⮑ [Ask on code lines](https://pr-agent-docs.codium.ai/tools/ask#ask-lines)                              | ✅ | ✅ |                    |              |
|       | [Update CHANGELOG](https://qodo-merge-docs.qodo.ai/tools/update_changelog/)                                                                                     | ✅ | ✅ | ✅ |      ✅       |
|       | [Ticket Context](https://qodo-merge-docs.qodo.ai/core-abilities/fetching_ticket_context/) 💎  | ✅ | ✅ |  ✅                  |   |
|       | [Utilizing Best Practices](https://qodo-merge-docs.qodo.ai/tools/improve/#best-practices) 💎  | ✅ | ✅ |  ✅                  |   |
|       | [PR Chat](https://qodo-merge-docs.qodo.ai/chrome-extension/features/#pr-chat) 💎  | ✅ |  |                    |   |
|       | [Suggestion Tracking](https://qodo-merge-docs.qodo.ai/tools/improve/#suggestion-tracking) 💎  | ✅ | ✅ |                    |   |
|       | [CI Feedback](https://pr-agent-docs.codium.ai/tools/ci_feedback/) 💎                                    | ✅ |                    |                    |              |
|       | [PR Documentation](https://pr-agent-docs.codium.ai/tools/documentation/) 💎                         | ✅ | ✅ |                   |              |
|       | [Custom Labels](https://pr-agent-docs.codium.ai/tools/custom_labels/) 💎                                | ✅ | ✅ |                    |              |
|       | [Analyze](https://pr-agent-docs.codium.ai/tools/analyze/) 💎                                            | ✅ | ✅ |                    |              |
|       | [Similar Code](https://pr-agent-docs.codium.ai/tools/similar_code/) 💎                                  | ✅ |                    |                    |              |
|       | [Custom Prompt](https://pr-agent-docs.codium.ai/tools/custom_prompt/) 💎                                | ✅ | ✅ | ✅ |              |
|       | [Test](https://pr-agent-docs.codium.ai/tools/test/) 💎                                                  | ✅ | ✅ |                    |              |
|       |                                                                                                         |                    |                    |                    |              |
| USAGE | [CLI](https://qodo-merge-docs.qodo.ai/usage-guide/automations_and_usage/#local-repo-cli)                                                                                                     | ✅ | ✅ | ✅ |      ✅       |
|       | [App / webhook](https://qodo-merge-docs.qodo.ai/usage-guide/automations_and_usage/#github-app)                                                                                           | ✅ | ✅ | ✅ |      ✅       |
|       | [Tagging bot](https://github.com/Codium-ai/pr-agent#try-it-now)                                                                                             | ✅ |                    |                    |              |
|       | [Actions](https://qodo-merge-docs.qodo.ai/installation/github/#run-as-a-github-action)                                                                                                 | ✅ |✅| ✅ |✅|
|       |                                                                                                         |                    |                    |                    |              |
| CORE  | [PR compression](https://qodo-merge-docs.qodo.ai/core-abilities/compression_strategy/)                                                                  | ✅ | ✅ | ✅ |      ✅       |
|       | Adaptive and token-aware file patch fitting                                                             | ✅ | ✅ | ✅ |      ✅       |
|       | [Multiple models support](https://qodo-merge-docs.qodo.ai/usage-guide/changing_a_model/)                                                                                 | ✅ | ✅ | ✅ |      ✅       |
|       | [Local and global metadata](https://qodo-merge-docs.qodo.ai/core-abilities/metadata/)          | ✅ | ✅ | ✅ | ✅             |
|       | [Dynamic context](https://qodo-merge-docs.qodo.ai/core-abilities/dynamic_context/)          | ✅ | ✅ | ✅ | ✅             |
|       | [Self reflection](https://qodo-merge-docs.qodo.ai/core-abilities/self_reflection/)          | ✅ | ✅ | ✅ | ✅             |
|       | [Static code analysis](https://qodo-merge-docs.qodo.ai/core-abilities/static_code_analysis/) 💎         | ✅ | ✅ | ✅ |              |
|       | [Global and wiki configurations](https://pr-agent-docs.codium.ai/usage-guide/configuration_options/) 💎 | ✅ | ✅ | ✅ |              |
|       | [PR interactive actions](https://www.codium.ai/images/pr_agent/pr-actions.mp4) 💎                       | ✅ |        ✅           |                    |              |
|       | [Impact Evaluation](https://qodo-merge-docs.qodo.ai/core-abilities/impact_evaluation/) 💎  | ✅ | ✅ |                    |   |

💎 marks a feature available only in [Qodo Merge Pro](https://www.qodo.ai/pricing/){:target="_blank"}


## Example Results
<hr>

#### [/describe](https://github.com/Codium-ai/pr-agent/pull/530)
<figure markdown="1">
![/describe](https://www.codium.ai/images/pr_agent/describe_new_short_main.png){width=512}
</figure>
<hr>

#### [/review](https://github.com/Codium-ai/pr-agent/pull/732#issuecomment-1975099151)
<figure markdown="1">
![/review](https://www.codium.ai/images/pr_agent/review_new_short_main.png){width=512}
</figure>
<hr>

#### [/improve](https://github.com/Codium-ai/pr-agent/pull/732#issuecomment-1975099159)
<figure markdown="1">
![/improve](https://www.codium.ai/images/pr_agent/improve_new_short_main.png){width=512}
</figure>
<hr>

#### [/generate_labels](https://github.com/Codium-ai/pr-agent/pull/530)
<figure markdown="1">
![/generate_labels](https://www.codium.ai/images/pr_agent/geneare_custom_labels_main_short.png){width=300}
</figure>
<hr>

## How it Works

The following diagram illustrates Qodo Merge tools and their flow:

![Qodo Merge Tools](https://codium.ai/images/pr_agent/diagram-v0.9.png)

Check out the [core abilities](core-abilities/index.md) page for a comprehensive overview of the variety of core abilities used by Qodo Merge.
