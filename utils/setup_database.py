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

from prt_src.config import get_db_credentials, data_dir, load_config, save_config

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
        secrets_file = data_path / "secrets" / "db_secrets.txt"
        if secrets_file.exists():
            secrets_file.unlink()
            if not quiet:
                console.print("Removed existing credentials file", style="yellow")
    
    username, password = get_db_credentials()
    if not quiet:
        console.print("Database credentials generated", style="green")
    
    # Encryption key generation removed as part of Issue #41
    
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
    config['db_encrypted'] = False  # Always false as part of Issue #41
    
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
    
    # Check if database already exists and is valid
    if db_file.exists():
        try:
            # Try to connect to existing database
            from prt_src.db import create_database
            db = create_database(db_file)
            
            if db.is_valid():
                if not quiet:
                    console.print("Database already exists and is valid", style="green")
                return True
            else:
                if not quiet:
                    console.print("Database exists but is corrupt", style="yellow")
        except Exception as e:
            if not quiet:
                console.print(f"Failed to connect to existing database: {e}", style="yellow")
    
    # Create new database
    try:
        if not quiet:
            console.print("Creating new database...", style="blue")
        
        # Ensure directory exists
        db_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create database
        from prt_src.db import create_database
        db = create_database(db_file)
        
        # Initialize schema
        db.initialize()
        
        if not quiet:
            console.print("Database initialized successfully", style="green")
        
        return True
        
    except Exception as e:
        if not quiet:
            console.print(f"Failed to initialize database: {e}", style="red")
        return False


@app.command()
def setup(
    force: bool = typer.Option(False, "--force", help="Force regeneration of credentials"),
    encrypted: bool = typer.Option(False, "--encrypted", help="Set up encrypted database"),
    quiet: bool = typer.Option(False, "--quiet", help="Suppress output messages")
):
    """Set up PRT database configuration and initialize database."""
    try:
        config = setup_database(force=force, quiet=quiet, encrypted=encrypted)
        
        if not quiet:
            console.print("Database configuration set up successfully", style="green")
        
        if initialize_database(config, quiet=quiet):
            if not quiet:
                console.print("Database initialized successfully", style="green")
        else:
            if not quiet:
                console.print("Failed to initialize database", style="red")
            raise typer.Exit(1)
            
    except Exception as e:
        if not quiet:
            console.print(f"Setup failed: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def encrypt(
    db_path: Optional[Path] = typer.Option(None, "--db-path", "-p", help="Path to database file"),
    key: Optional[str] = typer.Option(None, "--key", "-k", help="Encryption key (generates new one if not provided)"),
    no_backup: bool = typer.Option(False, "--no-backup", help="Skip backup creation"),
    no_verify: bool = typer.Option(False, "--no-verify", help="Skip verification after encryption"),
    force: bool = typer.Option(False, "--force", help="Force encryption even if already encrypted")
):
    """Encrypt an existing unencrypted database."""
    from utils.encrypt_database import encrypt_database
    
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
def status():
    """Check the encryption status of the database."""
    from utils.encrypt_database import status as check_status
    check_status()


if __name__ == "__main__":
    app()
