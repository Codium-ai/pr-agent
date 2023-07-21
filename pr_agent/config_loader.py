from os.path import abspath, dirname, join

from dynaconf import Dynaconf

current_dir = dirname(abspath(__file__))
settings = Dynaconf(
    envvar_prefix=False,
    merge_enabled=True,
    settings_files=[join(current_dir, f) for f in [
        "settings/.secrets.toml",
        "settings/configuration.toml",
        "settings/configuration_local.toml",
        "settings/pr_reviewer_prompts.toml",
        "settings/pr_questions_prompts.toml",
        "settings/pr_description_prompts.toml",
        "settings/pr_code_suggestions_prompts.toml",
        "settings/pr_information_from_user_prompts.toml",
        "settings_prod/.secrets.toml",
        "settings_prod/bad_extensions.toml",
    ]]
)
