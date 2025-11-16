"""
Search handling functions for PRT CLI.

Functions for handling search operations in the PRT system.
"""

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from ...api import PRTAPI
from ..bootstrap.guidance import show_empty_database_guidance
from ..bootstrap.health import check_database_health
from ..bootstrap.health import handle_database_error
from .contacts import handle_contact_search_results
from .notes import handle_note_search_results
from .tags import handle_tag_search_results

console = Console()


def handle_search_menu(api: PRTAPI) -> None:
    """Handle the search sub-menu."""
    # Check database health first
    health = check_database_health(api)
    if not health["healthy"]:
        handle_database_error(Exception(health["error"]), "searching")
        return

    if not health["has_data"]:
        show_empty_database_guidance()
        return

    while True:
        # Create search menu with safe colors
        table = Table.grid(padding=(0, 2))
        table.add_column(style="bright_blue bold", width=4)
        table.add_column(style="default")

        table.add_row(
            "1.", "[bright_cyan bold]Search Contacts[/bright_cyan bold] - Find contacts by name"
        )
        table.add_row(
            "2.",
            "[bright_yellow bold]Search Tags[/bright_yellow bold] - Find tags and associated contacts",
        )
        table.add_row(
            "3.",
            "[bright_magenta bold]Search Notes[/bright_magenta bold] - Find notes and associated contacts",
        )
        table.add_row("b.", "[bright_green bold]Back to Main Menu[/bright_green bold]")

        console.print("\n")
        console.print(
            Panel(
                table,
                title="[bright_blue bold]Search Menu[/bright_blue bold]",
                border_style="bright_blue",
            )
        )

        choice = Prompt.ask("Select option", choices=["1", "2", "3", "b"], default="1")

        if choice == "b":
            break
        elif choice == "1":
            query = Prompt.ask("Enter contact search term")
            if query.strip():
                handle_contact_search_results(api, query)
        elif choice == "2":
            query = Prompt.ask("Enter tag search term")
            if query.strip():
                handle_tag_search_results(api, query)
        elif choice == "3":
            query = Prompt.ask("Enter note search term")
            if query.strip():
                handle_note_search_results(api, query)

        # No continuation prompt - search menu handles its own flow
