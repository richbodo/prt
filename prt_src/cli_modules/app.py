"""
Main Typer application for PRT CLI.

This module creates the Typer app and registers all commands.
"""

import typer

from .commands.database import db_status_command
from .commands.database import test_db_command
from .commands.debug import prt_debug_info_command
from .commands.main import main_command
from .commands.models import list_models_command

# Create the Typer app
app = typer.Typer(
    help="Personal Relationship Toolkit (PRT) - Privacy-first contact management with AI-powered search",
    add_completion=False,
    no_args_is_help=False,
)

# Set the main callback
app.callback(invoke_without_command=True)(main_command)

# Register commands
app.command(name="test-db")(test_db_command)
app.command(name="list-models")(list_models_command)
app.command(name="prt-debug-info")(prt_debug_info_command)
app.command(name="db-status")(db_status_command)
