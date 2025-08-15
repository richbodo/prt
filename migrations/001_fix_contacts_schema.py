#!/usr/bin/env python3
"""
Migration 001: Fix Contacts Table Schema

This migration adds missing columns to the contacts table to match the current SQLAlchemy model.
- Adds 'phone' column (TEXT)
- Adds 'created_at' column (DATETIME with default)
- Adds 'updated_at' column (DATETIME with default)

Date: 2024-01-15
Author: PRT Migration System
"""

import sys
from pathlib import Path
import sqlite3
from rich.console import Console

console = Console()


def fix_contacts_schema(db_path: Path):
    """Add missing columns to contacts table."""
    console.print("Migration 001: Fixing contacts table schema...", style="bold blue")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check current schema
        cursor.execute("PRAGMA table_info(contacts)")
        columns = {row[1] for row in cursor.fetchall()}
        
        console.print(f"Current columns: {columns}", style="blue")
        
        # Add missing columns
        missing_columns = []
        
        if 'phone' not in columns:
            missing_columns.append('phone')
            cursor.execute("ALTER TABLE contacts ADD COLUMN phone TEXT")
            console.print("Added phone column", style="green")
        
        if 'created_at' not in columns:
            missing_columns.append('created_at')
            cursor.execute("ALTER TABLE contacts ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
            console.print("Added created_at column", style="green")
        
        if 'updated_at' not in columns:
            missing_columns.append('updated_at')
            cursor.execute("ALTER TABLE contacts ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP")
            console.print("Added updated_at column", style="green")
        
        if not missing_columns:
            console.print("All columns already exist. No changes needed.", style="green")
            return True
        
        # Update existing records to have timestamps
        cursor.execute("""
            UPDATE contacts 
            SET created_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP 
            WHERE created_at IS NULL OR updated_at IS NULL
        """)
        
        # Commit changes
        conn.commit()
        
        console.print(f"Successfully added columns: {missing_columns}", style="bold green")
        
        # Verify the new schema
        cursor.execute("PRAGMA table_info(contacts)")
        new_columns = {row[1] for row in cursor.fetchall()}
        console.print(f"Updated columns: {new_columns}", style="blue")
        
        return True
        
    except Exception as e:
        console.print(f"Migration failed: {e}", style="bold red")
        conn.rollback()
        return False
    finally:
        conn.close()


def rollback(db_path: Path):
    """Rollback migration by removing added columns."""
    console.print("Rolling back migration 001...", style="yellow")
    
    # Note: SQLite doesn't support DROP COLUMN in older versions
    # This would require recreating the table, which is complex
    console.print("Warning: Rollback not implemented for SQLite DROP COLUMN", style="red")
    console.print("Manual rollback required if needed", style="yellow")


def main():
    """Main migration function."""
    console.print("PRT Migration 001: Contacts Schema Fix", style="bold blue")
    console.print("=" * 40)
    
    # Find database file
    db_path = Path("../prt_data/prt.db")
    if not db_path.exists():
        console.print("Database not found. Please run the CLI first to create it.", style="red")
        return False
    
    console.print(f"Found database: {db_path}", style="green")
    
    # Create backup
    backup_path = db_path.with_suffix('.pre_migration_001.bak')
    import shutil
    shutil.copy(db_path, backup_path)
    console.print(f"Created backup: {backup_path}", style="blue")
    
    # Run migration
    try:
        success = fix_contacts_schema(db_path)
        if success:
            console.print("\nMigration 001 successful!", style="bold green")
            return True
        else:
            console.print("\nMigration 001 failed!", style="bold red")
            return False
    except Exception as e:
        console.print(f"\nMigration 001 failed: {e}", style="bold red")
        console.print("Your original database has been backed up.", style="yellow")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
