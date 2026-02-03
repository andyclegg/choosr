"""
Logging configuration for choosr.

Provides a consistent logging setup across all modules with support for
debug mode via --debug flag or CHOOSR_DEBUG environment variable.
"""

import logging
import os
import sys

_logger = None


def setup_logging(debug: bool = False) -> None:
    """
    Configure logging for choosr.

    Args:
        debug: If True, set log level to DEBUG. Also checks CHOOSR_DEBUG env var.
    """
    global _logger

    # Check environment variable
    env_debug = os.environ.get("CHOOSR_DEBUG", "").lower() in ("1", "true", "yes")

    level = logging.DEBUG if (debug or env_debug) else logging.WARNING

    # Create logger
    _logger = logging.getLogger("choosr")
    _logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    _logger.handlers.clear()

    # Create stderr handler
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)

    # Create formatter
    formatter = logging.Formatter("[choosr] %(levelname)s: %(message)s")
    handler.setFormatter(formatter)

    _logger.addHandler(handler)


def get_logger() -> logging.Logger:
    """
    Get the choosr logger.

    Returns:
        The configured logger instance.
    """
    global _logger
    if _logger is None:
        setup_logging()
    return _logger
