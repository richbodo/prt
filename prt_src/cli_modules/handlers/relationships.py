"""
Relationship handling functions for PRT CLI.

Functions for managing and displaying relationships between contacts in the PRT system.
"""

from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.prompt import Prompt
from rich.table import Table

from ...api import PRTAPI
from ..ui.prompts import _get_valid_date
from ..ui.selection import _select_contact_with_search
from ..ui.selection import _validate_contact_id

console = Console()

# Configuration constants for relationship management
DEFAULT_PAGE_SIZE = 20  # Default number of items per page
MAX_DISPLAY_CONTACTS = 30  # Maximum contacts to show without pagination
TABLE_WIDTH_LIMIT = 120  # Maximum table width

# Security constants
MAX_CSV_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
MAX_CSV_IMPORT_ROWS = 10000  # Maximum relationships to import
EXPORT_FILE_PERMISSIONS = 0o600  # rw-------
EXPORT_DIR_PERMISSIONS = 0o750  # rwxr-x---


def handle_relationships_menu(api: PRTAPI) -> None:
    """Handle the relationship management sub-menu."""
    while True:
        # Create relationships menu
        table = Table.grid(padding=(0, 2))
        table.add_column(style="bright_blue bold", width=4)
        table.add_column(style="default")

        # Basic Operations
        table.add_row(
            "1.",
            "[bright_cyan bold]View Contact Relationships[/bright_cyan bold] - See all relationships for a contact",
        )
        table.add_row(
            "2.",
            "[bright_green bold]Add Relationship[/bright_green bold] - Create a new relationship between contacts",
        )
        table.add_row(
            "3.",
            "[bright_yellow bold]List Relationship Types[/bright_yellow bold] - View available relationship types",
        )
        table.add_row(
            "4.",
            "[bright_magenta bold]Delete Relationship[/bright_magenta bold] - Remove a relationship",
        )

        # Advanced Features (Part 3)
        table.add_row("", "")  # Separator
        table.add_row(
            "5.",
            "[blue bold]Relationship Analytics[/blue bold] - View network statistics and insights",
        )
        table.add_row(
            "6.",
            "[cyan bold]Find Mutual Connections[/cyan bold] - Discover shared contacts",
        )
        table.add_row(
            "7.",
            "[green bold]Find Connection Path[/green bold] - Find how two contacts are connected",
        )
        table.add_row(
            "8.",
            "[yellow bold]Export Relationships[/yellow bold] - Export to CSV or JSON",
        )
        table.add_row(
            "9.",
            "[magenta bold]Bulk Operations[/magenta bold] - Add multiple relationships at once",
        )
        table.add_row("b.", "[bright_red bold]Back to Main Menu[/bright_red bold]")

        console.print("\n")
        console.print(
            Panel(
                table,
                title="[bright_blue bold]Relationship Management[/bright_blue bold]",
                border_style="bright_blue",
            )
        )

        choice = Prompt.ask(
            "Select option", choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "b"], default="1"
        )

        if choice == "b":
            break
        elif choice == "1":
            handle_view_relationships(api)
        elif choice == "2":
            handle_add_relationship(api)
        elif choice == "3":
            handle_list_relationship_types(api)
        elif choice == "4":
            handle_delete_relationship(api)
        elif choice == "5":
            handle_relationship_analytics(api)
        elif choice == "6":
            handle_find_mutual_connections(api)
        elif choice == "7":
            handle_find_connection_path(api)
        elif choice == "8":
            handle_export_relationships(api)
        elif choice == "9":
            handle_bulk_relationships(api)


