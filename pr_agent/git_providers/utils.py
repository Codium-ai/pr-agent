import copy
import os
import tempfile

from dynaconf import Dynaconf

from pr_agent.config_loader import get_settings
from pr_agent.git_providers import get_git_provider
from pr_agent.log import get_logger
from starlette_context import context


def apply_repo_settings(pr_url):
    if get_settings().config.use_repo_settings_file:
        repo_settings_file = None
        try:
            try:
                repo_settings = context.get("repo_settings", None)
            except Exception:
                repo_settings = None
                pass
            if repo_settings is None:  # None is different from "", which is a valid value
                git_provider = get_git_provider()(pr_url)
                repo_settings = git_provider.get_repo_settings()
                try:
                    context["repo_settings"] = repo_settings
                except Exception:
                    pass

            if repo_settings:
                repo_settings_file = None
                fd, repo_settings_file = tempfile.mkstemp(suffix='.toml')
                os.write(fd, repo_settings)
                new_settings = Dynaconf(settings_files=[repo_settings_file])
                for section, contents in new_settings.as_dict().items():
                    section_dict = copy.deepcopy(get_settings().as_dict().get(section, {}))
                    for key, value in contents.items():
                        section_dict[key] = value
                    get_settings().unset(section)
                    get_settings().set(section, section_dict, merge=False)
                get_logger().info(f"Applying repo settings:\n{new_settings.as_dict()}")
        except Exception as e:
            get_logger().exception("Failed to apply repo settings", e)
        finally:
            if repo_settings_file:
                try:
                    os.remove(repo_settings_file)
                except Exception as e:
                    get_logger().error(f"Failed to remove temporary settings file {repo_settings_file}", e)
