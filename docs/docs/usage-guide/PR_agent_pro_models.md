## PR-Agent Pro Models

The default models used by PR-Agent Pro are OpenAI's GPT-4 models. We use a combination of GPT-4-Turbo and GPT-4o to strike a balance between speed and quality.

However, users can change the model used by PR-Agent Pro to Claude-3.5-sonnet, which also excels at code tasks. 
To do so, add the following to your [configuration](https://pr-agent-docs.codium.ai/usage-guide/configuration_options/) file:

```
[config]
model="claude-3-5-sonnet"
```

Note that Claude models tend to give lower scores for each suggestion, so if you are using a [threshold](https://pr-agent-docs.codium.ai/tools/improve/#configuration-options):
```
[pr_code_suggestions]
suggestions_score_threshold=...
```
You might need to adjust this value when switching models.

### Dedicated models per tool

You can also use different models for different tools. For example, you can use the Claude-3.5-sonnet model only for the `improve` tool (and keep the default GPT-4 model for the other tools) by adding the following to your configuration file:
```
[github_app]
pr_commands = [
    "/describe --pr_description.final_update_message=false",
    "/review --pr_reviewer.num_code_suggestions=0",
    "/improve --config.model=claude-3-5-sonnet",
]
```
