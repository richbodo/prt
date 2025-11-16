"""
Database commands for PRT CLI.

This module contains commands for testing database connectivity and checking status.
"""

from pathlib import Path

import typer
from rich.console import Console

from ...config import load_config
from ...db import create_database
from ..bootstrap.setup import check_setup_status

console = Console()


def test_db_command():
    """Test database connection and credentials."""
    try:
        config = load_config()
        if not config:
            console.print("No configuration found. Run 'setup' first.", style="red")
            raise typer.Exit(1) from None

        db_path = Path(config.get("db_path", "prt_data/prt.db"))
        console.print(f"Testing database connection to: {db_path}", style="blue")

        if not db_path.exists():
            console.print("Database file not found.", style="red")
            raise typer.Exit(1) from None

        # Try to connect to database
        db = create_database(db_path)

        if db.is_valid():
            console.print("✓ Database connection successful", style="green")
            console.print(f"  Contacts: {db.count_contacts()}", style="green")
            console.print(f"  Relationships: {db.count_relationships()}", style="green")
        else:
            console.print("✗ Database is corrupted or invalid", style="red")
            raise typer.Exit(1) from None

    except Exception as e:
        console.print(f"✗ Database test failed: {e}", style="red")
        raise typer.Exit(1) from None


def db_status_command():
    """Check the database status."""
    status = check_setup_status()

    if status["needs_setup"]:
        console.print(f"PRT needs setup: {status['reason']}", style="yellow")
        raise typer.Exit(1) from None

    console.print("✓ PRT is properly configured", style="green")

    # Additional status information
    config = status["config"]
    db_path = Path(config.get("db_path", "prt_data/prt.db"))

    if db_path.exists():
        try:
            db = create_database(db_path)
            if db.is_valid():
                console.print(f"Database path: {db_path}", style="blue")
                console.print(f"Contacts: {db.count_contacts()}", style="green")
                console.print(f"Relationships: {db.count_relationships()}", style="green")
            else:
                console.print("Database status: [red]CORRUPT[/red]")
        except Exception as e:
            console.print(f"Database status: [red]ERROR[/red] - {e}")
    else:
        console.print("Database status: [yellow]NOT FOUND[/yellow]")