def handle_view_relationships(api: PRTAPI) -> None:
    """View all relationships for a specific contact."""
    try:
        # First, let user select a contact
        contacts = api.list_all_contacts()
        if not contacts:
            console.print("No contacts found in database.", style="yellow")
            return

        # Use the new search and select helper
        contact_id = _select_contact_with_search(contacts, "Select a Contact to View Relationships")
        if contact_id is None:
            return

        # Get relationships for this contact
        relationships = api.db.get_contact_relationships(contact_id)

        if not relationships:
            console.print(f"No relationships found for contact ID {contact_id}", style="yellow")
            return

        # Display relationships
        rel_table = Table(
            title=f"Relationships for Contact ID {contact_id}",
            show_header=True,
            header_style="bold magenta",
        )
        rel_table.add_column("Type", style="cyan", width=20)
        rel_table.add_column("Related Contact", style="green", width=30)
        rel_table.add_column("Email", style="yellow", width=30)
        rel_table.add_column("Start Date", style="blue", width=12)
        rel_table.add_column("End Date", style="red", width=12)

        for rel in relationships:
            rel_table.add_row(
                rel["type"],
                rel["other_contact_name"],
                rel.get("other_contact_email", "N/A") or "N/A",
                str(rel.get("start_date", "")) or "-",
                str(rel.get("end_date", "")) or "-",
            )

        console.print(rel_table)
        console.print(f"\nTotal relationships: {len(relationships)}", style="green")

    except Exception as e:
        console.print(f"Error viewing relationships: {e}", style="red")


def handle_add_relationship(api: PRTAPI) -> None:
    """Add a new relationship between two contacts."""
    try:
        # Get available relationship types
        rel_types = api.db.list_relationship_types()

        # Display relationship types
        type_table = Table(
            title="Available Relationship Types", show_header=True, header_style="bold magenta"
        )
        type_table.add_column("Type", style="cyan", width=20)
        type_table.add_column("Description", style="green", width=40)
        type_table.add_column("Inverse", style="yellow", width=20)

        for rt in rel_types:
            type_table.add_row(rt["type_key"], rt["description"], rt.get("inverse_type_key", "-"))

        console.print(type_table)

        # Get relationship type
        type_keys = [rt["type_key"] for rt in rel_types]
        rel_type = Prompt.ask("Enter relationship type", choices=type_keys)

        # Get contacts
        contacts = api.list_all_contacts()
        if len(contacts) < 2:
            console.print("Need at least 2 contacts to create a relationship.", style="yellow")
            return

        # Get first contact with search and validation
        console.print("\nSelect the first contact:", style="cyan")
        from_id = _select_contact_with_search(contacts, "Select First Contact")
        if from_id is None:
            return

        # Get second contact with search and validation
        console.print("\nSelect the second contact:", style="cyan")
        to_id = _select_contact_with_search(contacts, "Select Second Contact")
        if to_id is None:
            return

        if from_id == to_id:
            console.print("Cannot create relationship with same contact", style="red")
            return

        # Check if relationship already exists
        existing_relationships = api.db.get_contact_relationships(from_id)
        duplicate_exists = any(
            rel["other_contact_id"] == to_id and rel["type"] == rel_type
            for rel in existing_relationships
        )

        if duplicate_exists:
            console.print(
                f"⚠️  A '{rel_type}' relationship already exists between these contacts.",
                style="yellow",
            )
            if not Confirm.ask("Do you want to continue anyway?", default=False):
                console.print("Relationship creation cancelled.", style="yellow")
                return

        # Get start date with validation and retry
        start_date = _get_valid_date("Enter start date (YYYY-MM-DD) or press Enter to skip")

        # Create the relationship
        api.db.create_contact_relationship(from_id, to_id, rel_type, start_date=start_date)

        # Get the selected relationship type details
        selected_type = next((rt for rt in rel_types if rt["type_key"] == rel_type), None)

        # Show success message
        if selected_type and not selected_type.get("is_symmetrical"):
            console.print(
                f"✅ Created relationship: Contact {from_id} {rel_type} Contact {to_id}",
                style="green",
            )
            if selected_type.get("inverse_type_key"):
                console.print(
                    f"   Also created inverse: Contact {to_id} {selected_type['inverse_type_key']} Contact {from_id}",
                    style="green",
                )
        else:
            console.print(
                f"✅ Created symmetrical relationship: {rel_type} between contacts {from_id} and {to_id}",
                style="green",
            )

    except Exception as e:
        console.print(f"Error adding relationship: {e}", style="red")


