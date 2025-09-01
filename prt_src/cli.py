"""
PRT - Personal Relationship Toolkit CLI

This is the main CLI interface for PRT. It automatically detects if setup is needed
and provides a unified interface for all operations.
"""

from datetime import date
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text

from migrations.setup_database import initialize_database, setup_database

from .api import PRTAPI
from .config import config_path, data_dir, load_config
from .db import create_database
from .google_contacts import fetch_contacts
from .google_takeout import find_takeout_files, parse_takeout_contacts
from .llm_ollama import start_ollama_chat

# Encryption imports removed as part of Issue #41

app = typer.Typer(help="Personal Relationship Toolkit (PRT)")
console = Console()

# Required configuration fields
REQUIRED_FIELDS = ["db_username", "db_password", "db_path"]

# Configuration constants for relationship management
DEFAULT_PAGE_SIZE = 20  # Default number of items per page
MAX_DISPLAY_CONTACTS = 30  # Maximum contacts to show without pagination
TABLE_WIDTH_LIMIT = 120  # Maximum table width

# Security constants
MAX_CSV_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
MAX_CSV_IMPORT_ROWS = 10000  # Maximum relationships to import
EXPORT_FILE_PERMISSIONS = 0o600  # rw-------
EXPORT_DIR_PERMISSIONS = 0o750  # rwxr-x---


def show_empty_database_guidance():
    """Show helpful guidance when database is empty."""
    guidance_text = Text()
    guidance_text.append("📭 No contacts found in your database.\n\n", style="yellow")
    guidance_text.append("🚀 To get started with PRT:\n", style="bold blue")
    guidance_text.append("   1. Import Google Takeout (option 3)\n", style="cyan")
    guidance_text.append("   2. This will populate your database with contacts\n", style="cyan")
    guidance_text.append(
        "   3. Then you can view, search, and manage relationships\n\n", style="cyan"
    )
    guidance_text.append(
        "💡 PRT works best when you have contacts to build relationships with!", style="green"
    )

    console.print(Panel(guidance_text, title="Getting Started", border_style="yellow"))


def handle_database_error(error, operation: str):
    """Handle database errors with helpful messages."""
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
        console.print(
            "\n💡 If this persists, try restarting PRT or running setup again.", style="yellow"
        )


def check_database_health(api: PRTAPI) -> dict:
    """Check database health and return status information."""
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


def setup_debug_mode():
    """Set up debug mode with fixture data."""
    from tests.fixtures import setup_test_database

    # Create a temporary database in the data directory
    debug_db_path = data_dir() / "debug.db"

    # Remove existing debug database if it exists
    if debug_db_path.exists():
        debug_db_path.unlink()

    console.print(f"🔧 Creating debug database at: {debug_db_path}", style="blue")

    # Create database with fixture data
    from .db import create_database

    db = create_database(debug_db_path)
    fixtures = setup_test_database(db)

    console.print("📊 Loaded fixture data:", style="green")
    console.print(f"   • {len(fixtures['contacts'])} contacts with profile images", style="green")
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
    console.print("\n" + "=" * 60)
    console.print("PRT Setup Wizard", style="bold blue")
    console.print("=" * 60)
    console.print()
    console.print("Welcome to PRT! Let's get you set up.", style="green")
    console.print()

    try:
        # Run the setup process
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
        console.print("You can now use PRT to manage your personal relationships!", style="green")

        return config

    except Exception as e:
        console.print(f"✗ Setup failed: {e}", style="bold red")
        console.print("Please check the error and try again.", style="yellow")
        raise typer.Exit(1)


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
                if len(note_content) > 100:
                    if Confirm.ask("   Show full note?", default=False):
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


