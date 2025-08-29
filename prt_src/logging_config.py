"""
Centralized logging configuration for PRT.

This module provides a consistent logging setup across all PRT components.
It maintains separation between user-facing console output (Rich Console)
and system logging for debugging, error tracking, and monitoring.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from .config import data_dir


def setup_logging(
    log_level: str = "INFO", log_file: Optional[Path] = None, enable_console_logging: bool = False
) -> logging.Logger:
    """
    Set up centralized logging for PRT.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional path to log file (defaults to prt_data/prt.log)
        enable_console_logging: Whether to also log to console (disabled by default
                               to avoid interference with Rich Console UI)

    Returns:
        Configured logger instance
    """
    if log_file is None:
        log_file = Path(data_dir()) / "prt.log"

    # Ensure log directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Get root logger for PRT
    logger = logging.getLogger("prt")
    logger.setLevel(getattr(logging, log_level.upper()))

    # Clear any existing handlers to avoid duplicates
    logger.handlers.clear()

    # File handler (always enabled)
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler (optional, disabled by default)
    if enable_console_logging:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Prevent propagation to root logger to avoid duplicate messages
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: Logger name (typically __name__ from calling module)

    Returns:
        Logger instance configured with PRT settings
    """
    # Ensure logging is set up
    if not logging.getLogger("prt").handlers:
        setup_logging()

    # Return child logger
    return logging.getLogger(f"prt.{name}")


# Convenience function for quick logger access
def log_error(message: str, exception: Optional[Exception] = None, module: str = "general") -> None:
    """Log an error message with optional exception details."""
    logger = get_logger(module)
    if exception:
        logger.error(f"{message}: {exception}", exc_info=True)
    else:
        logger.error(message)


def log_warning(message: str, module: str = "general") -> None:
    """Log a warning message."""
    logger = get_logger(module)
    logger.warning(message)


def log_info(message: str, module: str = "general") -> None:
    """Log an info message."""
    logger = get_logger(module)
    logger.info(message)


def log_debug(message: str, module: str = "general") -> None:
    """Log a debug message."""
    logger = get_logger(module)
    logger.debug(message)
