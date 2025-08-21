import typer
import shutil
from pathlib import Path
from typing import Optional
import configparser


from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.text import Text
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from .config import (
    load_config,
    save_config,
    config_path,
    REQUIRED_FIELDS,
    data_dir,
    get_db_credentials,
    is_database_encrypted,
    get_encryption_key,
)

from .api import PRTAPI
from .google_contacts import fetch_contacts
from .llm import chat
from .cli_map import create_map_command

# Import setup functions
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.setup_database import setup_database, initialize_database
from utils.encrypt_database import encrypt_database, decrypt_database

app = typer.Typer(help="Personal Relationship Toolkit")
console = Console()


def test_db_credentials() -> None:
    """Verify DB credentials from alembic.ini and report record count."""
    parser = configparser.ConfigParser()
    if not parser.read("alembic.ini"):
        console.print("Alembic configuration not found.", style="bold red")
        return
    url = parser.get("alembic", "sqlalchemy.url", fallback="")
    if not url:
        console.print("Database URL not set in alembic.ini.", style="bold red")
        return
    url_obj = make_url(url)
    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            count = 0
            try:
                result = conn.execute(text("SELECT COUNT(*) FROM contacts"))
                count = result.scalar() or 0
            except Exception:
                console.print("Contacts table not found.", style="yellow")
        console.print(
            f"Credentials for user '{url_obj.username}' are valid. {count} records in database.",
            style="green",
        )
    except Exception as e:
        console.print(
            f"Failed to connect with credentials for user '{url_obj.username}': {e}",
            style="bold red",
        )


def show_main_menu() -> None:
    """Display the main menu with all available options."""
    menu_text = Text()
    menu_text.append("Personal Relationship Toolkit (PRT)\n", style="bold blue")
    menu_text.append("=" * 50 + "\n", style="blue")
    menu_text.append("1. ", style="cyan")
    menu_text.append("View Contacts\n", style="white")
    menu_text.append("2. ", style="cyan")
    menu_text.append("Search Contacts\n", style="white")
    menu_text.append("3. ", style="cyan")
    menu_text.append("Import Google Contacts from Takeout\n", style="white")
    menu_text.append("4. ", style="cyan")
    menu_text.append("View Tags\n", style="white")
    menu_text.append("5. ", style="cyan")
    menu_text.append("View Notes\n", style="white")
    menu_text.append("6. ", style="cyan")
    menu_text.append("Start LLM Chat\n", style="white")
    menu_text.append("7. ", style="cyan")
    menu_text.append("Database Status\n", style="white")
    menu_text.append("8. ", style="cyan")
    menu_text.append("Database Backup\n", style="white")
    menu_text.append("9. ", style="cyan")
    menu_text.append("Encrypt Database\n", style="white")
    menu_text.append("10. ", style="cyan")
    menu_text.append("Decrypt Database\n", style="white")
    menu_text.append("0. ", style="red")
    menu_text.append("Exit\n", style="red")
    menu_text.append("=" * 50, style="blue")
    
    console.print(Panel(menu_text, title="Main Menu", border_style="blue"))


def handle_contacts_view(api: PRTAPI) -> None:
    """Handle viewing contacts."""
    try:
        contacts = api.search_contacts("")  # Empty string to get all contacts
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
                    contact.get("phone", "N/A") or "N/A"
                )
            console.print(table)
            console.print(f"\nTotal contacts: {len(contacts)}", style="green")
        else:
            console.print("No contacts found in database.", style="yellow")
    except Exception as e:
        console.print(f"Error viewing contacts: {e}", style="red")


