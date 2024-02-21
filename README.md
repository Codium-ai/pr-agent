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
### Feb 21, 2024
- Added a new command, `/help`, to easily provide a list of available tools and their descriptions, and run them interactively.

<kbd>

<img src="https://www.codium.ai/images/pr_agent/help.png" width="512">

</kbd>


- GitLab webhook now supports controlling which commands will [run automatically](./docs/USAGE.md#working-with-gitlab-webhook) when a new PR is opened.
### Feb 18, 2024
- Introducing the `CI Feedback` tool 💎. The tool automatically triggers when a PR has a failed check. It analyzes the failed check, and provides summarized logs and analysis. Note that this feature requires read access to GitHub 'checks' and 'actions'. See [here](./docs/CI_FEEDBACK.md) for more details.
- New ability - you can run `/ask` on specific lines of code in the PR from the PR's diff view. See [here](./docs/ASK.md#ask-lines) for more details.
- Introducing support for [Azure DevOps Webhooks](./Usage.md#azure-devops-webhook), as well as bug fixes and improved support for several ADO commands.


### Feb 11, 2024
The `review` tool has been revamped, aiming to make the feedback clearer and more relevant, and better complement the `improve` tool.

### Feb 6, 2024
A new feature was added to the `review` tool - [Auto-approve PRs](./docs/REVIEW.md#auto-approval-1). If enabled, this feature enables to automatically approve PRs that meet specific criteria, by commenting on a PR: `/review auto_approve`.

### Feb 2, 2024
Added  ["PR Actions"](https://www.codium.ai/images/pr_agent/pr-actions.mp4) 💎 - interactively trigger PR-Agent tools from the PR page.


## Overview
<div style="text-align:left;">

CodiumAI PR-Agent is an open-source tool to help efficiently review and handle pull requests. It automatically analyzes the pull request and can provide several types of commands:
|       |                                                                                                                                         | GitHub             | Gitlab             | Bitbucket          | Azure DevOps       |
|-------|-----------------------------------------------------------------------------------------------------------------------------------------|:--------------------:|:--------------------:|:--------------------:|:--------------------:|
| TOOLS | Review                                                                                                                                  | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
|       | ⮑ Incremental                                                                                                                           | :white_check_mark: |                    |                    |                    |
|       | ⮑ [SOC2 Compliance](https://github.com/Codium-ai/pr-agent/blob/main/docs/REVIEW.md#soc2-ticket-compliance-) 💎                           | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
|       | Describe                                                                                                                                | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
|       | ⮑ [Inline File Summary](https://github.com/Codium-ai/pr-agent/blob/main/docs/DESCRIBE.md#inline-file-summary-) 💎                        | :white_check_mark: |                    |                    |                    |
|       | Improve                                                                                                                                 | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
|       | ⮑ Extended                                                                                                                              | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
|       | Ask                                                                                                                                     | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
|       | ⮑ [Ask on code lines](./docs/ASK.md#ask-lines)                                                                                          | :white_check_mark: | :white_check_mark: |                    |                    |
|       | [Custom Suggestions](https://github.com/Codium-ai/pr-agent/blob/main/docs/CUSTOM_SUGGESTIONS.md) 💎                                      | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
|       | [Test](https://github.com/Codium-ai/pr-agent/blob/main/docs/TEST.md) 💎                                                                  | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
|       | Reflect and Review                                                                                                                      | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
|       | Update CHANGELOG.md                                                                                                                     | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
|       | Find Similar Issue                                                                                                                      | :white_check_mark: |                    |                    |                    |
|       | [Add PR Documentation](https://github.com/Codium-ai/pr-agent/blob/main/docs/ADD_DOCUMENTATION.md) 💎                                     | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
|       | [Custom Labels](https://github.com/Codium-ai/pr-agent/blob/main/docs/DESCRIBE.md#handle-custom-labels-from-the-repos-labels-page-gem) 💎 | :white_check_mark: | :white_check_mark: |                    | :white_check_mark: |
|       | [Analyze](https://github.com/Codium-ai/pr-agent/blob/main/docs/Analyze.md) 💎                                                            | :white_check_mark: | :white_check_mark: |                    | :white_check_mark: |
|       | [CI Feedback](https://github.com/Codium-ai/pr-agent/blob/main/docs/CI_FEEDBACK.md) 💎                                                    | :white_check_mark: |                    |                    |                    |
|       |                                                                                                                                         |                    |                    |                    |                    |
| USAGE | CLI                                                                                                                                     | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
|       | App / webhook                                                                                                                           | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
|       | Tagging bot                                                                                                                             | :white_check_mark: |                    |                    |                    |
|       | Actions                                                                                                                                 | :white_check_mark: |                    | :white_check_mark: |                    |
|       |                                                                                                                                         |                    |                    |                    |                    |
| CORE  | PR compression                                                                                                                          | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
|       | Repo language prioritization                                                                                                            | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
|       | Adaptive and token-aware file patch fitting                                                                                             | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
|       | Multiple models support                                                                                                                 | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
|       | [Static code analysis](https://github.com/Codium-ai/pr-agent/blob/main/docs/Analyze.md) 💎                                               | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
|       | [Global configuration](https://github.com/Codium-ai/pr-agent/blob/main/Usage.md#global-configuration-file-) 💎                           | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
|       | [PR Actions](https://www.codium.ai/images/pr_agent/pr-actions.mp4) 💎                                                                    | :white_check_mark: |                    |                    |                    |
- 💎 means this feature is available only in [PR-Agent Pro](https://www.codium.ai/pricing/)
- Support for additional git providers is described in [here](./docs/Full_environments.md)
___

‣ **Auto Description ([`/describe`](./docs/DESCRIBE.md))**: Automatically generating PR description - title, type, summary, code walkthrough and labels.
\
‣ **Auto Review ([`/review`](./docs/REVIEW.md))**: Adjustable feedback about the PR, possible issues, security concerns, review effort and more.
\
‣ **Question Answering ([`/ask ...`](./docs/ASK.md))**: Answering free-text questions about the PR.
\
‣ **Code Suggestions ([`/improve`](./docs/IMPROVE.md))**: Code suggestions for improving the PR.
\
‣ **Update Changelog ([`/update_changelog`](./docs/UPDATE_CHANGELOG.md))**: Automatically updating the CHANGELOG.md file with the PR changes.
\
‣ **Find Similar Issue ([`/similar_issue`](./docs/SIMILAR_ISSUE.md))**: Automatically retrieves and presents similar issues.
\
‣ **Add Documentation 💎  ([`/add_docs`](./docs/ADD_DOCUMENTATION.md))**: Generates documentation to methods/functions/classes that changed in the PR.
\
‣ **Generate Custom Labels 💎 ([`/generate_labels`](./docs/GENERATE_CUSTOM_LABELS.md))**: Generates custom labels for the PR, based on specific guidelines defined by the user.
\
‣ **Analyze 💎 ([`/analyze`](./docs/Analyze.md))**: Identify code components that changed in the PR, and enables to interactively generate tests, docs, and code suggestions for each component.
\
‣ **Custom Suggestions 💎 ([`/custom_suggestions`](./docs/CUSTOM_SUGGESTIONS.md))**: Automatically generates custom suggestions for improving the PR code, based on specific guidelines defined by the user.
\
‣ **Generate Tests 💎 ([`/test component_name`](./docs/TEST.md))**: Automatically generates unit tests for a selected component, based on the PR code changes.
\
‣ **CI Feedback 💎 ([`/checks ci_job`](./docs/CI_FEEDBACK.md))**: Automatically generates feedback and analysis for a failed CI job.

See the [Installation Guide](./INSTALL.md) for instructions on installing and running the tool on different git platforms.

See the [Usage Guide](./Usage.md) for running the PR-Agent commands via different interfaces, including _CLI_, _online usage_, or by _automatically triggering_ them when a new PR is opened.

See the [Tools Guide](./docs/TOOLS_GUIDE.md) for a detailed description of the different tools (tools are run via the commands).


## Example results
</div>
<h4><a href="https://github.com/Codium-ai/pr-agent/pull/530">/describe</a></h4>
<div align="center">
<p float="center">
<img src="https://www.codium.ai/images/pr_agent/describe_new_short_main.png" width="800">
</p>
</div>
<hr>
<h4><a href="https://github.com/Codium-ai/pr-agent/pull/472#discussion_r1435819374">/improve</a></h4>

<div align="center">
<p float="center">
<kbd>
<img src="https://www.codium.ai/images/pr_agent/improve_short_main.png" width="768">
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


To set up your own PR-Agent, see the [Installation](#installation) section below.
Note that when you set your own PR-Agent or use CodiumAI hosted PR-Agent, there is no need to mention `@CodiumAI-Agent ...`. Instead, directly start with the command, e.g., `/ask ...`.

---

## Installation
To use your own version of PR-Agent, you first need to acquire two tokens:

1. An OpenAI key from [here](https://platform.openai.com/), with access to GPT-4.
2. A GitHub personal access token (classic) with the repo scope.

There are several ways to use PR-Agent:

**Locally**
- [Use Docker image (no installation required)](./INSTALL.md#use-docker-image-no-installation-required)
- [Run from source](./INSTALL.md#run-from-source)

**GitHub specific methods**
- [Run as a GitHub Action](./INSTALL.md#run-as-a-github-action)
- [Run as a GitHub App](./INSTALL.md#run-as-a-github-app)

**GitLab specific methods**
- [Run a GitLab webhook server](./INSTALL.md#run-a-gitlab-webhook-server)

**BitBucket specific methods**
- [Run as a Bitbucket Pipeline](./INSTALL.md#run-as-a-bitbucket-pipeline)

## PR-Agent Pro 💎
[PR-Agent Pro](https://www.codium.ai/pricing/) is a hosted version of PR-Agent, provided by CodiumAI. It is available for a monthly fee, and provides the following benefits:
1. **Fully managed** - We take care of everything for you - hosting, models, regular updates, and more. Installation is as simple as signing up and adding the PR-Agent app to your GitHub\BitBucket repo.
2. **Improved privacy** - No data will be stored or used to train models. PR-Agent Pro will employ zero data retention, and will use an OpenAI account with zero data retention.
3. **Improved support** - PR-Agent Pro users will receive priority support, and will be able to request new features and capabilities.
4. **Extra features** -In addition to the benefits listed above, PR-Agent Pro will emphasize more customization, and the usage of static code analysis, in addition to LLM logic, to improve results. It has the following additional tools and features:
    - [**Analyze PR components**](https://github.com/Codium-ai/pr-agent/blob/main/docs/Analyze.md)
    - [**Custom Code Suggestions**](https://github.com/Codium-ai/pr-agent/blob/main/docs/CUSTOM_SUGGESTIONS.md)
    - [**Tests**](https://github.com/Codium-ai/pr-agent/blob/main/docs/TEST.md)
    - [**PR documentation**](https://github.com/Codium-ai/pr-agent/blob/main/docs/ADD_DOCUMENTATION.md)
    - [**SOC2 compliance check**](https://github.com/Codium-ai/pr-agent/blob/main/docs/REVIEW.md#soc2-ticket-compliance-)
    - [**Custom labels**](https://github.com/Codium-ai/pr-agent/blob/main/docs/DESCRIBE.md#handle-custom-labels-from-the-repos-labels-page-gem)
    - [**Global configuration**](https://github.com/Codium-ai/pr-agent/blob/main/Usage.md#global-configuration-file-)



## How it works

The following diagram illustrates PR-Agent tools and their flow:

![PR-Agent Tools](https://codium.ai/images/pr_agent/diagram-v0.9.png)

Check out the [PR Compression strategy](./PR_COMPRESSION.md) page for more details on how we convert a code diff to a manageable LLM prompt

## Why use PR-Agent?

A reasonable question that can be asked is: `"Why use PR-Agent? What makes it stand out from existing tools?"`

Here are some advantages of PR-Agent:

- We emphasize **real-life practical usage**. Each tool (review, improve, ask, ...) has a single GPT-4 call, no more. We feel that this is critical for realistic team usage - obtaining an answer quickly (~30 seconds) and affordably.
- Our [PR Compression strategy](./PR_COMPRESSION.md)  is a core ability that enables to effectively tackle both short and long PRs.
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
