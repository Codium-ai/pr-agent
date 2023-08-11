<div align="center">

<div align="center">

<img src="./pics/logo-dark.png#gh-dark-mode-only" width="330"/>
<img src="./pics/logo-light.png#gh-light-mode-only" width="330"/><br/>
Making pull requests less painful with an AI agent
</div>

[![GitHub license](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://github.com/Codium-ai/pr-agent/blob/main/LICENSE)
[![Discord](https://badgen.net/badge/icon/discord?icon=discord&label&color=purple)](https://discord.com/channels/1057273017547378788/1126104260430528613)
    <a href="https://github.com/Codium-ai/pr-agent/commits/main">
    <img alt="GitHub" src="https://img.shields.io/github/last-commit/Codium-ai/pr-agent/main?style=for-the-badge" height="20">
    </a>
</div>
<div style="text-align:left;">

CodiumAI `PR-Agent` is an open-source tool aiming to help developers review pull requests faster and more efficiently. It automatically analyzes the pull request and can provide several types of feedback:

**Auto-Description**: Automatically generating PR description - title, type, summary, code walkthrough and PR labels.
\
**PR Review**: Adjustable feedback about the PR main theme, type, relevant tests, security issues, focus, score, and various suggestions for the PR content.
\
**Question Answering**: Answering free-text questions about the PR.
\
**Code Suggestions**: Committable code suggestions for improving the PR.
\
**Update Changelog**: Automatically updating the CHANGELOG.md file with the PR changes.

<h3>Example results:</h2>
</div>
<h4>/describe:</h4>
<div align="center">
<p float="center">
<img src="https://www.codium.ai/images/describe-2.gif" width="800">
</p>
</div>
<h4>/review:</h4>
<div align="center">
<p float="center">
<img src="https://www.codium.ai/images/review-2.gif" width="800">
</p>
</div>
<h4>/reflect_and_review:</h4>
<div align="center">
<p float="center">
<img src="https://www.codium.ai/images/reflect_and_review.gif" width="800">
</p>
</div>
<h4>/ask:</h4>
<div align="center">
<p float="center">
<img src="https://www.codium.ai/images/ask-2.gif" width="800">
</p>
</div>
<h4>/improve:</h4>
<div align="center">
<p float="center">
<img src="https://www.codium.ai/images/improve-2.gif" width="800">
</p>
</div>
<div align="left">


- [Overview](#overview)
- [Try it now](#try-it-now)
- [Installation](#installation)
- [Configuration](./CONFIGURATION.md)
- [How it works](#how-it-works)
- [Why use PR-Agent](#why-use-pr-agent)
- [Roadmap](#roadmap)
- [Similar projects](#similar-projects)
</div>


## Overview
`PR-Agent` offers extensive pull request functionalities across various git providers:
|       |                                             | GitHub | Gitlab | Bitbucket |
|-------|---------------------------------------------|:------:|:------:|:---------:|
| TOOLS | Review                                      |   :white_check_mark:    |   :white_check_mark:    |   :white_check_mark:       |
|       | ⮑ Inline review                             |   :white_check_mark:    |   :white_check_mark:    |           |
|       | Ask                                         |   :white_check_mark:    |   :white_check_mark:    |           |
|       | Auto-Description                            |   :white_check_mark:    |  :white_check_mark:      |           |
|       | Improve Code                                |   :white_check_mark:    |   :white_check_mark:    |           |
|       | Reflect and Review                          |   :white_check_mark:    |                         |           |
|       | Update CHANGELOG.md                         |   :white_check_mark:    |                         |           |
|       |                                             |        |        |           |
| USAGE | CLI                                         |   :white_check_mark:    |   :white_check_mark:    |   :white_check_mark:       |
|       | App / webhook                               |   :white_check_mark:    |   :white_check_mark:    |           |
|       | Tagging bot                                 |   :white_check_mark:    |        |           |
|       | Actions                                     |   :white_check_mark:    |        |           |
|       |                                             |        |        |           |
| CORE  | PR compression                              |   :white_check_mark:    |   :white_check_mark:    |   :white_check_mark:       |
|       | Repo language prioritization                |   :white_check_mark:    |   :white_check_mark:    |   :white_check_mark:       |
|       | Adaptive and token-aware<br />file patch fitting |   :white_check_mark:    |   :white_check_mark:    |   :white_check_mark:       |
|       | Multiple models support |   :white_check_mark:    |   :white_check_mark:    |   :white_check_mark:       |
|       | Incremental PR Review |   :white_check_mark:    |      |         |

Examples for invoking the different tools via the CLI:
- **Review**:       python cli.py --pr_url=<pr_url>  review
- **Describe**:     python cli.py --pr_url=<pr_url>  describe
- **Improve**:      python cli.py --pr_url=<pr_url>  improve
- **Ask**:          python cli.py --pr_url=<pr_url>  ask "Write me a poem about this PR"
- **Reflect**:      python cli.py --pr_url=<pr_url>  reflect
- **Update Changelog**:      python cli.py --pr_url=<pr_url>  update_changelog

"<pr_url>" is the url of the relevant PR (for example: https://github.com/Codium-ai/pr-agent/pull/50).

In the [configuration](./CONFIGURATION.md) file you can select your git provider (GitHub, Gitlab, Bitbucket), and further configure the different tools.

## Try it now

Try GPT-4 powered PR-Agent on your public GitHub repository for free. Just mention `@CodiumAI-Agent` and add the desired command in any PR comment! The agent will generate a response based on your command.

![Review generation process](https://www.codium.ai/images/demo-2.gif)

To set up your own PR-Agent, see the [Installation](#installation) section

---

## Installation

To get started with PR-Agent quickly, you first need to acquire two tokens:

1. An OpenAI key from [here](https://platform.openai.com/), with access to GPT-4.
2. A GitHub personal access token (classic) with the repo scope.

There are several ways to use PR-Agent:

- [Method 1: Use Docker image (no installation required)](INSTALL.md#method-1-use-docker-image-no-installation-required)
- [Method 2: Run as a GitHub Action](INSTALL.md#method-2-run-as-a-github-action)
- [Method 3: Run from source](INSTALL.md#method-3-run-from-source)
- [Method 4: Run as a polling server](INSTALL.md#method-4-run-as-a-polling-server)
  - Request reviews by tagging your GitHub user on a PR
- [Method 5: Run as a GitHub App](INSTALL.md#method-5-run-as-a-github-app)
  - Allowing you to automate the review process on your private or public repositories


## How it works

The following diagram illustrates PR-Agent tools and their flow:

![PR-Agent Tools](https://www.codium.ai/wp-content/uploads/2023/07/codiumai-diagram-v4.jpg)

Check out the [PR Compression strategy](./PR_COMPRESSION.md) page for more details on how we convert a code diff to a manageable LLM prompt

## Why use PR-Agent?

A reasonable question that can be asked is: `"Why use PR-Agent? What make it stand out from existing tools?"`

Here are some advantages of PR-Agent:

- We emphasize **real-life practical usage**. Each tool (review, improve, ask, ...) has a single GPT-4 call, no more. We feel that this is critical for realistic team usage - obtaining an answer quickly (~30 seconds) and affordably.
- Our [PR Compression strategy](./PR_COMPRESSION.md)  is a core ability that enables to effectively tackle both short and long PRs.
- Our JSON prompting strategy enables to have **modular, customizable tools**. For example, the '/review' tool categories can be controlled via the [configuration](./CONFIGURATION.md) file. Adding additional categories is easy and accessible.
- We support **multiple git providers** (GitHub, Gitlab, Bitbucket), **multiple ways** to use the tool (CLI, GitHub Action, GitHub App, Docker, ...), and **multiple models** (GPT-4, GPT-3.5, Anthropic, Cohere, Llama2).
- We are open-source, and welcome contributions from the community.


## Roadmap

- [x] Support additional models, as a replacement for OpenAI (see [here](https://github.com/Codium-ai/pr-agent/pull/172))
- [ ] Develop additional logic for handling large PRs
- [ ] Add additional context to the prompt. For example, repo (or relevant files) summarization, with tools such a [ctags](https://github.com/universal-ctags/ctags)
- [ ] Adding more tools. Possible directions:
  - [x] PR description
  - [x] Inline code suggestions
  - [x] Reflect and review
  - [x] Rank the PR (see [here](https://github.com/Codium-ai/pr-agent/pull/89))   
  - [ ] Enforcing CONTRIBUTING.md guidelines
  - [ ] Performance (are there any performance issues)
  - [ ] Documentation (is the PR properly documented)
  - [ ] ...

## Similar Projects

- [CodiumAI - Meaningful tests for busy devs](https://github.com/Codium-ai/codiumai-vscode-release)
- [Aider - GPT powered coding in your terminal](https://github.com/paul-gauthier/aider)
- [openai-pr-reviewer](https://github.com/coderabbitai/openai-pr-reviewer)
- [CodeReview BOT](https://github.com/anc95/ChatGPT-CodeReview)
- [AI-Maintainer](https://github.com/merwanehamadi/AI-Maintainer)
