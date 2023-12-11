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
<div style="text-align:left;">

CodiumAI `PR-Agent` is an open-source tool for efficient pull request reviewing and handling. It automatically analyzes the pull request and can provide several types of commands:

‣ **Auto Description ([`/describe`](./docs/DESCRIBE.md))**: Automatically generating PR description - title, type, summary, code walkthrough and labels.
\
‣ **Auto Review ([`/review`](./docs/REVIEW.md))**: Adjustable feedback about the PR main theme, type, relevant tests, security issues, score, and various suggestions for the PR content.
\
‣ **Question Answering ([`/ask ...`](./docs/ASK.md))**: Answering free-text questions about the PR.
\
‣ **Code Suggestions ([`/improve`](./docs/IMPROVE.md))**: Committable code suggestions for improving the PR.
\
‣ **Update Changelog ([`/update_changelog`](./docs/UPDATE_CHANGELOG.md))**: Automatically updating the CHANGELOG.md file with the PR changes.
\
‣ **Find Similar Issue ([`/similar_issue`](./docs/SIMILAR_ISSUE.md))**: Automatically retrieves and presents similar issues.
\
‣ **Add Documentation ([`/add_docs`](./docs/ADD_DOCUMENTATION.md))**: Automatically adds documentation to un-documented functions/classes in the PR.
\
‣ **Generate Custom Labels ([`/generate_labels`](./docs/GENERATE_CUSTOM_LABELS.md))**: Automatically suggests custom labels based on the PR code changes.

See the [Installation Guide](./INSTALL.md) for instructions on installing and running the tool on different git platforms.

See the [Usage Guide](./Usage.md) for running the PR-Agent commands via different interfaces, including _CLI_, _online usage_, or by _automatically triggering_ them when a new PR is opened.

See the [Tools Guide](./docs/TOOLS_GUIDE.md) for detailed description of the different tools (tools are run via the commands).

<h3>Example results:</h3>
</div>
<h4><a href="https://github.com/Codium-ai/pr-agent/pull/229#issuecomment-1687561986">/describe:</a></h4>
<div align="center">
<p float="center">
<img src="https://www.codium.ai/images/describe-2.gif" width="800">
</p>
</div>

<h4><a href="https://github.com/Codium-ai/pr-agent/pull/229#issuecomment-1695021901">/review:</a></h4>
<div align="center">
<p float="center">
<img src="https://www.codium.ai/images/review-2.gif" width="800">
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

