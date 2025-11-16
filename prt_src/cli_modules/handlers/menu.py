"""
Menu handling functions for PRT CLI.

Functions for displaying the main application menu.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ...api import PRTAPI

console = Console()


def show_main_menu(api: PRTAPI):
    """Display the improved main operations menu with safe, visible colors."""
    # Use Rich's table grid for consistent formatting and safe colors
    table = Table.grid(padding=(0, 2))
    table.add_column(style="bright_blue bold", width=4)  # High contrast for shortcuts
    table.add_column(style="default")  # Default terminal color for descriptions

    # Menu items with safe, high-contrast colors
    table.add_row(
        "c.",
        "[bright_green bold]Start Chat[/bright_green bold] - AI-powered chat mode that does anything the cli and tools can do and more",
    )
    table.add_row(
        "v.", "[bright_cyan bold]View Contacts[/bright_cyan bold] - Browse contact information"
    )
    table.add_row(
        "r.",
        "[bright_yellow bold]Manage Relationships[/bright_yellow bold] - View and manage contact relationships",
    )
    table.add_row(
        "s.",
        "[bright_magenta bold]Search[/bright_magenta bold] - Search contacts by contact, tag, or note content - export any results list to a directory",
    )
    table.add_row(
        "t.",
        "[bright_yellow bold]Manage Tags[/bright_yellow bold] - Browse and manage contact tags",
    )
    table.add_row("n.", "[blue bold]Manage Notes[/blue bold] - Browse and manage contact notes")
    table.add_row(
        "d.", "[magenta bold]Manage Database[/magenta bold] - Check database stats and backup"
    )
    table.add_row(
        "i.",
        "[green bold]Import Google Takeout[/green bold] - Import contacts from Google Takeout zip file",
    )
    table.add_row("q.", "[bright_red bold]Exit[/bright_red bold] - Exit the application")

    console.print(
        Panel(
            table,
            title="[bright_blue bold]Personal Relationship Toolkit (PRT)[/bright_blue bold]",
            border_style="bright_blue",
        )
    )