def handle_contacts_search(api: PRTAPI) -> None:
    """Handle searching contacts."""
    query = Prompt.ask("Enter search term")
    if not query.strip():
        console.print("Search term cannot be empty.", style="yellow")
        return
    
    try:
        contacts = api.search_contacts(query)
        if contacts:
            table = Table(title=f"Search Results for '{query}'", show_header=True, header_style="bold magenta")
            table.add_column("ID", style="cyan", width=8)
            table.add_column("Name", style="green", width=30)
            table.add_column("Email", style="yellow", width=40)
            table.add_column("Phone", style="blue", width=20)
            
            for contact in contacts:
                table.add_row(
                    str(contact["id"]),
                    contact["name"] or "N/A",
                    contact["email"] or "N/A",
                    contact.get("phone", "N/A") or "N/A"
                )
            console.print(table)
            console.print(f"\nFound {len(contacts)} contacts matching '{query}'", style="green")
        else:
            console.print(f"No contacts found matching '{query}'", style="yellow")
    except Exception as e:
        console.print(f"Error searching contacts: {e}", style="red")


def handle_import_google_takeout(api: PRTAPI) -> None:
    """Handle importing contacts from Google Takeout zip file."""
    from .google_takeout import find_takeout_files, GoogleTakeoutParser
    from .config import data_dir
    
    console.print("\n" + "="*50)
    console.print("Import Google Contacts from Takeout", style="bold blue")
    console.print("="*50)
    console.print()
    
    # Find Google Takeout zip files in prt_data directory
    takeout_files = find_takeout_files(data_dir())
    
    if not takeout_files:
        console.print("No Google Takeout zip files found in prt_data/ directory.", style="yellow")
        console.print()
        console.print("To import contacts with images:", style="cyan")
        console.print("1. Go to Google Takeout (https://takeout.google.com/)", style="cyan")
        console.print("2. Select only 'Contacts' for export", style="cyan")
        console.print("3. Choose 'Export once' and 'ZIP' format", style="cyan")
        console.print("4. Download the zip file", style="cyan")
        console.print("5. Place the zip file in the prt_data/ directory", style="cyan")
        console.print("6. Run this import command again", style="cyan")
        return
    
    # Display available zip files
    console.print("Available Google Takeout files:", style="bold blue")
    for i, zip_file in enumerate(takeout_files, 1):
        console.print(f"  {i}. {zip_file.name}")
    console.print()
    
    # Let user select a file
    while True:
        try:
            choice = int(Prompt.ask(f"Select a file (1-{len(takeout_files)})"))
            if 1 <= choice <= len(takeout_files):
                selected_file = takeout_files[choice - 1]
                break
            else:
                console.print(f"Please enter a number between 1 and {len(takeout_files)}", style="red")
        except ValueError:
            console.print("Please enter a valid number", style="red")
    
    # Parse and validate the selected file
    console.print(f"Analyzing {selected_file.name}...", style="blue")
    parser = GoogleTakeoutParser(selected_file)
    preview = parser.get_preview_info()
    
    if not preview['valid']:
        console.print(f"Error: {preview['error']}", style="red")
        return
    
    # Show preview information
    console.print(f"✓ Valid Google Takeout file", style="green")
    console.print(f"  Contacts found: {preview['contact_count']}", style="white")
    console.print(f"  Images found: {preview['image_count']}", style="white")
    console.print(f"  Contacts with images: {preview['contacts_with_images']}", style="white")
    console.print()
    
    if preview['sample_contacts']:
        console.print("Sample contacts:", style="bold green")
        for contact in preview['sample_contacts']:
            image_indicator = "📷" if contact['has_image'] else "👤"
            console.print(f"  {image_indicator} {contact['name']}")
        console.print()
    
    if not Confirm.ask("Does this look correct? Import these contacts?"):
        console.print("Import cancelled.", style="yellow")
        return
    
    # Import the contacts
    console.print("Importing contacts...", style="blue")
    try:
        contacts, info = parser.extract_contacts_and_images()
        
        if contacts:
            success = api.import_contacts(contacts)
            if success:
                console.print(f"✓ Successfully imported {len(contacts)} contacts", style="green")
                contacts_with_images = len([c for c in contacts if c.get('profile_image')])
                if contacts_with_images > 0:
                    console.print(f"  Including {contacts_with_images} contacts with profile images", style="green")
            else:
                console.print("Failed to import contacts to database", style="red")
        else:
            console.print("No contacts found in the file", style="yellow")
            
    except Exception as e:
        console.print(f"Failed to import contacts: {e}", style="red")


