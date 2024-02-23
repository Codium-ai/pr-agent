import json
import logging
import os
import sys
from enum import Enum

from loguru import logger

from pr_agent.config_loader import get_settings


class LoggingFormat(str, Enum):
    CONSOLE = "CONSOLE"
    JSON = "JSON"


def json_format(record: dict) -> str:
    return record["message"]


def analytics_filter(record: dict) -> bool:
    return record.get("extra", {}).get("analytics", False)


def setup_logger(level: str = "INFO", fmt: LoggingFormat = LoggingFormat.CONSOLE):
    level: int = logging.getLevelName(level.upper())
    if type(level) is not int:
        level = logging.INFO

    if fmt == LoggingFormat.JSON:
        logger.remove(None)
        logger.add(
            sys.stdout,
            level=level,
            format="{message}",
            colorize=False,
            serialize=True,
        )
    elif fmt == LoggingFormat.CONSOLE:
        logger.remove(None)
        logger.add(sys.stdout, level=level, colorize=True)

    log_folder = get_settings().get("CONFIG.ANALYTICS_FOLDER", "")
    if log_folder:
        pid = os.getpid()
        log_file = os.path.join(log_folder, f"pr-agent.{pid}.log")
        logger.add(
            log_file,
            filter=analytics_filter,
            level=level,
            format="{message}",
            colorize=False,
            serialize=True,
        )

    return logger


def get_logger(*args, **kwargs):
    return logger