def paginate_results(items: list, items_per_page: int = 24) -> None:
    """Paginate through a list of items with navigation."""
    if not items:
        return

    total_pages = (len(items) + items_per_page - 1) // items_per_page
    current_page = 0

    while True:
        start_idx = current_page * items_per_page
        end_idx = min(start_idx + items_per_page, len(items))
        page_items = items[start_idx:end_idx]

        # Display current page items
        for item in page_items:
            if callable(item):
                item()  # Execute function to display item
            else:
                console.print(item)

        # Show pagination info
        console.print(
            f"\nPage {current_page + 1} of {total_pages} | Showing {start_idx + 1}-{end_idx} of {len(items)} results",
            style="dim",
        )

        # Build navigation options dynamically
        nav_choices = []
        nav_descriptions = []

        if current_page > 0:
            nav_choices.append("p")
            nav_descriptions.append("(p)revious")

        if current_page < total_pages - 1:
            nav_choices.append("n")
            nav_descriptions.append("(n)ext")

        nav_choices.append("e")  # export
        nav_descriptions.append("(e)xport")

        nav_choices.append("q")  # quit
        nav_descriptions.append("(q)uit")

        # Create a compact, terminal-friendly prompt
        nav_text = " | ".join(nav_descriptions)
        prompt_text = f"Navigation: {nav_text}"

        # Use a shorter prompt if it's too long
        if len(prompt_text) > 60:
            nav_short = "/".join([f"{choice}" for choice in nav_choices])
            prompt_text = f"Options [{nav_short}]"

        choice = Prompt.ask(prompt_text, choices=nav_choices, default="q")

        if choice == "q":
            break
        elif choice == "n" and current_page < total_pages - 1:
            current_page += 1
        elif choice == "p" and current_page > 0:
            current_page -= 1
        elif choice == "e":
            return "export"  # Signal to calling function to handle export


def offer_directory_generation(export_dir: Path) -> None:
    """Offer to generate an interactive directory from the export."""
    import subprocess
    import sys
    from pathlib import Path

    console.print()

    # Ask user if they want to generate interactive directory
    generate = Prompt.ask(
        "🌐 Generate interactive directory from this export?", choices=["y", "n"], default="y"
    )

    if generate == "y":
        try:
            # Create directories subdirectory in the project root
            directories_dir = Path("directories")
            directories_dir.mkdir(exist_ok=True)

            # Generate timestamp-based output directory name
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = directories_dir / f"directory_{timestamp}"

            console.print("🔧 Generating interactive directory...", style="blue")

            # Run make_directory.py tool
            tools_dir = Path(__file__).parent.parent / "tools"
            make_directory_script = tools_dir / "make_directory.py"

            # Run the command - pass the export directory, not the JSON file
            cmd = [
                sys.executable,
                str(make_directory_script),
                "generate",
                str(export_dir),
                "--output",
                str(output_dir),
                "--force",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())

            if result.returncode == 0:
                # Success! Show the local file URL
                index_file = output_dir / "index.html"
                if index_file.exists():
                    file_url = f"file://{index_file.absolute()}"
                    console.print("✅ Interactive directory generated!", style="bold green")
                    console.print(f"🌐 Open in browser: {file_url}", style="blue")
                    console.print(f"📁 Directory location: {output_dir}", style="dim")
                else:
                    console.print(f"✅ Directory generated at: {output_dir}", style="green")
            else:
                console.print(f"❌ Error generating directory: {result.stderr}", style="red")

        except Exception as e:
            console.print(f"❌ Error running make_directory tool: {e}", style="red")

    console.print()


def export_search_results(
    api: PRTAPI, search_type: str, query: str, results: list, *, interactive: bool = True
) -> Path:
    """Export search results to JSON with timestamped folder and optional profile images."""
    import json
    from datetime import datetime
    from pathlib import Path

    # Create timestamped export directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_dir = Path("exports") / f"{search_type}_search_{timestamp}"
    export_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"📁 Creating export directory: {export_dir}", style="blue")

    # Clean results for JSON serialization (remove binary data)
    clean_results = clean_results_for_json(results)

    # Export JSON data
    export_data = {
        "export_info": {
            "search_type": search_type,
            "query": query,
            "timestamp": timestamp,
            "total_results": len(results),
            "search_request": {"type": search_type, "term": query, "executed_at": timestamp},
        },
        "results": clean_results,
    }

    json_file = export_dir / f"{search_type}_search_results.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

    console.print(
        f"💾 Exported {len(results)} {search_type} results to: {json_file}", style="green"
    )

    # Export profile images for contacts
    images_exported = export_profile_images_from_results(results, export_dir, timestamp)
    if images_exported > 0:
        console.print(f"🖼️  Exported {images_exported} profile images", style="green")

    # Create README for export
    create_export_readme(export_dir, search_type, query, len(results), images_exported)

    console.print(f"✅ Export complete! Check: {export_dir}", style="bold green")

    # Offer to generate interactive directory (only in interactive mode)
    if interactive:
        offer_directory_generation(export_dir)

    return export_dir


