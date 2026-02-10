"""Tests for logging configuration."""

import logging
import os
from unittest.mock import patch


class TestSetupLogging:
    def test_default_level_is_warning(self):
        """Default log level should be WARNING."""
        from logging_config import setup_logging, get_logger

        setup_logging()
        logger = get_logger()
        assert logger.level == logging.WARNING

    def test_debug_flag_sets_debug_level(self):
        """--debug flag should set DEBUG level."""
        from logging_config import setup_logging, get_logger

        setup_logging(debug=True)
        logger = get_logger()
        assert logger.level == logging.DEBUG

    def test_env_var_sets_debug_level(self):
        """CHOOSR_DEBUG=1 should set DEBUG level."""
        from logging_config import setup_logging, get_logger

        with patch.dict(os.environ, {"CHOOSR_DEBUG": "1"}):
            setup_logging()
            logger = get_logger()
            assert logger.level == logging.DEBUG

    def test_logger_name_is_choosr(self):
        """Logger should be named 'choosr'."""
        from logging_config import get_logger

        logger = get_logger()
        assert logger.name == "choosr"
