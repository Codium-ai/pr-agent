## Configuration

The different tools and sub-tools used by CodiumAI PR-Agent are adjustable via the **[configuration file](pr_agent/settings/configuration.toml)**

### Working from CLI
When running from source (CLI), your local configuration file will be initially used.

Example for invoking the 'review' tools via the CLI: 

```
python cli.py --pr-url=<pr_url>  review
```
In addition to general configurations, the 'review' tool will use parameters from the `[pr_reviewer]` section (every tool has a dedicated section in the configuration file).

Note that you can print results locally, without publishing them, by setting in `configuration.toml`:

```
[config]
publish_output=true
verbosity_level=2
```
This is useful for debugging or experimenting with the different tools.

### Working from pre-built repo (GitHub Action/GitHub App/Docker)
When running PR-Agent from a pre-built repo, the default configuration file will be loaded.

To edit the configuration, you have two options: 
1. Place a local configuration file in the root of your local repo. The local file will be used instead of the default one.
2. For online usage, just add `--config_path=<value>` to you command, to edit a specific configuration value.
For example if you want to edit `pr_reviewer` configurations, you can run:
```
/review --pr_reviewer.extra_instructions="..." --pr_reviewer.require_score_review=false ...
```

Any configuration value in `configuration.toml` file can be similarly edited.

### General configuration parameters

#### Changing a model
See [here](pr_agent/algo/__init__.py) for the list of available models.

To use Llama2 model, for example, set:
```
[config]
model = "replicate/llama-2-70b-chat:2c1608e18606fad2812020dc541930f2d0495ce32eee50074220b87300bc16e1"
[replicate]
key = ...
```
(you can obtain a Llama2 key from [here](https://replicate.com/replicate/llama-2-70b-chat/api))

Also review the [AiHandler](pr_agent/algo/ai_handler.py) file for instruction how to set keys for other models.

#### Extra instructions
All PR-Agent tools have a parameter called `extra_instructions`, that enables to add free-text extra instructions. Example usage:
```
/update_changelog --pr_update_changelog.extra_instructions="Make sure to update also the version ..."
```