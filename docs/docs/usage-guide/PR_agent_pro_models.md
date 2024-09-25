## PR-Agent Pro Models

The default models used by PR-Agent Pro are a combination of Claude-3.5-sonnet and  OpenAI's GPT-4 models.

Users can configure PR-Agent to use solely a specific model by editing the [configuration](https://pr-agent-docs.codium.ai/usage-guide/configuration_options/) file.

For example, to restrict PR-Agent to using only `Claude-3.5-sonnet`, add this setting:

```
[config]
model="claude-3-5-sonnet"
```

Or to restrict PR-Agent to using only `GPT-4o`, add this setting:
```
[config]
model="gpt-4o"
```