def handle_list_relationship_types(api: PRTAPI) -> None:
    """List all available relationship types."""
    try:
        rel_types = api.db.list_relationship_types()

        if not rel_types:
            console.print("No relationship types found", style="yellow")
            return

        # Display relationship types
        table = Table(title="Relationship Types", show_header=True, header_style="bold magenta")
        table.add_column("Type Key", style="cyan", width=20)
        table.add_column("Description", style="green", width=35)
        table.add_column("Inverse Type", style="yellow", width=20)
        table.add_column("Symmetrical", style="blue", width=12)

        for rt in rel_types:
            table.add_row(
                rt["type_key"],
                rt["description"],
                rt.get("inverse_type_key", "-"),
                "Yes" if rt.get("is_symmetrical") else "No",
            )

        console.print(table)
        console.print(f"\nTotal relationship types: {len(rel_types)}", style="green")

    except Exception as e:
        console.print(f"Error listing relationship types: {e}", style="red")


def handle_delete_relationship(api: PRTAPI) -> None:
    """Delete a relationship between two contacts."""
    try:
        # First show a contact to see their relationships
        console.print("First, select a contact to view their relationships:", style="cyan")

        contacts = api.list_all_contacts()
        if not contacts:
            console.print("No contacts found in database.", style="yellow")
            return

        # Use search and select helper
        contact_id = _select_contact_with_search(contacts, "Select a Contact to View Relationships")
        if contact_id is None:
            return

        # Get relationships
        relationships = api.db.get_contact_relationships(contact_id)

        if not relationships:
            console.print(f"No relationships found for contact ID {contact_id}", style="yellow")
            return

        # Display relationships with indices
        rel_table = Table(
            title=f"Relationships for Contact ID {contact_id}",
            show_header=True,
            header_style="bold magenta",
        )
        rel_table.add_column("#", style="cyan", width=5)
        rel_table.add_column("Type", style="green", width=20)
        rel_table.add_column("Related Contact", style="yellow", width=30)
        rel_table.add_column("Contact ID", style="blue", width=10)

        for idx, rel in enumerate(relationships, 1):
            rel_table.add_row(
                str(idx), rel["type"], rel["other_contact_name"], str(rel["other_contact_id"])
            )

        console.print(rel_table)

        # Select relationship to delete
        rel_num = Prompt.ask(f"Enter relationship number to delete (1-{len(relationships)})")
        try:
            rel_num = int(rel_num)
            if rel_num < 1 or rel_num > len(relationships):
                console.print("Invalid selection", style="red")
                return
        except ValueError:
            console.print("Invalid number", style="red")
            return

        selected_rel = relationships[rel_num - 1]

        # Confirm deletion
        confirm = Confirm.ask(
            f"Delete relationship: {selected_rel['type']} with {selected_rel['other_contact_name']}?",
            default=False,
        )

        if confirm:
            # Delete the relationship
            api.db.delete_contact_relationship(
                contact_id, selected_rel["other_contact_id"], selected_rel["type"]
            )
            console.print("✅ Relationship deleted successfully", style="green")
        else:
            console.print("Deletion cancelled", style="yellow")

    except Exception as e:
        console.print(f"Error deleting relationship: {e}", style="red")


