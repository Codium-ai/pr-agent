
The default models used by Qodo Merge are a combination of Claude-3.5-sonnet and  OpenAI's GPT-4 models.

### Selecting a Specific Model

Users can configure Qodo Merge to use a specific model by editing the [configuration](https://qodo-merge-docs.qodo.ai/usage-guide/configuration_options/) file.
The models supported by Qodo Merge are:

- `claude-3-5-sonnet`
- `gpt-4o`
- `o3-mini`

To restrict Qodo Merge to using only `Claude-3.5-sonnet`, add this setting:

```
[config]
model="claude-3-5-sonnet"
```

To restrict Qodo Merge to using only `GPT-4o`, add this setting:
```
[config]
model="gpt-4o"
```

[//]: # (To restrict Qodo Merge to using only `deepseek-r1` us-hosted, add this setting:)
[//]: # (```)
[//]: # ([config])
[//]: # (model="deepseek/r1")
[//]: # (```)

To restrict Qodo Merge to using only `o3-mini`, add this setting:
```
[config]
model="o3-mini"
```