## Table of Contents
- [Overview](#overview)
- [Try it now](#try-it-now)
- [Installation](#installation)
- [How it works](#how-it-works)
- [Why use PR-Agent?](#why-use-pr-agent)
- [Roadmap](#roadmap)
</div>


## Overview
`PR-Agent` offers extensive pull request functionalities across various git providers:
|       |                                             | GitHub | Gitlab | Bitbucket | CodeCommit | Azure DevOps | Gerrit |
|-------|---------------------------------------------|:------:|:------:|:---------:|:----------:|:----------:|:----------:|
| TOOLS | Review                                      |   :white_check_mark:    |   :white_check_mark:    |   :white_check_mark:       |   :white_check_mark:    |   :white_check_mark:    |   :white_check_mark:    |
|       | ⮑ Incremental                              |   :white_check_mark:    |       |           |       |          |     |
|       | Ask                                         |   :white_check_mark:    |   :white_check_mark:    |   :white_check_mark:          |   :white_check_mark:          | :white_check_mark: |  :white_check_mark:    |
|       | Auto-Description                            |   :white_check_mark:    |   :white_check_mark:    |   :white_check_mark:        |   :white_check_mark:    |   :white_check_mark:    | :white_check_mark:    |
|       | Improve Code                                |   :white_check_mark:    |   :white_check_mark:    |   :white_check_mark:        |   :white_check_mark:    |          |    :white_check_mark:    |
|       | ⮑ Extended                             |   :white_check_mark:    |   :white_check_mark:    |        :white_check_mark:   |   :white_check_mark:    |          | :white_check_mark:    |
|       | Reflect and Review                          |   :white_check_mark:    |   :white_check_mark:    |   :white_check_mark:        |          |   :white_check_mark:    |    :white_check_mark:    |
|       | Update CHANGELOG.md                         |   :white_check_mark:    |   :white_check_mark:    |   :white_check_mark:        |   :white_check_mark:    |          |       |
|       | Find similar issue                          |   :white_check_mark:    |                         |                             |          |          |       |
|       | Add Documentation                           |   :white_check_mark:    |   :white_check_mark:    |   :white_check_mark:        |   :white_check_mark:    |          |    :white_check_mark:    |
|       | Generate Labels                           |   :white_check_mark:    |   :white_check_mark:    |         |     |          |      |
|       |                                             |        |        |      |      |      |
| USAGE | CLI                                         |   :white_check_mark:    |   :white_check_mark:    |   :white_check_mark:       |   :white_check_mark:    |   :white_check_mark:    |
|       | App / webhook                               |   :white_check_mark:    |   :white_check_mark:    |           |          |          |
|       | Tagging bot                                 |   :white_check_mark:    |        |           |          |          |
|       | Actions                                     |   :white_check_mark:    |        |           |          |          |
|       | Web server                                  |       |        |           |          |          |  :white_check_mark:   |
|       |                                             |        |        |      |      |      |
| CORE  | PR compression                              |   :white_check_mark:    |   :white_check_mark:    |   :white_check_mark:       | :white_check_mark: |   :white_check_mark:       | :white_check_mark:       |
|       | Repo language prioritization                |   :white_check_mark:    |   :white_check_mark:    |   :white_check_mark:       | :white_check_mark: |   :white_check_mark:       | :white_check_mark:       |
|       | Adaptive and token-aware<br />file patch fitting |   :white_check_mark:    |   :white_check_mark:    |   :white_check_mark:       | :white_check_mark: |   :white_check_mark:       | :white_check_mark:       |
|       | Multiple models support |   :white_check_mark:    |   :white_check_mark:    |   :white_check_mark:       | :white_check_mark: |   :white_check_mark:       | :white_check_mark:       |
|       | Incremental PR Review |   :white_check_mark:    |      |      |      |      |      |

Review the [usage guide](./Usage.md) section for detailed instructions how to use the different tools, select the relevant git provider (GitHub, Gitlab, Bitbucket,...), and adjust the configuration file to your needs.

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

To get started with PR-Agent quickly, you first need to acquire two tokens:

1. An OpenAI key from [here](https://platform.openai.com/), with access to GPT-4.
2. A GitHub personal access token (classic) with the repo scope.

There are several ways to use PR-Agent:

- [Method 1: Use Docker image (no installation required)](INSTALL.md#method-1-use-docker-image-no-installation-required)
- [Method 2: Run from source](INSTALL.md#method-2-run-from-source)
- [Method 3: Run as a GitHub Action](INSTALL.md#method-3-run-as-a-github-action)
- [Method 4: Run as a polling server](INSTALL.md#method-4-run-as-a-polling-server)
  - Request reviews by tagging your GitHub user on a PR
- [Method 5: Run as a GitHub App](INSTALL.md#method-5-run-as-a-github-app)
  - Allowing you to automate the review process on your private or public repositories
- [Method 6: Deploy as a Lambda Function](INSTALL.md#method-6---deploy-as-a-lambda-function)
- [Method 7: AWS CodeCommit](INSTALL.md#method-7---aws-codecommit-setup)
- [Method 8: Run a GitLab webhook server](INSTALL.md#method-8---run-a-gitlab-webhook-server)
- [Method 9: Run as a Bitbucket Pipeline](INSTALL.md#method-9-run-as-a-bitbucket-pipeline)

## How it works

The following diagram illustrates PR-Agent tools and their flow:

![PR-Agent Tools](https://codium.ai/images/pr_agent/diagram-v0.9.png)

Check out the [PR Compression strategy](./PR_COMPRESSION.md) page for more details on how we convert a code diff to a manageable LLM prompt

## Why use PR-Agent?

A reasonable question that can be asked is: `"Why use PR-Agent? What make it stand out from existing tools?"`

Here are some advantages of PR-Agent:

- We emphasize **real-life practical usage**. Each tool (review, improve, ask, ...) has a single GPT-4 call, no more. We feel that this is critical for realistic team usage - obtaining an answer quickly (~30 seconds) and affordably.
- Our [PR Compression strategy](./PR_COMPRESSION.md)  is a core ability that enables to effectively tackle both short and long PRs.
- Our JSON prompting strategy enables to have **modular, customizable tools**. For example, the '/review' tool categories can be controlled via the [configuration](pr_agent/settings/configuration.toml) file. Adding additional categories is easy and accessible.
- We support **multiple git providers** (GitHub, Gitlab, Bitbucket, CodeCommit), **multiple ways** to use the tool (CLI, GitHub Action, GitHub App, Docker, ...), and **multiple models** (GPT-4, GPT-3.5, Anthropic, Cohere, Llama2).
- We are open-source, and welcome contributions from the community.


## Roadmap

- [x] Support additional models, as a replacement for OpenAI (see [here](https://github.com/Codium-ai/pr-agent/pull/172))
- [x] Develop additional logic for handling large PRs (see [here](https://github.com/Codium-ai/pr-agent/pull/229))
- [ ] Add additional context to the prompt. For example, repo (or relevant files) summarization, with tools such a [ctags](https://github.com/universal-ctags/ctags)
- [x] PR-Agent for issues
- [ ] Adding more tools. Possible directions:
  - [x] PR description
  - [x] Inline code suggestions
  - [x] Reflect and review
  - [x] Rank the PR (see [here](https://github.com/Codium-ai/pr-agent/pull/89))   
  - [ ] Enforcing CONTRIBUTING.md guidelines
  - [ ] Performance (are there any performance issues)
  - [x] Documentation (is the PR properly documented)
  - [ ] ...

See the [Release notes](./RELEASE_NOTES.md) for updates on the latest changes.


## Similar Projects

- [CodiumAI - Meaningful tests for busy devs](https://github.com/Codium-ai/codiumai-vscode-release) (although various capabilities are much more advanced in the CodiumAI IDE plugins)
- [Aider - GPT powered coding in your terminal](https://github.com/paul-gauthier/aider)
- [openai-pr-reviewer](https://github.com/coderabbitai/openai-pr-reviewer)
- [CodeReview BOT](https://github.com/anc95/ChatGPT-CodeReview)
- [AI-Maintainer](https://github.com/merwanehamadi/AI-Maintainer)

## Data Privacy

If you use a self-hosted PR-Agent with your OpenAI API key, it is between you and OpenAI. You can read their API data privacy policy here:
https://openai.com/enterprise-privacy

When using a PR-Agent app hosted by CodiumAI, we will not store any of your data, nor will we used it for training.
You will also benefit from an OpenAI account with zero data retention.

## Links

[![Join our Discord community](https://raw.githubusercontent.com/Codium-ai/codiumai-vscode-release/main/media/docs/Joincommunity.png)](https://discord.gg/kG35uSHDBc)

- Discord community: https://discord.gg/kG35uSHDBc
- CodiumAI site: https://codium.ai
- Blog: https://www.codium.ai/blog/
- Troubleshooting: https://www.codium.ai/blog/technical-faq-and-troubleshooting/
- Support: support@codium.ai
