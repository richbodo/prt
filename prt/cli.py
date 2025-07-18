import typer
from pathlib import Path
from typing import Optional

from .config import load_config, save_config, config_path, data_dir, REQUIRED_FIELDS
from .db import Database
from .google_contacts import fetch_contacts
from .llm import chat

app = typer.Typer(help="Personal Relationship Toolkit")


@app.command()
def run(debug: Optional[bool] = True):
    """Run the interactive CLI."""
    cfg = load_config()
    if not cfg:
        typer.echo("Config file not found.")
        typer.echo("See documentation at https://github.com/example/prt")
        if typer.confirm("Create a new config file?"):
            cfg = {}
            cfg["google_api_key"] = typer.prompt("Google API key", default="demo")
            cfg["openai_api_key"] = typer.prompt("OpenAI API key", default="demo")
            default_db = str(data_dir() / "prt.db")
            cfg["db_path"] = typer.prompt("Database path", default=default_db)
            save_config(cfg)
            typer.echo(f"Config saved to {config_path()}")
        else:
            raise typer.Exit()
    missing = [f for f in REQUIRED_FIELDS if f not in cfg]
    for field in missing:
        cfg[field] = typer.prompt(f"Enter value for {field}")
    if missing:
        save_config(cfg)

    db = Database(Path(cfg["db_path"]))
    db.connect()
    schema_path = Path(__file__).resolve().parents[1] / "docs" / "latest_google_people_schema.json"
    db.initialize(schema_path)
    typer.echo("Database initialized.")
    db.backup()

    if db.count_contacts() == 0:
        typer.echo("No contacts in database.")
        if typer.confirm("Sync contacts from Google?"):
            contacts = fetch_contacts(cfg)
            db.insert_contacts(contacts)
            typer.echo(f"Inserted {len(contacts)} contacts.")
    else:
        typer.echo(f"{db.count_contacts()} contacts in database.")

    if db.count_relationships() == 0:
        typer.echo("No relationship data found.")
        if typer.confirm("Add a relationship now?"):
            contacts = db.list_contacts()
            for cid, name, email in contacts:
                typer.echo(f"{cid}: {name} <{email}>")
            chosen = int(typer.prompt("Select contact id"))
            tag = typer.prompt("Tag")
            note = typer.prompt("Note", default="")
            db.add_relationship(chosen, tag, note)
            typer.echo("Relationship added.")
    else:
        typer.echo(f"{db.count_relationships()} relationships in database.")
        typer.echo(chat("introduce", cfg))


if __name__ == "__main__":
    app()
