"""
Database handling functions for PRT CLI.

Functions for managing and monitoring the database in the PRT system.
"""

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from ...api import PRTAPI
from ...config import load_config
from ...db import create_database

console = Console()


def handle_database_status(api: PRTAPI) -> None:
    """Handle database status check."""
    try:
        config = load_config()
        db_path = Path(config.get("db_path", "prt_data/prt.db"))

        console.print(f"Database path: {db_path}", style="blue")
        # Encryption status removed as part of Issue #41

        if db_path.exists():
            # Try to connect and verify
            try:
                db = create_database(db_path)

                if db.is_valid():
                    console.print("Database status: [green]OK[/green]")
                    console.print(f"Contacts: {db.count_contacts()}", style="green")
                    console.print(f"Relationships: {db.count_relationships()}", style="green")
                else:
                    console.print("Database status: [red]CORRUPT[/red]")
            except Exception as e:
                console.print(f"Database status: [red]ERROR[/red] - {e}")
        else:
            console.print("Database status: [yellow]NOT FOUND[/yellow]")

    except Exception as e:
        console.print(f"Failed to check status: {e}", style="red")


def handle_database_backup(api: PRTAPI) -> None:
    """Handle database backup."""
    try:
        config = load_config()
        db_path = Path(config.get("db_path", "prt_data/prt.db"))

        if not db_path.exists():
            console.print("Database file not found.", style="red")
            return

        # Create backup path
        backup_path = db_path.with_suffix(f".backup.{int(db_path.stat().st_mtime)}")

        # Copy the database file
        import shutil

        shutil.copy2(db_path, backup_path)

        console.print(f"Database backed up to: {backup_path}", style="green")

    except Exception as e:
        console.print(f"Failed to create backup: {e}", style="red")


def handle_database_menu(api: PRTAPI) -> None:
    """Handle the database management sub-menu."""
    while True:
        # Create database menu with safe colors
        table = Table.grid(padding=(0, 2))
        table.add_column(style="bright_blue bold", width=4)
        table.add_column(style="default")

        table.add_row(
            "1.",
            "[bright_cyan bold]Database Status[/bright_cyan bold] - Check database health and info",
        )
        table.add_row(
            "2.", "[bright_green bold]Create Backup[/bright_green bold] - Create timestamped backup"
        )
        table.add_row(
            "3.",
            "[bright_yellow bold]Test Connection[/bright_yellow bold] - Validate database connection",
        )
        table.add_row("4.", "[blue bold]View Statistics[/blue bold] - Detailed database statistics")
        table.add_row("b.", "[bright_magenta bold]Back to Main Menu[/bright_magenta bold]")

        console.print("\n")
        console.print(
            Panel(
                table,
                title="[bright_blue bold]Database Management[/bright_blue bold]",
                border_style="bright_blue",
            )
        )

        choice = Prompt.ask("Select option", choices=["1", "2", "3", "4", "b"], default="1")

        if choice == "b":
            break
        elif choice == "1":
            handle_database_status(api)
        elif choice == "2":
            handle_database_backup(api)
        elif choice == "3":
            handle_database_test(api)
        elif choice == "4":
            handle_database_stats(api)

        # No continuation prompt - database menu handles its own flow


def handle_database_test(api: PRTAPI) -> None:
    """Handle database connection testing."""
    console.print("Testing database connection...", style="blue")

    try:
        if api.test_database_connection():
            console.print("✓ Database connection successful", style="green")

            # Show basic stats
            stats = api.get_database_stats()
            console.print(f"  Contacts: {stats['contacts']}", style="green")
            console.print(f"  Relationships: {stats['relationships']}", style="green")
        else:
            console.print("✗ Database connection failed", style="red")
    except Exception as e:
        console.print(f"✗ Database test failed: {e}", style="red")


def handle_database_stats(api: PRTAPI) -> None:
    """Handle detailed database statistics."""
    try:
        config = load_config()
        db_path = Path(config.get("db_path", "prt_data/prt.db"))

        console.print("\n[bright_blue bold]Database Statistics[/bright_blue bold]")
        console.print(f"Database path: {db_path}")

        if db_path.exists():
            # File size
            file_size = db_path.stat().st_size
            size_mb = file_size / (1024 * 1024)
            console.print(f"File size: {size_mb:.2f} MB ({file_size:,} bytes)")

            # Basic stats
            stats = api.get_database_stats()
            console.print(f"Contacts: {stats['contacts']}")
            console.print(f"Relationships: {stats['relationships']}")

            # Additional stats from API
            all_tags = api.list_all_tags()
            all_notes = api.list_all_notes()
            console.print(f"Tags: {len(all_tags)}")
            console.print(f"Notes: {len(all_notes)}")

            # Database health
            if api.validate_database():
                console.print("Database integrity: ✓ OK", style="green")
            else:
                console.print("Database integrity: ✗ Issues detected", style="red")
        else:
            console.print("Database file not found.", style="red")

    except Exception as e:
        console.print(f"Failed to get database statistics: {e}", style="red")