def handle_relationship_analytics(api: PRTAPI) -> None:
    """Display comprehensive relationship analytics."""
    try:
        console.print("\n[bright_blue bold]Relationship Analytics[/bright_blue bold]", style="blue")
        analytics = api.db.get_relationship_analytics()

        if not analytics:
            console.print("No analytics data available.", style="yellow")
            return

        # Display summary statistics
        stats_table = Table(
            title="Network Statistics", show_header=True, header_style="bold magenta"
        )
        stats_table.add_column("Metric", style="cyan", width=35)
        stats_table.add_column("Value", style="green", width=20)

        stats_table.add_row("Total Contacts", str(analytics["total_contacts"]))
        stats_table.add_row("Total Relationships", str(analytics["total_relationships"]))
        stats_table.add_row(
            "Average Relationships per Contact", str(analytics["average_relationships_per_contact"])
        )
        stats_table.add_row(
            "Isolated Contacts (no relationships)", str(analytics["isolated_contacts"])
        )

        console.print(stats_table)

        # Display most connected contacts
        if analytics["most_connected"]:
            console.print("\n[bright_cyan bold]Most Connected Contacts[/bright_cyan bold]")
            connected_table = Table(show_header=True, header_style="bold green")
            connected_table.add_column("Rank", style="cyan", width=6)
            connected_table.add_column("Name", style="green", width=25)
            connected_table.add_column("Email", style="yellow", width=30)
            connected_table.add_column("Connections", style="blue", width=12)

            for i, contact in enumerate(analytics["most_connected"], 1):
                connected_table.add_row(
                    str(i),
                    contact["name"] or "N/A",
                    contact["email"] or "N/A",
                    str(contact["relationship_count"]),
                )

            console.print(connected_table)

        # Display relationship type distribution
        if analytics["type_distribution"]:
            console.print(
                "\n[bright_yellow bold]Relationship Type Distribution[/bright_yellow bold]"
            )
            type_table = Table(show_header=True, header_style="bold yellow")
            type_table.add_column("Type", style="cyan", width=20)
            type_table.add_column("Description", style="green", width=30)
            type_table.add_column("Count", style="blue", width=10)

            for rel_type in analytics["type_distribution"]:
                type_table.add_row(
                    rel_type["type"], rel_type["description"], str(rel_type["count"])
                )

            console.print(type_table)

    except Exception as e:
        console.print(f"Error getting analytics: {e}", style="red")


def handle_find_mutual_connections(api: PRTAPI) -> None:
    """Find mutual connections between two contacts."""
    try:
        contacts = api.list_all_contacts()
        if len(contacts) < 2:
            console.print("Need at least 2 contacts to find mutual connections.", style="yellow")
            return

        console.print("\n[bright_blue bold]Find Mutual Connections[/bright_blue bold]")
        console.print("Select two contacts to find their mutual connections:", style="cyan")

        # Select first contact
        console.print("\nSelect the first contact:")
        contact1_id = _select_contact_with_search(contacts, "Select First Contact")
        if contact1_id is None:
            return

        # Select second contact
        console.print("\nSelect the second contact:")
        contact2_id = _select_contact_with_search(contacts, "Select Second Contact")
        if contact2_id is None:
            return

        if contact1_id == contact2_id:
            console.print("Please select two different contacts.", style="red")
            return

        # Find mutual connections
        mutual = api.db.find_mutual_connections(contact1_id, contact2_id)

        if not mutual:
            console.print(
                f"\nNo mutual connections found between contacts {contact1_id} and {contact2_id}.",
                style="yellow",
            )
            return

        # Display mutual connections
        console.print(f"\n[green]Found {len(mutual)} mutual connection(s):[/green]")

        table = Table(title="Mutual Connections", show_header=True, header_style="bold magenta")
        table.add_column("ID", style="cyan", width=8)
        table.add_column("Name", style="green", width=30)
        table.add_column("Email", style="yellow", width=40)
        table.add_column("Phone", style="blue", width=20)

        for contact in mutual:
            table.add_row(
                str(contact["id"]),
                contact["name"] or "N/A",
                contact["email"] or "N/A",
                contact.get("phone", "N/A") or "N/A",
            )

        console.print(table)

    except Exception as e:
        console.print(f"Error finding mutual connections: {e}", style="red")


