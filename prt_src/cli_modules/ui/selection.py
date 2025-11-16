"""
Selection utilities for PRT CLI.

Functions for contact selection, validation, and search with pagination support.
These utilities provide consistent selection patterns across the CLI.
"""

from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

# Import constants that need to be defined or imported
DEFAULT_PAGE_SIZE = 20  # Default number of items per page
MAX_DISPLAY_CONTACTS = 30  # Maximum contacts to show without pagination


def _validate_contact_id(contact_id: int, contacts: list) -> bool:
    """Verify that a contact ID exists in the contact list."""
    return any(c["id"] == contact_id for c in contacts)


def _display_contacts_paginated(contacts: list, title: str = "Select a Contact") -> None:
    """Display contacts with pagination support."""
    console = Console()

    total_contacts = len(contacts)
    page_size = DEFAULT_PAGE_SIZE
    current_page = 0
    total_pages = (total_contacts + page_size - 1) // page_size

    while True:
        # Calculate page boundaries
        start_idx = current_page * page_size
        end_idx = min(start_idx + page_size, total_contacts)

        # Create table for current page
        table = Table(
            title=f"{title} (Page {current_page + 1}/{total_pages})",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("ID", style="cyan", width=8)
        table.add_column("Name", style="green", width=30)
        table.add_column("Email", style="yellow", width=40)

        for contact in contacts[start_idx:end_idx]:
            table.add_row(str(contact["id"]), contact["name"] or "N/A", contact["email"] or "N/A")

        console.print(table)
        console.print(f"[dim]Showing contacts {start_idx + 1}-{end_idx} of {total_contacts}[/dim]")

        # Navigation options
        nav_choices = []
        nav_prompt = "Options: "

        if current_page > 0:
            nav_choices.append("p")
            nav_prompt += "[p]revious, "
        if current_page < total_pages - 1:
            nav_choices.append("n")
            nav_prompt += "[n]ext, "
        nav_choices.extend(["s", "q"])
        nav_prompt += "[s]elect ID, [q]uit"

        choice = Prompt.ask(nav_prompt, choices=nav_choices, default="s")

        if choice == "p" and current_page > 0:
            current_page -= 1
        elif choice == "n" and current_page < total_pages - 1:
            current_page += 1
        elif choice == "s" or choice == "q":
            break

    return choice == "s"  # Return True if user wants to select


def _select_contact_with_search(contacts: list, prompt_text: str) -> int | None:
    """Select a contact with search and pagination support."""
    console = Console()

    # Option to search first
    search_term = Prompt.ask("Search contacts (press Enter to see all)", default="")

    if search_term:
        # Filter contacts based on search
        search_lower = search_term.lower()
        filtered = [
            c
            for c in contacts
            if (
                c.get("name", "").lower().find(search_lower) >= 0
                or c.get("email", "").lower().find(search_lower) >= 0
            )
        ]

        if not filtered:
            console.print(f"No contacts found matching '{search_term}'", style="yellow")
            return None

        contacts = filtered
        console.print(f"Found {len(contacts)} matching contacts", style="green")

    # Display with pagination if needed
    if len(contacts) > MAX_DISPLAY_CONTACTS:
        if not _display_contacts_paginated(contacts, prompt_text):
            return None
    else:
        # Display all contacts
        table = Table(title=prompt_text, show_header=True, header_style="bold magenta")
        table.add_column("ID", style="cyan", width=8)
        table.add_column("Name", style="green", width=30)
        table.add_column("Email", style="yellow", width=40)

        for contact in contacts:
            table.add_row(str(contact["id"]), contact["name"] or "N/A", contact["email"] or "N/A")
        console.print(table)

    # Get contact ID with validation
    while True:
        contact_id_str = Prompt.ask("Enter contact ID (or 'q' to quit)")
        if contact_id_str.lower() == "q":
            return None

        try:
            contact_id = int(contact_id_str)
            if _validate_contact_id(contact_id, contacts):
                return contact_id
            else:
                console.print(
                    f"Contact ID {contact_id} not found. Please select a valid ID.", style="red"
                )
        except ValueError:
            console.print("Invalid input. Please enter a number or 'q' to quit.", style="red")
