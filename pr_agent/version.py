import os
import sys
from importlib.metadata import version, PackageNotFoundError

from pr_agent.log import get_logger

def get_version() -> str:
    # First check pyproject.toml if running directly out of repository
    if os.path.exists("pyproject.toml") and sys.version_info >= (3, 11):
        import tomllib
        with open("pyproject.toml", "rb") as f:
            data = tomllib.load(f)
            return data["project"]["version"]

    # Otherwise get the installed pip package version
    try:
        return version('pr-agent')
    except PackageNotFoundError:
        get_logger().error("Unable to find package named 'pr-agent'")
        return "unknown"