def clean_results_for_json(results: list) -> list:
    """Clean results for JSON serialization by removing binary data."""
    import copy

    clean_results = copy.deepcopy(results)

    def clean_item(item):
        if isinstance(item, dict):
            # Remove binary data but keep metadata and add image path
            if "profile_image" in item:
                item["has_profile_image"] = item["profile_image"] is not None
                if item["profile_image"] is not None:
                    # Add relative path to exported image
                    item["exported_image_path"] = f"profile_images/{item['id']}.jpg"
                del item["profile_image"]  # Remove binary data

            # Recursively clean nested dictionaries and lists
            for key, value in item.items():
                if isinstance(value, (dict, list)):
                    item[key] = clean_item(value)
        elif isinstance(item, list):
            return [clean_item(x) for x in item]

        return item

    return clean_item(clean_results)


def export_profile_images_from_results(results: list, export_dir: Path, timestamp: str) -> int:
    """Export profile images from any result structure (contacts, tags with contacts, notes with contacts)."""
    images_dir = export_dir / "profile_images"
    images_dir.mkdir(exist_ok=True)

    images_exported = 0
    contacts_to_process = []

    # Extract contacts from different result structures
    for result in results:
        if "associated_contacts" in result:
            # Tag or note search results
            contacts_to_process.extend(result["associated_contacts"])
        elif "id" in result and "name" in result:
            # Direct contact search results
            contacts_to_process.append(result)

    # Export images for all found contacts
    for contact in contacts_to_process:
        if contact.get("profile_image"):
            try:
                # Generate filename: contact_id.jpg
                contact_id = contact["id"]
                filename = f"{contact_id}.jpg"

                # Save image data
                image_path = images_dir / filename
                with open(image_path, "wb") as f:
                    f.write(contact["profile_image"])
                images_exported += 1

            except Exception as e:
                console.print(
                    f"Warning: Failed to export image for contact {contact['id']}: {e}",
                    style="yellow",
                )

    return images_exported


def create_export_readme(
    export_dir: Path, search_type: str, query: str, result_count: int, image_count: int
) -> None:
    """Create a README file explaining the export structure."""
    readme_content = f"""# PRT Search Export

## Export Information
- **Search Type**: {search_type}
- **Query**: "{query}"
- **Results**: {result_count} {search_type}
- **Profile Images**: {image_count} exported

## File Structure
```
{export_dir.name}/
├── README.md                           # This file
├── {search_type}_search_results.json   # Search results data
└── profile_images/                     # Profile images (if any)
    ├── 1.jpg                          # Contact ID 1's profile image
    ├── 4.jpg                          # Contact ID 4's profile image
    └── ...                            # Additional images
```

## How to Associate Contacts with Images

### Method 1: Using exported_image_path (Recommended)
Each contact in the JSON includes an `exported_image_path` field:
```json
{{
  "id": 4,
  "name": "Alice Johnson",
  "exported_image_path": "profile_images/4.jpg",
  "has_profile_image": true
}}
```

### Method 2: Using Contact ID
Profile images are named using the contact ID:
- Contact ID 1 → `profile_images/1.jpg`
- Contact ID 4 → `profile_images/4.jpg`

## JSON Fields Explained
- `has_profile_image`: Boolean indicating if contact has a profile image
- `exported_image_path`: Relative path to the exported image file
- `profile_image_filename`: Original filename from the database
- `profile_image_mime_type`: Image format (e.g., "image/jpeg")

## Usage Examples
```python
import json

# Load the JSON data
with open('{search_type}_search_results.json') as f:
    data = json.load(f)

# Access contact image
for contact in data['results']:
    if contact['has_profile_image']:
        image_path = contact['exported_image_path']
        print(f"{{contact['name']}}: {{image_path}}")
```

Generated: {export_dir.name.split('_')[-1]}
"""

    readme_file = export_dir / "README.md"
    with open(readme_file, "w", encoding="utf-8") as f:
        f.write(readme_content)


def export_contact_profile_images(
    api: PRTAPI, contacts: list, export_dir: Path, timestamp: str
) -> int:
    """Export profile images for contacts. (Deprecated - use export_profile_images_from_results)"""
    return export_profile_images_from_results(contacts, export_dir, timestamp)


def show_full_note(title: str, content: str) -> None:
    """Show full note content with scrolling capability."""
    from rich.text import Text

    note_text = Text()
    note_text.append(f"Note: {title}\n", style="bold cyan")
    note_text.append("=" * 50 + "\n", style="blue")
    note_text.append(content, style="white")

    console.print(Panel(note_text, title=f"Full Note: {title}", border_style="cyan"))
    Prompt.ask("\nPress Enter to return to search results")


