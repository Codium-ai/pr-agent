## Configuration

The different tools and sub-tools used by CodiumAI PR-Agent are adjustable via the configuration file: `/pr-agent/settings/configuration.toml`.

### CLI
When running from source (CLI), your local configuration file will be used.

Example for invoking the 'review' tools via the CLI: 

```
python cli.py --pr-url=<pr_url>  review
```
In addition to general configurations, The 'review' tool will use parameters from the `[pr_reviewer]` section. Every tool has a dedicated section in the configuration file

Note that you can print results locally, without publishing them, by setting in `configuration.toml`:

```
[config]
publish_output=true
verbosity_level=2
```
This is useful for debugging or experimenting with the different tools.

### Working from pre-built repo (GitHub Action/GitHub App/Docker/...)
When running PR-Agent from a pre-built repo, the default configuration file will be loaded.

To edit the configuration of any tool, just add `--config_path=<value>` to you command.
For example if you want to edit online `pr_reviewer` configurations, you can run:
```
/review --pr_reviewer.extra_instructions="focus on the file xyz" --pr_reviewer.require_score_review=false ...
```

Any configuration value in `configuration.toml` file can be similarly edited.

