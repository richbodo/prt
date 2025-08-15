#!/usr/bin/env python3
"""
Migration 002: Fix Relationships Table Schema

This migration updates the relationships table from the old schema (tag, note columns)
to the new schema with proper many-to-many relationships.
- Recreates relationships table with created_at, updated_at columns
- Creates tags, notes, relationship_tags, relationship_notes tables
- Migrates existing data to new schema structure

Date: 2024-01-15
Author: PRT Migration System
"""

import sys
from pathlib import Path
import sqlite3
from rich.console import Console

console = Console()


def fix_relationships_schema(db_path: Path):
    """Update relationships table schema."""
    console.print("Migration 002: Fixing relationships table schema...", style="bold blue")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check current schema
        cursor.execute("PRAGMA table_info(relationships)")
        columns = {row[1] for row in cursor.fetchall()}
        
        console.print(f"Current columns: {columns}", style="blue")
        
        # Check if this is the old schema (has tag/note columns)
        if 'tag' in columns or 'note' in columns:
            console.print("Found old relationships schema. Migrating to new schema...", style="yellow")
            
            # Get existing data
            cursor.execute("SELECT contact_id, tag, note FROM relationships")
            old_data = cursor.fetchall()
            
            console.print(f"Found {len(old_data)} existing relationships to migrate.", style="blue")
            
            # Drop old table
            cursor.execute("DROP TABLE relationships")
            
            # Create new table with correct schema
            cursor.execute("""
                CREATE TABLE relationships (
                    id INTEGER PRIMARY KEY,
                    contact_id INTEGER NOT NULL UNIQUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (contact_id) REFERENCES contacts (id)
                )
            """)
            
            # Create tags table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create relationship_tags table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS relationship_tags (
                    relationship_id INTEGER NOT NULL,
                    tag_id INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (relationship_id, tag_id),
                    FOREIGN KEY (relationship_id) REFERENCES relationships (id),
                    FOREIGN KEY (tag_id) REFERENCES tags (id)
                )
            """)
            
            # Create notes table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create relationship_notes table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS relationship_notes (
                    relationship_id INTEGER NOT NULL,
                    note_id INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (relationship_id, note_id),
                    FOREIGN KEY (relationship_id) REFERENCES relationships (id),
                    FOREIGN KEY (note_id) REFERENCES notes (id)
                )
            """)
            
            # Migrate data
            console.print("Migrating relationship data...", style="blue")
            
            # Collect unique tags and notes
            unique_tags = set()
            unique_notes = {}
            
            for contact_id, tag, note in old_data:
                if tag:
                    unique_tags.add(tag)
                if note and note not in unique_notes:
                    # Create a title for the note
                    cursor.execute("SELECT name FROM contacts WHERE id = ?", (contact_id,))
                    contact_name = cursor.fetchone()
                    contact_name = contact_name[0] if contact_name else f"Contact {contact_id}"
                    note_title = f"Note for {contact_name}"
                    unique_notes[note] = note_title
            
            # Insert tags
            tag_map = {}
            for tag_name in sorted(unique_tags):
                cursor.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,))
                cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
                tag_id = cursor.fetchone()[0]
                tag_map[tag_name] = tag_id
            
            # Insert notes
            note_map = {}
            for note_content, note_title in unique_notes.items():
                cursor.execute("INSERT INTO notes (title, content) VALUES (?, ?)", (note_title, note_content))
                note_id = cursor.lastrowid
                note_map[note_content] = note_id
            
            # Migrate relationships
            for contact_id, tag, note in old_data:
                # Create new relationship
                cursor.execute(
                    "INSERT INTO relationships (contact_id) VALUES (?)",
                    (contact_id,)
                )
                relationship_id = cursor.lastrowid
                
                # Add tag if present
                if tag and tag in tag_map:
                    cursor.execute(
                        "INSERT INTO relationship_tags (relationship_id, tag_id) VALUES (?, ?)",
                        (relationship_id, tag_map[tag])
                    )
                
                # Add note if present
                if note and note in note_map:
                    cursor.execute(
                        "INSERT INTO relationship_notes (relationship_id, note_id) VALUES (?, ?)",
                        (relationship_id, note_map[note])
                    )
            
            console.print(f"Successfully migrated {len(old_data)} relationships", style="green")
            console.print(f"Created {len(unique_tags)} unique tags", style="green")
            console.print(f"Created {len(unique_notes)} unique notes", style="green")
            
        else:
            # Check if new schema columns exist
            missing_columns = []
            
            if 'created_at' not in columns:
                missing_columns.append('created_at')
                cursor.execute("ALTER TABLE relationships ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
                console.print("Added created_at column", style="green")
            
            if 'updated_at' not in columns:
                missing_columns.append('updated_at')
                cursor.execute("ALTER TABLE relationships ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP")
                console.print("Added updated_at column", style="green")
            
            if not missing_columns:
                console.print("All columns already exist. No changes needed.", style="green")
                return True
            
            # Update existing records to have timestamps
            cursor.execute("""
                UPDATE relationships 
                SET created_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP 
                WHERE created_at IS NULL OR updated_at IS NULL
            """)
            
            console.print(f"Successfully added columns: {missing_columns}", style="green")
        
        # Commit changes
        conn.commit()
        
        # Verify the new schema
        cursor.execute("PRAGMA table_info(relationships)")
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
    """Rollback migration (not implemented for complex schema changes)."""
    console.print("Rolling back migration 002...", style="yellow")
    console.print("Warning: Rollback not implemented for complex schema changes", style="red")
    console.print("Manual rollback required if needed", style="yellow")


def main():
    """Main migration function."""
    console.print("PRT Migration 002: Relationships Schema Fix", style="bold blue")
    console.print("=" * 45)
    
    # Find database file
    db_path = Path("../prt_data/prt.db")
    if not db_path.exists():
        console.print("Database not found. Please run the CLI first to create it.", style="red")
        return False
    
    console.print(f"Found database: {db_path}", style="green")
    
    # Create backup
    backup_path = db_path.with_suffix('.pre_migration_002.bak')
    import shutil
    shutil.copy(db_path, backup_path)
    console.print(f"Created backup: {backup_path}", style="blue")
    
    # Run migration
    try:
        success = fix_relationships_schema(db_path)
        if success:
            console.print("\nMigration 002 successful!", style="bold green")
            return True
        else:
            console.print("\nMigration 002 failed!", style="bold red")
            return False
    except Exception as e:
        console.print(f"\nMigration 002 failed: {e}", style="bold red")
        console.print("Your original database has been backed up.", style="yellow")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
