"""
PRT API Layer

This module provides a clean API for PRT operations that can be used by both
the CLI interface and AI chat mode. It abstracts database operations and
provides a consistent interface for all PRT functionality.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import data_dir, load_config
from .db import Database
from .logging_config import get_logger
from .schema_manager import SchemaManager


class PRTAPI:
    """Main API class for PRT operations."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize PRT API with configuration."""
        self.logger = get_logger(__name__)

        try:
            if config is None:
                config = load_config()
            # Get database path from config
            db_path = Path(config["db_path"])
        except Exception as e:
            raise RuntimeError(f"Failed to initialize configuration: {e}") from e

        # Create database instance
        self.db = Database(db_path)
        try:
            self.db.connect()
        except Exception as e:
            raise RuntimeError(f"Failed to connect to database: {e}") from e

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
            "relationships": self.db.count_relationships(),
        }

    def validate_database(self) -> bool:
        """Validate database integrity."""
        return self.db.is_valid()

    def backup_database(self, suffix: str = ".bak") -> Path:
        """Create database backup."""
        return self.db.backup(suffix)

    def create_backup_with_comment(self, comment: str = None, auto: bool = False) -> Dict[str, Any]:
        """Create a tracked backup with optional comment.

        Args:
            comment: Description of why backup was created
            auto: Whether this is an automatic backup

        Returns:
            Dictionary with backup details
        """
        if not comment and not auto:
            comment = "Manual backup"
        elif not comment and auto:
            from datetime import datetime

            comment = f"Automatic backup at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        return self.db.create_backup_with_metadata(comment, is_auto=auto)

    def get_backup_history(self) -> List[Dict[str, Any]]:
        """Get list of all tracked backups with metadata.

        Returns:
            List of backup dictionaries sorted by date (newest first)
        """
        return self.db.list_backups()

    def restore_from_backup(self, backup_id: int) -> bool:
        """Restore database from a specific backup.

        Args:
            backup_id: ID of the backup to restore

        Returns:
            True if restoration was successful

        Raises:
            ValueError: If backup ID not found
            FileNotFoundError: If backup file doesn't exist
        """
        # Create safety backup before restore
        self.create_backup_with_comment(
            comment=f"Safety backup before restoring backup ID {backup_id}", auto=True
        )

        return self.db.restore_backup(backup_id)

    def cleanup_auto_backups(self, keep_count: int = 10):
        """Clean up old automatic backups.

        Args:
            keep_count: Number of automatic backups to keep
        """
        self.db.cleanup_old_auto_backups(keep_count)

    def auto_backup_before_operation(self, operation: str) -> Dict[str, Any]:
        """Create automatic backup before a potentially dangerous operation.

        Args:
            operation: Description of the operation about to be performed

        Returns:
            Backup details dictionary
        """
        comment = f"Auto-backup before: {operation}"
        return self.create_backup_with_comment(comment, auto=True)

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

        contacts = (
            self.db.session.query(Contact)
            .filter(Contact.name.ilike(f"%{query}%"))
            .order_by(Contact.name)
            .all()
        )

        return [
            {
                "id": c.id,
                "name": c.name,
                "email": c.email,
                "phone": c.phone,
                "profile_image": c.profile_image,
                "profile_image_filename": c.profile_image_filename,
                "profile_image_mime_type": c.profile_image_mime_type,
                "relationship_info": self.get_relationship_info(c.id),
            }
            for c in contacts
        ]

    def search_tags(self, query: str) -> List[Dict[str, Any]]:
        """Search tags by name (case-insensitive partial match)."""
        from .models import Tag

        tags = (
            self.db.session.query(Tag).filter(Tag.name.ilike(f"%{query}%")).order_by(Tag.name).all()
        )

        return [{"id": t.id, "name": t.name, "contact_count": len(t.relationships)} for t in tags]

    def search_notes(self, query: str) -> List[Dict[str, Any]]:
        """Search notes by title or content (case-insensitive partial match)."""
        from .models import Note

        notes = (
            self.db.session.query(Note)
            .filter((Note.title.ilike(f"%{query}%")) | (Note.content.ilike(f"%{query}%")))
            .order_by(Note.title)
            .all()
        )

        return [
            {
                "id": n.id,
                "title": n.title,
                "content": n.content,
                "contact_count": len(n.relationships),
            }
            for n in notes
        ]

    def get_contacts_by_tag(self, tag_name: str) -> List[Dict[str, Any]]:
        """Get all contacts that have a specific tag."""
        from .models import Tag

        tag = self.db.session.query(Tag).filter(Tag.name == tag_name).first()
        if not tag:
            return []

        contacts = []
        for relationship in tag.relationships:
            contact = relationship.contact
            contacts.append(
                {
                    "id": contact.id,
                    "name": contact.name,
                    "email": contact.email,
                    "phone": contact.phone,
                    "profile_image": contact.profile_image,
                    "profile_image_filename": contact.profile_image_filename,
                    "profile_image_mime_type": contact.profile_image_mime_type,
                    "relationship_info": self.get_relationship_info(contact.id),
                }
            )

        return sorted(contacts, key=lambda c: c["name"])

    def get_contacts_by_note(self, note_title: str) -> List[Dict[str, Any]]:
        """Get all contacts that have a specific note."""
        from .models import Note

        note = self.db.session.query(Note).filter(Note.title == note_title).first()
        if not note:
            return []

        contacts = []
        for relationship in note.relationships:
            contact = relationship.contact
            contacts.append(
                {
                    "id": contact.id,
                    "name": contact.name,
                    "email": contact.email,
                    "phone": contact.phone,
                    "profile_image": contact.profile_image,
                    "profile_image_filename": contact.profile_image_filename,
                    "profile_image_mime_type": contact.profile_image_mime_type,
                    "relationship_info": self.get_relationship_info(contact.id),
                }
            )

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
        return [{"id": t.id, "name": t.name, "contact_count": len(t.relationships)} for t in tags]

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

        return {"id": tag.id, "name": tag.name, "contact_count": 0}

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
                "contact_count": len(n.relationships),
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
            "contact_count": 0,
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
            "profile_image": contact.profile_image,
            "profile_image_filename": contact.profile_image_filename,
            "profile_image_mime_type": contact.profile_image_mime_type,
            "relationship_info": self.get_relationship_info(contact.id),
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
                "profile_image": c.profile_image,
                "profile_image_filename": c.profile_image_filename,
                "profile_image_mime_type": c.profile_image_mime_type,
                "relationship_info": self.get_relationship_info(c.id),
            }
            for c in contacts
        ]

    def import_contacts(self, contacts: List[Dict[str, Any]]) -> bool:
        """Import contacts from parsed CSV data."""
        try:
            self.db.insert_contacts(contacts)
            return True
        except Exception as e:
            self.logger.error(f"Error importing contacts: {e}", exc_info=True)
            return False

    def insert_contacts(self, contacts: List[Dict[str, Any]]) -> bool:
        """Insert contacts into the database."""
        try:
            self.db.insert_contacts(contacts)
            return True
        except Exception as e:
            self.logger.error(f"Error inserting contacts: {e}", exc_info=True)
            return False

    def parse_csv_contacts(self, csv_path: str) -> List[Dict[str, Any]]:
        """Parse CSV file and return contacts data."""
        try:
            from utils.google_contacts_summary import parse_contacts

            return parse_contacts(csv_path)
        except Exception as e:
            self.logger.error(f"Error parsing CSV file: {e}", exc_info=True)
            return []

    def get_csv_files(self) -> List[Path]:
        """Get list of available CSV files in data directory."""
        data_dir_path = self.get_data_directory()
        return list(data_dir_path.glob("*.csv"))

    # ========== New Relationship Type Management API Methods ==========

    def list_all_relationship_types(self) -> List[Dict[str, Any]]:
        """List all available relationship types."""
        types = self.db.list_relationship_types()

        # Add usage count for each type
        from .models import ContactRelationship

        for rel_type in types:
            count = (
                self.db.session.query(ContactRelationship)
                .filter(ContactRelationship.type_id == rel_type["id"])
                .count()
            )
            rel_type["usage_count"] = count

        return types

    def create_relationship_type(
        self,
        type_key: str,
        description: str,
        inverse_key: str,
        is_symmetrical: bool = False,
    ) -> bool:
        """Create a new relationship type."""
        try:
            self.db.create_relationship_type(type_key, description, inverse_key, is_symmetrical)
            return True
        except Exception as e:
            self.logger.error(f"Error creating relationship type: {e}", exc_info=True)
            return False

    def delete_relationship_type(self, type_key: str) -> bool:
        """Delete a relationship type if not in use."""
        from .models import ContactRelationship, RelationshipType

        try:
            # Check if type exists
            rel_type = (
                self.db.session.query(RelationshipType)
                .filter(RelationshipType.type_key == type_key)
                .first()
            )
            if not rel_type:
                return False

            # Check if it's in use
            count = (
                self.db.session.query(ContactRelationship)
                .filter(ContactRelationship.type_id == rel_type.id)
                .count()
            )
            if count > 0:
                print(
                    f"Cannot delete relationship type '{type_key}' - it's used by {count} relationships"
                )
                return False

            # Delete the type
            self.db.session.delete(rel_type)
            self.db.session.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error deleting relationship type: {e}", exc_info=True)
            self.db.session.rollback()
            return False

    def add_contact_relationship(
        self,
        from_contact_name: str,
        to_contact_name: str,
        type_key: str,
        start_date=None,
        end_date=None,
    ) -> bool:
        """Add a relationship between two contacts by name."""
        try:
            # Find contacts by name
            from_contacts = self.search_contacts(from_contact_name)
            to_contacts = self.search_contacts(to_contact_name)

            if not from_contacts:
                print(f"Contact '{from_contact_name}' not found")
                return False
            if not to_contacts:
                print(f"Contact '{to_contact_name}' not found")
                return False

            # Use the first match for each
            from_id = from_contacts[0]["id"]
            to_id = to_contacts[0]["id"]

            self.db.create_contact_relationship(from_id, to_id, type_key, start_date, end_date)
            return True
        except Exception as e:
            self.logger.error(f"Error adding relationship: {e}", exc_info=True)
            return False

    def remove_contact_relationship(
        self, from_contact_name: str, to_contact_name: str, type_key: str
    ) -> bool:
        """Remove a relationship between two contacts."""
        try:
            # Find contacts by name
            from_contacts = self.search_contacts(from_contact_name)
            to_contacts = self.search_contacts(to_contact_name)

            if not from_contacts or not to_contacts:
                return False

            from_id = from_contacts[0]["id"]
            to_id = to_contacts[0]["id"]

            self.db.delete_contact_relationship(from_id, to_id, type_key)
            return True
        except Exception as e:
            self.logger.error(f"Error removing relationship: {e}", exc_info=True)
            return False

    def get_contact_relationships(
        self, contact_name: str, type_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all relationships for a contact."""
        contacts = self.search_contacts(contact_name)
        if not contacts:
            return []

        relationships = self.db.get_contact_relationships(contacts[0]["id"])

        # Apply type filter if specified
        if type_filter:
            relationships = [r for r in relationships if r["type"] == type_filter]

        return relationships

    def get_family_tree(self, contact_name: str) -> Dict[str, Any]:
        """Get family tree structure for a contact."""
        contacts = self.search_contacts(contact_name)
        if not contacts:
            return {}

        contact_id = contacts[0]["id"]
        relationships = self.db.get_contact_relationships(contact_id)

        # Build family tree structure
        family = {
            "contact": contacts[0],
            "parents": [],
            "children": [],
            "siblings": [],
            "spouse": None,
        }

        for rel in relationships:
            if rel["type"] == "parent_of":
                family["children"].append(rel)
            elif rel["type"] == "child_of":
                family["parents"].append(rel)
            elif rel["type"] == "sibling_of":
                family["siblings"].append(rel)
            elif rel["type"] == "spouse_of":
                family["spouse"] = rel

        return family

    def get_relationship_graph(self) -> Dict[str, Any]:
        """Get all relationships in a graph structure."""
        from .models import Contact, ContactRelationship, RelationshipType

        # Get all relationships
        relationships = (
            self.db.session.query(ContactRelationship, RelationshipType, Contact, Contact)
            .join(RelationshipType, ContactRelationship.type_id == RelationshipType.id)
            .join(Contact, ContactRelationship.from_contact_id == Contact.id)
            .join(Contact, ContactRelationship.to_contact_id == Contact.id, isouter=True)
            .all()
        )

        # Build graph structure
        nodes = set()
        edges = []

        for rel, rel_type, from_contact, to_contact in relationships:
            if from_contact:
                nodes.add((from_contact.id, from_contact.name))
            if to_contact:
                nodes.add((to_contact.id, to_contact.name))

            if from_contact and to_contact:
                edges.append(
                    {
                        "from": from_contact.id,
                        "to": to_contact.id,
                        "type": rel_type.type_key,
                        "description": rel_type.description,
                    }
                )

        return {
            "nodes": [{"id": id, "name": name} for id, name in nodes],
            "edges": edges,
        }
