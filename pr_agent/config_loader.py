from os.path import abspath, dirname, join
from pathlib import Path
from typing import Optional

from dynaconf import Dynaconf

PR_AGENT_TOML_KEY = 'pr-agent'

current_dir = dirname(abspath(__file__))
settings = Dynaconf(
    envvar_prefix=False,
    merge_enabled=True,
    settings_files=[join(current_dir, f) for f in [
         "settings/.secrets.toml",
         "settings/configuration.toml",
         "settings/language_extensions.toml",
         "settings/pr_reviewer_prompts.toml",
         "settings/pr_questions_prompts.toml",
         "settings/pr_description_prompts.toml",
         "settings/pr_code_suggestions_prompts.toml",
         "settings/pr_information_from_user_prompts.toml",
         "settings_prod/.secrets.toml"
        ]]
)


# Add local configuration from pyproject.toml of the project being reviewed
def _find_repository_root() -> Path:
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
    raise FileNotFoundError("Could not find the repository root directory")


def _find_pyproject() -> Optional[Path]:
    """
    Search for file pyproject.toml in the repository root.
    """
    pyproject = _find_repository_root() / "pyproject.toml"
    return pyproject if pyproject.is_file() else None


pyproject_path = _find_pyproject()
if pyproject_path is not None:
    settings.load_file(pyproject_path, env=f'tool.{PR_AGENT_TOML_KEY}')
