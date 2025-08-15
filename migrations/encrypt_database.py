#!/usr/bin/env python3
"""
Database encryption migration utility for PRT.

This module provides functions to migrate from unencrypted to encrypted
databases using SQLCipher encryption.
"""

import sys
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.text import Text

# Add the prt package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from prt.config import get_encryption_key, load_config, save_config, is_database_encrypted
from prt.db import Database, create_database
from prt.encrypted_db import migrate_to_encrypted, create_encrypted_database

app = typer.Typer(help="PRT Database Encryption Utility")
console = Console()


def backup_database(db_path: Path, backup_suffix: str = ".pre_encryption") -> Path:
    """Create a backup of the database before encryption."""
    backup_path = db_path.with_name(db_path.name + backup_suffix)
    
    if db_path.exists():
        console.print(f"Creating backup at {backup_path}", style="blue")
        shutil.copy(db_path, backup_path)
        console.print("Backup created successfully", style="green")
    else:
        console.print("Database file not found, skipping backup", style="yellow")
    
    return backup_path


def export_encryption_key(encryption_key: str, export_path: Optional[Path] = None) -> Path:
    """Export encryption key to a secure location."""
    if export_path is None:
        export_path = Path.cwd() / "encryption_key_backup.txt"
    
    console.print(f"Exporting encryption key to {export_path}", style="yellow")
    
    with open(export_path, 'w') as f:
        f.write("# PRT Database Encryption Key Backup\n")
        f.write("# IMPORTANT: Keep this file secure and separate from your database\n")
        f.write("# Losing this key means losing access to your encrypted data\n")
        f.write("# Store this file in a secure location (password manager, safe, etc.)\n\n")
        f.write(f"ENCRYPTION_KEY={encryption_key}\n")
    
    console.print("Encryption key exported successfully", style="green")
    console.print("⚠️  IMPORTANT: Store this file securely and separately from your database!", style="bold red")
    
    return export_path


def verify_encryption_key(encryption_key: str, db_path: Path) -> bool:
    """Verify that an encryption key can decrypt a database."""
    try:
        db = create_encrypted_database(db_path, encryption_key)
        return db.test_encryption()
    except Exception:
        return False


def verify_database_integrity(db: Database) -> bool:
    """Verify that the database is valid and accessible."""
    try:
        if not db.is_valid():
            console.print("Database integrity check failed", style="red")
            return False
        
        # Test basic operations
        contact_count = db.count_contacts()
        relationship_count = db.count_relationships()
        
        console.print(f"Database verification successful:", style="green")
        console.print(f"  - Contacts: {contact_count}", style="green")
        console.print(f"  - Relationships: {relationship_count}", style="green")
        
        return True
    except Exception as e:
        console.print(f"Database verification failed: {e}", style="red")
        return False


def show_encryption_warnings():
    """Display important warnings about encryption."""
    warning_text = Text()
    warning_text.append("⚠️  ENCRYPTION WARNINGS ⚠️\n\n", style="bold red")
    warning_text.append("• Keep your encryption key safe - losing it means losing access to your data\n", style="red")
    warning_text.append("• The encryption key is stored in secrets/db_encryption_key.txt\n", style="yellow")
    warning_text.append("• Consider backing up your encryption key to a secure location\n", style="yellow")
    warning_text.append("• Never commit encryption keys to version control\n", style="red")
    warning_text.append("• Encrypted databases may be slightly slower than unencrypted ones\n", style="yellow")
    
    console.print(Panel(warning_text, title="Security Notice", border_style="red"))


