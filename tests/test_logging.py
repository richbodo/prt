"""Tests for the logging configuration system."""

import logging
import tempfile
from pathlib import Path
from unittest.mock import patch

from prt_src.logging_config import get_logger
from prt_src.logging_config import setup_logging


class TestLoggingConfiguration:
    """Test the centralized logging system."""

    def test_setup_logging_creates_logger(self):
        """Test that setup_logging creates a properly configured logger."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            logger = setup_logging(log_level="DEBUG", log_file=log_file)

            assert logger.name == "prt"
            assert logger.level == logging.DEBUG
            assert len(logger.handlers) == 1  # File handler only
            assert log_file.exists()

    def test_setup_logging_with_console(self):
        """Test setup with console logging enabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            logger = setup_logging(log_level="INFO", log_file=log_file, enable_console_logging=True)

            assert len(logger.handlers) == 2  # File and console handlers

    def test_get_logger_returns_child_logger(self):
        """Test that get_logger returns properly named child loggers."""
        logger = get_logger("test_module")
        assert logger.name == "prt.test_module"

    def test_logging_writes_to_file(self):
        """Test that logging actually writes to the log file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"

            # Setup logging
            setup_logging(log_level="INFO", log_file=log_file)

            # Get logger and write message
            logger = get_logger("test")
            test_message = "Test logging message"
            logger.info(test_message)

            # Verify message was written
            log_content = log_file.read_text()
            assert test_message in log_content
            assert "prt.test" in log_content
            assert "INFO" in log_content

    def test_logging_levels_work(self):
        """Test that different log levels work correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"

            # Setup with WARNING level
            setup_logging(log_level="WARNING", log_file=log_file)
            logger = get_logger("test")

            # Log at different levels
            logger.debug("Debug message")  # Should not appear
            logger.info("Info message")  # Should not appear
            logger.warning("Warning message")  # Should appear
            logger.error("Error message")  # Should appear

            log_content = log_file.read_text()
            assert "Debug message" not in log_content
            assert "Info message" not in log_content
            assert "Warning message" in log_content
            assert "Error message" in log_content

    @patch("prt_src.logging_config.data_dir")
    def test_default_log_file_location(self, mock_data_dir):
        """Test that default log file is created in data directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_data_dir.return_value = temp_dir

            logger = setup_logging()
            logger.info("Test message")

            expected_log_file = Path(temp_dir) / "prt.log"
            assert expected_log_file.exists()
