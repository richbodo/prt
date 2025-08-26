"""
PRT API Layer

This module provides a clean API for PRT operations that can be used by both
the CLI interface and AI chat mode. It abstracts database operations and
provides a consistent interface for all PRT functionality.
"""

from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from .db import Database
from .config import load_config, data_dir
from .schema_manager import SchemaManager


class PRTAPI:
    """Main API class for PRT operations."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize PRT API with configuration."""
        if config is None:
            config = load_config()
        
        # Get database path from config
        db_path = Path(config["db_path"])
        
        # Create database instance
        self.db = Database(db_path)
        self.db.connect()
        
        # Initialize schema manager and check for migrations
        self.schema_manager = SchemaManager(self.db)
        
        # Auto-migrate if needed (with user safety)
        current_version = self.schema_manager.get_schema_version()
        if current_version > 0 and self.schema_manager.check_migration_needed():
            # Only auto-migrate if we have an existing schema to migrate
            from rich.console import Console
            console = Console()
            console.print("\n🔄 Database schema update needed...", style="blue")
            success = self.schema_manager.migrate_safely()
            if not success:
                raise RuntimeError("Database migration failed. See instructions above to recover.")
    
    # Database management operations
    def get_database_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        return {
            "contacts": self.db.count_contacts(),
            "relationships": self.db.count_relationships()
        }
    
    def validate_database(self) -> bool:
        """Validate database integrity."""
        return self.db.is_valid()
    
    def backup_database(self, suffix: str = ".bak") -> Path:
        """Create database backup."""
        return self.db.backup(suffix)
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        return load_config()
    
    def get_data_directory(self) -> Path:
        """Get data directory path."""
        return data_dir()
    
    def test_database_connection(self) -> bool:
        """Test database connection and credentials."""
        try:
            return self.db.is_valid()
        except Exception:
            return False

    # Search operations
    def search_contacts(self, query: str) -> List[Dict[str, Any]]:
        """Search contacts by name (case-insensitive partial match)."""
        from .models import Contact
        
        contacts = self.db.session.query(Contact).filter(
            Contact.name.ilike(f"%{query}%")
        ).order_by(Contact.name).all()
        
        return [
            {
                "id": c.id,
                "name": c.name,
                "email": c.email,
                "phone": c.phone,
                "relationship_info": self.get_relationship_info(c.id)
            }
            for c in contacts
        ]
    
    def search_tags(self, query: str) -> List[Dict[str, Any]]:
        """Search tags by name (case-insensitive partial match)."""
        from .models import Tag
        
        tags = self.db.session.query(Tag).filter(
            Tag.name.ilike(f"%{query}%")
        ).order_by(Tag.name).all()
        
        return [
            {
                "id": t.id,
                "name": t.name,
                "contact_count": len(t.relationships)
            }
            for t in tags
        ]
    
    def search_notes(self, query: str) -> List[Dict[str, Any]]:
        """Search notes by title or content (case-insensitive partial match)."""
        from .models import Note
        
        notes = self.db.session.query(Note).filter(
            (Note.title.ilike(f"%{query}%")) | (Note.content.ilike(f"%{query}%"))
        ).order_by(Note.title).all()
        
        return [
            {
                "id": n.id,
                "title": n.title,
                "content": n.content,
                "contact_count": len(n.relationships)
            }
            for n in notes
        ]
    
    def get_contacts_by_tag(self, tag_name: str) -> List[Dict[str, Any]]:
        """Get all contacts that have a specific tag."""
        from .models import Tag, Contact
        
        tag = self.db.session.query(Tag).filter(Tag.name == tag_name).first()
        if not tag:
            return []
        
        contacts = []
        for relationship in tag.relationships:
            contact = relationship.contact
            contacts.append({
                "id": contact.id,
                "name": contact.name,
                "email": contact.email,
                "phone": contact.phone,
                "relationship_info": self.get_relationship_info(contact.id)
            })
        
        return sorted(contacts, key=lambda c: c["name"])
    
    def get_contacts_by_note(self, note_title: str) -> List[Dict[str, Any]]:
        """Get all contacts that have a specific note."""
        from .models import Note, Contact
        
        note = self.db.session.query(Note).filter(Note.title == note_title).first()
        if not note:
            return []
        
        contacts = []
        for relationship in note.relationships:
            contact = relationship.contact
            contacts.append({
                "id": contact.id,
                "name": contact.name,
                "email": contact.email,
                "phone": contact.phone,
                "relationship_info": self.get_relationship_info(contact.id)
            })
        
        return sorted(contacts, key=lambda c: c["name"])
    
    def get_relationship_info(self, contact_id: int) -> Dict[str, Any]:
        """Get relationship information for a contact."""
        return self.db.get_relationship_info(contact_id)
    
    # CRUD operations for relationships
    def add_tag_to_contact(self, contact_id: int, tag_name: str) -> bool:
        """Add a tag to a contact's relationship."""
        try:
            self.db.add_relationship_tag(contact_id, tag_name)
            return True
        except ValueError:
            return False
    
    def remove_tag_from_contact(self, contact_id: int, tag_name: str) -> bool:
        """Remove a tag from a contact's relationship."""
        from .models import Contact, Tag
        
        contact = self.db.session.query(Contact).filter(Contact.id == contact_id).first()
        if not contact or not contact.relationship:
            return False
        
        tag = self.db.session.query(Tag).filter(Tag.name == tag_name).first()
        if not tag or tag not in contact.relationship.tags:
            return False
        
        contact.relationship.tags.remove(tag)
        self.db.session.commit()
        return True
    
    def add_note_to_contact(self, contact_id: int, note_title: str, note_content: str) -> bool:
        """Add a note to a contact's relationship."""
        try:
            self.db.add_relationship_note(contact_id, note_title, note_content)
            return True
        except ValueError:
            return False
    
    def remove_note_from_contact(self, contact_id: int, note_title: str) -> bool:
        """Remove a note from a contact's relationship."""
        from .models import Contact, Note
        
        contact = self.db.session.query(Contact).filter(Contact.id == contact_id).first()
        if not contact or not contact.relationship:
            return False
        
        note = self.db.session.query(Note).filter(Note.title == note_title).first()
        if not note or note not in contact.relationship.notes:
            return False
        
        contact.relationship.notes.remove(note)
        self.db.session.commit()
        return True
    
    # Management operations for tags and notes
    def list_all_tags(self) -> List[Dict[str, Any]]:
        """List all tags with usage information."""
        from .models import Tag
        
        tags = self.db.session.query(Tag).order_by(Tag.name).all()
        return [
            {
                "id": t.id,
                "name": t.name,
                "contact_count": len(t.relationships)
            }
            for t in tags
        ]
    
    def create_tag(self, name: str) -> Optional[Dict[str, Any]]:
        """Create a new tag."""
        from .models import Tag
        
        # Check if tag already exists
        existing = self.db.session.query(Tag).filter(Tag.name == name).first()
        if existing:
            return None
        
        tag = Tag(name=name)
        self.db.session.add(tag)
        self.db.session.commit()
        
        return {
            "id": tag.id,
            "name": tag.name,
            "contact_count": 0
        }
    
    def delete_tag(self, name: str) -> bool:
        """Delete a tag (removes it from all relationships)."""
        from .models import Tag
        
        tag = self.db.session.query(Tag).filter(Tag.name == name).first()
        if not tag:
            return False
        
        # Remove tag from all relationships
        for relationship in tag.relationships:
            relationship.tags.remove(tag)
        
        self.db.session.delete(tag)
        self.db.session.commit()
        return True
    
    def list_all_notes(self) -> List[Dict[str, Any]]:
        """List all notes with usage information."""
        from .models import Note
        
        notes = self.db.session.query(Note).order_by(Note.title).all()
        return [
            {
                "id": n.id,
                "title": n.title,
                "content": n.content,
                "contact_count": len(n.relationships)
            }
            for n in notes
        ]
    
    def create_note(self, title: str, content: str) -> Optional[Dict[str, Any]]:
        """Create a new note."""
        from .models import Note
        
        # Check if note already exists
        existing = self.db.session.query(Note).filter(Note.title == title).first()
        if existing:
            return None
        
        note = Note(title=title, content=content)
        self.db.session.add(note)
        self.db.session.commit()
        
        return {
            "id": note.id,
            "title": note.title,
            "content": note.content,
            "contact_count": 0
        }
    
    def update_note(self, title: str, content: str) -> bool:
        """Update an existing note's content."""
        from .models import Note
        
        note = self.db.session.query(Note).filter(Note.title == title).first()
        if not note:
            return False
        
        note.content = content
        self.db.session.commit()
        return True
    
    def delete_note(self, title: str) -> bool:
        """Delete a note (removes it from all relationships)."""
        from .models import Note
        
        note = self.db.session.query(Note).filter(Note.title == title).first()
        if not note:
            return False
        
        # Remove note from all relationships
        for relationship in note.relationships:
            relationship.notes.remove(note)
        
        self.db.session.delete(note)
        self.db.session.commit()
        return True
    
    def get_contact_details(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific contact."""
        from .models import Contact
        
        contact = self.db.session.query(Contact).filter(Contact.id == contact_id).first()
        if not contact:
            return None
        
        return {
            "id": contact.id,
            "name": contact.name,
            "email": contact.email,
            "phone": contact.phone,
            "relationship_info": self.get_relationship_info(contact.id)
        }
    
    def list_all_contacts(self) -> List[Dict[str, Any]]:
        """List all contacts with basic relationship info."""
        from .models import Contact
        
        contacts = self.db.session.query(Contact).order_by(Contact.name).all()
        return [
            {
                "id": c.id,
                "name": c.name,
                "email": c.email,
                "phone": c.phone,
                "relationship_info": self.get_relationship_info(c.id)
            }
            for c in contacts
        ]
    
    def import_contacts(self, contacts: List[Dict[str, Any]]) -> bool:
        """Import contacts from parsed CSV data."""
        try:
            self.db.insert_contacts(contacts)
            return True
        except Exception as e:
            print(f"Error importing contacts: {e}")
            return False
    
    def insert_contacts(self, contacts: List[Dict[str, Any]]) -> bool:
        """Insert contacts into the database."""
        try:
            self.db.insert_contacts(contacts)
            return True
        except Exception as e:
            print(f"Error inserting contacts: {e}")
            return False
    
    def parse_csv_contacts(self, csv_path: str) -> List[Dict[str, Any]]:
        """Parse CSV file and return contacts data."""
        try:
            from utils.google_contacts_summary import parse_contacts
            return parse_contacts(csv_path)
        except Exception as e:
            print(f"Error parsing CSV file: {e}")
            return []
    
    def get_csv_files(self) -> List[Path]:
        """Get list of available CSV files in data directory."""
        data_dir_path = self.get_data_directory()
        return list(data_dir_path.glob("*.csv"))
