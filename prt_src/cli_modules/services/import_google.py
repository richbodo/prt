"""
Google import services for PRT CLI.

Functions for importing contacts from Google Takeout and Google API.
These functions handle the business logic of contact import operations.
"""

from pathlib import Path

from rich.console import Console
from rich.prompt import Confirm
from rich.prompt import Prompt

from ...config import data_dir
from ...google_contacts import fetch_contacts

# Import required functions from other modules
from ...google_takeout import find_takeout_files
from ...google_takeout import parse_takeout_contacts


def handle_import_google_takeout(api, config: dict) -> None:
    """Handle importing contacts from Google Takeout zip file."""
    console = Console()

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

    if takeout_path.suffix.lower() != ".zip":
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
        console.print(f"❌ Error processing takeout file: {e}", style="red")
        console.print("Please check the file format and try again.", style="yellow")


def handle_import_google_contacts(api, config: dict) -> None:
    """Handle importing contacts from Google API (kept for compatibility but not used in CLI)."""
    console = Console()

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
