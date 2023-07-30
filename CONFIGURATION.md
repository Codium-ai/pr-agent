## Configuration

The different tools and sub-tools used by CodiumAI pr-agent are adjustable via the configuration file: `/pr-agent/settings/configuration.toml`.

To edit the configuration of any tool, just add `--config_path=<value>` to you command.
For example if you want to edit online the `pr_reviewer` configurations, you can run:
```
/review --pr_reviewer.extra_instructions="focus on the file xyz" --require_score_review=false ...
```

Any configuration value in `configuration.toml` file can be similarly edited.

