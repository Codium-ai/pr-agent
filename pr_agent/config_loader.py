from os.path import abspath, dirname, join
from pathlib import Path
from typing import Union

from dynaconf import Dynaconf

PYPROJECT_NAME = Path("pyproject.toml")
PR_AGENT_TOML_KEY = 'pr-agent'

current_dir = dirname(abspath(__file__))
settings = Dynaconf(
    envvar_prefix=False,
    merge_enabled=True,
    settings_files=[join(current_dir, f) for f in [
         "settings/.secrets.toml",
         "settings/configuration.toml",
         "settings/configuration_local.toml",
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
def _find_pyproject() -> Union[Path, None]:
    """
    Search for file pyproject.toml in the parent directories recursively.
    """
    current_dir = Path.cwd().resolve()
    is_root = False
    while not is_root:
        if (current_dir / PYPROJECT_NAME).is_file():
            return current_dir / PYPROJECT_NAME
        is_root = (
                current_dir == current_dir.parent
                or (current_dir / ".git").is_dir()
        )
        current_dir = current_dir.parent
    return None


pyproject_path = _find_pyproject()
if pyproject_path is not None:
    settings.load_file(pyproject_path, env=f'tool.{PR_AGENT_TOML_KEY}')
