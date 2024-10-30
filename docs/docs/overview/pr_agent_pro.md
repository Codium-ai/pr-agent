### Overview

[Qodo Merge Pro](https://www.codium.ai/pricing/) is a hosted version of Qodo Merge, provided by Qodo. A complimentary two-week trial is offered, followed by a monthly subscription fee.
Qodo Merge Pro is designed for companies and teams that require additional features and capabilities. It provides the following benefits:

1. **Fully managed** - We take care of everything for you - hosting, models, regular updates, and more. Installation is as simple as signing up and adding the Qodo Merge app to your GitHub\GitLab\BitBucket repo.

2. **Improved privacy** - No data will be stored or used to train models. Qodo Merge Pro will employ zero data retention, and will use an OpenAI and Claude accounts with zero data retention.

3. **Improved support** - Qodo Merge Pro users will receive priority support, and will be able to request new features and capabilities.

4. **Supporting self-hosted git servers** - Qodo Merge Pro can be installed on GitHub Enterprise Server, GitLab, and BitBucket. For more information, see the [installation guide](https://qodo-merge-docs.qodo.ai/installation/pr_agent_pro/).

5. **PR Chat** - Qodo Merge Pro allows you to engage in [private chat](https://qodo-merge-docs.qodo.ai/chrome-extension/features/#pr-chat) about your pull requests on private repositories.

### Additional features

Here are some of the additional features and capabilities that Qodo Merge Pro offers:

| Feature                                                                                                              | Description                                                                                                                                                      |
|----------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [**Model selection**](https://qodo-merge-docs.qodo.ai/usage-guide/PR_agent_pro_models/)          | Choose the model that best fits your needs, among top models like `GPT4` and `Claude-Sonnet-3.5`
| [**Global and wiki configuration**](https://qodo-merge-docs.qodo.ai/usage-guide/configuration_options/)              | Control configurations for many repositories from a single location; <br>Edit configuration of a single repo without committing code                              |
| [**Apply suggestions**](https://qodo-merge-docs.qodo.ai/tools/improve/#overview)                                     | Generate committable code from the relevant suggestions interactively by clicking on a checkbox                                                                   |
| [**Suggestions impact**](https://qodo-merge-docs.qodo.ai/tools/improve/#assessing-impact)                         | Automatically mark suggestions that were implemented by the user (either directly in GitHub, or indirectly in the IDE) to enable tracking of the impact of the suggestions |
| [**CI feedback**](https://qodo-merge-docs.qodo.ai/tools/ci_feedback/) | Automatically analyze failed CI checks on GitHub and provide actionable feedback in the PR conversation, helping to resolve issues quickly |
| [**Advanced usage statistics**](https://www.codium.ai/contact/#/)                                                    | Qodo Merge Pro offers detailed statistics at user, repository, and company levels, including metrics about Qodo Merge usage, and also general statistics and insights |
| [**Incorporating companies' best practices**](https://qodo-merge-docs.qodo.ai/tools/improve/#best-practices)         | Use the companies' best practices as reference to increase the effectiveness and the relevance of the code suggestions                                           |
| [**Interactive triggering**](https://qodo-merge-docs.qodo.ai/tools/analyze/#example-usage)                           | Interactively apply different tools via the `analyze` command                                                                                                    |
| [**Custom labels**](https://qodo-merge-docs.qodo.ai/tools/describe/#handle-custom-labels-from-the-repos-labels-page) | Define custom labels for Qodo Merge to assign to the PR                                                                                                            |

### Additional tools

Here are additional tools that are available only for Qodo Merge Pro users:

| Feature | Description |
|---------|-------------|
| [**Custom Prompt Suggestions**](https://qodo-merge-docs.qodo.ai/tools/custom_prompt/) | Generate code suggestions based on custom prompts from the user |
| [**Analyze PR components**](https://qodo-merge-docs.qodo.ai/tools/analyze/) | Identify the components that changed in the PR, and enable to interactively apply different tools to them |
| [**Tests**](https://qodo-merge-docs.qodo.ai/tools/test/) | Generate tests for code components that changed in the PR |
| [**PR documentation**](https://qodo-merge-docs.qodo.ai/tools/documentation/) | Generate docstring for code components that changed in the PR |
| [**Improve Component**](https://qodo-merge-docs.qodo.ai/tools/improve_component/) | Generate code suggestions for code components that changed in the PR |
| [**Similar code search**](https://qodo-merge-docs.qodo.ai/tools/similar_code/) | Search for similar code in the repository, organization, or entire GitHub |


### Supported languages

Qodo Merge Pro leverages the world's leading code models - Claude 3.5 Sonnet and GPT-4.
As a result, its primary tools such as `describe`, `review`, and `improve`, as well as the PR-chat feature, support virtually all programming languages.

For specialized commands that require static code analysis, Qodo Merge Pro offers support for specific languages. For more details about features that require static code analysis, please refer to the [documentation](https://qodo-merge-docs.qodo.ai/tools/analyze/#overview).
