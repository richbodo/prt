import typer
from pathlib import Path
from typing import Optional


from rich.console import Console
from rich.table import Table

from .config import load_config, save_config, config_path, REQUIRED_FIELDS

from .db import Database
from .google_contacts import fetch_contacts
from .llm import chat

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
        if typer.confirm("Sync contacts from Google?"):
            contacts = fetch_contacts(cfg)
            db.insert_contacts(contacts)
            console.print(f"Inserted {len(contacts)} contacts.", style="green")
            console.print()
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
