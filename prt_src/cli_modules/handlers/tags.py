"""
Tag handling functions for PRT CLI.

Functions for managing and displaying tags in the PRT system.
"""

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.prompt import Prompt
from rich.table import Table

from ...api import PRTAPI
from ..bootstrap.guidance import show_empty_database_guidance
from ..bootstrap.health import handle_database_error
from ..services.export import export_search_results
from ..ui.pagination import paginate_results

console = Console()


def handle_view_tags(api: PRTAPI) -> None:
    """Handle viewing tags."""
    try:
        tags = api.list_all_tags()
        if tags:
            table = Table(title="Tags", show_header=True, header_style="bold magenta")
            table.add_column("ID", style="cyan", width=8)
            table.add_column("Name", style="green", width=30)
            table.add_column("Contact Count", style="yellow", width=15)

            for tag in tags:
                table.add_row(str(tag["id"]), tag["name"], str(tag["contact_count"]))
            console.print(table)
            console.print(f"\nTotal tags: {len(tags)}", style="green")
        else:
            show_empty_database_guidance()
    except Exception as e:
        handle_database_error(e, "viewing tags")


def handle_tag_search_results(api: PRTAPI, query: str) -> None:
    """Handle tag search results - show matching tags and their associated contacts."""
    tags = api.search_tags(query)
    if not tags:
        console.print(f"No tags found matching '{query}'", style="yellow")
        return

    console.print(f"Found {len(tags)} tags matching '{query}'", style="green")

    # Collect all data for export
    all_contacts = []
    tag_info = []

    # Create display functions for pagination
    def create_tag_display_func(tag_batch):
        def display():
            for tag in tag_batch:
                tag_name = tag["name"]
                console.print(f"\n📌 Tag: [bold cyan]{tag_name}[/bold cyan]")

                # Get contacts associated with this tag
                contacts = api.get_contacts_by_tag(tag_name)
                if contacts:
                    table = Table(show_header=True, header_style="bold green")
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
                        # Add to export data
                        if contact not in all_contacts:
                            all_contacts.append(contact)

                    console.print(table)
                    console.print(
                        f"   {len(contacts)} contacts with tag '{tag_name}'", style="green"
                    )

                    # Store tag info for export
                    tag_info.append({"tag": tag, "contacts": contacts})
                else:
                    console.print(f"   No contacts found with tag '{tag_name}'", style="yellow")

        return display

    # Group tags into pages for display (fewer per page since each tag shows multiple contacts)
    items_per_page = 3  # 3 tags per page to avoid too much scrolling
    pages = []
    for i in range(0, len(tags), items_per_page):
        batch = tags[i : i + items_per_page]
        pages.append(create_tag_display_func(batch))

    # Show results with pagination
    result = paginate_results(pages, 1)  # 1 page function per "page"
    if result == "export":
        # Prepare export data with tag-contact relationships
        export_data = []
        for info in tag_info:
            export_data.append({"tag": info["tag"], "associated_contacts": info["contacts"]})
        export_search_results(api, "tags", query, export_data)


def handle_tags_menu(api: PRTAPI) -> None:
    """Handle the tags management sub-menu."""
    while True:
        # Create tags menu with safe colors
        table = Table.grid(padding=(0, 2))
        table.add_column(style="bright_blue bold", width=4)
        table.add_column(style="default")

        table.add_row(
            "1.",
            "[bright_cyan bold]View All Tags[/bright_cyan bold] - Display all tags with contact counts",
        )
        table.add_row(
            "2.",
            "[bright_green bold]Create New Tag[/bright_green bold] - Add a new tag to the system",
        )
        table.add_row(
            "3.", "[bright_yellow bold]Search Tags[/bright_yellow bold] - Find specific tags"
        )
        table.add_row(
            "4.", "[bright_red bold]Delete Tag[/bright_red bold] - Remove a tag from the system"
        )
        table.add_row("b.", "[bright_magenta bold]Back to Main Menu[/bright_magenta bold]")

        console.print("\n")
        console.print(
            Panel(
                table,
                title="[bright_blue bold]Tag Management[/bright_blue bold]",
                border_style="bright_blue",
            )
        )

        choice = Prompt.ask("Select option", choices=["1", "2", "3", "4", "b"], default="1")

        if choice == "b":
            break
        elif choice == "1":
            handle_view_tags(api)
        elif choice == "2":
            handle_create_tag(api)
        elif choice == "3":
            query = Prompt.ask("Enter tag search term")
            if query.strip():
                handle_tag_search_results(api, query)
        elif choice == "4":
            handle_delete_tag(api)

        # No continuation prompt - tags menu handles its own flow


def handle_create_tag(api: PRTAPI) -> None:
    """Handle creating a new tag."""
    tag_name = Prompt.ask("Enter new tag name").strip()
    if not tag_name:
        console.print("Tag name cannot be empty.", style="red")
        return

    try:
        result = api.create_tag(tag_name)
        if result:
            console.print(f"✓ Created tag: '{tag_name}'", style="green")
        else:
            console.print(f"Tag '{tag_name}' already exists.", style="yellow")
    except Exception as e:
        console.print(f"Failed to create tag: {e}", style="red")


def handle_delete_tag(api: PRTAPI) -> None:
    """Handle deleting a tag."""
    # First show available tags
    tags = api.list_all_tags()
    if not tags:
        console.print("No tags available to delete.", style="yellow")
        return

    console.print("\n[bright_blue bold]Available Tags:[/bright_blue bold]")
    for tag in tags:
        console.print(f"  • {tag['name']} ({tag['contact_count']} contacts)")

    tag_name = Prompt.ask("\nEnter tag name to delete").strip()
    if not tag_name:
        console.print("Tag name cannot be empty.", style="red")
        return

    # Confirm deletion
    if not Confirm.ask(
        f"Are you sure you want to delete tag '{tag_name}'? This will remove it from all contacts."
    ):
        console.print("Deletion cancelled.", style="yellow")
        return

    try:
        if api.delete_tag(tag_name):
            console.print(f"✓ Deleted tag: '{tag_name}'", style="green")
        else:
            console.print(f"Tag '{tag_name}' not found.", style="yellow")
    except Exception as e:
        console.print(f"Failed to delete tag: {e}", style="red")
