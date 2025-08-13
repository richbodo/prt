#!/usr/bin/env python3
"""
Database setup utility for PRT.

This module provides functions to set up the database configuration
and initialize the database schema. Designed to be called automatically
by the CLI when needed.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any
import typer
from rich.console import Console

# Add the prt package to the path
sys.path.insert(0, str(Path(__file__).parent / "prt"))

from config import get_db_credentials, data_dir, load_config, save_config
from db import Database
import shutil

app = typer.Typer(help="PRT Database Setup Utility")
console = Console()


def setup_database(force: bool = False, quiet: bool = False) -> Dict[str, Any]:
    """
    Set up database configuration and initialize database if needed.
    
    Args:
        force: Force regeneration of credentials
        quiet: Suppress output messages
        
    Returns:
        Dictionary containing the configuration
    """
    if not quiet:
        console.print("Setting up PRT database...", style="bold blue")
    
    # Ensure data directory exists
    data_path = data_dir()
    
    # Get or generate database credentials
    if force:
        secrets_file = Path.cwd() / "secrets" / "db_secrets.txt"
        if secrets_file.exists():
            secrets_file.unlink()
            if not quiet:
                console.print("Removed existing credentials file", style="yellow")
    
    username, password = get_db_credentials()
    if not quiet:
        console.print("Database credentials generated", style="green")
    
    # Update config with credentials
    try:
        config = load_config()
    except ValueError:
        if not quiet:
            console.print("Existing config is corrupt. Creating new config...", style="yellow")
        config = {}
    
    if not config:
        config = {
            "google_api_key": "demo",
            "openai_api_key": "demo",
            "db_path": str(data_path / "prt.db")
        }
    
    config['db_username'] = username
    config['db_password'] = password
    config['db_type'] = "sqlite"
    
    # Ensure db_path is absolute and points to prt_data
    if 'db_path' in config:
        db_path = Path(config['db_path'])
        if not db_path.is_absolute():
            config['db_path'] = str(data_path / "prt.db")
    
    save_config(config)
    if not quiet:
        console.print("Database configuration updated", style="green")
    
    return config


def initialize_database(config: Dict[str, Any], quiet: bool = False) -> bool:
    """
    Initialize the database with schema if it doesn't exist or is corrupt.
    
    Args:
        config: Database configuration dictionary
        quiet: Suppress output messages
        
    Returns:
        True if database was initialized successfully, False otherwise
    """
    db_file = Path(config["db_path"])
    
    # Check if database exists and is valid
    if db_file.exists():
        db = Database(db_file)
        db.connect()
        if db.is_valid():
            if not quiet:
                console.print("Database exists and is valid", style="green")
            return True
        else:
            # Database is corrupt, backup and recreate
            backup_path = db_file.with_name(db_file.name + ".corrupt.bak")
            shutil.move(db_file, backup_path)
            if not quiet:
                console.print(f"Database was corrupt. Backed up to {backup_path}", style="yellow")
    
    # Create new database
    if not quiet:
        console.print("Creating new database...", style="blue")
    
    db = Database(db_file)
    db.connect()
    db.initialize()
    
    if not quiet:
        console.print("Database initialized successfully", style="green")
    
    return True


@app.command()
def setup(
    force: bool = typer.Option(False, "--force", "-f", help="Force regeneration of credentials"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress output"),
):
    """Set up database configuration for SQLite."""
    config = setup_database(force=force, quiet=quiet)
    
    if not quiet:
        console.print("\nDatabase setup complete!", style="bold green")
        console.print("You can now run: python -m prt.cli", style="cyan")


@app.command()
def show_config():
    """Show current database configuration."""
    try:
        config = load_config()
    except ValueError:
        console.print("Configuration file is corrupt.", style="red")
        return
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