def encrypt_database(
    db_path: Optional[Path] = None,
    encryption_key: Optional[str] = None,
    backup: bool = True,
    verify: bool = True,
    force: bool = False,
    export_key: bool = True
) -> bool:
    """
    Encrypt an existing unencrypted database.
    
    Args:
        db_path: Path to the database file (uses config if None)
        encryption_key: Encryption key to use (generates new one if None)
        backup: Whether to create a backup before encryption
        verify: Whether to verify the encrypted database after migration
        force: Force encryption even if database appears to be encrypted
        export_key: Whether to export the encryption key to a backup file
        
    Returns:
        True if encryption was successful, False otherwise
    """
    console.print("Starting database encryption process...", style="bold blue")
    
    # Show encryption warnings
    show_encryption_warnings()
    
    if not typer.confirm("Do you understand the risks and want to proceed?"):
        console.print("Encryption cancelled", style="yellow")
        return False
    
    # Get database path from config if not provided
    if db_path is None:
        try:
            config = load_config()
            db_path = Path(config.get('db_path', 'prt_data/prt.db'))
        except Exception as e:
            console.print(f"Failed to load config: {e}", style="red")
            return False
    
    # Check if database exists
    if not db_path.exists():
        console.print(f"Database file not found: {db_path}", style="red")
        return False
    
    # Check if database is already encrypted
    try:
        config = load_config()
        if is_database_encrypted(config) and not force:
            console.print("Database is already configured as encrypted", style="yellow")
            if not typer.confirm("Force re-encryption?"):
                return False
    except Exception:
        pass  # Config might not exist yet
    
    # Create backup if requested
    if backup:
        backup_path = backup_database(db_path)
    
    # Generate encryption key if not provided
    if encryption_key is None:
        encryption_key = get_encryption_key()
        console.print("Generated new encryption key", style="green")
    
    # Export encryption key if requested
    if export_key:
        export_encryption_key(encryption_key)
    
    try:
        # Connect to source database
        console.print("Connecting to source database...", style="blue")
        source_db = create_database(db_path, encrypted=False)
        
        # Verify source database
        if not verify_database_integrity(source_db):
            return False
        
        # Create temporary path for encrypted database
        temp_encrypted_path = db_path.with_name(db_path.name + ".encrypted")
        
        # Migrate to encrypted database
        console.print("Migrating data to encrypted database...", style="blue")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Migrating data...", total=None)
            
            encrypted_db = migrate_to_encrypted(
                source_db, 
                temp_encrypted_path, 
                encryption_key
            )
            
            progress.update(task, description="Migration completed")
        
        # Verify encrypted database
        if verify:
            console.print("Verifying encrypted database...", style="blue")
            if not verify_database_integrity(encrypted_db):
                console.print("Encrypted database verification failed", style="red")
                return False
        
        # Replace original database with encrypted version
        console.print("Replacing original database with encrypted version...", style="blue")
        source_db.session.close()
        encrypted_db.session.close()
        
        # Remove original and rename encrypted
        db_path.unlink()
        temp_encrypted_path.rename(db_path)
        
        # Update configuration
        try:
            config = load_config()
        except Exception:
            config = {}
        
        config['db_encrypted'] = True
        save_config(config)
        
        console.print("Database encryption completed successfully!", style="bold green")
        console.print("Your database is now encrypted and secure.", style="green")
        return True
        
    except Exception as e:
        console.print(f"Encryption failed: {e}", style="red")
        
        # Clean up temporary files
        temp_encrypted_path = db_path.with_name(db_path.name + ".encrypted")
        if temp_encrypted_path.exists():
            temp_encrypted_path.unlink()
        
        return False


def decrypt_database(
    db_path: Optional[Path] = None,
    encryption_key: Optional[str] = None,
    backup: bool = True
) -> bool:
    """
    Decrypt an encrypted database (emergency function).
    
    Args:
        db_path: Path to the database file (uses config if None)
        encryption_key: Encryption key to use (loads from secrets if None)
        backup: Whether to create a backup before decryption
        
    Returns:
        True if decryption was successful, False otherwise
    """
    console.print("Starting database decryption process...", style="bold yellow")
    
    warning_text = Text()
    warning_text.append("⚠️  DECRYPTION WARNING ⚠️\n\n", style="bold red")
    warning_text.append("This will decrypt your database, making it unencrypted.\n", style="red")
    warning_text.append("Only use this in emergency situations.\n", style="yellow")
    warning_text.append("Your data will no longer be encrypted at rest.\n", style="red")
    
    console.print(Panel(warning_text, title="Security Warning", border_style="red"))
    
    if not typer.confirm("Are you sure you want to decrypt your database?"):
        console.print("Decryption cancelled", style="yellow")
        return False
    
    # Get database path from config if not provided
    if db_path is None:
        try:
            config = load_config()
            db_path = Path(config.get('db_path', 'prt_data/prt.db'))
        except Exception as e:
            console.print(f"Failed to load config: {e}", style="red")
            return False
    
    # Check if database exists
    if not db_path.exists():
        console.print(f"Database file not found: {db_path}", style="red")
        return False
    
    # Get encryption key if not provided
    if encryption_key is None:
        encryption_key = get_encryption_key()
    
    # Verify encryption key works
    if not verify_encryption_key(encryption_key, db_path):
        console.print("Invalid encryption key or database is not encrypted", style="red")
        return False
    
    # Create backup if requested
    if backup:
        backup_path = backup_database(db_path, ".pre_decryption")
    
    try:
        # Connect to encrypted database
        console.print("Connecting to encrypted database...", style="blue")
        encrypted_db = create_database(db_path, encrypted=True, encryption_key=encryption_key)
        
        # Verify encrypted database
        if not verify_database_integrity(encrypted_db):
            return False
        
        # Create temporary path for decrypted database
        temp_decrypted_path = db_path.with_name(db_path.name + ".decrypted")
        
        # Migrate to unencrypted database
        console.print("Migrating data to unencrypted database...", style="blue")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Migrating data...", total=None)
            
            decrypted_db = migrate_to_encrypted(
                encrypted_db, 
                temp_decrypted_path, 
                None  # No encryption key for unencrypted database
            )
            
            progress.update(task, description="Migration completed")
        
        # Replace encrypted database with decrypted version
        console.print("Replacing encrypted database with decrypted version...", style="blue")
        encrypted_db.session.close()
        decrypted_db.session.close()
        
        # Remove encrypted and rename decrypted
        db_path.unlink()
        temp_decrypted_path.rename(db_path)
        
        # Update configuration
        try:
            config = load_config()
            config['db_encrypted'] = False
            save_config(config)
        except Exception:
            pass
        
        console.print("Database decryption completed successfully!", style="bold green")
        console.print("⚠️  WARNING: Your database is now unencrypted!", style="bold red")
        return True
        
    except Exception as e:
        console.print(f"Decryption failed: {e}", style="red")
        
        # Clean up temporary files
        temp_decrypted_path = db_path.with_name(db_path.name + ".decrypted")
        if temp_decrypted_path.exists():
            temp_decrypted_path.unlink()
        
        return False