def handle_find_connection_path(api: PRTAPI) -> None:
    """Find the shortest path between two contacts."""
    try:
        contacts = api.list_all_contacts()
        if len(contacts) < 2:
            console.print("Need at least 2 contacts to find a connection path.", style="yellow")
            return

        console.print("\n[bright_blue bold]Find Connection Path[/bright_blue bold]")
        console.print("Find how two contacts are connected through relationships:", style="cyan")

        # Select first contact
        console.print("\nSelect the starting contact:")
        from_id = _select_contact_with_search(contacts, "Select Starting Contact")
        if from_id is None:
            return

        # Select second contact
        console.print("\nSelect the destination contact:")
        to_id = _select_contact_with_search(contacts, "Select Destination Contact")
        if to_id is None:
            return

        if from_id == to_id:
            console.print("Please select two different contacts.", style="red")
            return

        # Find path
        console.print("\nSearching for connection path...", style="blue")
        path = api.db.find_relationship_path(from_id, to_id)

        if not path:
            console.print(
                f"\n❌ No connection path found between contacts {from_id} and {to_id}.",
                style="yellow",
            )
            console.print(
                "These contacts are not connected through any relationships.", style="dim"
            )
            return

        # Display path
        console.print(
            f"\n✅ [green]Found connection path with {len(path) - 1} degree(s) of separation:[/green]"
        )

        # Get contact details for the path
        path_contacts = []
        for contact_id in path:
            contact = next((c for c in contacts if c["id"] == contact_id), None)
            if contact:
                path_contacts.append(contact)

        # Display the path
        for i, contact in enumerate(path_contacts):
            if i == 0:
                console.print(f"  🚀 Start: {contact['name']} (ID: {contact['id']})", style="cyan")
            elif i == len(path_contacts) - 1:
                console.print(f"  🎯 End: {contact['name']} (ID: {contact['id']})", style="green")
            else:
                console.print(f"  → Via: {contact['name']} (ID: {contact['id']})", style="yellow")

        console.print(f"\nDegrees of separation: {len(path) - 1}", style="blue")

    except Exception as e:
        console.print(f"Error finding connection path: {e}", style="red")


def handle_export_relationships(api: PRTAPI) -> None:
    """Export all relationships to file."""
    import os
    import re

    try:
        console.print("\n[bright_blue bold]Export Relationships[/bright_blue bold]")

        # Choose export format
        format_choice = Prompt.ask("Select export format", choices=["json", "csv"], default="json")

        # Get export data
        if format_choice == "csv":
            data = api.db.export_relationships(format="csv")
            filename = "relationships_export.csv"
        else:
            data = api.db.export_relationships(format="json")
            filename = "relationships_export.json"

        if not data:
            console.print("No relationships to export.", style="yellow")
            return

        # Create exports directory if it doesn't exist with secure permissions
        export_dir = Path("exports")
        export_dir.mkdir(exist_ok=True, mode=EXPORT_DIR_PERMISSIONS)

        # Validate export directory is not a symlink (prevent directory traversal)
        if export_dir.is_symlink():
            console.print("Error: Export directory cannot be a symbolic link.", style="red")
            return

        # Ensure export directory is within current working directory
        try:
            export_dir = export_dir.resolve()
            cwd = Path.cwd()
            export_dir.relative_to(cwd)  # Will raise ValueError if not relative
        except ValueError:
            console.print("Error: Export directory must be within current directory.", style="red")
            return

        # Sanitize filename - remove any path components and dangerous characters
        safe_filename = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)

        # Add timestamp to filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_filename = f"{timestamp}_{safe_filename}"
        export_path = export_dir / export_filename

        # Final path validation
        if export_path.is_symlink():
            console.print("Error: Cannot write to symbolic link.", style="red")
            return

        # Write file with explicit permissions
        if format_choice == "csv":
            # Create file with restricted permissions first
            export_path.touch(mode=EXPORT_FILE_PERMISSIONS)
            with open(export_path, "w", encoding="utf-8") as f:
                f.write(data)
        else:
            import json

            # Create file with restricted permissions first
            export_path.touch(mode=EXPORT_FILE_PERMISSIONS)
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        # Ensure file permissions are set correctly (in case umask overrode)
        os.chmod(export_path, EXPORT_FILE_PERMISSIONS)

        # Show summary
        if format_choice == "json":
            console.print(f"✅ Exported {len(data)} relationships to: {export_path}", style="green")
        else:
            # Count CSV lines (minus header)
            line_count = data.count("\n") - 1
            console.print(
                f"✅ Exported {line_count} relationships to: {export_path}", style="green"
            )

        console.print(f"📁 File location: {export_path.absolute()}", style="blue")

    except Exception as e:
        console.print(f"Error exporting relationships: {e}", style="red")