def handle_import_google_takeout(api: PRTAPI, config: dict) -> None:
    """Handle importing contacts from Google Takeout zip file."""
    from pathlib import Path

    from rich.prompt import Prompt

    console.print("📦 Google Takeout Import", style="bold blue")
    console.print()
    console.print("This will import contacts from a Google Takeout zip file.", style="white")
    console.print("To get your Google Takeout:", style="yellow")
    console.print("  1. Go to https://takeout.google.com", style="cyan")
    console.print("  2. Select 'Contacts' only", style="cyan")
    console.print("  3. Choose 'Export once' and download the zip file", style="cyan")
    console.print()

    # First, try to find existing takeout files in common locations
    search_paths = [
        Path.home() / "Downloads",  # Most common location
        Path.cwd(),  # Current directory
        data_dir(),  # PRT data directory
    ]

    existing_files = []
    for search_path in search_paths:
        if search_path.exists():
            existing_files.extend(find_takeout_files(search_path))

    if existing_files:
        console.print(f"🔍 Found {len(existing_files)} potential takeout file(s):", style="green")
        for i, file_path in enumerate(existing_files, 1):
            console.print(f"  {i}. {file_path.name}", style="cyan")
        console.print(f"  {len(existing_files) + 1}. Browse for a different file", style="cyan")
        console.print()

        choice = Prompt.ask(
            "Select a file to import",
            choices=[str(i) for i in range(1, len(existing_files) + 2)],
            default="1",
        )

        if int(choice) <= len(existing_files):
            takeout_path = existing_files[int(choice) - 1]
        else:
            takeout_path = Path(Prompt.ask("Enter the full path to your Google Takeout zip file"))
    else:
        takeout_path = Path(Prompt.ask("Enter the full path to your Google Takeout zip file"))

    if not takeout_path.exists():
        console.print(f"❌ File not found: {takeout_path}", style="red")
        return

    if not takeout_path.suffix.lower() == ".zip":
        console.print("❌ File must be a zip file", style="red")
        return

    console.print(f"📂 Processing: {takeout_path.name}", style="blue")

    try:
        # Parse the takeout file
        contacts, info = parse_takeout_contacts(takeout_path)

        if "error" in info:
            console.print(f"❌ Error parsing takeout file: {info['error']}", style="red")
            return

        if not contacts:
            console.print("⚠️  No contacts found in the takeout file", style="yellow")
            return

        # Show preview with de-duplication info
        console.print(f"📊 Found {info['contact_count']} contacts", style="green")
        if "raw_contact_count" in info and info["raw_contact_count"] != info["contact_count"]:
            console.print(
                f"🔧 Deduplicated from {info['raw_contact_count']} raw contacts", style="blue"
            )
            console.print(f"🗑️  Removed {info['duplicates_removed']} duplicates", style="blue")
        console.print(
            f"🖼️  {info['contacts_with_images']} contacts have profile images", style="green"
        )
        console.print()

        if not Confirm.ask(f"Import {len(contacts)} contacts into your database?"):
            console.print("Import cancelled", style="yellow")
            return

        # Import contacts
        console.print("💾 Importing contacts...", style="blue")
        success = api.insert_contacts(contacts)

        if success:
            console.print(f"✅ Successfully imported {len(contacts)} contacts!", style="bold green")
            console.print(
                f"🖼️  {info['contacts_with_images']} contacts include profile images", style="green"
            )
            console.print()
            console.print("🎉 You can now:", style="bold blue")
            console.print("   • View your contacts (option 1)", style="cyan")
            console.print("   • Search contacts and tags (option 2)", style="cyan")
            console.print("   • Export interactive directories", style="cyan")
        else:
            console.print("❌ Failed to import contacts to database", style="red")

    except Exception as e:
        console.print(f"❌ Error importing takeout file: {e}", style="red")
        console.print("Make sure the file is a valid Google Takeout zip file", style="yellow")


def handle_import_google_contacts(api: PRTAPI, config: dict) -> None:
    """Handle importing contacts from Google API (kept for compatibility but not used in CLI)."""
    if not Confirm.ask("This will fetch contacts from Google. Continue?"):
        return

    console.print("Fetching contacts from Google...", style="blue")
    try:
        contacts = fetch_contacts(config)
        if contacts:
            # Insert contacts into database
            success = api.insert_contacts(contacts)
            if success:
                console.print(
                    f"Successfully imported {len(contacts)} contacts from Google", style="green"
                )
            else:
                console.print("Failed to import contacts to database", style="red")
        else:
            console.print("No contacts found in Google account", style="yellow")
    except Exception as e:
        console.print(f"Failed to fetch contacts: {e}", style="red")


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


