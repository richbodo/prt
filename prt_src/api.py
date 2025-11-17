"""
PRT API Layer

This module provides a clean API for PRT operations that can be used by both
the CLI interface and AI chat mode. It abstracts database operations and
provides a consistent interface for all PRT functionality.
"""

import re
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .config import data_dir
from .config import load_config
from .db import Database
from .logging_config import get_logger
from .schema_info import get_schema_for_llm
from .schema_info import validate_sql_schema
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

        # Auto-migrate if needed (with user safety) - but skip in test environments
        if not self._is_test_environment():
            current_version = self.schema_manager.get_schema_version()
            if current_version > 0 and self.schema_manager.check_migration_needed():
                # Only auto-migrate if we have an existing schema to migrate
                from rich.console import Console

                console = Console()
                console.print("\n🔄 Database schema update needed...", style="blue")
                success = self.schema_manager.migrate_safely()
                if not success:
                    raise RuntimeError(
                        "Database migration failed. See instructions above to recover."
                    )
        else:
            self.logger.debug("[PRTAPI] Test environment detected - skipping auto-migration")

    def _is_test_environment(self) -> bool:
        """Detect if we're running in a test environment.

        Returns:
            True if running in tests, False otherwise
        """
        import os
        import sys

        # Check for pytest in the command line or modules
        if "pytest" in sys.modules or (sys.argv and "pytest" in sys.argv[0]):
            return True

        # Check for test database paths
        db_path_str = str(self.db.path)
        if any(
            test_indicator in db_path_str.lower()
            for test_indicator in ["test.db", "test_", "/tmp/", "debug.db", "empty_test"]
        ):
            return True

        # Check for test environment variables
        if os.environ.get("PYTEST_CURRENT_TEST") or os.environ.get("PRT_TEST_MODE"):
            return True

        # Check if we're in a temp directory (common for test fixtures)
        return "/tmp" in db_path_str or "temp" in db_path_str.lower()

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

    def execute_sql(self, sql: str, confirm: bool = False) -> Dict[str, Any]:
        """Execute raw SQL against the database.

        Args:
            sql: SQL query to execute
            confirm: Required for write operations

        Returns:
            Dict containing rows (for SELECT), rowcount, and error message if any
        """
        result: Dict[str, Any] = {"rows": None, "rowcount": 0, "error": None}

        # Basic detection of write operations
        normalized = re.sub(r"\s+", " ", sql.strip()).lower()
        write_ops = ("insert", "update", "delete", "replace", "drop", "create", "alter")
        is_write = not normalized.startswith(("select", "with", "pragma", "explain")) and any(
            op in normalized for op in write_ops
        )

        if is_write and not confirm:
            result["error"] = "Write operation requires confirmation"
            return result

        if is_write:
            try:
                self.auto_backup_before_operation("execute_sql")
            except Exception as e:
                self.logger.error(f"Backup before SQL execution failed: {e}")

        try:
            res = self.db.session.execute(text(sql))
            if res.returns_rows:
                rows = [dict(row._mapping) for row in res]
                result["rows"] = rows
                result["rowcount"] = len(rows)
            else:
                result["rowcount"] = res.rowcount
            if is_write:
                self.db.session.commit()
        except SQLAlchemyError as e:
            self.db.session.rollback()

            # Enhanced error handling with schema information
            error_msg = str(e)
            enhanced_error = self._enhance_sql_error(sql, error_msg)
            result["error"] = enhanced_error
            self.logger.error(f"Error executing SQL: {e}", exc_info=True)

        return result

    def _enhance_sql_error(self, sql: str, error_msg: str) -> str:
        """Enhance SQL error messages with schema information and suggestions.

        Args:
            sql: The SQL query that failed
            error_msg: The original error message

        Returns:
            Enhanced error message with schema guidance
        """
        enhanced_msg = error_msg

        # Check for common schema-related errors
        if "no such column" in error_msg.lower():
            # Extract column name from error
            import re

            match = re.search(r"no such column:\s*(\w+)", error_msg, re.IGNORECASE)
            if match:
                missing_column = match.group(1)
                enhanced_msg += "\n\n📋 SCHEMA HELP:\n"
                enhanced_msg += f"Column '{missing_column}' does not exist in the database.\n"

                # Validate SQL to get suggestions
                validation = validate_sql_schema(sql)
                if validation.get("suggestions"):
                    enhanced_msg += "\n💡 SUGGESTIONS:\n"
                    for suggestion in validation["suggestions"]:
                        enhanced_msg += f"• {suggestion}\n"

        elif "no such table" in error_msg.lower():
            # Extract table name from error
            import re

            match = re.search(r"no such table:\s*(\w+)", error_msg, re.IGNORECASE)
            if match:
                missing_table = match.group(1)
                enhanced_msg += "\n\n📋 SCHEMA HELP:\n"
                enhanced_msg += f"Table '{missing_table}' does not exist in the database.\n"

                from .schema_info import schema_generator

                valid_tables = schema_generator.get_table_names()
                enhanced_msg += "\n💡 AVAILABLE TABLES:\n"
                for table in valid_tables:
                    enhanced_msg += f"• {table}\n"

        # Always add a reference to schema information
        enhanced_msg += "\n\n📖 For complete schema information, ask: 'Show me the database schema'"

        return enhanced_msg

    def get_database_schema(self) -> str:
        """Get formatted database schema information for display.

        Returns:
            Formatted schema information
        """
        try:
            return get_schema_for_llm()
        except Exception as e:
            self.logger.error(f"Error getting schema info: {e}")
            return f"Error retrieving schema information: {str(e)}"

    def validate_sql_query(self, sql: str) -> Dict[str, Any]:
        """Validate SQL query against database schema.

        Args:
            sql: SQL query to validate

        Returns:
            Dictionary with validation results
        """
        try:
            return validate_sql_schema(sql)
        except Exception as e:
            self.logger.error(f"Error validating SQL: {e}")
            return {
                "valid": False,
                "errors": [f"Validation error: {str(e)}"],
                "warnings": [],
                "suggestions": [],
            }

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

    def _query_relationships(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """Query contact-to-contact relationships with optional filtering.

        Private helper method used by both search_relationships and list_all_relationships
        to reduce code duplication.

        Args:
            query: Optional search query (case-insensitive partial match on contact names
                   or relationship type). If None, returns all relationships.

        Returns:
            List of relationship dictionaries with from/to contact info and type
        """
        from sqlalchemy.orm import aliased

        from .models import Contact
        from .models import ContactRelationship
        from .models import RelationshipType

        # Create aliases for from_contact and to_contact to distinguish them in the query
        FromContact = aliased(Contact)
        ToContact = aliased(Contact)

        # Build base query
        relationship_query = (
            self.db.session.query(ContactRelationship, FromContact, ToContact, RelationshipType)
            .join(FromContact, ContactRelationship.from_contact_id == FromContact.id)
            .join(ToContact, ContactRelationship.to_contact_id == ToContact.id, isouter=True)
            .join(RelationshipType, ContactRelationship.type_id == RelationshipType.id)
        )

        # Add filter if query provided
        if query:
            relationship_query = relationship_query.filter(
                (FromContact.name.ilike(f"%{query}%"))
                | (ToContact.name.ilike(f"%{query}%"))
                | (RelationshipType.type_key.ilike(f"%{query}%"))
                | (RelationshipType.description.ilike(f"%{query}%"))
            )

        relationships = relationship_query.all()

        # Format results and deduplicate
        results = []
        seen = set()  # Track (from_id, to_id, type_id) to avoid duplicates

        for rel, from_contact, to_contact, rel_type in relationships:
            key = (rel.from_contact_id, rel.to_contact_id, rel.type_id)
            if key in seen:
                continue
            seen.add(key)

            results.append(
                {
                    "relationship_id": rel.id,
                    "from_contact_id": from_contact.id,
                    "from_contact_name": from_contact.name,
                    "to_contact_id": to_contact.id if to_contact else None,
                    "to_contact_name": to_contact.name if to_contact else None,
                    "type_key": rel_type.type_key,
                    "type_description": rel_type.description,
                    "start_date": rel.start_date.isoformat() if rel.start_date else None,
                    "end_date": rel.end_date.isoformat() if rel.end_date else None,
                }
            )

        return results

    def search_relationships(self, query: str) -> List[Dict[str, Any]]:
        """Search contact-to-contact relationships by contact name or relationship type.

        Args:
            query: Search query (case-insensitive partial match)

        Returns:
            List of relationship dictionaries with from/to contact info and type
        """
        return self._query_relationships(query=query)

    def list_all_relationships(self) -> List[Dict[str, Any]]:
        """List all contact-to-contact relationships.

        Returns:
            List of all relationship dictionaries with from/to contact info and type
        """
        return self._query_relationships(query=None)

    def search_relationship_types(self, query: str) -> List[Dict[str, Any]]:
        """Search relationship types by type key or description.

        Args:
            query: Search query (case-insensitive partial match)

        Returns:
            List of relationship type dictionaries
        """
        from .models import ContactRelationship
        from .models import RelationshipType

        types = (
            self.db.session.query(RelationshipType)
            .filter(
                (RelationshipType.type_key.ilike(f"%{query}%"))
                | (RelationshipType.description.ilike(f"%{query}%"))
            )
            .order_by(RelationshipType.type_key)
            .all()
        )

        results = []
        for rel_type in types:
            # Get usage count
            count = (
                self.db.session.query(ContactRelationship)
                .filter(ContactRelationship.type_id == rel_type.id)
                .count()
            )

            results.append(
                {
                    "id": rel_type.id,
                    "type_key": rel_type.type_key,
                    "description": rel_type.description,
                    "inverse_type_key": rel_type.inverse_type_key,
                    "is_symmetrical": bool(rel_type.is_symmetrical),
                    "usage_count": count,
                }
            )

        return results

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
        from .models import Contact
        from .models import Tag

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

    def get_contact_notes(self, contact_id: int) -> List[Dict[str, Any]]:
        """Get all notes associated with a specific contact.

        Args:
            contact_id: The contact ID to get notes for

        Returns:
            List of note dictionaries associated with the contact
        """
        try:
            from .models import Contact

            contact = self.db.session.query(Contact).filter(Contact.id == contact_id).first()
            if not contact or not contact.relationship:
                return []

            # Get notes associated with this contact's relationship
            notes = contact.relationship.notes if contact.relationship else []
            return [
                {
                    "id": note.id,
                    "title": note.title,
                    "content": note.content,
                    "created_at": note.created_at.isoformat() if note.created_at else None,
                    "updated_at": note.updated_at.isoformat() if note.updated_at else None,
                }
                for note in notes
            ]
        except Exception as e:
            self.logger.error(f"Error getting notes for contact {contact_id}: {e}", exc_info=True)
            return []

    def associate_note_with_contact(self, note_id: int, contact_id: int) -> bool:
        """Associate an existing note with a contact.

        Args:
            note_id: The note ID to associate
            contact_id: The contact ID to associate with

        Returns:
            True if association was successful, False otherwise
        """
        try:
            from .models import Contact
            from .models import Note

            # Verify both note and contact exist
            note = self.db.session.query(Note).filter(Note.id == note_id).first()
            contact = self.db.session.query(Contact).filter(Contact.id == contact_id).first()

            if not note or not contact:
                return False

            # Ensure contact has a relationship metadata object
            if not contact.relationship:
                # Create relationship metadata if it doesn't exist
                from .models import ContactMetadata

                metadata = ContactMetadata(contact_id=contact_id)
                self.db.session.add(metadata)
                self.db.session.flush()  # Get the ID

            # Associate note with contact's relationship
            if note not in contact.relationship.notes:
                contact.relationship.notes.append(note)
                self.db.session.commit()

            return True
        except Exception as e:
            self.logger.error(
                f"Error associating note {note_id} with contact {contact_id}: {e}", exc_info=True
            )
            self.db.session.rollback()
            return False

    def remove_note_from_contact(self, contact_id: int, note_title: str) -> bool:
        """Remove a note from a contact's relationship."""
        from .models import Contact
        from .models import Note

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

    def get_contacts_paginated(self, page: int, limit: int) -> List[Dict[str, Any]]:
        """Get contacts with pagination.

        Args:
            page: Page number (1-based)
            limit: Number of contacts per page

        Returns:
            List of contact dictionaries for the requested page
        """
        try:
            # Calculate offset (convert 1-based page to 0-based offset)
            offset = (page - 1) * limit

            # Get all contacts using existing method, then slice
            all_contacts = self.list_all_contacts()
            return all_contacts[offset : offset + limit]
        except Exception as e:
            self.logger.error(f"Error getting paginated contacts: {e}", exc_info=True)
            return []

    def get_contacts_with_images(self) -> List[Dict[str, Any]]:
        """Get all contacts that have profile images.

        Optimized query using database index on profile_image IS NOT NULL.
        This is specifically designed for the LLM use case:
        'create a directory of all contacts with images'
        """
        import time

        from .models import Contact

        self.logger.info("[API_QUERY_START] get_contacts_with_images() called")

        try:
            # SQL logging
            self.logger.debug("[SQL_QUERY] Executing optimized contacts with images query")
            self.logger.debug("[SQL_DETAIL] WHERE profile_image IS NOT NULL ORDER BY name")

            # Check index usage (if possible)
            self.logger.debug("[INDEX_CHECK] Assuming idx_contacts_profile_image_not_null exists")

            start_time = time.time()

            contacts = (
                self.db.session.query(Contact)
                .filter(Contact.profile_image.isnot(None))
                .order_by(Contact.name)
                .all()
            )

            query_time = time.time() - start_time

            # Convert to dict format and analyze
            result = []
            total_size = 0
            corrupted_count = 0

            for contact in contacts:
                contact_dict = {
                    "id": contact.id,
                    "name": contact.name,
                    "email": contact.email,
                    "phone": contact.phone,
                    "profile_image": contact.profile_image,
                    "profile_image_filename": contact.profile_image_filename,
                    "profile_image_mime_type": contact.profile_image_mime_type,
                    "relationship_info": self.get_relationship_info(contact.id),
                }

                # Image validation
                if contact.profile_image:
                    image_size = len(contact.profile_image)
                    total_size += image_size

                    # Check for suspicious data
                    if image_size < 100:  # Suspiciously small
                        self.logger.warning(
                            f"[IMAGE_SUSPICIOUS] Contact {contact.id} has tiny image: {image_size} bytes"
                        )
                        corrupted_count += 1
                    elif image_size > 5 * 1024 * 1024:  # Suspiciously large (>5MB)
                        self.logger.warning(
                            f"[IMAGE_LARGE] Contact {contact.id} has huge image: {image_size/1024/1024:.1f}MB"
                        )

                    # Basic format validation
                    if (
                        contact.profile_image_mime_type
                        and not contact.profile_image_mime_type.startswith("image/")
                    ):
                        self.logger.warning(
                            f"[IMAGE_FORMAT] Contact {contact.id} has non-image MIME type: {contact.profile_image_mime_type}"
                        )
                        corrupted_count += 1

                result.append(contact_dict)

            self.logger.info(
                f"[API_QUERY_SUCCESS] Retrieved {len(result)} contacts in {query_time:.3f}s"
            )
            self.logger.info(
                f"[API_DATA_ANALYSIS] Total image data: {total_size/1024/1024:.1f}MB, corrupted: {corrupted_count}"
            )

            if corrupted_count > 0:
                self.logger.warning(
                    f"[API_DATA_QUALITY] Found {corrupted_count} potentially corrupted images"
                )

            return result

        except Exception as e:
            self.logger.error(
                f"[API_QUERY_ERROR] Exception in get_contacts_with_images: {e}", exc_info=True
            )
            raise

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
        from .models import ContactRelationship
        from .models import RelationshipType

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
    ):
        """Add a relationship between two contacts by name.

        Returns:
            Dict with success status, message, and relationship details
        """
        try:
            # Find contacts by name
            from_contacts = self.search_contacts(from_contact_name)
            to_contacts = self.search_contacts(to_contact_name)

            # Handle not found
            if not from_contacts:
                return {
                    "success": False,
                    "error": f"Contact '{from_contact_name}' not found",
                    "message": f"No contacts match '{from_contact_name}'. Please check the name and try again.",
                }
            if not to_contacts:
                return {
                    "success": False,
                    "error": f"Contact '{to_contact_name}' not found",
                    "message": f"No contacts match '{to_contact_name}'. Please check the name and try again.",
                }

            # Handle ambiguous matches
            if len(from_contacts) > 1:
                names = [c["name"] for c in from_contacts[:5]]
                return {
                    "success": False,
                    "error": "Multiple contacts found",
                    "message": f"Multiple contacts match '{from_contact_name}': {', '.join(names)}. Please be more specific.",
                }
            if len(to_contacts) > 1:
                names = [c["name"] for c in to_contacts[:5]]
                return {
                    "success": False,
                    "error": "Multiple contacts found",
                    "message": f"Multiple contacts match '{to_contact_name}': {', '.join(names)}. Please be more specific.",
                }

            # Use the first (and only) match for each
            from_id = from_contacts[0]["id"]
            to_id = to_contacts[0]["id"]
            from_name = from_contacts[0]["name"]
            to_name = to_contacts[0]["name"]

            self.db.create_contact_relationship(from_id, to_id, type_key, start_date, end_date)

            return {
                "success": True,
                "from_contact": from_name,
                "to_contact": to_name,
                "relationship_type": type_key,
                "message": f"Added '{type_key}' relationship from {from_name} to {to_name}",
            }
        except Exception as e:
            self.logger.error(f"Error adding relationship: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to add relationship: {str(e)}",
            }

    def remove_contact_relationship(
        self, from_contact_name: str, to_contact_name: str, type_key: str
    ):
        """Remove a relationship between two contacts.

        Returns:
            Dict with success status, message, and relationship details
        """
        try:
            # Find contacts by name
            from_contacts = self.search_contacts(from_contact_name)
            to_contacts = self.search_contacts(to_contact_name)

            # Handle not found
            if not from_contacts:
                return {
                    "success": False,
                    "error": f"Contact '{from_contact_name}' not found",
                    "message": f"No contacts match '{from_contact_name}'. Please check the name and try again.",
                }
            if not to_contacts:
                return {
                    "success": False,
                    "error": f"Contact '{to_contact_name}' not found",
                    "message": f"No contacts match '{to_contact_name}'. Please check the name and try again.",
                }

            # Handle ambiguous matches
            if len(from_contacts) > 1:
                names = [c["name"] for c in from_contacts[:5]]
                return {
                    "success": False,
                    "error": "Multiple contacts found",
                    "message": f"Multiple contacts match '{from_contact_name}': {', '.join(names)}. Please be more specific.",
                }
            if len(to_contacts) > 1:
                names = [c["name"] for c in to_contacts[:5]]
                return {
                    "success": False,
                    "error": "Multiple contacts found",
                    "message": f"Multiple contacts match '{to_contact_name}': {', '.join(names)}. Please be more specific.",
                }

            from_id = from_contacts[0]["id"]
            to_id = to_contacts[0]["id"]
            from_name = from_contacts[0]["name"]
            to_name = to_contacts[0]["name"]

            self.db.delete_contact_relationship(from_id, to_id, type_key)

            return {
                "success": True,
                "from_contact": from_name,
                "to_contact": to_name,
                "relationship_type": type_key,
                "message": f"Removed '{type_key}' relationship from {from_name} to {to_name}",
            }
        except Exception as e:
            self.logger.error(f"Error removing relationship: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to remove relationship: {str(e)}",
            }

    def delete_relationship_by_id(self, relationship_id: int) -> Dict[str, Any]:
        """Delete a relationship by its ID directly.

        Args:
            relationship_id: The ID of the relationship to delete

        Returns:
            Dict with success status, message, and relationship details
        """
        try:
            # First, get relationship details for the response
            relationships = self.db.get_all_relationships()
            target_relationship = None
            for rel in relationships:
                if rel.get("relationship_id") == relationship_id:
                    target_relationship = rel
                    break

            if not target_relationship:
                return {
                    "success": False,
                    "error": f"Relationship with ID {relationship_id} not found",
                    "message": f"No relationship found with ID {relationship_id}",
                }

            # Delete the relationship using the database layer
            success = self.db.delete_relationship_by_id(relationship_id)

            if success:
                return {
                    "success": True,
                    "relationship_id": relationship_id,
                    "from_contact": target_relationship.get("person1"),
                    "to_contact": target_relationship.get("person2"),
                    "relationship_type": target_relationship.get("type_key"),
                    "message": f"Successfully deleted relationship {relationship_id}",
                }
            else:
                return {
                    "success": False,
                    "error": "Database deletion failed",
                    "message": f"Failed to delete relationship {relationship_id} from database",
                }

        except Exception as e:
            self.logger.error(
                f"Error deleting relationship by ID {relationship_id}: {e}", exc_info=True
            )
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to delete relationship {relationship_id}: {str(e)}",
            }

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
        from .models import Contact
        from .models import ContactRelationship
        from .models import RelationshipType

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

        for _rel, rel_type, from_contact, to_contact in relationships:
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

    # ========== Additional API Methods for TUI DataService ==========

    def get_all_relationships(self) -> List[Dict[str, Any]]:
        """Get all relationships using the database layer method.

        This method provides API access to the database's get_all_relationships
        functionality for TUI DataService to eliminate direct database access.

        Returns:
            List of relationship dictionaries
        """
        try:
            return self.db.get_all_relationships()
        except Exception as e:
            self.logger.error(f"Error getting all relationships: {e}", exc_info=True)
            return []

    def update_note_by_id(self, note_id: int, title: str, content: str) -> bool:
        """Update a note by ID.

        Args:
            note_id: Note ID to update
            title: New title
            content: New content

        Returns:
            True if successful, False otherwise
        """
        try:
            return self.db.update_note_by_id(note_id, title=title, content=content)
        except Exception as e:
            self.logger.error(f"Error updating note {note_id}: {e}", exc_info=True)
            return False

    def delete_note_by_id(self, note_id: int) -> bool:
        """Delete a note by ID.

        Args:
            note_id: Note ID to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            return self.db.delete_note_by_id(note_id)
        except Exception as e:
            self.logger.error(f"Error deleting note {note_id}: {e}", exc_info=True)
            return False

    def get_note_by_id(self, note_id: int) -> Optional[Dict[str, Any]]:
        """Get a note by ID.

        Args:
            note_id: Note ID to retrieve

        Returns:
            Note dictionary or None if not found
        """
        try:
            note_data = self.db.get_note_by_id(note_id)
            if note_data:
                # Add contact count if needed (keeping API backward compatibility)
                # Note: We'll need to get this from relationships if required
                note_data["contact_count"] = 0  # TODO: Implement proper contact count
            return note_data
        except Exception as e:
            self.logger.error(f"Error getting note {note_id}: {e}", exc_info=True)
            return None

    def unified_search(
        self, query: str, entity_types: Optional[List[str]] = None, limit: int = 100
    ) -> Dict[str, Any]:
        """Perform unified search across all entity types through API layer.

        This method provides API access to the unified search functionality,
        eliminating direct core module imports from TUI layer.

        Args:
            query: Search query string
            entity_types: List of entity types to search ('contacts', 'notes', 'tags', 'relationships')
            limit: Maximum number of results to return

        Returns:
            Dictionary with search results grouped by entity type
        """
        try:
            from .core.search_unified import EntityType
            from .core.search_unified import UnifiedSearchAPI

            # Map string types to EntityType enum
            type_mapping = {
                "contacts": EntityType.CONTACT,
                "notes": EntityType.NOTE,
                "tags": EntityType.TAG,
                "relationships": EntityType.RELATIONSHIP,
            }

            # Convert entity_types if provided
            enum_types = None
            if entity_types:
                enum_types = [type_mapping.get(t) for t in entity_types if t in type_mapping]
                enum_types = [t for t in enum_types if t is not None]

            # Initialize unified search API
            search_api = UnifiedSearchAPI(self.db, max_results=limit)

            # Perform search
            results = search_api.search(query=query, entity_types=enum_types, limit=limit)

            return results

        except Exception as e:
            self.logger.error(f"Failed to perform unified search: {e}")
            return {
                "query": query,
                "results": {},
                "total": 0,
                "suggestions": [],
                "stats": {
                    "search_time": 0.0,
                    "cache_used": False,
                    "fts_used": False,
                    "sources": [],
                },
            }

    def export_relationships_data(self, format: str = "json") -> str:
        """Export relationships data.

        Args:
            format: Export format ('json' or 'csv')

        Returns:
            Exported data as string
        """
        try:
            if format.lower() == "csv":
                return self.db.export_relationships(format="csv")
            else:
                # For JSON, build comprehensive export
                export_data = {
                    "contacts": self.list_all_contacts(),
                    "tags": self.list_all_tags(),
                    "notes": self.list_all_notes(),
                    "relationships": self.get_all_relationships(),
                }
                import json

                return json.dumps(export_data, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Error exporting relationships: {e}", exc_info=True)
            return ""

    def vacuum_database(self) -> bool:
        """Vacuum/optimize the database through API layer.

        Returns:
            True if successful, False otherwise
        """
        try:
            self.db.session.execute(text("VACUUM"))
            self.db.session.commit()
            return True
        except Exception as e:
            self.logger.error(f"Failed to vacuum database: {e}")
            self.db.session.rollback()
            return False

    def add_relationship(
        self, from_contact_id: int, to_contact_id: int, relationship_type: str
    ) -> bool:
        """Add a relationship between two contacts by ID.

        Args:
            from_contact_id: Source contact ID
            to_contact_id: Target contact ID
            relationship_type: Type of relationship

        Returns:
            True if successful, False otherwise
        """
        try:
            self.db.create_contact_relationship(from_contact_id, to_contact_id, relationship_type)
            return True
        except Exception as e:
            self.logger.error(f"Error adding relationship: {e}", exc_info=True)
            return False

    def tag_contact(self, contact_id: int, tag_name: str) -> bool:
        """Add a tag to a contact (wrapper for existing method).

        Args:
            contact_id: Contact ID
            tag_name: Tag name

        Returns:
            True if successful, False otherwise
        """
        return self.add_tag_to_contact(contact_id, tag_name)

    def get_contact(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Get a contact by ID (wrapper for existing method).

        Args:
            contact_id: Contact ID

        Returns:
            Contact dictionary or None
        """
        return self.get_contact_details(contact_id)

    def add_contact(
        self, first_name: str, last_name: str, email: str = None, phone: str = None
    ) -> Optional[Dict[str, Any]]:
        """Add a new contact.

        Args:
            first_name: First name
            last_name: Last name
            email: Email address
            phone: Phone number

        Returns:
            Created contact dictionary or None
        """
        from .models import Contact

        try:
            name = f"{first_name} {last_name}".strip()
            contact = Contact(name=name, email=email, phone=phone)
            self.db.session.add(contact)
            self.db.session.commit()

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
        except Exception as e:
            self.logger.error(f"Error adding contact: {e}", exc_info=True)
            self.db.session.rollback()
            return None

    def update_contact(self, contact_id: int, **kwargs) -> bool:
        """Update a contact.

        Args:
            contact_id: Contact ID
            **kwargs: Fields to update

        Returns:
            True if successful, False otherwise
        """
        from .models import Contact

        try:
            contact = self.db.session.query(Contact).filter(Contact.id == contact_id).first()
            if not contact:
                return False

            for key, value in kwargs.items():
                if hasattr(contact, key):
                    setattr(contact, key, value)

            self.db.session.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error updating contact: {e}", exc_info=True)
            self.db.session.rollback()
            return False

    def delete_contact(self, contact_id: int) -> bool:
        """Delete a contact.

        Args:
            contact_id: Contact ID

        Returns:
            True if successful, False otherwise
        """
        from .models import Contact

        try:
            contact = self.db.session.query(Contact).filter(Contact.id == contact_id).first()
            if not contact:
                return False

            self.db.session.delete(contact)
            self.db.session.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error deleting contact: {e}", exc_info=True)
            self.db.session.rollback()
            return False

    def add_note(self, title: str, content: str) -> Optional[Dict[str, Any]]:
        """Add a new note (wrapper for existing method).

        Args:
            title: Note title
            content: Note content

        Returns:
            Created note dictionary or None
        """
        return self.create_note(title, content)

    def get_all_notes(self) -> List[Dict[str, Any]]:
        """Get all notes (wrapper for existing method).

        Returns:
            List of note dictionaries
        """
        return self.list_all_notes()

    def get_all_tags(self) -> List[Dict[str, Any]]:
        """Get all tags (wrapper for existing method).

        Returns:
            List of tag dictionaries
        """
        return self.list_all_tags()