@app.command()
def encrypt(
    db_path: Optional[Path] = typer.Option(None, "--db-path", "-p", help="Path to database file"),
    key: Optional[str] = typer.Option(None, "--key", "-k", help="Encryption key (generates new one if not provided)"),
    no_backup: bool = typer.Option(False, "--no-backup", help="Skip backup creation"),
    no_verify: bool = typer.Option(False, "--no-verify", help="Skip verification after encryption"),
    force: bool = typer.Option(False, "--force", help="Force encryption even if already encrypted"),
    no_export_key: bool = typer.Option(False, "--no-export-key", help="Skip encryption key export")
):
    """Encrypt an existing unencrypted database."""
    success = encrypt_database(
        db_path=db_path,
        encryption_key=key,
        backup=not no_backup,
        verify=not no_verify,
        force=force,
        export_key=not no_export_key
    )
    
    if success:
        console.print(Panel("Database encryption completed successfully!", style="green"))
    else:
        console.print(Panel("Database encryption failed!", style="red"))
        raise typer.Exit(1)


@app.command()
def decrypt(
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
        console.print(Panel("Database decryption completed successfully!", style="green"))
    else:
        console.print(Panel("Database decryption failed!", style="red"))
        raise typer.Exit(1)


@app.command()
def export_key(
    export_path: Optional[Path] = typer.Option(None, "--path", "-p", help="Path to export encryption key")
):
    """Export the current encryption key to a backup file."""
    try:
        encryption_key = get_encryption_key()
        export_encryption_key(encryption_key, export_path)
        console.print(Panel("Encryption key exported successfully!", style="green"))
    except Exception as e:
        console.print(f"Failed to export encryption key: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def verify_key(
    key: str = typer.Option(..., "--key", "-k", help="Encryption key to verify"),
    db_path: Optional[Path] = typer.Option(None, "--db-path", "-p", help="Path to database file")
):
    """Verify that an encryption key can decrypt a database."""
    if db_path is None:
        try:
            config = load_config()
            db_path = Path(config.get('db_path', 'prt_data/prt.db'))
        except Exception as e:
            console.print(f"Failed to load config: {e}", style="red")
            raise typer.Exit(1)
    
    if not db_path.exists():
        console.print(f"Database file not found: {db_path}", style="red")
        raise typer.Exit(1)
    
    if verify_encryption_key(key, db_path):
        console.print("✅ Encryption key is valid", style="green")
    else:
        console.print("❌ Encryption key is invalid", style="red")
        raise typer.Exit(1)


@app.command()
def status():
    """Check the encryption status of the database."""
    try:
        config = load_config()
        db_path = Path(config.get('db_path', 'prt_data/prt.db'))
        
        console.print(f"Database path: {db_path}", style="blue")
        console.print(f"Encrypted: {is_database_encrypted(config)}", style="blue")
        
        if db_path.exists():
            # Try to connect and verify
            try:
                if is_database_encrypted(config):
                    db = create_database(db_path, encrypted=True)
                else:
                    db = create_database(db_path, encrypted=False)
                
                if verify_database_integrity(db):
                    console.print("Database status: [green]OK[/green]")
                else:
                    console.print("Database status: [red]CORRUPT[/red]")
            except Exception as e:
                console.print(f"Database status: [red]ERROR[/red] - {e}")
        else:
            console.print("Database status: [yellow]NOT FOUND[/yellow]")
            
    except Exception as e:
        console.print(f"Failed to check status: {e}", style="red")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
