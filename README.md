<div align="center">

<div align="center">


<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://codium.ai/images/pr_agent/logo-dark.png" width="330">
  <source media="(prefers-color-scheme: light)" srcset="https://codium.ai/images/pr_agent/logo-light.png" width="330">
  <img src="https://codium.ai/images/pr_agent/logo-light.png" alt="logo" width="330">

</picture>
<br/>
Qode Merge 1 1223 PR-Agent aims to help efficiently review and handle pull requests, by providing AI feedback and suggestions
</div>

[![Static Badge](https://img.shields.io/badge/Chrome-Extension-violet)](https://chromewebstore.google.com/detail/pr-agent-chrome-extension/ephlnjeghhogofkifjloamocljapahnl)
[![Static Badge](https://img.shields.io/badge/Pro-App-blue)](https://github.com/apps/qodo-merge-pro/)
[![Static Badge](https://img.shields.io/badge/OpenSource-App-red)](https://github.com/apps/qodo-merge-pro-for-open-source/)
[![Discord](https://badgen.net/badge/icon/discord?icon=discord&label&color=purple)](https://discord.com/channels/1057273017547378788/1126104260430528613)
<a href="https://github.com/Codium-ai/pr-agent/commits/main">
<img alt="GitHub" src="https://img.shields.io/github/last-commit/Codium-ai/pr-agent/main?style=for-the-badge" height="20">
</a>
</div>

### [Documentation](https://pr-agent-docs.codium.ai/)
- See the [Installation Guide](https://qodo-merge-docs.qodo.ai/installation/) for instructions on installing Qode Merge PR-Agent on different platforms.

- See the [Usage Guide](https://qodo-merge-docs.qodo.ai/usage-guide/) for instructions on running Qode Merge PR-Agent tools via different interfaces, such as CLI, PR Comments, or by automatically triggering them when a new PR is opened.

- See the [Tools Guide](https://qodo-merge-docs.qodo.ai/tools/) for a detailed description of the different tools, and the available configurations for each tool.


## Table of Contents
- [News and Updates](#news-and-updates)
- [Overview](#overview)
- [Example results](#example-results)
- [Try it now](#try-it-now)
- [PR-Agent Pro 💎](https://pr-agent-docs.codium.ai/overview/pr_agent_pro/)
- [How it works](#how-it-works)
- [Why use PR-Agent?](#why-use-pr-agent)

## News and Updates

### Jan 2, 2025

New tool  [/Implement](https://qodo-merge-docs.qodo.ai/tools/implement/) (💎), which converts human code review discussions and feedback into ready-to-commit code changes.

<kbd><img src="https://codium.ai/images/pr_agent/implement1.png" width="512"></kbd>


### Jan 1, 2025

Update logic and [documentation](https://qodo-merge-docs.qodo.ai/usage-guide/changing_a_model/#ollama) for running local models via Ollama.

### December 30, 2024

Following [feedback](https://research.kudelskisecurity.com/2024/08/29/careful-where-you-code-multiple-vulnerabilities-in-ai-powered-pr-agent/) from the community, we have addressed two vulnerabilities identified in the open-source PR-Agent project. The fixes are now included in the newly released version (v0.26), available as of today.

### December 25, 2024

The `review` tool previously included a legacy feature for providing code suggestions (controlled by '--pr_reviewer.num_code_suggestion'). This functionality has been deprecated. Use instead the [`improve`](https://qodo-merge-docs.qodo.ai/tools/improve/) tool, which offers higher quality and more actionable code suggestions.

### December 2, 2024

Open-source repositories can now freely use Qodo Merge Pro, and enjoy easy one-click installation using a marketplace [app](https://github.com/apps/qodo-merge-pro-for-open-source).

<kbd><img src="https://github.com/user-attachments/assets/b0838724-87b9-43b0-ab62-73739a3a855c" width="512"></kbd>

See [here](https://qodo-merge-docs.qodo.ai/installation/pr_agent_pro/) for more details about installing Qodo Merge Pro for private repositories.


### November 18, 2024

A new mode was enabled by default for code suggestions - `--pr_code_suggestions.focus_only_on_problems=true`:

- This option reduces the number of code suggestions received
- The suggestions will focus more on identifying and fixing code problems, rather than style considerations like best practices, maintainability, or readability.
- The suggestions will be categorized into just two groups: "Possible Issues" and "General".

Still, if you prefer the previous mode, you can set `--pr_code_suggestions.focus_only_on_problems=false` in the [configuration file](https://qodo-merge-docs.qodo.ai/usage-guide/configuration_options/).

**Example results:**

Original mode

<kbd><img src="https://qodo.ai/images/pr_agent/code_suggestions_original_mode.png" width="512"></kbd>

Focused mode

<kbd><img src="https://qodo.ai/images/pr_agent/code_suggestions_focused_mode.png" width="512"></kbd>


## Overview
<div style="text-align:left;">

Supported commands per platform:

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
|       | [Implement](https://pr-agent-docs.codium.ai/tools/implement/) 💎                                        | ✅ | ✅ |         ✅          |              |
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
- 💎 means this feature is available only in [PR-Agent Pro](https://www.codium.ai/pricing/)

[//]: # (- Support for additional git providers is described in [here]&#40;./docs/Full_environments.md&#41;)
___

‣ **Auto Description ([`/describe`](https://pr-agent-docs.codium.ai/tools/describe/))**: Automatically generating PR description - title, type, summary, code walkthrough and labels.
\
‣ **Auto Review ([`/review`](https://pr-agent-docs.codium.ai/tools/review/))**: Adjustable feedback about the PR, possible issues, security concerns, review effort and more.
\
‣ **Code Suggestions ([`/improve`](https://pr-agent-docs.codium.ai/tools/improve/))**: Code suggestions for improving the PR.
\
‣ **Question Answering ([`/ask ...`](https://pr-agent-docs.codium.ai/tools/ask/))**: Answering free-text questions about the PR.
\
‣ **Update Changelog ([`/update_changelog`](https://pr-agent-docs.codium.ai/tools/update_changelog/))**: Automatically updating the CHANGELOG.md file with the PR changes.
\
‣ **Find Similar Issue ([`/similar_issue`](https://pr-agent-docs.codium.ai/tools/similar_issues/))**: Automatically retrieves and presents similar issues.
\
‣ **Add Documentation 💎  ([`/add_docs`](https://pr-agent-docs.codium.ai/tools/documentation/))**: Generates documentation to methods/functions/classes that changed in the PR.
\
‣ **Generate Custom Labels 💎 ([`/generate_labels`](https://pr-agent-docs.codium.ai/tools/custom_labels/))**: Generates custom labels for the PR, based on specific guidelines defined by the user.
\
‣ **Analyze 💎 ([`/analyze`](https://pr-agent-docs.codium.ai/tools/analyze/))**: Identify code components that changed in the PR, and enables to interactively generate tests, docs, and code suggestions for each component.
\
‣ **Test 💎 ([`/test`](https://pr-agent-docs.codium.ai/tools/test/))**: Generate tests for a selected component, based on the PR code changes.
\
‣ **Custom Prompt 💎 ([`/custom_prompt`](https://pr-agent-docs.codium.ai/tools/custom_prompt/))**: Automatically generates custom suggestions for improving the PR code, based on specific guidelines defined by the user.
\
‣ **Generate Tests 💎 ([`/test component_name`](https://pr-agent-docs.codium.ai/tools/test/))**: Generates unit tests for a selected component, based on the PR code changes.
\
‣ **CI Feedback 💎 ([`/checks ci_job`](https://pr-agent-docs.codium.ai/tools/ci_feedback/))**: Automatically generates feedback and analysis for a failed CI job.
\
‣ **Similar Code 💎 ([`/find_similar_component`](https://pr-agent-docs.codium.ai/tools/similar_code/))**: Retrieves the most similar code components from inside the organization's codebase, or from open-source code.
\
‣ **Implement 💎 ([`/implement`](https://qodo-merge-docs.qodo.ai/tools/implement/))**: Generates implementation code from review suggestions.
___

## Example results
</div>
<h4><a href="https://github.com/Codium-ai/pr-agent/pull/530">/describe</a></h4>
<div align="center">
<p float="center">
<img src="https://www.codium.ai/images/pr_agent/describe_new_short_main.png" width="512">
</p>
</div>
<hr>

<h4><a href="https://github.com/Codium-ai/pr-agent/pull/732#issuecomment-1975099151">/review</a></h4>
<div align="center">
<p float="center">
<kbd>
<img src="https://www.codium.ai/images/pr_agent/review_new_short_main.png" width="512">
</kbd>
</p>
</div>
<hr>

<h4><a href="https://github.com/Codium-ai/pr-agent/pull/732#issuecomment-1975099159">/improve</a></h4>
<div align="center">
<p float="center">
<kbd>
<img src="https://www.codium.ai/images/pr_agent/improve_new_short_main.png" width="512">
</kbd>
</p>
</div>


<div align="left">


</div>
<hr>


## Try it now

Try the GPT-4 powered PR-Agent instantly on _your public GitHub repository_. Just mention `@CodiumAI-Agent` and add the desired command in any PR comment. The agent will generate a response based on your command.
For example, add a comment to any pull request with the following text:
```
@CodiumAI-Agent /review
```
and the agent will respond with a review of your PR.

Note that this is a promotional bot, suitable only for initial experimentation.
It does not have 'edit' access to your repo, for example, so it cannot update the PR description or add labels (`@CodiumAI-Agent /describe` will publish PR description as a comment). In addition, the bot cannot be used on private repositories, as it does not have access to the files there.


![Review generation process](https://www.codium.ai/images/demo-2.gif)


To set up your own PR-Agent, see the [Installation](https://pr-agent-docs.codium.ai/installation/) section below.
Note that when you set your own PR-Agent or use CodiumAI hosted PR-Agent, there is no need to mention `@CodiumAI-Agent ...`. Instead, directly start with the command, e.g., `/ask ...`.

---


## PR-Agent Pro 💎
[PR-Agent Pro](https://www.codium.ai/pricing/) is a hosted version of PR-Agent, provided by CodiumAI. It is available for a monthly fee, and provides the following benefits:
1. **Fully managed** - We take care of everything for you - hosting, models, regular updates, and more. Installation is as simple as signing up and adding the PR-Agent app to your GitHub\GitLab\BitBucket repo.
2. **Improved privacy** - No data will be stored or used to train models. PR-Agent Pro will employ zero data retention, and will use an OpenAI account with zero data retention.
3. **Improved support** - PR-Agent Pro users will receive priority support, and will be able to request new features and capabilities.
4. **Extra features** -In addition to the benefits listed above, PR-Agent Pro will emphasize more customization, and the usage of static code analysis, in addition to LLM logic, to improve results.
See [here](https://qodo-merge-docs.qodo.ai/overview/pr_agent_pro/) for a list of features available in PR-Agent Pro.



## How it works

The following diagram illustrates PR-Agent tools and their flow:

![PR-Agent Tools](https://codium.ai/images/pr_agent/diagram-v0.9.png)

Check out the [PR Compression strategy](https://pr-agent-docs.codium.ai/core-abilities/#pr-compression-strategy) page for more details on how we convert a code diff to a manageable LLM prompt

## Why use PR-Agent?

A reasonable question that can be asked is: `"Why use PR-Agent? What makes it stand out from existing tools?"`

Here are some advantages of PR-Agent:

- We emphasize **real-life practical usage**. Each tool (review, improve, ask, ...) has a single GPT-4 call, no more. We feel that this is critical for realistic team usage - obtaining an answer quickly (~30 seconds) and affordably.
- Our [PR Compression strategy](https://pr-agent-docs.codium.ai/core-abilities/#pr-compression-strategy)  is a core ability that enables to effectively tackle both short and long PRs.
- Our JSON prompting strategy enables to have **modular, customizable tools**. For example, the '/review' tool categories can be controlled via the [configuration](pr_agent/settings/configuration.toml) file. Adding additional categories is easy and accessible.
- We support **multiple git providers** (GitHub, Gitlab, Bitbucket), **multiple ways** to use the tool (CLI, GitHub Action, GitHub App, Docker, ...), and **multiple models** (GPT-4, GPT-3.5, Anthropic, Cohere, Llama2).


## Data privacy

### Self-hosted PR-Agent

- If you host PR-Agent with your OpenAI API key, it is between you and OpenAI. You can read their API data privacy policy here:
https://openai.com/enterprise-privacy

### CodiumAI-hosted PR-Agent Pro 💎

- When using PR-Agent Pro 💎, hosted by CodiumAI, we will not store any of your data, nor will we use it for training. You will also benefit from an OpenAI account with zero data retention.

- For certain clients, CodiumAI-hosted PR-Agent Pro will use CodiumAI’s proprietary models — if this is the case, you will be notified.

- No passive collection of Code and Pull Requests’ data — PR-Agent will be active only when you invoke it, and it will then extract and analyze only data relevant to the executed command and queried pull request.

### PR-Agent Chrome extension

- The [PR-Agent Chrome extension](https://chromewebstore.google.com/detail/pr-agent-chrome-extension/ephlnjeghhogofkifjloamocljapahnl) serves solely to modify the visual appearance of a GitHub PR screen. It does not transmit any user's repo or pull request code. Code is only sent for processing when a user submits a GitHub comment that activates a PR-Agent tool, in accordance with the standard privacy policy of PR-Agent.

## Links

[![Join our Discord community](https://raw.githubusercontent.com/Codium-ai/codiumai-vscode-release/main/media/docs/Joincommunity.png)](https://discord.gg/kG35uSHDBc)

- Discord community: https://discord.gg/kG35uSHDBc
- CodiumAI site: https://codium.ai
- Blog: https://www.codium.ai/blog/
- Troubleshooting: https://www.codium.ai/blog/technical-faq-and-troubleshooting/
- Support: support@codium.ai
