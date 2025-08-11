import typer
from pathlib import Path
from typing import Optional


from rich.console import Console
from rich.table import Table

from .config import (
    load_config,
    save_config,
    config_path,
    REQUIRED_FIELDS,
    data_dir,
)

from .db import Database
from .google_contacts import fetch_contacts
from .llm import chat
from utils.google_contacts_summary import parse_contacts

app = typer.Typer(help="Personal Relationship Toolkit")
console = Console()


@app.command()
def run(debug: Optional[bool] = True):
    """Run the interactive CLI."""
    cfg = load_config()
    if not cfg:
        console.print("Config file not found.", style="bold red")
        console.print(
            "See documentation at https://github.com/example/prt",
            style="cyan",
        )
        console.print()
        if typer.confirm("Create a new config file?"):
            cfg = {}
            cfg["google_api_key"] = typer.prompt("Google API key", default="demo")
            cfg["openai_api_key"] = typer.prompt("OpenAI API key", default="demo")
            default_db = str(data_dir() / "prt.db")
            cfg["db_path"] = typer.prompt("Database path", default=default_db)
            save_config(cfg)
            console.print(f"Config saved to {config_path()}", style="green")
            console.print()
        else:
            raise typer.Exit()
    missing = [f for f in REQUIRED_FIELDS if f not in cfg]
    for field in missing:
        cfg[field] = typer.prompt(f"Enter value for {field}")
    if missing:
        save_config(cfg)
        console.print()

    db = Database(Path(cfg["db_path"]))
    db.connect()

    schema_path = Path(__file__).resolve().parents[1] / "docs" / "latest_google_people_schema.json"
    db.initialize(schema_path)
    console.print("Database initialized.", style="bold green")
    console.print()
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
        if typer.confirm("Add a relationship now?"):
            contacts = db.list_contacts()
            table = Table(title="Contacts")
            table.add_column("ID", style="cyan", justify="right")
            table.add_column("Name", style="green")
            table.add_column("Email", style="magenta")
            for cid, name, email in contacts:
                table.add_row(str(cid), name, email)
            console.print(table)
            chosen = int(typer.prompt("Select contact id"))
            tag = typer.prompt("Tag")
            note = typer.prompt("Note", default="")
            db.add_relationship(chosen, tag, note)
            console.print("Relationship added.", style="green")
            console.print()
    else:
        console.print(
            f"{db.count_relationships()} relationships in database.", style="green"
        )
        console.print(chat("introduce", cfg), style="bold blue")


if __name__ == "__main__":
    app()
