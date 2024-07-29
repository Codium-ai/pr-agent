from os.path import abspath, dirname, join
from pathlib import Path
from typing import Optional

from dynaconf import Dynaconf
from starlette_context import context

PR_AGENT_TOML_KEY = 'pr-agent'

current_dir = dirname(abspath(__file__))
global_settings = Dynaconf(
    envvar_prefix=False,
    merge_enabled=True,
    settings_files=[join(current_dir, f) for f in [
        "settings/.secrets.toml",
        "settings/configuration.toml",
        "settings/ignore.toml",
        "settings/language_extensions.toml",
        "settings/pr_reviewer_prompts.toml",
        "settings/pr_questions_prompts.toml",
        "settings/pr_line_questions_prompts.toml",
        "settings/pr_description_prompts.toml",
        "settings/pr_code_suggestions_prompts.toml",
        "settings/pr_code_suggestions_reflect_prompts.toml",
        "settings/pr_sort_code_suggestions_prompts.toml",
        "settings/pr_information_from_user_prompts.toml",
        "settings/pr_update_changelog_prompts.toml",
        "settings/pr_custom_labels.toml",
        "settings/pr_add_docs.toml",
        "settings_prod/.secrets.toml",
        "settings/custom_labels.toml"
    ]]
)


def get_settings():
    """
    Retrieves the current settings.

    This function attempts to fetch the settings from the starlette_context's context object. If it fails,
    it defaults to the global settings defined outside of this function.

    Returns:
        Dynaconf: The current settings object, either from the context or the global default.
    """
    try:
        return context["settings"]
    except Exception:
        return global_settings


# Add local configuration from pyproject.toml of the project being reviewed
def _find_repository_root() -> Optional[Path]:
    """
    Identify project root directory by recursively searching for the .git directory in the parent directories.
    """
    cwd = Path.cwd().resolve()
    no_way_up = False
    while not no_way_up:
        no_way_up = cwd == cwd.parent
        if (cwd / ".git").is_dir():
            return cwd
        cwd = cwd.parent
    return None


def _find_pyproject() -> Optional[Path]:
    """
    Search for file pyproject.toml in the repository root.
    """
    repo_root = _find_repository_root()
    if repo_root:
        pyproject = repo_root / "pyproject.toml"
        return pyproject if pyproject.is_file() else None
    return None


pyproject_path = _find_pyproject()
if pyproject_path is not None:
    get_settings().load_file(pyproject_path, env=f'tool.{PR_AGENT_TOML_KEY}')
