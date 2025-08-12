#!/usr/bin/env python3
"""
Database setup script for PRT.

This script helps set up the database configuration and generates
Alembic configuration for database migrations.
"""

import sys
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console

# Add the prt package to the path
sys.path.insert(0, str(Path(__file__).parent / "prt"))

from config import get_db_credentials, data_dir, load_config, save_config

app = typer.Typer(help="PRT Database Setup Utility")
console = Console()


@app.command()
def setup(
    db_type: str = typer.Option("sqlite", "--db-type", "-t", help="Database type (sqlite/postgresql)"),
    db_host: str = typer.Option("localhost", "--host", "-h", help="Database host"),
    db_port: int = typer.Option(5432, "--port", "-p", help="Database port"),
    db_name: str = typer.Option("prt", "--name", "-n", help="Database name"),
    force: bool = typer.Option(False, "--force", "-f", help="Force regeneration of credentials"),
    show_alembic: bool = typer.Option(True, "--show-alembic", help="Show Alembic configuration"),
):
    """Set up database configuration and generate credentials."""
    console.print("PRT Database Setup", style="bold blue")
    console.print("=" * 50)
    
    # Ensure data directory exists
    data_path = data_dir()
    console.print(f"Data directory: {data_path}", style="green")
    
    # Get or generate database credentials
    if force:
        # Remove existing secrets file to force regeneration
        secrets_file = Path.cwd() / "secrets" / "db_secrets.txt"
        if secrets_file.exists():
            secrets_file.unlink()
            console.print("Removed existing credentials file", style="yellow")
    
    username, password = get_db_credentials()
    console.print(f"Database username: {username}", style="cyan")
    console.print(f"Database password: {password}", style="cyan")
    console.print(f"Credentials saved to: secrets/db_secrets.txt", style="green")
    
    # Update config with credentials
    config = load_config()
    if not config:
        console.print("No config found. Creating new config...", style="yellow")
        config = {
            "google_api_key": "demo",
            "openai_api_key": "demo",
            "db_path": str(data_path / "prt.db")
        }
    
    config['db_username'] = username
    config['db_password'] = password
    config['db_type'] = db_type
    config['db_host'] = db_host
    config['db_port'] = db_port
    config['db_name'] = db_name
    
    # Ensure db_path is absolute and points to prt_data
    if 'db_path' in config:
        db_path = Path(config['db_path'])
        if not db_path.is_absolute():
            config['db_path'] = str(data_path / "prt.db")
    
    save_config(config)
    console.print(f"Config updated: {data_path / 'prt_config.json'}", style="green")
    
    if show_alembic:
        console.print("\nAlembic Configuration:", style="bold blue")
        console.print("=" * 30)
        console.print("For alembic.ini line 87, use these settings:", style="cyan")
        
        if db_type.lower() == "postgresql":
            url = f"postgresql://{username}:{password}@{db_host}:{db_port}/{db_name}"
        else:
            url = f"sqlite:///{data_path}/prt.db"
        
        console.print(f"sqlalchemy.url = {url}", style="bold green")
        
        if db_type.lower() == "sqlite":
            console.print("\nNote: Currently using SQLite. To switch to PostgreSQL:", style="yellow")
            console.print("1. Run: python setup_database.py setup --db-type postgresql")
            console.print("2. Create a PostgreSQL database named 'prt'")
            console.print("3. Update the Database class in prt/db.py to use SQLAlchemy")
            console.print("4. Run: alembic upgrade head")


@app.command()
def show_config():
    """Show current database configuration."""
    config = load_config()
    if not config:
        console.print("No configuration found.", style="red")
        return
    
    console.print("Current Database Configuration:", style="bold blue")
    console.print("=" * 40)
    
    for key, value in config.items():
        if 'password' in key.lower():
            value = '*' * len(str(value))
        console.print(f"{key}: {value}", style="cyan")


@app.command()
def generate_credentials(
    force: bool = typer.Option(False, "--force", "-f", help="Force regeneration of credentials")
):
    """Generate new database credentials."""
    if force:
        secrets_file = Path.cwd() / "secrets" / "db_secrets.txt"
        if secrets_file.exists():
            secrets_file.unlink()
            console.print("Removed existing credentials file", style="yellow")
    
    username, password = get_db_credentials()
    console.print("New Database Credentials:", style="bold blue")
    console.print("=" * 30)
    console.print(f"Username: {username}", style="cyan")
    console.print(f"Password: {password}", style="cyan")
    console.print(f"Saved to: secrets/db_secrets.txt", style="green")


if __name__ == "__main__":
    app()
