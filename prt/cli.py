import typer
import shutil
from pathlib import Path
from typing import Optional
import configparser


from rich.console import Console
from rich.table import Table
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from .config import (
    load_config,
    save_config,
    config_path,
    REQUIRED_FIELDS,
    data_dir,
    get_db_credentials,
)

from .db import Database
from .google_contacts import fetch_contacts
from .llm import chat
from utils.google_contacts_summary import parse_contacts

# Import setup functions
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from setup_database import setup_database, initialize_database

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


@app.command()
def run(debug: Optional[bool] = True):
    """Run the interactive CLI."""
    try:
        cfg = load_config()
    except ValueError:
        console.print("Config file is corrupt.", style="bold red")
        cfg = {}
    if not cfg:
        console.print("Config file not found.", style="bold red")
        console.print(
            "See documentation at https://github.com/richbodo/prt",
            style="cyan",
        )
        console.print()
        if typer.confirm("Create a new config file?"):
            # Use the setup function to create config
            cfg = setup_database(quiet=True)
            console.print(f"Config saved to {config_path()}", style="green")
            console.print()
        else:
            raise typer.Exit()
    # Check for missing required fields and handle them automatically
    missing = [f for f in REQUIRED_FIELDS if f not in cfg]
    if missing:
        console.print("Updating configuration with missing fields...", style="blue")
        
        # Handle database credentials automatically
        if 'db_username' in missing or 'db_password' in missing:
            db_username, db_password = get_db_credentials()
            cfg['db_username'] = db_username
            cfg['db_password'] = db_password
            console.print("Database credentials updated", style="green")
        
        # Handle other missing fields
        for field in missing:
            if field not in ['db_username', 'db_password']:
                cfg[field] = typer.prompt(f"Enter value for {field}")
        
        save_config(cfg)
        console.print()

    # Check if database exists and is valid
    db = Database(Path(cfg["db_path"]))
    db.connect()
    
    if not db.is_valid():
        console.print("Database not found or invalid. Setting up...", style="yellow")
        
        # Backup existing database if it exists
        db_file = Path(cfg["db_path"])
        if db_file.exists():
            backup_path = db_file.with_name(db_file.name + ".backup")
            shutil.move(db_file, backup_path)
            console.print(f"Backed up existing database to {backup_path}", style="blue")
        
        # Initialize database
        if initialize_database(cfg, quiet=True):
            console.print("Database initialized successfully.", style="bold green")
        else:
            console.print("Failed to initialize database.", style="bold red")
            raise typer.Exit(1)
    else:
        console.print("Database connected successfully.", style="bold green")
    
    console.print()
    test_db_credentials()
    db.backup()

    if db.count_contacts() == 0:
        console.print("No contacts in database.", style="yellow")
        """  We are not going to sync for now - takes too long to configure - no one will use it       
        if typer.confirm("Sync contacts from Google?"):
            contacts = fetch_contacts(cfg)
            db.insert_contacts(contacts)
            console.print(f"Inserted {len(contacts)} contacts.", style="green")
            console.print()
        """
        if typer.confirm("Import contacts from a Google Contacts CSV file?"):
            # Find CSV files in prt_data directory
            csv_files = list(data_dir().glob("*.csv"))
            
            if not csv_files:
                console.print("No CSV files found in prt_data/ directory.", style="yellow")
                console.print("Please export your Google Contacts to CSV and place the file in the prt_data/ directory, then run the CLI again.", style="cyan")
                raise typer.Exit()
            
            # Display available CSV files
            console.print("Available CSV files:", style="bold blue")
            for i, csv_file in enumerate(csv_files, 1):
                console.print(f"  {i}. {csv_file.name}")
            console.print()
            
            # Let user select a file
            while True:
                try:
                    choice = int(typer.prompt(f"Select a file (1-{len(csv_files)})"))
                    if 1 <= choice <= len(csv_files):
                        csv_path = str(csv_files[choice - 1])
                        break
                    else:
                        console.print(f"Please enter a number between 1 and {len(csv_files)}", style="red")
                except ValueError:
                    console.print("Please enter a valid number", style="red")
            
            contacts = parse_contacts(csv_path)
            
            # Show contact count and first contact for verification
            console.print(f"Found {len(contacts)} contacts in the CSV file.", style="bold blue")
            console.print()
            
            if contacts:
                first_contact = contacts[0]
                name = f"{first_contact['first']} {first_contact['last']}".strip()
                if not name:
                    name = "(No name)"
                
                console.print("First contact details:", style="bold green")
                console.print(f"  Name: {name}")
                if first_contact['emails']:
                    console.print("  Emails:")
                    for email in first_contact['emails']:
                        console.print(f"    {email}")
                if first_contact['phones']:
                    console.print("  Phones:")
                    for phone in first_contact['phones']:
                        console.print(f"    {phone}")
                console.print()
            else:
                console.print("No contacts found in the CSV file.", style="yellow")
                console.print()
            
            if not typer.confirm("Does the contact count and the first contact look correct?"):
                console.print("Stopping program - see the utils directory for parsing utilities to test with.", style="red")
                raise typer.Exit()
            
            """db.insert_contacts(contacts)
            console.print(f"Inserted {len(contacts)} contacts.", style="green")
            console.print()"""
    else:
        console.print(f"{db.count_contacts()} contacts in database.", style="green")
        console.print()

    if db.count_relationships() == 0:
        console.print("No relationship data found.", style="yellow")
        if typer.confirm("Add relationship data now?"):
            contacts = db.list_contacts()
            table = Table(title="Contacts")
            table.add_column("ID", style="cyan", justify="right")
            table.add_column("Name", style="green")
            table.add_column("Email", style="magenta")
            for cid, name, email in contacts:
                table.add_row(str(cid), name, email)
            console.print(table)
            chosen = int(typer.prompt("Select contact id"))
            
            # Add tags
            while True:
                tag = typer.prompt("Add a tag (or press Enter to skip)")
                if not tag:
                    break
                try:
                    db.add_relationship_tag(chosen, tag)
                    console.print(f"Added tag: {tag}", style="green")
                except ValueError as e:
                    console.print(f"Error: {e}", style="red")
                    break
            
            # Add notes
            while True:
                note_title = typer.prompt("Add a note title (or press Enter to skip)")
                if not note_title:
                    break
                note_content = typer.prompt("Note content")
                try:
                    db.add_relationship_note(chosen, note_title, note_content)
                    console.print(f"Added note: {note_title}", style="green")
                except ValueError as e:
                    console.print(f"Error: {e}", style="red")
                    break
            
            console.print("Relationship data added.", style="green")
            console.print()
    else:
        console.print(
            f"{db.count_relationships()} relationships in database.", style="green"
        )
        
        # Show some relationship examples
        contacts = db.list_contacts()
        if contacts:
            console.print("\nRelationship examples:", style="bold blue")
            for cid, name, email in contacts[:3]:  # Show first 3 contacts
                rel_info = db.get_relationship_info(cid)
                if rel_info["tags"] or rel_info["notes"]:
                    console.print(f"  {name}:", style="cyan")
                    if rel_info["tags"]:
                        console.print(f"    Tags: {', '.join(rel_info['tags'])}", style="green")
                    if rel_info["notes"]:
                        for note in rel_info["notes"][:2]:  # Show first 2 notes
                            console.print(f"    Note: {note['title']} - {note['content'][:50]}...", style="yellow")
        
        console.print(chat("introduce", cfg), style="bold blue")
        
        # Transition to regular operations menu
        console.print("\n" + "="*50)
        console.print("Setup complete! Starting regular operations...", style="bold green")
        console.print("="*50)
        
        # Import and run the regular operations CLI
        from .cli_operations import run_cli
        run_cli()


if __name__ == "__main__":
    app()
