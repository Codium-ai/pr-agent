<div align="center">

<div align="center">


<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://codium.ai/images/pr_agent/logo-dark.png" width="330">
  <source media="(prefers-color-scheme: light)" srcset="https://codium.ai/images/pr_agent/logo-light.png" width="330">
  <img src="https://codium.ai/images/pr_agent/logo-light.png" alt="logo" width="330">

</picture>
<br/>
CodiumAI PR-Agent aims to help efficiently review and handle pull requests, by providing AI feedbacks and suggestions
</div>

[![GitHub license](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://github.com/Codium-ai/pr-agent/blob/main/LICENSE)
[![Static Badge](https://img.shields.io/badge/Chrome-Extension-violet)](https://chromewebstore.google.com/detail/pr-agent-chrome-extension/ephlnjeghhogofkifjloamocljapahnl)
[![Static Badge](https://img.shields.io/badge/Code-Benchmark-blue)](https://pr-agent-docs.codium.ai/finetuning_benchmark/)
[![Discord](https://badgen.net/badge/icon/discord?icon=discord&label&color=purple)](https://discord.com/channels/1057273017547378788/1126104260430528613)
[![Twitter](https://img.shields.io/twitter/follow/codiumai)](https://twitter.com/codiumai)
    <a href="https://github.com/Codium-ai/pr-agent/commits/main">
    <img alt="GitHub" src="https://img.shields.io/github/last-commit/Codium-ai/pr-agent/main?style=for-the-badge" height="20">
    </a>
</div>

### [Documentation](https://pr-agent-docs.codium.ai/)
- See the [Installation Guide](https://pr-agent-docs.codium.ai/installation/) for instructions on installing PR-Agent on different platforms.

- See the [Usage Guide](https://pr-agent-docs.codium.ai/usage-guide/) for instructions on running PR-Agent tools via different interfaces, such as CLI, PR Comments, or by automatically triggering them when a new PR is opened.

- See the [Tools Guide](https://pr-agent-docs.codium.ai/tools/) for a detailed description of the different tools, and the available configurations for each tool.


## Table of Contents
- [News and Updates](#news-and-updates)
- [Overview](#overview)
- [Example results](#example-results)
- [Try it now](#try-it-now)
- [PR-Agent Pro 💎](#pr-agent-pro-)
- [How it works](#how-it-works)
- [Why use PR-Agent?](#why-use-pr-agent)
  
## News and Updates

### June 6, 2024

New option now available (💎) - **apply suggestions**:

<kbd><img src="https://www.codium.ai/images/pr_agent/apply_suggestion_1.png" width="512"></kbd>

&rarr;

<kbd><img src="https://www.codium.ai/images/pr_agent/apply_suggestion_2.png" width="512"></kbd>



### May 31, 2024

Check out the new [**PR-Agent Code Fine-tuning Benchmark**](https://pr-agent-docs.codium.ai/finetuning_benchmark/)

### May 23, 2024

We released a new version of [PR-Agent Chrome extension](https://chromewebstore.google.com/detail/pr-agent-chrome-extension/ephlnjeghhogofkifjloamocljapahnl), with two new features:

- PR-Agent filters 🎨
- Code suggestions interactions 🔗

See more [here](https://www.youtube.com/watch?v=v9bJ1frtPcg)


## Overview
<div style="text-align:left;">

Supported commands per platform:

|       |                                                                                                         | GitHub             | Gitlab             | Bitbucket          | Azure DevOps       |
|-------|---------------------------------------------------------------------------------------------------------|:--------------------:|:--------------------:|:--------------------:|:--------------------:|
| TOOLS | Review                                                                                                  | ✅ | ✅ | ✅ | ✅ |
|       | ⮑ Incremental                                                                                           | ✅ |                    |                    |                    |
|       | ⮑ [SOC2 Compliance](https://pr-agent-docs.codium.ai/tools/review/#soc2-ticket-compliance) 💎            | ✅ | ✅ | ✅ | ✅ |
|       | Describe                                                                                                | ✅ | ✅ | ✅ | ✅ |
|       | ⮑ [Inline File Summary](https://pr-agent-docs.codium.ai/tools/describe#inline-file-summary) 💎          | ✅ |                    |                    |                    |
|       | Improve                                                                                                 | ✅ | ✅ | ✅ | ✅ |
|       | ⮑ Extended                                                                                              | ✅ | ✅ | ✅ | ✅ |
|       | Ask                                                                                                     | ✅ | ✅ | ✅ | ✅ |
|       | ⮑ [Ask on code lines](https://pr-agent-docs.codium.ai/tools/ask#ask-lines)                              | ✅ | ✅ |                    |                    |
|       | [Custom Prompt](https://pr-agent-docs.codium.ai/tools/custom_prompt/) 💎                                | ✅ | ✅ | ✅ | ✅ |
|       | [Test](https://pr-agent-docs.codium.ai/tools/test/) 💎                                                  | ✅ | ✅ |                    | ✅ |
|       | Reflect and Review                                                                                      | ✅ | ✅ | ✅ | ✅ |
|       | Update CHANGELOG.md                                                                                     | ✅ | ✅ | ✅ | ✅ |
|       | Find Similar Issue                                                                                      | ✅ |                    |                    |                    |
|       | [Add PR Documentation](https://pr-agent-docs.codium.ai/tools/documentation/) 💎                         | ✅ | ✅ |                   | ✅ |
|       | [Custom Labels](https://pr-agent-docs.codium.ai/tools/custom_labels/) 💎                                | ✅ | ✅ |                    | ✅ |
|       | [Analyze](https://pr-agent-docs.codium.ai/tools/analyze/) 💎                                            | ✅ | ✅ |                    | ✅ |
|       | [CI Feedback](https://pr-agent-docs.codium.ai/tools/ci_feedback/) 💎                                    | ✅ |                    |                    |                    |
|       | [Similar Code](https://pr-agent-docs.codium.ai/tools/similar_code/) 💎                                  | ✅ |                    |                    |                    |
|       |                                                                                                         |                    |                    |                    |                    |
| USAGE | CLI                                                                                                     | ✅ | ✅ | ✅ | ✅ |
|       | App / webhook                                                                                           | ✅ | ✅ | ✅ | ✅ |
|       | Tagging bot                                                                                             | ✅ |                    |                    |                    |
|       | Actions                                                                                                 | ✅ |                    | ✅ |                    |
|       |                                                                                                         |                    |                    |                    |                    |
| CORE  | PR compression                                                                                          | ✅ | ✅ | ✅ | ✅ |
|       | Repo language prioritization                                                                            | ✅ | ✅ | ✅ | ✅ |
|       | Adaptive and token-aware file patch fitting                                                             | ✅ | ✅ | ✅ | ✅ |
|       | Multiple models support                                                                                 | ✅ | ✅ | ✅ | ✅ |
|       | [Static code analysis](https://pr-agent-docs.codium.ai/core-abilities/#static-code-analysis) 💎         | ✅ | ✅ | ✅ | ✅ |
|       | [Global and wiki configurations](https://pr-agent-docs.codium.ai/usage-guide/configuration_options/) 💎 | ✅ | ✅ | ✅ | ✅ |
|       | [PR interactive actions](https://www.codium.ai/images/pr_agent/pr-actions.mp4) 💎                       | ✅ |                    |                    |                    |
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
‣ **Custom Prompt 💎 ([`/custom_prompt`](https://pr-agent-docs.codium.ai/tools/custom_prompt/))**: Automatically generates custom suggestions for improving the PR code, based on specific guidelines defined by the user.
\
‣ **Generate Tests 💎 ([`/test component_name`](https://pr-agent-docs.codium.ai/tools/test/))**: Generates unit tests for a selected component, based on the PR code changes.
\
‣ **CI Feedback 💎 ([`/checks ci_job`](https://pr-agent-docs.codium.ai/tools/ci_feedback/))**: Automatically generates feedback and analysis for a failed CI job.
\
‣ **Similar Code 💎 ([`/find_similar_component`](https://pr-agent-docs.codium.ai/tools/similar_code/))**: Retrieves the most similar code components from inside the organization's codebase, or from open-source code.
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
<hr>

<h4><a href="https://github.com/Codium-ai/pr-agent/pull/530">/generate_labels</a></h4>
<div align="center">
<p float="center">
<kbd><img src="https://www.codium.ai/images/pr_agent/geneare_custom_labels_main_short.png" width="300"></kbd>
</p>
</div>

[//]: # (<h4><a href="https://github.com/Codium-ai/pr-agent/pull/78#issuecomment-1639739496">/reflect_and_review:</a></h4>)

[//]: # (<div align="center">)

[//]: # (<p float="center">)

[//]: # (<img src="https://www.codium.ai/images/reflect_and_review.gif" width="800">)

[//]: # (</p>)

[//]: # (</div>)

[//]: # (<h4><a href="https://github.com/Codium-ai/pr-agent/pull/229#issuecomment-1695020538">/ask:</a></h4>)

[//]: # (<div align="center">)

[//]: # (<p float="center">)

[//]: # (<img src="https://www.codium.ai/images/ask-2.gif" width="800">)

[//]: # (</p>)

[//]: # (</div>)

[//]: # (<h4><a href="https://github.com/Codium-ai/pr-agent/pull/229#issuecomment-1695024952">/improve:</a></h4>)

[//]: # (<div align="center">)

[//]: # (<p float="center">)

[//]: # (<img src="https://www.codium.ai/images/improve-2.gif" width="800">)

[//]: # (</p>)

[//]: # (</div>)
<div align="left">


</div>
<hr>


## Try it now

Try the GPT-4 powered PR-Agent instantly on _your public GitHub repository_. Just mention `@CodiumAI-Agent` and add the desired command in any PR comment. The agent will generate a response based on your command.
For example, add a comment to any pull request with the following text:
```
@CodiumAI-Agent /review
```
and the agent will respond with a review of your PR

![Review generation process](https://www.codium.ai/images/demo-2.gif)


To set up your own PR-Agent, see the [Installation](https://pr-agent-docs.codium.ai/installation/) section below.
Note that when you set your own PR-Agent or use CodiumAI hosted PR-Agent, there is no need to mention `@CodiumAI-Agent ...`. Instead, directly start with the command, e.g., `/ask ...`.

---

[//]: # (## Installation)

[//]: # (To use your own version of PR-Agent, you first need to acquire two tokens:)

[//]: # ()
[//]: # (1. An OpenAI key from [here]&#40;https://platform.openai.com/&#41;, with access to GPT-4.)

[//]: # (2. A GitHub personal access token &#40;classic&#41; with the repo scope.)

[//]: # ()
[//]: # (There are several ways to use PR-Agent:)

[//]: # ()
[//]: # (**Locally**)

[//]: # (- [Using pip package]&#40;https://pr-agent-docs.codium.ai/installation/locally/#using-pip-package&#41;)

[//]: # (- [Using Docker image]&#40;https://pr-agent-docs.codium.ai/installation/locally/#using-docker-image&#41;)

[//]: # (- [Run from source]&#40;https://pr-agent-docs.codium.ai/installation/locally/#run-from-source&#41;)

[//]: # ()
[//]: # (**GitHub specific methods**)

[//]: # (- [Run as a GitHub Action]&#40;https://pr-agent-docs.codium.ai/installation/github/#run-as-a-github-action&#41;)

[//]: # (- [Run as a GitHub App]&#40;https://pr-agent-docs.codium.ai/installation/github/#run-as-a-github-app&#41;)

[//]: # ()
[//]: # (**GitLab specific methods**)

[//]: # (- [Run a GitLab webhook server]&#40;https://pr-agent-docs.codium.ai/installation/gitlab/&#41;)

[//]: # ()
[//]: # (**BitBucket specific methods**)

[//]: # (- [Run as a Bitbucket Pipeline]&#40;https://pr-agent-docs.codium.ai/installation/bitbucket/&#41;)

## PR-Agent Pro 💎
[PR-Agent Pro](https://www.codium.ai/pricing/) is a hosted version of PR-Agent, provided by CodiumAI. It is available for a monthly fee, and provides the following benefits:
1. **Fully managed** - We take care of everything for you - hosting, models, regular updates, and more. Installation is as simple as signing up and adding the PR-Agent app to your GitHub\GitLab\BitBucket repo.
2. **Improved privacy** - No data will be stored or used to train models. PR-Agent Pro will employ zero data retention, and will use an OpenAI account with zero data retention.
3. **Improved support** - PR-Agent Pro users will receive priority support, and will be able to request new features and capabilities.
4. **Extra features** -In addition to the benefits listed above, PR-Agent Pro will emphasize more customization, and the usage of static code analysis, in addition to LLM logic, to improve results. 
See [here](https://pr-agent-docs.codium.ai/#pr-agent-pro) for a list of features available in PR-Agent Pro.



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
