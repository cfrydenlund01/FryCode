"""Application-wide logging configuration using loguru."""

from __future__ import annotations

import os
import sys
import logging as std_logging
from loguru import logger


LOG_FILE = "application.log"


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the application.

    Parameters
    ----------
    verbose: bool, optional
        When ``True``, the log level is set to ``DEBUG``; otherwise ``INFO``.
    """

    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, LOG_FILE)

    logger.remove()  # remove default handlers
    logger.configure(extra={"logger_name": "root"})

    level = "DEBUG" if verbose else "INFO"
    fmt = "{time} - {extra[logger_name]} - {level} - {message}"

    logger.add(sys.stdout, level=level, format=fmt)
    logger.add(log_path, level=level, format=fmt)

    # Silence overly verbose loggers from libraries
    std_logging.getLogger("requests_oauthlib").setLevel(std_logging.WARNING)
    std_logging.getLogger("urllib3").setLevel(std_logging.WARNING)
    std_logging.getLogger("transformers").setLevel(std_logging.WARNING)
    std_logging.getLogger("huggingface_hub").setLevel(std_logging.WARNING)

    get_logger(__name__).info("Logging setup complete.")


def get_logger(name: str):
    """Return a logger instance for a specific module."""

    return logger.bind(logger_name=name)