def handle_bulk_relationships(api: PRTAPI) -> None:
    """Handle bulk relationship operations."""
    try:
        console.print("\n[bright_blue bold]Bulk Relationship Operations[/bright_blue bold]")

        # Choose operation type
        op_table = Table.grid(padding=(0, 2))
        op_table.add_column(style="cyan", width=4)
        op_table.add_column(style="default")

        op_table.add_row("1.", "Add multiple relationships of the same type")
        op_table.add_row("2.", "Import relationships from CSV file")
        op_table.add_row("3.", "Create group relationships (one contact to many)")

        console.print(op_table)

        op_choice = Prompt.ask("Select operation", choices=["1", "2", "3"], default="1")

        if op_choice == "1":
            _handle_bulk_same_type(api)
        elif op_choice == "2":
            _handle_import_relationships_csv(api)
        elif op_choice == "3":
            _handle_group_relationships(api)

    except Exception as e:
        console.print(f"Error in bulk operations: {e}", style="red")


def _handle_bulk_same_type(api: PRTAPI) -> None:
    """Add multiple relationships of the same type."""
    # Get relationship type
    rel_types = api.db.list_relationship_types()

    type_table = Table(
        title="Available Relationship Types", show_header=True, header_style="bold magenta"
    )
    type_table.add_column("Type", style="cyan", width=20)
    type_table.add_column("Description", style="green", width=40)

    for rt in rel_types:
        type_table.add_row(rt["type_key"], rt["description"])

    console.print(type_table)

    type_keys = [rt["type_key"] for rt in rel_types]
    rel_type = Prompt.ask("Enter relationship type for all", choices=type_keys)

    # Get contacts
    contacts = api.list_all_contacts()
    if len(contacts) < 2:
        console.print("Need at least 2 contacts.", style="yellow")
        return

    relationships = []
    console.print("\nEnter relationship pairs (or 'done' to finish):", style="cyan")

    while True:
        pair = Prompt.ask("Enter pair (e.g., '1,2' for IDs 1→2) or 'done'")
        if pair.lower() == "done":
            break

        try:
            from_id, to_id = map(int, pair.split(","))

            # Validate IDs
            if not _validate_contact_id(from_id, contacts):
                console.print(f"Contact ID {from_id} not found.", style="red")
                continue
            if not _validate_contact_id(to_id, contacts):
                console.print(f"Contact ID {to_id} not found.", style="red")
                continue
            if from_id == to_id:
                console.print("Cannot create relationship with same contact.", style="red")
                continue

            relationships.append(
                {"from_contact_id": from_id, "to_contact_id": to_id, "type_key": rel_type}
            )
            console.print(f"  Added: {from_id} → {to_id}", style="green")

        except ValueError:
            console.print("Invalid format. Use 'ID1,ID2' (e.g., '1,2')", style="red")

    if not relationships:
        console.print("No relationships to create.", style="yellow")
        return

    # Confirm and create
    if Confirm.ask(f"Create {len(relationships)} relationships?"):
        result = api.db.bulk_create_relationships(relationships)

        console.print(f"\n✅ Created: {result['created']} relationships", style="green")
        if result["skipped"] > 0:
            console.print(f"⚠️  Skipped: {result['skipped']} (already exist)", style="yellow")
        if result["errors"]:
            console.print(f"❌ Errors: {len(result['errors'])}", style="red")
            for error in result["errors"][:5]:  # Show first 5 errors
                console.print(f"  - {error}", style="red")


