<div align="center">

<div align="center">


<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://codium.ai/images/pr_agent/logo-dark.png" width="330">
  <source media="(prefers-color-scheme: light)" srcset="https://codium.ai/images/pr_agent/logo-light.png" width="330">
  <img alt="logo">
</picture>
<br/>
Making pull requests less painful with an AI agent
</div>

[![GitHub license](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://github.com/Codium-ai/pr-agent/blob/main/LICENSE)
[![Discord](https://badgen.net/badge/icon/discord?icon=discord&label&color=purple)](https://discord.com/channels/1057273017547378788/1126104260430528613)
[![Twitter](https://img.shields.io/twitter/follow/codiumai)](https://twitter.com/codiumai)
    <a href="https://github.com/Codium-ai/pr-agent/commits/main">
    <img alt="GitHub" src="https://img.shields.io/github/last-commit/Codium-ai/pr-agent/main?style=for-the-badge" height="20">
    </a>
</div>

## Table of Contents
- [News and Updates](#news-and-updates)
- [Overview](#overview)
- [Example results](#example-results)
- [Try it now](#try-it-now)
- [Installation](#installation)
- [PR-Agent Pro 💎](#pr-agent-pro-)
- [How it works](#how-it-works)
- [Why use PR-Agent?](#why-use-pr-agent)
  
## News and Updates

### Jan 17, 2024
- A new feature is now available for the review tool: [`require_can_be_split_review`](https://pr-agent-docs.codium.ai/tools/review/#enabledisable-features). 
If set to true, the tool will add a section that checks if the PR contains several themes, and can be split into smaller PRs.

<kbd><img src="https://codium.ai/images/pr_agent/multiple_pr_themes.png" width="512"></kbd>

### Jan 10, 2024
- A new [knowledge-base website](https://pr-agent-docs.codium.ai/) for PR-Agent is now available. It includes detailed information about the different tools, usage guides and more, in an accessible and organized format.

### Jan 8, 2024

- A new tool, [Find Similar Code](https://pr-agent-docs.codium.ai/tools/similar_code/) 💎 is now available. 
<br>This tool retrieves the most similar code components from inside the organization's codebase, or from open-source code:

<kbd><a href="https://codium.ai/images/pr_agent/similar_code.mp4"><img src="https://codium.ai/images/pr_agent/similar_code_global2.png" width="512"></a></kbd>

(click on the image to see an instructional video)

### Feb 29, 2024
- You can now use the repo's [wiki page](https://pr-agent-docs.codium.ai/usage-guide/configuration_options/) to set configurations for PR-Agent 💎

<kbd><img src="https://codium.ai/images/pr_agent/wiki_configuration.png" width="512"></kbd>


## Overview
<div style="text-align:left;">

CodiumAI PR-Agent is an open-source tool to help efficiently review and handle pull requests.

- See the [Installation Guide](https://pr-agent-docs.codium.ai/installation/) for instructions on installing and running the tool on different git platforms.

- See the [Usage Guide](https://pr-agent-docs.codium.ai/usage-guide/) for instructions on running the PR-Agent commands via different interfaces, including _CLI_, _online usage_, or by _automatically triggering_ them when a new PR is opened.

- See the [Tools Guide](https://pr-agent-docs.codium.ai/tools/) for a detailed description of the different tools.

Supported commands per platform:

|       |                                                                                                                   | GitHub             | Gitlab             | Bitbucket          | Azure DevOps       |
|-------|-------------------------------------------------------------------------------------------------------------------|:--------------------:|:--------------------:|:--------------------:|:--------------------:|
| TOOLS | Review                                                                                                            | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
|       | ⮑ Incremental                                                                                                     | :white_check_mark: |                    |                    |                    |
|       | ⮑ [SOC2 Compliance](https://pr-agent-docs.codium.ai/tools/review/#soc2-ticket-compliance) 💎            | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
|       | Describe                                                                                                          | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
|       | ⮑ [Inline File Summary](https://pr-agent-docs.codium.ai/tools/describe#inline-file-summary) 💎          | :white_check_mark: |                    |                    |                    |
|       | Improve                                                                                                           | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
|       | ⮑ Extended                                                                                                        | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
|       | Ask                                                                                                               | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
|       | ⮑ [Ask on code lines](https://pr-agent-docs.codium.ai/tools/ask#ask-lines)                              | :white_check_mark: | :white_check_mark: |                    |                    |
|       | [Custom Suggestions](https://pr-agent-docs.codium.ai/tools/custom_suggestions/) 💎                      | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
|       | [Test](https://pr-agent-docs.codium.ai/tools/test/) 💎                                                  | :white_check_mark: | :white_check_mark: |                    | :white_check_mark: |
|       | Reflect and Review                                                                                                | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
|       | Update CHANGELOG.md                                                                                               | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
|       | Find Similar Issue                                                                                                | :white_check_mark: |                    |                    |                    |
|       | [Add PR Documentation](https://pr-agent-docs.codium.ai/tools/documentation/) 💎                         | :white_check_mark: | :white_check_mark: |                   | :white_check_mark: |
|       | [Custom Labels](https://pr-agent-docs.codium.ai/tools/custom_labels/) 💎                                | :white_check_mark: | :white_check_mark: |                    | :white_check_mark: |
|       | [Analyze](https://pr-agent-docs.codium.ai/tools/analyze/) 💎                                            | :white_check_mark: | :white_check_mark: |                    | :white_check_mark: |
|       | [CI Feedback](https://pr-agent-docs.codium.ai/tools/ci_feedback/) 💎                                    | :white_check_mark: |                    |                    |                    |
|       | [Similar Code](https://pr-agent-docs.codium.ai/tools/similar_code/) 💎                                  | :white_check_mark: |                    |                    |                    |
|       |                                                                                                                   |                    |                    |                    |                    |
| USAGE | CLI                                                                                                               | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
|       | App / webhook                                                                                                     | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
|       | Tagging bot                                                                                                       | :white_check_mark: |                    |                    |                    |
|       | Actions                                                                                                           | :white_check_mark: |                    | :white_check_mark: |                    |
|       |                                                                                                                   |                    |                    |                    |                    |
| CORE  | PR compression                                                                                                    | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
|       | Repo language prioritization                                                                                      | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
|       | Adaptive and token-aware file patch fitting                                                                       | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
|       | Multiple models support                                                                                           | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
|       | [Static code analysis](https://pr-agent-docs.codium.ai/core-abilities/#static-code-analysis) 💎         | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
|       | [Global and wiki configurations](https://pr-agent-docs.codium.ai/usage-guide/configuration_options/) 💎 | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
|       | [PR interactive actions](https://www.codium.ai/images/pr_agent/pr-actions.mp4) 💎                                 | :white_check_mark: |                    |                    |                    |
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
‣ **Custom Suggestions 💎 ([`/custom_suggestions`](https://pr-agent-docs.codium.ai/tools/custom_suggestions/))**: Automatically generates custom suggestions for improving the PR code, based on specific guidelines defined by the user.
\
‣ **Generate Tests 💎 ([`/test component_name`](https://pr-agent-docs.codium.ai/tools/test/))**: Generates unit tests for a selected component, based on the PR code changes.
\
‣ **CI Feedback 💎 ([`/checks ci_job`](https://pr-agent-docs.codium.ai/tools/ci_feedback/))**: Automatically generates feedback and analysis for a failed CI job.
\
‣ **Similar Code 💎 ([`/find_similar_component`](https://pr-agent-docs.codium.ai/tools/similar_code//))**: Retrieves the most similar code components from inside the organization's codebase, or from open-source code.
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

## Installation
To use your own version of PR-Agent, you first need to acquire two tokens:

1. An OpenAI key from [here](https://platform.openai.com/), with access to GPT-4.
2. A GitHub personal access token (classic) with the repo scope.

There are several ways to use PR-Agent:

**Locally**
- [Use Docker image (no installation required)](https://pr-agent-docs.codium.ai/installation/locally/#use-docker-image-no-installation-required)
- [Run from source](https://pr-agent-docs.codium.ai/installation/locally/#run-from-source)

**GitHub specific methods**
- [Run as a GitHub Action](https://pr-agent-docs.codium.ai/installation/github/#run-as-a-github-action)
- [Run as a GitHub App](https://pr-agent-docs.codium.ai/installation/github/#run-as-a-github-app)

**GitLab specific methods**
- [Run a GitLab webhook server](https://pr-agent-docs.codium.ai/installation/gitlab/)

**BitBucket specific methods**
- [Run as a Bitbucket Pipeline](https://pr-agent-docs.codium.ai/installation/bitbucket/)

## PR-Agent Pro 💎
[PR-Agent Pro](https://www.codium.ai/pricing/) is a hosted version of PR-Agent, provided by CodiumAI. It is available for a monthly fee, and provides the following benefits:
1. **Fully managed** - We take care of everything for you - hosting, models, regular updates, and more. Installation is as simple as signing up and adding the PR-Agent app to your GitHub\BitBucket repo.
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

If you host PR-Agent with your OpenAI API key, it is between you and OpenAI. You can read their API data privacy policy here:
https://openai.com/enterprise-privacy

When using PR-Agent Pro 💎, hosted by CodiumAI, we will not store any of your data, nor will we use it for training.
You will also benefit from an OpenAI account with zero data retention.

## Links

[![Join our Discord community](https://raw.githubusercontent.com/Codium-ai/codiumai-vscode-release/main/media/docs/Joincommunity.png)](https://discord.gg/kG35uSHDBc)

- Discord community: https://discord.gg/kG35uSHDBc
- CodiumAI site: https://codium.ai
- Blog: https://www.codium.ai/blog/
- Troubleshooting: https://www.codium.ai/blog/technical-faq-and-troubleshooting/
- Support: support@codium.ai
