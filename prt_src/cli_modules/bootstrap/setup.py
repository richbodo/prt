"""
Setup and initialization utilities for PRT CLI.

Functions for handling application setup, debug mode configuration, and setup wizard.
These functions manage the initial configuration and database setup process.
"""

from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Prompt

from migrations.setup_database import initialize_database
from migrations.setup_database import setup_database

from ...config import config_path
from ...config import data_dir
from ...config import load_config
from ...db import create_database

# Required configuration fields
REQUIRED_FIELDS = ["db_username", "db_password", "db_path"]


def setup_debug_mode(regenerate: bool = False):
    """Set up debug mode with fixture data.

    Args:
        regenerate: If True, force regeneration of debug.db even if it exists.
                   If False, reuse existing debug.db if present.
    """
    console = Console()

    from tests.fixtures import setup_test_database

    # Enable DEBUG logging in debug mode for better troubleshooting
    from ...logging_config import setup_logging

    setup_logging(log_level="DEBUG")
    console.print("🔍 DEBUG logging enabled (check prt_data/prt.log)", style="dim")

    # Create a temporary database in the data directory
    debug_db_path = data_dir() / "debug.db"

    # Check if debug database already exists
    if debug_db_path.exists() and not regenerate:
        console.print(f"📂 Using existing debug database: {debug_db_path}", style="blue")
        console.print(
            "   (Use --regenerate-fixtures to create a fresh fixture database)", style="dim"
        )
        console.print()
    else:
        # Remove existing debug database if regenerating
        if debug_db_path.exists():
            debug_db_path.unlink()
            console.print("🔄 Regenerating debug database...", style="yellow")

        console.print(f"🔧 Creating debug database at: {debug_db_path}", style="blue")

        # Create database with fixture data
        db = create_database(debug_db_path)
        fixtures = setup_test_database(db)

        console.print("📊 Loaded fixture data:", style="green")
        console.print(
            f"   • {len(fixtures['contacts'])} contacts with profile images", style="green"
        )
        console.print(f"   • {len(fixtures['tags'])} tags", style="green")
        console.print(f"   • {len(fixtures['notes'])} notes", style="green")
        console.print(f"   • {len(fixtures['relationships'])} relationships", style="green")
        console.print()

    # Return debug configuration
    return {
        "db_path": str(debug_db_path),
        "db_encrypted": False,
        "db_username": "debug_user",
        "db_password": "debug_pass",
        "db_type": "sqlite",
    }


def check_setup_status():
    """Check if PRT is properly set up and return status information."""
    try:
        config = load_config()
        if not config:
            return {"needs_setup": True, "reason": "No configuration file found"}

        # Check for missing required fields
        missing = [f for f in REQUIRED_FIELDS if f not in config]
        if missing:
            return {
                "needs_setup": True,
                "reason": f"Missing configuration fields: {', '.join(missing)}",
            }

        # Check if database exists and is accessible
        db_path = Path(config.get("db_path", "prt_data/prt.db"))
        if not db_path.exists():
            return {"needs_setup": True, "reason": "Database file not found"}

        # Try to connect to database
        try:
            db = create_database(db_path)

            if not db.is_valid():
                return {"needs_setup": True, "reason": "Database is corrupted or invalid"}

        except Exception as e:
            return {"needs_setup": True, "reason": f"Database connection failed: {e}"}

        return {"needs_setup": False, "config": config, "db_path": db_path}

    except Exception as e:
        return {"needs_setup": True, "reason": f"Configuration error: {e}"}


def run_setup_wizard():
    """Run the interactive setup wizard."""
    console = Console()

    console.print("\n" + "=" * 60)
    console.print("PRT Setup Wizard", style="bold blue")
    console.print("=" * 60)
    console.print()
    console.print("Welcome to PRT! Let's get you set up.", style="green")
    console.print()

    # Ask user what type of setup they want
    console.print("Choose your setup option:", style="bold")
    console.print()
    console.print("[1] Set up for real use")
    console.print("    → Create your personal contact database")
    console.print()
    console.print("[2] Try with demo data")
    console.print("    → Safe mode with sample contacts (your real data stays safe)")
    console.print()

    while True:
        choice = Prompt.ask("Enter your choice", choices=["1", "2"], default="1")
        if choice in ["1", "2"]:
            break
        console.print("Please enter 1 or 2", style="red")

    try:
        if choice == "1":
            # Regular setup for real use
            console.print("\n🔧 Setting up your personal database...", style="blue")
            config = setup_database()
            console.print("✓ Configuration created successfully", style="green")

            # Initialize the database
            if initialize_database(config):
                console.print("✓ Database initialized successfully", style="green")
            else:
                console.print("✗ Database initialization failed", style="red")
                raise Exception("Database initialization failed")

            console.print()
            console.print("🎉 PRT setup completed successfully!", style="bold green")
            console.print(f"Configuration saved to: {config_path()}", style="cyan")
            console.print(
                f"Database location: {config.get('db_path', 'prt_data/prt.db')}", style="cyan"
            )
            console.print()
            console.print(
                "You can now use PRT to manage your personal relationships!", style="green"
            )

        else:
            # Demo/fixture mode setup
            console.print("\n🎯 Setting up demo mode with sample data...", style="blue")
            from ...fixture_manager import setup_fixture_mode

            config = setup_fixture_mode(regenerate=True, quiet=False)
            console.print()
            console.print("🎉 Demo mode setup completed successfully!", style="bold green")
            console.print(
                "🔒 Your real data is completely safe - demo uses isolated database", style="green"
            )
            console.print(
                f"Demo database location: {config.get('db_path', 'prt_data/fixture.db')}",
                style="cyan",
            )
            console.print()
            console.print("You can now explore PRT with sample data!", style="green")
            console.print(
                "💡 To switch back to real mode later, restart PRT without --setup", style="dim"
            )

        return config

    except Exception as e:
        console.print(f"✗ Setup failed: {e}", style="bold red")
        console.print("Please check the error and try again.", style="yellow")
        raise typer.Exit(1) from None
