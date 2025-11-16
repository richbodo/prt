"""
Note handling functions for PRT CLI.

Functions for managing and displaying notes in the PRT system.
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
from ..ui.formatting import show_full_note
from ..ui.pagination import paginate_results

console = Console()


def handle_view_notes(api: PRTAPI) -> None:
    """Handle viewing notes."""
    try:
        notes = api.list_all_notes()
        if notes:
            table = Table(title="Notes", show_header=True, header_style="bold magenta")
            table.add_column("ID", style="cyan", width=8)
            table.add_column("Title", style="green", width=30)
            table.add_column("Content", style="yellow", width=50)
            table.add_column("Contact Count", style="blue", width=15)

            for note in notes:
                content_preview = (
                    note["content"][:47] + "..." if len(note["content"]) > 50 else note["content"]
                )
                table.add_row(
                    str(note["id"]), note["title"], content_preview, str(note["contact_count"])
                )
            console.print(table)
            console.print(f"\nTotal notes: {len(notes)}", style="green")
        else:
            show_empty_database_guidance()
    except Exception as e:
        handle_database_error(e, "viewing notes")


def handle_note_search_results(api: PRTAPI, query: str) -> None:
    """Handle note search results - show matching notes and their associated contacts."""
    notes = api.search_notes(query)
    if not notes:
        console.print(f"No notes found matching '{query}'", style="yellow")
        return

    console.print(f"Found {len(notes)} notes matching '{query}'", style="green")

    # Collect all data for export
    all_contacts = []
    note_info = []

    # Create display functions for pagination
    def create_note_display_func(note_batch):
        def display():
            for note in note_batch:
                note_title = note["title"]
                note_content = note.get("content", "")

                console.print(f"\n📝 Note: [bold cyan]{note_title}[/bold cyan]")

                # Show note preview (first 100 characters)
                if note_content:
                    preview = (
                        note_content[:100] + "..." if len(note_content) > 100 else note_content
                    )
                    console.print(f"   Preview: {preview}", style="dim")

                # Ask if user wants to see full note
                if len(note_content) > 100 and Confirm.ask("   Show full note?", default=False):
                    show_full_note(note_title, note_content)
                    continue

                # Get contacts associated with this note
                contacts = api.get_contacts_by_note(note_title)
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
                        f"   {len(contacts)} contacts with note '{note_title}'", style="green"
                    )

                    # Store note info for export
                    note_info.append({"note": note, "contacts": contacts})
                else:
                    console.print(f"   No contacts found with note '{note_title}'", style="yellow")

        return display

    # Group notes into pages for display (fewer per page since each note shows multiple contacts)
    items_per_page = 2  # 2 notes per page to avoid too much scrolling
    pages = []
    for i in range(0, len(notes), items_per_page):
        batch = notes[i : i + items_per_page]
        pages.append(create_note_display_func(batch))

    # Show results with pagination
    result = paginate_results(pages, 1)  # 1 page function per "page"
    if result == "export":
        # Prepare export data with note-contact relationships
        export_data = []
        for info in note_info:
            export_data.append({"note": info["note"], "associated_contacts": info["contacts"]})
        export_search_results(api, "notes", query, export_data)


def handle_notes_menu(api: PRTAPI) -> None:
    """Handle the notes management sub-menu."""
    while True:
        # Create notes menu with safe colors
        table = Table.grid(padding=(0, 2))
        table.add_column(style="bright_blue bold", width=4)
        table.add_column(style="default")

        table.add_row(
            "1.",
            "[bright_cyan bold]View All Notes[/bright_cyan bold] - Display all notes with previews",
        )
        table.add_row(
            "2.",
            "[bright_green bold]Create New Note[/bright_green bold] - Add a new note to the system",
        )
        table.add_row(
            "3.", "[bright_yellow bold]Search Notes[/bright_yellow bold] - Find specific notes"
        )
        table.add_row("4.", "[blue bold]Edit Note[/blue bold] - Modify an existing note")
        table.add_row(
            "5.", "[bright_red bold]Delete Note[/bright_red bold] - Remove a note from the system"
        )
        table.add_row("b.", "[bright_magenta bold]Back to Main Menu[/bright_magenta bold]")

        console.print("\n")
        console.print(
            Panel(
                table,
                title="[bright_blue bold]Note Management[/bright_blue bold]",
                border_style="bright_blue",
            )
        )

        choice = Prompt.ask("Select option", choices=["1", "2", "3", "4", "5", "b"], default="1")

        if choice == "b":
            break
        elif choice == "1":
            handle_view_notes(api)
        elif choice == "2":
            handle_create_note(api)
        elif choice == "3":
            query = Prompt.ask("Enter note search term")
            if query.strip():
                handle_note_search_results(api, query)
        elif choice == "4":
            handle_edit_note(api)
        elif choice == "5":
            handle_delete_note(api)

        # No continuation prompt - notes menu handles its own flow


def handle_create_note(api: PRTAPI) -> None:
    """Handle creating a new note."""
    title = Prompt.ask("Enter note title").strip()
    if not title:
        console.print("Note title cannot be empty.", style="red")
        return

    content = Prompt.ask("Enter note content").strip()
    if not content:
        console.print("Note content cannot be empty.", style="red")
        return

    try:
        result = api.create_note(title, content)
        if result:
            console.print(f"✓ Created note: '{title}'", style="green")
        else:
            console.print(f"Note '{title}' already exists.", style="yellow")
    except Exception as e:
        console.print(f"Failed to create note: {e}", style="red")


def handle_edit_note(api: PRTAPI) -> None:
    """Handle editing an existing note."""
    # First show available notes
    notes = api.list_all_notes()
    if not notes:
        console.print("No notes available to edit.", style="yellow")
        return

    console.print("\n[bright_blue bold]Available Notes:[/bright_blue bold]")
    for note in notes:
        preview = note["content"][:50] + "..." if len(note["content"]) > 50 else note["content"]
        console.print(f"  • {note['title']}: {preview}")

    title = Prompt.ask("\nEnter note title to edit").strip()
    if not title:
        console.print("Note title cannot be empty.", style="red")
        return

    # Find the existing note
    existing_note = next((n for n in notes if n["title"] == title), None)
    if not existing_note:
        console.print(f"Note '{title}' not found.", style="yellow")
        return

    console.print("\n[bright_blue bold]Current content:[/bright_blue bold]")
    console.print(existing_note["content"])
    console.print()

    new_content = Prompt.ask(
        "Enter new content (or press Enter to keep current)", default=existing_note["content"]
    ).strip()

    if new_content == existing_note["content"]:
        console.print("No changes made.", style="yellow")
        return

    try:
        if api.update_note(title, new_content):
            console.print(f"✓ Updated note: '{title}'", style="green")
        else:
            console.print(f"Failed to update note: '{title}'", style="red")
    except Exception as e:
        console.print(f"Failed to update note: {e}", style="red")


def handle_delete_note(api: PRTAPI) -> None:
    """Handle deleting a note."""
    # First show available notes
    notes = api.list_all_notes()
    if not notes:
        console.print("No notes available to delete.", style="yellow")
        return

    console.print("\n[bright_blue bold]Available Notes:[/bright_blue bold]")
    for note in notes:
        console.print(f"  • {note['title']} ({note['contact_count']} contacts)")

    title = Prompt.ask("\nEnter note title to delete").strip()
    if not title:
        console.print("Note title cannot be empty.", style="red")
        return

    # Confirm deletion
    if not Confirm.ask(
        f"Are you sure you want to delete note '{title}'? This will remove it from all contacts."
    ):
        console.print("Deletion cancelled.", style="yellow")
        return

    try:
        if api.delete_note(title):
            console.print(f"✓ Deleted note: '{title}'", style="green")
        else:
            console.print(f"Note '{title}' not found.", style="yellow")
    except Exception as e:
        console.print(f"Failed to delete note: {e}", style="red")
