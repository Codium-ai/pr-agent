import os
import sys
from importlib.metadata import version, PackageNotFoundError

from pr_agent.log import get_logger

def get_version() -> str:
    # First check pyproject.toml if running directly out of repository
    if os.path.exists("pyproject.toml"):
        if sys.version_info >= (3, 11):
            import tomllib
            with open("pyproject.toml", "rb") as f:
                data = tomllib.load(f)
                return data["project"]["version"]
        else:
            get_logger().warn("Unable to determine local version from pyproject.toml")

    # Otherwise get the installed pip package version
    try:
        return version('pr-agent')
    except PackageNotFoundError:
        get_logger().error("Unable to find package named 'pr-agent'")
        return "unknown"
