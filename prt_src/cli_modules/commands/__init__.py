"""
Command layer for PRT CLI.

This module contains thin Typer command wrappers that delegate to handlers.
Commands are grouped by functionality and provide a clean interface to the CLI.
"""

from .database import db_status_command
from .database import test_db_command
from .debug import prt_debug_info_command
from .main import main_command
from .models import list_models_command

__all__ = [
    "main_command",
    "test_db_command",
    "db_status_command",
    "list_models_command",
    "prt_debug_info_command",
]