def handle_fetch_google_contacts(api: PRTAPI, config: dict) -> None:
    """Handle fetching contacts from Google (legacy method - kept for reference)."""
    if not Confirm.ask("This will fetch contacts from Google. Continue?"):
        return
    
    console.print("Fetching contacts from Google...", style="blue")
    try:
        contacts = fetch_contacts(config)
        if contacts:
            # Insert contacts into database
            success = api.insert_contacts(contacts)
            if success:
                console.print(f"Successfully imported {len(contacts)} contacts from Google", style="green")
            else:
                console.print("Failed to import contacts to database", style="red")
        else:
            console.print("No contacts found in Google account", style="yellow")
    except Exception as e:
        console.print(f"Failed to fetch contacts: {e}", style="red")


def handle_view_tags(api: PRTAPI) -> None:
    """Handle viewing tags."""
    try:
        tags = api.search_tags("")  # Empty string to get all tags
        if tags:
            table = Table(title="Tags", show_header=True, header_style="bold magenta")
            table.add_column("ID", style="cyan", width=8)
            table.add_column("Name", style="green", width=30)
            table.add_column("Contact Count", style="yellow", width=15)
            
            for tag in tags:
                table.add_row(
                    str(tag["id"]),
                    tag["name"],
                    str(tag["contact_count"])
                )
            console.print(table)
            console.print(f"\nTotal tags: {len(tags)}", style="green")
        else:
            console.print("No tags found in database.", style="yellow")
    except Exception as e:
        console.print(f"Error viewing tags: {e}", style="red")


def handle_view_notes(api: PRTAPI) -> None:
    """Handle viewing notes."""
    try:
        notes = api.search_notes("")  # Empty string to get all notes
        if notes:
            table = Table(title="Notes", show_header=True, header_style="bold magenta")
            table.add_column("ID", style="cyan", width=8)
            table.add_column("Title", style="green", width=40)
            table.add_column("Content Preview", style="yellow", width=50)
            
            for note in notes:
                content_preview = note["content"][:47] + "..." if len(note["content"]) > 50 else note["content"]
                table.add_row(
                    str(note["id"]),
                    note["title"],
                    content_preview
                )
            console.print(table)
            console.print(f"\nTotal notes: {len(notes)}", style="green")
        else:
            console.print("No notes found in database.", style="yellow")
    except Exception as e:
        console.print(f"Error viewing notes: {e}", style="red")


def handle_database_status(api: PRTAPI) -> None:
    """Handle database status display."""
    try:
        stats = api.get_database_stats()
        console.print("Database Status:", style="bold blue")
        console.print(f"  Contacts: {stats['contacts']}", style="green")
        console.print(f"  Relationships: {stats['relationships']}", style="green")
        
        if api.validate_database():
            console.print("  Status: [green]OK[/green]")
        else:
            console.print("  Status: [red]CORRUPT[/red]")
    except Exception as e:
        console.print(f"Error checking database status: {e}", style="red")


def handle_database_backup(api: PRTAPI) -> None:
    """Handle database backup."""
    if not Confirm.ask("Create a backup of the database?"):
        return
    
    try:
        backup_path = api.backup_database()
        console.print(f"Database backed up to: {backup_path}", style="green")
    except Exception as e:
        console.print(f"Error creating backup: {e}", style="red")


def handle_encrypt_database() -> None:
    """Handle database encryption."""
    if not Confirm.ask("This will encrypt the database. Continue?"):
        return
    
    try:
        success = encrypt_database()
        if success:
            console.print("Database encryption completed successfully!", style="bold green")
        else:
            console.print("Database encryption failed!", style="bold red")
    except Exception as e:
        console.print(f"Error encrypting database: {e}", style="red")


