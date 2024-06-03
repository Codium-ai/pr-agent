# PR-Agent Code Fine-tuning Benchmark

On coding tasks, the gap between open-source models and top closed-source models such as GPT4 is significant.
<br>
In practice, open-source models are unsuitable for most real-world code tasks, and require further fine-tuning to produce acceptable results.

_PR-Agent fine-tuning benchmark_ aims to benchmark open-source models on their ability to be fine-tuned for a coding task.
Specifically, we chose to fine-tune open-source models on the task of analyzing a pull request, and providing useful feedback and code suggestions.

Here are the results:
<br>
<br>

**Model performance:**

| Model name                  | Model size [B] | Better than gpt-4 rate, after fine-tuning [%] |
|-----------------------------|----------------|----------------------------------------------|
| **DeepSeek 34B-instruct**   | **34**         | **40.7**                                     |
| DeepSeek 34B-base           | 34             | 38.2                                         |
| Phind-34b                   | 34             | 38                                           |
| Granite-34B                 | 34             | 37.6                                         |
| Codestral-22B-v0.1          | 22             | 32.7                                         |
| QWEN-1.5-32B                | 32             | 29                                           |
|                             |                |                                              |
| **CodeQwen1.5-7B**          | **7**          | **35.4**                                     |
| Granite-8b-code-instruct    | 8              | 34.2                                         |
| CodeLlama-7b-hf             | 7              | 31.8                                         |
| Gemma-7B                    | 7              | 27.2                                         |
| DeepSeek coder-7b-instruct  | 7              | 26.8                                         |
| Llama-3-8B-Instruct         | 8              | 26.8                                         |
| Mistral-7B-v0.1             | 7              | 16.1                                         |

<br>

**Fine-tuning impact:**

| Model name                | Model size [B] | Fine-tuned | Better than gpt-4 rate [%] |
|---------------------------|----------------|------------|----------------------------|
| DeepSeek 34B-instruct     | 34             | yes        | 40.7                       |
| DeepSeek 34B-instruct     | 34             | no         | 3.6                        |

## Results analysis

- **Fine-tuning is a must** - without fine-tuning, open-source models provide poor results on most real-world code tasks, which include complicated prompt and lengthy context. We clearly see that without fine-tuning, deepseek model was 96.4% of the time inferior to GPT-4, while after fine-tuning, it is better 40.7% of the time.
- **Always start from a code-dedicated model** — When fine-tuning, always start from a code-dedicated model, and not from a general-usage model. The gaps in downstream results are very big.
- **Don't believe the hype** —newer models, or models from big-tech companies (Llama3, Gemma, Mistral), are not always better for fine-tuning.
- **The best large model** - For large 34B code-dedicated models, the gaps when doing proper fine-tuning are small. The current top model is **DeepSeek 34B-instruct**
- **The best small model** - For small 7B code-dedicated models, the gaps when fine-tuning are much larger. **CodeQWEN 1.5-7B** is by far the best model for fine-tuning.
- **Base vs. instruct** - For the top model (deepseek), we saw small advantage when starting from the instruct version. However, we recommend testing both versions on each specific task, as the base model is generally considered more suitable for fine-tuning.

## The dataset

### Training dataset

Our training dataset comprises 25,000 pull requests, aggregated from permissive license repos. For each pull request, we generated responses for the three main tools of PR-Agent:
[Describe](https://pr-agent-docs.codium.ai/tools/describe/), [Review](https://pr-agent-docs.codium.ai/tools/improve/) and [Improve](https://pr-agent-docs.codium.ai/tools/improve/).

On the raw data collected, we employed various automatic and manual cleaning techniques to ensure the outputs were of the highest quality, and suitable for instruct-tuning.

Here are the prompts, and example outputs, used as input-output pairs to fine-tune the models:

| Tool     | Prompt                                                                                                     | Example output |
|----------|------------------------------------------------------------------------------------------------------------|----------------|
| Describe | [link](https://github.com/Codium-ai/pr-agent/blob/main/pr_agent/settings/pr_description_prompts.toml) | [link](https://github.com/Codium-ai/pr-agent/pull/910#issue-2303989601)           |
| Review   | [link](https://github.com/Codium-ai/pr-agent/blob/main/pr_agent/settings/pr_reviewer_prompts.toml) | [link](https://github.com/Codium-ai/pr-agent/pull/910#issuecomment-2118761219)           |
| Improve  | [link](https://github.com/Codium-ai/pr-agent/blob/main/pr_agent/settings/pr_code_suggestions_prompts.toml) | [link](https://github.com/Codium-ai/pr-agent/pull/910#issuecomment-2118761309)           |

### Evaluation dataset

- For each tool, we aggregated 100 additional examples to be used for evaluation. These examples were not used in the training dataset, and were manually selected to represent diverse real-world use-cases.
- For each test example, we generated two responses: one from the fine-tuned model, and one from the best code model in the world, `gpt-4-turbo-2024-04-09`.

- We used a third LLM to judge which response better answers the prompt, and will likely be perceived by a human as better response.
<br>

We experimented with three model as judges: `gpt-4-turbo-2024-04-09`, `gpt-4o`, and `claude-3-opus-20240229`. All three produced similar results, with the same ranking order. This strengthens the validity of our testing protocol.
The evaluation prompt can be found [here](https://github.com/Codium-ai/pr-agent/blob/main/pr_agent/settings/pr_evaluate_prompt_response.toml)

Here is an example of a judge model feedback:

```
command: improve
model1_score: 9,
model2_score: 6,
why: |
  Response 1 is better because it provides more actionable and specific suggestions that directly 
  enhance the code's maintainability, performance, and best practices. For example, it suggests 
  using a variable for reusable widget instances and using named routes for navigation, which 
  are practical improvements. In contrast, Response 2 focuses more on general advice and less 
  actionable suggestions, such as changing variable names and adding comments, which are less 
  critical for immediate code improvement."
```
