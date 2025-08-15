#!/usr/bin/env python3
"""
Migration script to convert from old schema to new schema.

This script helps migrate existing data from the old relationship schema
to the new schema with separate tags and notes tables.
"""

import sys
from pathlib import Path
import sqlite3
from rich.console import Console

console = Console()


def migrate_old_schema(db_path: Path):
    """Migrate data from old schema to new schema."""
    console.print("Starting schema migration...", style="bold blue")
    
    # Connect to the old database
    old_conn = sqlite3.connect(db_path)
    old_cursor = old_conn.cursor()
    
    try:
        # Check if old schema exists
        old_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='relationships'")
        if not old_cursor.fetchone():
            console.print("No old relationships table found. Migration not needed.", style="green")
            return
        
        # Check if new schema already exists
        old_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tags'")
        if old_cursor.fetchone():
            console.print("New schema already exists. Migration not needed.", style="green")
            return
        
        console.print("Found old schema. Starting migration...", style="yellow")
        
        # Get old relationship data
        old_cursor.execute("SELECT contact_id, tag, note FROM relationships")
        old_relationships = old_cursor.fetchall()
        
        if not old_relationships:
            console.print("No old relationship data found.", style="yellow")
            return
        
        console.print(f"Found {len(old_relationships)} old relationships to migrate.", style="blue")
        
        # Create new tables
        console.print("Creating new tables...", style="blue")
        
        # Create tags table
        old_cursor.execute("""
            CREATE TABLE tags (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create new relationships table
        old_cursor.execute("""
            CREATE TABLE relationships_new (
                id INTEGER PRIMARY KEY,
                contact_id INTEGER NOT NULL UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (contact_id) REFERENCES contacts (id)
            )
        """)
        
        # Create relationship_tags table
        old_cursor.execute("""
            CREATE TABLE relationship_tags (
                relationship_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (relationship_id, tag_id),
                FOREIGN KEY (relationship_id) REFERENCES relationships_new (id),
                FOREIGN KEY (tag_id) REFERENCES tags (id)
            )
        """)
        
        # Create notes table
        old_cursor.execute("""
            CREATE TABLE notes (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create relationship_notes table
        old_cursor.execute("""
            CREATE TABLE relationship_notes (
                relationship_id INTEGER NOT NULL,
                note_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (relationship_id, note_id),
                FOREIGN KEY (relationship_id) REFERENCES relationships_new (id),
                FOREIGN KEY (note_id) REFERENCES notes (id)
            )
        """)
        
        # Migrate data
        console.print("Migrating data...", style="blue")
        
        # Collect unique tags
        unique_tags = set()
        for contact_id, tag, note in old_relationships:
            if tag:
                unique_tags.add(tag)
        
        # Insert tags
        tag_map = {}
        for tag_name in sorted(unique_tags):
            old_cursor.execute("INSERT INTO tags (name) VALUES (?)", (tag_name,))
            tag_id = old_cursor.lastrowid
            tag_map[tag_name] = tag_id
        
        # Collect unique notes
        unique_notes = {}
        for contact_id, tag, note in old_relationships:
            if note and note not in unique_notes:
                # Create a title for the note based on the contact and content
                old_cursor.execute("SELECT name FROM contacts WHERE id = ?", (contact_id,))
                contact_name = old_cursor.fetchone()
                contact_name = contact_name[0] if contact_name else f"Contact {contact_id}"
                note_title = f"Note for {contact_name}"
                unique_notes[note] = note_title
        
        # Insert notes
        note_map = {}
        for note_content, note_title in unique_notes.items():
            old_cursor.execute("INSERT INTO notes (title, content) VALUES (?, ?)", (note_title, note_content))
            note_id = old_cursor.lastrowid
            note_map[note_content] = note_id
        
        # Migrate relationships
        for contact_id, tag, note in old_relationships:
            # Create new relationship
            old_cursor.execute(
                "INSERT INTO relationships_new (contact_id) VALUES (?)",
                (contact_id,)
            )
            relationship_id = old_cursor.lastrowid
            
            # Add tag if present
            if tag and tag in tag_map:
                old_cursor.execute(
                    "INSERT INTO relationship_tags (relationship_id, tag_id) VALUES (?, ?)",
                    (relationship_id, tag_map[tag])
                )
            
            # Add note if present
            if note and note in note_map:
                old_cursor.execute(
                    "INSERT INTO relationship_notes (relationship_id, note_id) VALUES (?, ?)",
                    (relationship_id, note_map[note])
                )
        
        # Drop old table and rename new one
        old_cursor.execute("DROP TABLE relationships")
        old_cursor.execute("ALTER TABLE relationships_new RENAME TO relationships")
        
        # Commit changes
        old_conn.commit()
        
        console.print("Migration completed successfully!", style="bold green")
        console.print(f"Migrated {len(old_relationships)} relationships", style="green")
        console.print(f"Created {len(unique_tags)} unique tags", style="green")
        console.print(f"Created {len(unique_notes)} unique notes", style="green")
        
    except Exception as e:
        console.print(f"Migration failed: {e}", style="bold red")
        old_conn.rollback()
        raise
    finally:
        old_conn.close()


def main():
    """Main migration function."""
    console.print("PRT Schema Migration Tool", style="bold blue")
    console.print("=" * 40)
    
    # Find database file
    db_path = Path("prt_data/prt.db")
    if not db_path.exists():
        console.print("Database not found. Please run the CLI first to create it.", style="red")
        return
    
    console.print(f"Found database: {db_path}", style="green")
    
    # Create backup
    backup_path = db_path.with_suffix('.pre_migration.bak')
    import shutil
    shutil.copy(db_path, backup_path)
    console.print(f"Created backup: {backup_path}", style="blue")
    
    # Run migration
    try:
        migrate_old_schema(db_path)
        console.print("\nMigration successful! You can now run the CLI normally.", style="bold green")
    except Exception as e:
        console.print(f"\nMigration failed: {e}", style="bold red")
        console.print("Your original database has been backed up.", style="yellow")


if __name__ == "__main__":
    main()
