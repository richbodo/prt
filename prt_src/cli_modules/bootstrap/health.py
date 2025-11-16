"""
Database health checking utilities for PRT CLI.

Functions for checking database health, handling errors, and providing recovery guidance.
These functions help diagnose and recover from database issues.
"""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text


def handle_database_error(error, operation: str):
    """Handle database errors with helpful messages."""
    console = Console()
    error_str = str(error).lower()

    if "no such table" in error_str:
        error_text = Text()
        error_text.append("🚨 Database Error: Tables not found\n\n", style="bold red")
        error_text.append(
            "It looks like your database hasn't been properly initialized.\n", style="yellow"
        )
        error_text.append("This can happen if:\n", style="yellow")
        error_text.append("• You're using a new or empty database\n", style="cyan")
        error_text.append("• The database was corrupted\n", style="cyan")
        error_text.append("• Migration scripts haven't been run\n\n", style="cyan")
        error_text.append("🔧 To fix this:\n", style="bold blue")
        error_text.append(
            "   1. Try importing Google Takeout (option 3) to initialize tables\n", style="green"
        )
        error_text.append("   2. Or run: python -m migrations.setup_database\n", style="green")
        error_text.append(
            "   3. If problems persist, restart PRT to run setup again\n", style="green"
        )

        console.print(Panel(error_text, title="Database Setup Required", border_style="red"))

    elif "database is locked" in error_str:
        console.print("🔒 Database is currently locked by another process.", style="red")
        console.print("Please close any other PRT instances and try again.", style="yellow")

    elif "permission denied" in error_str or "access" in error_str:
        console.print("🚫 Permission denied accessing database.", style="red")
        console.print("Check file permissions on your database file.", style="yellow")

    else:
        console.print(f"❌ Database error while {operation}:", style="red")
        console.print(f"   {error}", style="red")


def check_database_health(api) -> dict:
    """Check database health and return status information."""
    console = Console()

    try:
        # Try a simple query to check if tables exist and are accessible
        contacts = api.search_contacts("")
        contact_count = len(contacts) if contacts else 0

        # Try to get some basic stats
        try:
            # These might not exist if database is completely empty
            all_contacts = api.list_all_contacts()
            total_contacts = len(all_contacts) if all_contacts else 0
        except Exception as e:
            console.print(f"Warning: failed to list all contacts: {e}", style="yellow")
            total_contacts = contact_count

        return {
            "healthy": True,
            "contact_count": contact_count,
            "total_contacts": total_contacts,
            "has_data": contact_count > 0,
            "tables_exist": True,
        }
    except Exception as e:
        error_str = str(e).lower()
        return {
            "healthy": False,
            "error": str(e),
            "contact_count": 0,
            "total_contacts": 0,
            "has_data": False,
            "tables_exist": "no such table" not in error_str,
            "needs_initialization": "no such table" in error_str,
        }