# Helper functions for relationship management
def _get_valid_date(prompt_text: str) -> date | None:
    """Get a valid date from user input with retry logic."""
    from datetime import datetime

    while True:
        date_str = Prompt.ask(prompt_text)
        if not date_str:  # Empty input means skip
            return None

        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            console.print("Invalid date format. Please use YYYY-MM-DD format.", style="red")
            if not Confirm.ask("Try again?", default=True):
                return None


def _validate_contact_id(contact_id: int, contacts: list) -> bool:
    """Verify that a contact ID exists in the contact list."""
    return any(c["id"] == contact_id for c in contacts)


def _display_contacts_paginated(contacts: list, title: str = "Select a Contact") -> None:
    """Display contacts with pagination support."""
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


# Advanced Relationship Management Features (Issue #64 Part 3)


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
    from datetime import datetime
    from pathlib import Path

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

        with open(csv_file, "r", encoding="utf-8") as f:
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


def smart_continue_prompt(operation_type: str):
    """Smart continuation prompt - only when data would scroll off screen."""
    # Only prompt for operations that display lots of data that user needs time to review
    prompt_when_data_heavy = [
        "v",  # View contacts - displays table that might be long
        "i",  # Import - shows import results that user should review
    ]

    # Everything else: menus, quick operations, errors - no prompting needed
    # User can navigate at their own pace
    if operation_type in prompt_when_data_heavy:
        Prompt.ask("\nPress Enter to continue", default="")
    # Default: no prompt - let user flow naturally through menus


# Encryption handler functions removed as part of Issue #41


def run_interactive_cli(debug: bool = False):
    """Run the main interactive CLI."""
    if debug:
        console.print(
            "🐛 [bold cyan]DEBUG MODE ENABLED[/bold cyan] - Using fixture data", style="cyan"
        )
        config = setup_debug_mode()
    else:
        # Check setup status
        status = check_setup_status()

        if status["needs_setup"]:
            console.print(f"PRT needs to be set up: {status['reason']}", style="yellow")
            console.print()

            if Confirm.ask("Would you like to run the setup wizard now?"):
                config = run_setup_wizard()
            else:
                console.print("Setup is required to use PRT. Exiting.", style="red")
                raise typer.Exit(1)
        else:
            config = status["config"]

    # Create API instance
    try:
        api = PRTAPI(config)
    except Exception as e:
        console.print(f"Failed to initialize API: {e}", style="bold red")
        raise typer.Exit(1)

    # Check database health on startup (only in non-debug mode)
    if not debug:
        health = check_database_health(api)
        if not health["healthy"] and health.get("needs_initialization"):
            startup_text = Text()
            startup_text.append("🏗️  Database Initialization Required\n\n", style="bold yellow")
            startup_text.append("Your database needs to be set up with tables.\n", style="yellow")
            startup_text.append("This is normal for first-time use!\n\n", style="yellow")
            startup_text.append("📋 Recommended next steps:\n", style="bold blue")
            startup_text.append("   • Use option 3 to import Google Takeout\n", style="green")
            startup_text.append(
                "   • This will automatically create the required tables\n", style="green"
            )
            startup_text.append("   • Then you can explore all PRT features!\n", style="green")

            console.print(Panel(startup_text, title="Welcome to PRT", border_style="blue"))
            console.print()  # Add some spacing
        elif health["healthy"] and not health["has_data"]:
            startup_text = Text()
            startup_text.append("📭 Database is set up but empty\n\n", style="yellow")
            startup_text.append(
                "Ready to import your contacts! Use option 3 to import Google Takeout.",
                style="green",
            )

            console.print(Panel(startup_text, title="Ready to Import", border_style="green"))
            console.print()

    # Main interactive loop with new menu structure
    while True:
        try:
            show_main_menu(api)
            choice = Prompt.ask(
                "Select an option",
                choices=["c", "v", "r", "s", "t", "n", "d", "i", "q"],
                default="c",
            )

            if choice == "q":
                console.print("Goodbye!", style="green")
                break
            elif choice == "c":
                try:
                    start_ollama_chat(api)
                    # Chat mode handles its own flow - no continue prompt needed
                    continue
                except Exception as e:
                    console.print(f"Error starting chat mode: {e}", style="red")
                    console.print(
                        "Make sure Ollama is running and gpt-oss:20b model is available.",
                        style="yellow",
                    )
            elif choice == "v":
                handle_contacts_view(api)
            elif choice == "r":
                handle_relationships_menu(api)
            elif choice == "s":
                handle_search_menu(api)
            elif choice == "t":
                handle_tags_menu(api)
            elif choice == "n":
                handle_notes_menu(api)
            elif choice == "d":
                handle_database_menu(api)
            elif choice == "i":
                handle_import_google_takeout(api, config)

            # Smart continuation - only prompt when needed
            if choice not in ["q", "c"]:
                smart_continue_prompt(choice)

        except KeyboardInterrupt:
            console.print("\nGoodbye!", style="green")
            break
        except Exception as e:
            console.print(f"Error: {e}", style="red")
            smart_continue_prompt("error")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    debug: bool = typer.Option(False, "--debug", "-d", help="Run in debug mode with fixture data"),
    classic: bool = typer.Option(False, "--classic", help="Run the classic CLI instead of TUI"),
):
    """Personal Relationship Toolkit (PRT) - Manage your personal relationships."""
    if ctx.invoked_subcommand is None:
        if classic:
            run_interactive_cli(debug=debug)
        else:
            # Launch TUI by default
            try:
                from prt_src.tui.app import PRTApp

                app = PRTApp()
                app.run()
            except Exception as e:
                console.print(f"Failed to launch TUI: {e}", style="red")
                console.print("Falling back to classic CLI...", style="yellow")
                run_interactive_cli(debug=debug)