def _handle_import_relationships_csv(api: PRTAPI) -> None:
    """Import relationships from CSV file with security validations."""
    from pathlib import Path

    # Use global security constants

    csv_path = Prompt.ask("Enter path to CSV file")

    try:
        csv_file = Path(csv_path).resolve()  # Resolve to absolute path
    except (OSError, RuntimeError) as e:
        console.print(f"Invalid file path: {e}", style="red")
        return

    # Security validations
    if not csv_file.exists():
        console.print(f"File not found: {csv_path}", style="red")
        return

    if not csv_file.is_file():
        console.print(
            "Error: Path must be a regular file, not a directory or special file.", style="red"
        )
        return

    if csv_file.is_symlink():
        console.print("Error: Cannot read from symbolic links for security reasons.", style="red")
        return

    # Check file size
    file_size = csv_file.stat().st_size
    if file_size > MAX_CSV_FILE_SIZE:
        console.print(
            f"Error: File too large ({file_size:,} bytes). Maximum size is {MAX_CSV_FILE_SIZE:,} bytes.",
            style="red",
        )
        return

    if file_size == 0:
        console.print("Error: File is empty.", style="red")
        return

    try:
        import csv
        import re

        relationships = []
        row_count = 0
        errors = []

        # Validate allowed characters in type_key
        type_key_pattern = re.compile(r"^[a-zA-Z0-9_-]+$")

        # Get valid relationship types for validation
        valid_types = {rt["type_key"] for rt in api.db.list_relationship_types()}

        # Get valid contact IDs for validation
        valid_contact_ids = {c["id"] for c in api.list_all_contacts()}

        with open(csv_file, encoding="utf-8") as f:
            # Use csv.Sniffer to detect dialect, but limit sample size
            sample = f.read(8192)  # Read first 8KB for dialect detection
            f.seek(0)

            try:
                dialect = csv.Sniffer().sniff(sample)
                reader = csv.DictReader(f, dialect=dialect)
            except csv.Error:
                # Fall back to default dialect if detection fails
                reader = csv.DictReader(f)

            # Validate required columns
            if reader.fieldnames:
                required_fields = {"from_id", "to_id", "type"}
                missing_fields = required_fields - set(reader.fieldnames)
                if missing_fields:
                    console.print(
                        f"Error: CSV missing required columns: {missing_fields}", style="red"
                    )
                    return

            for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is line 1)
                row_count += 1

                # Enforce row limit
                if row_count > MAX_CSV_IMPORT_ROWS:
                    console.print(
                        f"Warning: Reached maximum row limit ({MAX_CSV_IMPORT_ROWS}). Stopping import.",
                        style="yellow",
                    )
                    break

                try:
                    # Validate and sanitize from_id
                    from_id = int(row.get("from_id", "").strip())
                    if from_id not in valid_contact_ids:
                        errors.append(f"Row {row_num}: Invalid from_id {from_id}")
                        continue

                    # Validate and sanitize to_id
                    to_id = int(row.get("to_id", "").strip())
                    if to_id not in valid_contact_ids:
                        errors.append(f"Row {row_num}: Invalid to_id {to_id}")
                        continue

                    # Validate same contact check
                    if from_id == to_id:
                        errors.append(f"Row {row_num}: Cannot create self-relationship")
                        continue

                    # Validate and sanitize type_key
                    type_key = row.get("type", "").strip()
                    if not type_key_pattern.match(type_key):
                        errors.append(f"Row {row_num}: Invalid characters in type '{type_key}'")
                        continue

                    if type_key not in valid_types:
                        errors.append(f"Row {row_num}: Unknown relationship type '{type_key}'")
                        continue

                    relationships.append(
                        {
                            "from_contact_id": from_id,
                            "to_contact_id": to_id,
                            "type_key": type_key,
                        }
                    )

                except (ValueError, KeyError) as e:
                    errors.append(f"Row {row_num}: {str(e)}")
                    continue

        if not relationships:
            console.print("No valid relationships found in CSV.", style="yellow")
            if errors:
                console.print(f"\nErrors found ({len(errors)} total):", style="red")
                for error in errors[:10]:  # Show first 10 errors
                    console.print(f"  - {error}", style="red")
                if len(errors) > 10:
                    console.print(f"  ... and {len(errors) - 10} more errors", style="red")
            return

        console.print(f"Found {len(relationships)} valid relationships in CSV", style="green")
        if errors:
            console.print(f"Skipped {len(errors)} invalid rows", style="yellow")
            if Confirm.ask("Show error details?"):
                for error in errors[:20]:  # Show first 20 errors
                    console.print(f"  - {error}", style="yellow")
                if len(errors) > 20:
                    console.print(f"  ... and {len(errors) - 20} more errors", style="yellow")

        if Confirm.ask(f"Import {len(relationships)} valid relationships?"):
            result = api.db.bulk_create_relationships(relationships)

            console.print(f"\n✅ Created: {result['created']} relationships", style="green")
            if result["skipped"] > 0:
                console.print(f"⚠️  Skipped: {result['skipped']} (already exist)", style="yellow")
            if result["errors"]:
                console.print(f"❌ Errors: {len(result['errors'])}", style="red")

    except PermissionError:
        console.print(f"Error: Permission denied reading file: {csv_path}", style="red")
    except UnicodeDecodeError:
        console.print(f"Error: File is not valid UTF-8 text: {csv_path}", style="red")
    except csv.Error as e:
        console.print(f"Error parsing CSV: {e}", style="red")
    except Exception as e:
        console.print(f"Unexpected error reading CSV: {e}", style="red")