def handle_decrypt_database() -> None:
    """Handle database decryption."""
    if not Confirm.ask("This will decrypt the database. Continue?"):
        return
    
    try:
        success = decrypt_database()
        if success:
            console.print("Database decryption completed successfully!", style="bold green")
        else:
            console.print("Database decryption failed!", style="bold red")
    except Exception as e:
        console.print(f"Error decrypting database: {e}", style="red")


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Personal Relationship Toolkit - Main entry point."""
    if ctx.invoked_subcommand is None:
        # No subcommand provided, run the interactive CLI
        run_interactive_cli()


def run_interactive_cli():
    """Run the interactive CLI with menu-driven interface."""
    # Validate configuration and database
    try:
        config = load_config()
    except ValueError:
        console.print("Config file is corrupt.", style="bold red")
        config = {}
    
    if not config:
        console.print("Config file not found.", style="bold red")
        console.print("See documentation at https://github.com/richbodo/prt", style="cyan")
        console.print()
        if Confirm.ask("Create a new config file?"):
            config = setup_database(quiet=True)
            console.print(f"Config saved to {config_path()}", style="green")
            console.print()
        else:
            raise typer.Exit()
    
    # Check for missing required fields and handle them automatically
    missing = [f for f in REQUIRED_FIELDS if f not in config]
    if missing:
        console.print("Updating configuration with missing fields...", style="blue")
        
        # Handle database credentials automatically
        if 'db_username' in missing or 'db_password' in missing:
            db_username, db_password = get_db_credentials()
            config['db_username'] = db_username
            config['db_password'] = db_password
            console.print("Database credentials updated", style="green")
        
        # Handle other missing fields
        for field in missing:
            if field not in ['db_username', 'db_password']:
                if field == 'google_api_key':
                    config[field] = Prompt.ask("Enter your Google API key")
                elif field == 'openai_api_key':
                    config[field] = Prompt.ask("Enter your OpenAI API key")
                elif field == 'db_path':
                    config[field] = str(data_dir() / "prt.db")
        
        save_config(config)
        console.print("Configuration updated", style="green")
    
    # Initialize database if needed
    if not initialize_database(config, quiet=True):
        console.print("Failed to initialize database", style="bold red")
        raise typer.Exit(1)
    
    # Create API instance
    try:
        api = PRTAPI(config)
    except Exception as e:
        console.print(f"Failed to initialize API: {e}", style="bold red")
        raise typer.Exit(1)
    
    # Main interactive loop
    while True:
        try:
            show_main_menu()
            choice = Prompt.ask("Select an option", choices=["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"])
            
            if choice == "0":
                console.print("Goodbye!", style="green")
                break
            elif choice == "1":
                handle_contacts_view(api)
            elif choice == "2":
                handle_contacts_search(api)
            elif choice == "3":
                handle_import_google_takeout(api)
            elif choice == "4":
                handle_view_tags(api)
            elif choice == "5":
                handle_view_notes(api)
            elif choice == "6":
                chat(config)
            elif choice == "7":
                handle_database_status(api)
            elif choice == "8":
                handle_database_backup(api)
            elif choice == "9":
                handle_encrypt_database()
            elif choice == "10":
                handle_decrypt_database()
            
            if choice != "0":
                Prompt.ask("\nPress Enter to continue")
                
        except KeyboardInterrupt:
            console.print("\nGoodbye!", style="green")
            break
        except Exception as e:
            console.print(f"Error: {e}", style="red")
            Prompt.ask("\nPress Enter to continue")


@app.command()
def run(debug: Optional[bool] = True):
    """Run the interactive CLI."""
    run_interactive_cli()


@app.command()
def encrypt_db(
    db_path: Optional[Path] = typer.Option(None, "--db-path", "-p", help="Path to database file"),
    key: Optional[str] = typer.Option(None, "--key", "-k", help="Encryption key (generates new one if not provided)"),
    no_backup: bool = typer.Option(False, "--no-backup", help="Skip backup creation"),
    no_verify: bool = typer.Option(False, "--no-verify", help="Skip verification after encryption"),
    force: bool = typer.Option(False, "--force", help="Force encryption even if already encrypted")
):
    """Encrypt an existing unencrypted database."""
    success = encrypt_database(
        db_path=db_path,
        encryption_key=key,
        backup=not no_backup,
        verify=not no_verify,
        force=force
    )
    
    if success:
        console.print("Database encryption completed successfully!", style="bold green")
    else:
        console.print("Database encryption failed!", style="bold red")
        raise typer.Exit(1)


@app.command()
def decrypt_db(
    db_path: Optional[Path] = typer.Option(None, "--db-path", "-p", help="Path to database file"),
    key: Optional[str] = typer.Option(None, "--key", "-k", help="Encryption key (loads from secrets if not provided)"),
    no_backup: bool = typer.Option(False, "--no-backup", help="Skip backup creation")
):
    """Decrypt an encrypted database (emergency function)."""
    success = decrypt_database(
        db_path=db_path,
        encryption_key=key,
        backup=not no_backup
    )
    
    if success:
        console.print("Database decryption completed successfully!", style="bold green")
    else:
        console.print("Database decryption failed!", style="bold red")
        raise typer.Exit(1)


@app.command()
def db_status():
    """Check the encryption status of the database."""
    try:
        config = load_config()
        db_path = Path(config.get('db_path', 'prt_data/prt.db'))
        
        console.print(f"Database path: {db_path}", style="blue")
        console.print(f"Encrypted: {is_database_encrypted(config)}", style="blue")
        
        if db_path.exists():
            # Try to connect and verify
            try:
                from .db import create_database
                if is_database_encrypted(config):
                    db = create_database(db_path, encrypted=True)
                else:
                    db = create_database(db_path, encrypted=False)
                
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
        raise typer.Exit(1)


@app.command()
def setup():
    """Set up PRT configuration and database."""
    try:
        cfg = setup_database()
        console.print("PRT setup completed successfully!", style="bold green")
        console.print(f"Configuration saved to {config_path()}", style="green")
        
        if initialize_database(cfg):
            console.print("Database initialized successfully", style="green")
        else:
            console.print("Database initialization failed", style="red")
            
    except Exception as e:
        console.print(f"Setup failed: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def test():
    """Test database connection and credentials."""
    test_db_credentials()


# Add the map command
app.command(name="map")(create_map_command(app))


@app.command()
def migrate():
    """Migrate database schema to latest version."""
    from .schema_manager import SchemaManager
    from .config import load_config
    from .db import Database
    from pathlib import Path
    
    try:
        config = load_config()
        db_path = Path(config["db_path"])
        
        # Check if database exists
        if not db_path.exists():
            console.print("❌ Database not found. Run 'setup' command first.", style="red")
            raise typer.Exit(1)
        
        # Connect to database
        encrypted = config.get('db_encrypted', False)
        encryption_key = None
        if encrypted:
            from .config import get_encryption_key
            encryption_key = get_encryption_key()
        
        db = Database(db_path, encrypted=encrypted, encryption_key=encryption_key)
        db.connect()
        
        # Run migration
        schema_manager = SchemaManager(db)
        info = schema_manager.get_migration_info()
        
        console.print(f"Current database version: {info['current_version']}", style="blue")
        console.print(f"Target version: {info['target_version']}", style="blue")
        
        if not info['migration_needed']:
            console.print("✅ Database is already up to date!", style="green")
            return
        
        if not info['migration_available']:
            console.print("❌ No migration path available for this database version.", style="red")
            raise typer.Exit(1)
        
        success = schema_manager.migrate_safely()
        if not success:
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"Migration failed: {e}", style="red")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