@app.command()
def run(
    debug: bool = typer.Option(False, "--debug", "-d", help="Run in debug mode with fixture data")
):
    """Run the interactive CLI."""
    run_interactive_cli(debug=debug)


@app.command()
def setup():
    """Set up PRT configuration and database."""
    run_setup_wizard()


@app.command()
def test():
    """Test database connection and credentials."""
    try:
        config = load_config()
        if not config:
            console.print("No configuration found. Run 'setup' first.", style="red")
            raise typer.Exit(1)

        db_path = Path(config.get("db_path", "prt_data/prt.db"))
        console.print(f"Testing database connection to: {db_path}", style="blue")

        if not db_path.exists():
            console.print("Database file not found.", style="red")
            raise typer.Exit(1)

        # Try to connect to database
        db = create_database(db_path)

        if db.is_valid():
            console.print("✓ Database connection successful", style="green")
            console.print(f"  Contacts: {db.count_contacts()}", style="green")
            console.print(f"  Relationships: {db.count_relationships()}", style="green")
        else:
            console.print("✗ Database is corrupted or invalid", style="red")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"✗ Database test failed: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def chat():
    """Start LLM chat mode directly."""
    # Check setup status
    status = check_setup_status()

    if status["needs_setup"]:
        console.print(f"PRT needs to be set up: {status['reason']}", style="yellow")
        console.print()

        if Confirm.ask("Would you like to run the setup wizard now?"):
            config = run_setup_wizard()
        else:
            console.print("Setup is required to use PRT chat. Exiting.", style="red")
            raise typer.Exit(1)
    else:
        config = status["config"]

    # Create API instance
    try:
        api = PRTAPI(config)
    except Exception as e:
        console.print(f"Failed to initialize API: {e}", style="bold red")
        raise typer.Exit(1)

    # Start chat mode directly
    console.print("Starting LLM chat mode...", style="blue")
    try:
        start_ollama_chat(api)
    except Exception as e:
        console.print(f"Error starting chat mode: {e}", style="red")
        console.print(
            "Make sure Ollama is running and gpt-oss:20b model is available.", style="yellow"
        )
        raise typer.Exit(1)


# encrypt-db and decrypt-db commands removed as part of Issue #41


@app.command()
def db_status():
    """Check the database status."""
    status = check_setup_status()

    if status["needs_setup"]:
        console.print(f"PRT needs setup: {status['reason']}", style="yellow")
        raise typer.Exit(1)

    config = status["config"]
    db_path = Path(config.get("db_path", "prt_data/prt.db"))

    console.print(f"Database path: {db_path}", style="blue")
    # Encryption status removed as part of Issue #41

    if db_path.exists():
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


if __name__ == "__main__":
    app()
