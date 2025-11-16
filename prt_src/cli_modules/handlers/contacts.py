"""
Contact handling functions for PRT CLI.

Functions for managing and displaying contacts in the PRT system.
"""

from rich.console import Console
from rich.table import Table

from ...api import PRTAPI
from ..bootstrap.guidance import show_empty_database_guidance
from ..bootstrap.health import handle_database_error
from ..services.export import export_search_results
from ..ui.pagination import paginate_results

console = Console()


def handle_contacts_view(api: PRTAPI) -> None:
    """Handle viewing contacts."""
    try:
        contacts = api.list_all_contacts()  # Get all contacts
        if contacts:
            table = Table(title="Contacts", show_header=True, header_style="bold magenta")
            table.add_column("ID", style="cyan", width=8)
            table.add_column("Name", style="green", width=30)
            table.add_column("Email", style="yellow", width=40)
            table.add_column("Phone", style="blue", width=20)

            for contact in contacts:
                table.add_row(
                    str(contact["id"]),
                    contact["name"] or "N/A",
                    contact["email"] or "N/A",
                    contact.get("phone", "N/A") or "N/A",
                )
            console.print(table)
            console.print(f"\nTotal contacts: {len(contacts)}", style="green")
        else:
            show_empty_database_guidance()
    except Exception as e:
        handle_database_error(e, "viewing contacts")


def handle_contact_search_results(api: PRTAPI, query: str) -> None:
    """Handle contact search results display with pagination and export."""
    contacts = api.search_contacts(query)
    if not contacts:
        console.print(f"No contacts found matching '{query}'", style="yellow")
        return

    console.print(f"Found {len(contacts)} contacts matching '{query}'", style="green")

    # Create display functions for pagination
    def create_contact_display_func(contact_batch):
        def display():
            table = Table(
                title=f"Contact Search Results for '{query}'",
                show_header=True,
                header_style="bold magenta",
            )
            table.add_column("ID", style="cyan", width=8)
            table.add_column("Name", style="green", width=30)
            table.add_column("Email", style="yellow", width=40)
            table.add_column("Phone", style="blue", width=20)

            for contact in contact_batch:
                table.add_row(
                    str(contact["id"]),
                    contact["name"] or "N/A",
                    contact["email"] or "N/A",
                    contact.get("phone", "N/A") or "N/A",
                )
            console.print(table)

        return display

    # Group contacts into pages for display
    items_per_page = 20  # Table rows fit better with 20 per page
    pages = []
    for i in range(0, len(contacts), items_per_page):
        batch = contacts[i : i + items_per_page]
        pages.append(create_contact_display_func(batch))

    # Show results with pagination
    result = paginate_results(pages, 1)  # 1 page function per "page"
    if result == "export":
        export_search_results(api, "contacts", query, contacts)