def _handle_group_relationships(api: PRTAPI) -> None:
    """Create relationships from one contact to many."""
    contacts = api.list_all_contacts()
    if len(contacts) < 2:
        console.print("Need at least 2 contacts.", style="yellow")
        return

    # Select source contact
    console.print("\nSelect the source contact:")
    source_id = _select_contact_with_search(contacts, "Select Source Contact")
    if source_id is None:
        return

    # Get relationship type
    rel_types = api.db.list_relationship_types()
    type_keys = [rt["type_key"] for rt in rel_types]
    rel_type = Prompt.ask("Enter relationship type", choices=type_keys)

    # Select target contacts
    console.print("\nEnter target contact IDs (comma-separated, e.g., '2,3,4'):")
    targets_str = Prompt.ask("Target IDs")

    try:
        target_ids = [int(id_str.strip()) for id_str in targets_str.split(",")]
    except ValueError:
        console.print("Invalid ID format.", style="red")
        return

    # Validate and create relationships
    relationships = []
    for target_id in target_ids:
        if not _validate_contact_id(target_id, contacts):
            console.print(f"Contact ID {target_id} not found, skipping.", style="yellow")
            continue
        if target_id == source_id:
            console.print(f"Skipping self-relationship for {source_id}.", style="yellow")
            continue

        relationships.append(
            {"from_contact_id": source_id, "to_contact_id": target_id, "type_key": rel_type}
        )

    if not relationships:
        console.print("No valid relationships to create.", style="yellow")
        return

    console.print(f"\nWill create {len(relationships)} relationships from contact {source_id}")

    if Confirm.ask("Proceed?"):
        result = api.db.bulk_create_relationships(relationships)

        console.print(f"\n✅ Created: {result['created']} relationships", style="green")
        if result["skipped"] > 0:
            console.print(f"⚠️  Skipped: {result['skipped']} (already exist)", style="yellow")
