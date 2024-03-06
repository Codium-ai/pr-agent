# Overview

CodiumAI PR-Agent is an open-source tool to help efficiently review and handle pull requests.

- See the [Installation Guide](./installation/index.md) for instructions on installing and running the tool on different git platforms.

- See the [Usage Guide](./usage-guide/index.md) for instructions on running the PR-Agent commands via different interfaces, including _CLI_, _online usage_, or by _automatically triggering_ them when a new PR is opened.

- See the [Tools Guide](./tools/index.md) for a detailed description of the different tools (tools are run via the commands).


## Features table
PR-Agent offers extensive pull request functionalities across various git providers.

|       |                                                                                                                     | GitHub | Gitlab | Bitbucket | Azure DevOps |
|-------|---------------------------------------------------------------------------------------------------------------------|:------:|:------:|:---------:|:------------:|
| TOOLS | Review                                                                                                              |   ✔️    |   ✔️    |   ✔️       |      ✔️      |
|       | ⮑ Incremental                                                                                                       |   ✔️    |        |            |              |
|       | ⮑ [SOC2 Compliance](/tools/REVIEW/#soc2-ticket-compliance){:target="_blank"} 💎                                     |   ✔️    |   ✔️    |   ✔️        |      ✔️      |
|       | Ask                                                                                                                 |   ✔️    |   ✔️    |   ✔️        |      ✔️      |
|       | Describe                                                                                                            |   ✔️    |   ✔️    |   ✔️        |      ✔️      |
|       | ⮑ [Inline file summary](/tools//DESCRIBE/#inline-file-summary){:target="_blank"} 💎                                 |   ✔️    |   ✔️    |   ✔️        |      ✔️      |
|       | Improve                                                                                                             |   ✔️    |   ✔️    |   ✔️        |      ✔️      |
|       | ⮑ Extended                                                                                                          |   ✔️    |   ✔️    |   ✔️        |      ✔️      |
|       | [Custom Suggestions](/tools/CUSTOM_SUGGESTIONS/){:target="_blank"} 💎                                               |   ✔️    |   ✔️    |   ✔️        |      ✔️      |
|       | Reflect and Review                                                                                                  |   ✔️    |   ✔️    |   ✔️        |      ✔️      |
|       | Update CHANGELOG.md                                                                                                 |   ✔️    |   ✔️    |   ✔️        |      ️       |
|       | Find Similar Issue                                                                                                  |   ✔️    |        |             |      ️       |
|       | [Add PR Documentation](/tools/DOCUMENTATION/){:target="_blank"} 💎                                                  |   ✔️    |   ✔️    |   ✔️        |      ✔️      |
|       | [Generate Custom Labels](/tools/DESCRIBE/#handle-custom-labels-from-the-repos-labels-page-gem){:target="_blank"} 💎 |   ✔️    |   ✔️    |            |      ✔️      |
|       | [Analyze PR Components](/tools/Analyze/){:target="_blank"} 💎                                                       |   ✔️    |   ✔️    |   ✔️      |      ✔️      |
|       |                                                                                                                     |        |        |            |      ️       |
| USAGE | CLI                                                                                                                 |   ✔️    |   ✔️    |   ✔️       |      ✔️      |
|       | App / webhook                                                                                                       |   ✔️    |   ✔️    |            |      ✔️      |
|       | Tagging bot                                                                                                         |   ✔️    |        |            |      ✔️      |
|       | Actions                                                                                                             |   ✔️    |        |            |      ️       |
|       |                                                                                                                     |        |        |            |
| CORE  | PR compression                                                                                                      |   ✔️    |   ✔️    |   ✔️       |   ✔️        |
|       | Repo language prioritization                                                                                        |   ✔️    |   ✔️    |   ✔️       |   ✔️        |
|       | Adaptive and token-aware file patch fitting                                                                         |   ✔️    |   ✔️    |   ✔️     |   ✔️        |
|       | Multiple models support                                                                                             |   ✔️    |   ✔️    |   ✔️       |   ✔️        |
|       | Incremental PR review                                                                                               |   ✔️    |        |            |           |
|       | [Static code analysis](/tools/analyze/){:target="_blank"} 💎                                                        |   ✔️    |   ✔️     |    ✔️    |   ✔️        |
|       | [Multiple configuration options](usage-guide/configuration_options/){:target="_blank"} 💎                           |   ✔️    |   ✔️     |    ✔️    |   ✔️        |

💎 marks a feature available only in [PR-Agent Pro](https://www.codium.ai/pricing/){:target="_blank"}


## Example results
<hr>
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


## How it works

The following diagram illustrates PR-Agent tools and their flow:

![PR-Agent Tools](https://codium.ai/images/pr_agent/diagram-v0.9.png)

Check out the [PR Compression strategy](./PR_COMPRESSION.md) page for more details on how we convert a code diff to a manageable LLM prompt



## PR-Agent Pro 💎

[PR-Agent Pro](https://www.codium.ai/pricing/) is a hosted version of PR-Agent, provided by CodiumAI. It is available for a monthly fee, and provides the following benefits:

1. **Fully managed** - We take care of everything for you - hosting, models, regular updates, and more. Installation is as simple as signing up and adding the PR-Agent app to your GitHub\BitBucket repo.
2. **Improved privacy** - No data will be stored or used to train models. PR-Agent Pro will employ zero data retention, and will use an OpenAI account with zero data retention.
3. **Improved support** - PR-Agent Pro users will receive priority support, and will be able to request new features and capabilities.
4. **Extra features** -In addition to the benefits listed above, PR-Agent Pro will emphasize more customization, and the usage of static code analysis, in addition to LLM logic, to improve results. It has the following additional tools and features:
    - [**Analyze PR components**](/tools/analyze/)
    - [**Custom Code Suggestions**](/tools/custom_suggestions/)
    - [**Tests**](/tools/test/)
    - [**PR documentation**](/tools/documentation/)
    - [**CI feedback**](./tools/ci_feedback/)
    - [**SOC2 compliance check**](/tools/review/#soc2-ticket-compliance)
    - [**Custom labels**](/tools/describe/#handle-custom-labels-from-the-repos-labels-page)
    - [**Global and wiki configuration**](/usage-guide/configuration_options/#wiki-configuration-file)



## Why use PR-Agent?

A reasonable question that can be asked is: `"Why use PR-Agent? What makes it stand out from existing tools?"`

Here are some advantages of PR-Agent:

- PR-Agent emphasize **real-life practical usage**. Each tool (review, improve, ask, ...) has a single GPT-4 call, no more. We believe this is critical for realistic team usage - obtaining an answer quickly (~30 seconds) and affordably.
- PR-Agent [Compression strategy](./PR_COMPRESSION.md)  is a core ability that enables to effectively tackle both short and long PRs.
- YAML prompting strategy enables to have **modular, customizable, highly efficient tools**. 
- PR-Agent is flexible and **highly configurable**.
- PR-Agent supports **multiple git providers** (GitHub, Gitlab, Bitbucket, Azure devops), **multiple ways** to use the tool (CLI, GitHub Action, GitHub App, Docker, ...), and **multiple models** (GPT-4, GPT-3.5, Anthropic, Cohere, Llama, ...).


## Data privacy

If you host PR-Agent with your OpenAI API key, it is between you and OpenAI. You can read their API data privacy policy here:
https://openai.com/enterprise-privacy

When using PR-Agent Pro 💎, hosted by CodiumAI, we will not store any of your data, nor will we use it for training.
You will also benefit from an OpenAI account with zero data retention.

## Links

- [Discord community](https://discord.gg/kG35uSHDBc)
- [CodiumAI site](https://codium.ai)
- [Blogs](https://www.codium.ai/blog/)
- [Troubleshooting](https://www.codium.ai/blog/technical-faq-and-troubleshooting/)
- [Support](support@codium.ai)
