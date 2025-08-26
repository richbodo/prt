"""
PRT - Personal Relationship Toolkit CLI

This is the main CLI interface for PRT. It automatically detects if setup is needed
and provides a unified interface for all operations.
"""

import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.text import Text

from .api import PRTAPI
from .config import load_config, save_config, config_path, data_dir
from .db import create_database
from .google_contacts import fetch_contacts
from .llm_ollama import start_ollama_chat
from migrations.setup_database import get_db_credentials, setup_database, initialize_database
# Encryption imports removed as part of Issue #41

app = typer.Typer(help="Personal Relationship Toolkit (PRT)")
console = Console()

# Required configuration fields
REQUIRED_FIELDS = ['db_username', 'db_password', 'db_path', 'google_api_key', 'openai_api_key']


def check_setup_status():
    """Check if PRT is properly set up and return status information."""
    try:
        config = load_config()
        if not config:
            return {"needs_setup": True, "reason": "No configuration file found"}
        
        # Check for missing required fields
        missing = [f for f in REQUIRED_FIELDS if f not in config]
        if missing:
            return {"needs_setup": True, "reason": f"Missing configuration fields: {', '.join(missing)}"}
        
        # Check if database exists and is accessible
        db_path = Path(config.get('db_path', 'prt_data/prt.db'))
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
    console.print("\n" + "="*60)
    console.print("PRT Setup Wizard", style="bold blue")
    console.print("="*60)
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
        console.print(f"Database location: {config.get('db_path', 'prt_data/prt.db')}", style="cyan")
        console.print()
        console.print("You can now use PRT to manage your personal relationships!", style="green")
        
        return config
        
    except Exception as e:
        console.print(f"✗ Setup failed: {e}", style="bold red")
        console.print("Please check the error and try again.", style="yellow")
        raise typer.Exit(1)


def show_main_menu(api: PRTAPI):
    """Display the main operations menu."""
    menu_text = Text()
    menu_text.append("Personal Relationship Toolkit (PRT)\n", style="bold blue")
    menu_text.append("=" * 50 + "\n", style="blue")
    menu_text.append("1. ", style="cyan")
    menu_text.append("View Contacts\n", style="white")
    menu_text.append("2. ", style="cyan")
    menu_text.append("Search Contacts\n", style="white")
    menu_text.append("3. ", style="cyan")
    menu_text.append("Import Google Contacts\n", style="white")
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


def handle_import_google_contacts(api: PRTAPI, config: dict) -> None:
    """Handle importing contacts from Google."""
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
        tags = api.list_all_tags()
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
        notes = api.list_all_notes()
        if notes:
            table = Table(title="Notes", show_header=True, header_style="bold magenta")
            table.add_column("ID", style="cyan", width=8)
            table.add_column("Title", style="green", width=30)
            table.add_column("Content", style="yellow", width=50)
            table.add_column("Contact Count", style="blue", width=15)
            
            for note in notes:
                content_preview = note["content"][:47] + "..." if len(note["content"]) > 50 else note["content"]
                table.add_row(
                    str(note["id"]),
                    note["title"],
                    content_preview,
                    str(note["contact_count"])
                )
            console.print(table)
            console.print(f"\nTotal notes: {len(notes)}", style="green")
        else:
            console.print("No notes found in database.", style="yellow")
    except Exception as e:
        console.print(f"Error viewing notes: {e}", style="red")


def handle_database_status(api: PRTAPI) -> None:
    """Handle database status check."""
    try:
        config = load_config()
        db_path = Path(config.get('db_path', 'prt_data/prt.db'))
        
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
        db_path = Path(config.get('db_path', 'prt_data/prt.db'))
        
        if not db_path.exists():
            console.print("Database file not found.", style="red")
            return
        
        # Create backup path
        backup_path = db_path.with_suffix(f'.backup.{int(db_path.stat().st_mtime)}')
        
        # Copy the database file
        import shutil
        shutil.copy2(db_path, backup_path)
        
        console.print(f"Database backed up to: {backup_path}", style="green")
        
    except Exception as e:
        console.print(f"Failed to create backup: {e}", style="red")


# Encryption handler functions removed as part of Issue #41


def run_interactive_cli():
    """Run the main interactive CLI."""
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
    
    # Main interactive loop
    while True:
        try:
            show_main_menu(api)
            choice = Prompt.ask("Select an option", choices=["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"])
            
            if choice == "0":
                console.print("Goodbye!", style="green")
                break
            elif choice == "1":
                handle_contacts_view(api)
            elif choice == "2":
                handle_contacts_search(api)
            elif choice == "3":
                handle_import_google_contacts(api, config)
            elif choice == "4":
                handle_view_tags(api)
            elif choice == "5":
                handle_view_notes(api)
            elif choice == "6":
                try:
                    start_ollama_chat(api)
                except Exception as e:
                    console.print(f"Error starting chat mode: {e}", style="red")
                    console.print("Make sure Ollama is running and gpt-oss:20b model is available.", style="yellow")
            elif choice == "7":
                handle_database_status(api)
            elif choice == "8":
                handle_database_backup(api)
            # Encryption menu options removed as part of Issue #41
            
            if choice != "0":
                Prompt.ask("\nPress Enter to continue")
                
        except KeyboardInterrupt:
            console.print("\nGoodbye!", style="green")
            break
        except Exception as e:
            console.print(f"Error: {e}", style="red")
            Prompt.ask("\nPress Enter to continue")


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Personal Relationship Toolkit (PRT) - Manage your personal relationships."""
    if ctx.invoked_subcommand is None:
        run_interactive_cli()


@app.command()
def run():
    """Run the interactive CLI."""
    run_interactive_cli()


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
        
        db_path = Path(config.get('db_path', 'prt_data/prt.db'))
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
        console.print("Make sure Ollama is running and gpt-oss:20b model is available.", style="yellow")
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
    db_path = Path(config.get('db_path', 'prt_data/prt.db'))
    
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
