"""Data service for PRT TUI screens.

Wraps PRTAPI to provide data access for screens.
"""

from typing import Any, Dict, List, Optional

from prt_src.api import PRTAPI
from prt_src.logging_config import get_logger

logger = get_logger(__name__)


class DataService:
    """Service providing data access for TUI screens.

    Wraps the PRTAPI to provide a clean interface for screens
    to access contacts, relationships, tags, and notes.
    """

    def __init__(self, api: Optional[PRTAPI] = None):
        """Initialize data service.

        Args:
            api: PRTAPI instance, or creates one if None
        """
        self.api = api or PRTAPI()

    # Contact operations

    async def get_contacts(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get paginated list of contacts.

        Args:
            limit: Maximum number of contacts to return
            offset: Number of contacts to skip

        Returns:
            List of contact dictionaries
        """
        try:
            # TODO: Add pagination to PRTAPI
            contacts = self.api.list_all_contacts()
            return contacts[offset : offset + limit]
        except Exception as e:
            logger.error(f"Failed to get contacts: {e}")
            return []

    async def get_contact(self, contact_id: int) -> Optional[Dict]:
        """Get a single contact by ID.

        Args:
            contact_id: Contact ID

        Returns:
            Contact dictionary or None
        """
        try:
            return self.api.get_contact(contact_id)
        except Exception as e:
            logger.error(f"Failed to get contact {contact_id}: {e}")
            return None

    async def create_contact(self, data: Dict) -> Optional[Dict]:
        """Create a new contact.

        Args:
            data: Contact data

        Returns:
            Created contact or None
        """
        try:
            return self.api.add_contact(
                first_name=data.get("first_name", ""),
                last_name=data.get("last_name", ""),
                email=data.get("email"),
                phone=data.get("phone"),
            )
        except Exception as e:
            logger.error(f"Failed to create contact: {e}")
            return None

    async def update_contact(self, contact_id: int, data: Dict) -> bool:
        """Update an existing contact.

        Args:
            contact_id: Contact ID
            data: Updated contact data

        Returns:
            True if successful
        """
        try:
            return self.api.update_contact(contact_id, **data)
        except Exception as e:
            logger.error(f"Failed to update contact {contact_id}: {e}")
            return False

    async def delete_contact(self, contact_id: int) -> bool:
        """Delete a contact.

        Args:
            contact_id: Contact ID

        Returns:
            True if successful
        """
        try:
            return self.api.delete_contact(contact_id)
        except Exception as e:
            logger.error(f"Failed to delete contact {contact_id}: {e}")
            return False

    async def search_contacts(self, query: str) -> List[Dict]:
        """Search contacts.

        Args:
            query: Search query

        Returns:
            List of matching contacts
        """
        try:
            return self.api.search_contacts(query)
        except Exception as e:
            logger.error(f"Failed to search contacts: {e}")
            return []

    # Relationship operations

    async def get_relationships(self, contact_id: Optional[int] = None) -> List[Dict]:
        """Get relationships.

        Args:
            contact_id: Optional contact ID to filter by

        Returns:
            List of relationship dictionaries
        """
        try:
            if contact_id:
                # Get relationships for a specific contact
                contact = self.api.get_contact(contact_id)
                if contact:
                    return self.api.get_contact_relationships(contact["name"])
                return []
            else:
                # Get all relationships
                return self.api.db.get_all_relationships()
        except Exception as e:
            logger.error(f"Failed to get relationships: {e}")
            return []

    async def create_relationship(
        self, from_contact: int, to_contact: int, relationship_type: str
    ) -> bool:
        """Create a relationship.

        Args:
            from_contact: Source contact ID
            to_contact: Target contact ID
            relationship_type: Type of relationship

        Returns:
            True if successful
        """
        try:
            return self.api.add_relationship(from_contact, to_contact, relationship_type)
        except Exception as e:
            logger.error(f"Failed to create relationship: {e}")
            return False

    async def delete_relationship(self, relationship_id: int) -> bool:
        """Delete a relationship.

        Args:
            relationship_id: Relationship ID

        Returns:
            True if successful
        """
        try:
            # Get the relationship details first
            all_relationships = self.api.db.get_all_relationships()
            target_relationship = None
            for rel in all_relationships:
                if rel.get("relationship_id") == relationship_id:
                    target_relationship = rel
                    break

            if not target_relationship:
                logger.error(f"Relationship with ID {relationship_id} not found")
                return False

            # Delete using the database method
            self.api.db.delete_contact_relationship(
                target_relationship["person1_id"],
                target_relationship["person2_id"],
                target_relationship["type_key"],
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete relationship: {e}")
            return False

    # Tag operations

    async def get_tags(self) -> List[Dict]:
        """Get all tags.

        Returns:
            List of tag dictionaries
        """
        try:
            return self.api.list_all_tags()
        except Exception as e:
            logger.error(f"Failed to get tags: {e}")
            return []

    async def create_tag(self, name: str) -> Optional[Dict]:
        """Create a new tag.

        Args:
            name: Tag name

        Returns:
            Created tag dictionary or None
        """
        try:
            return self.api.create_tag(name)
        except Exception as e:
            logger.error(f"Failed to create tag '{name}': {e}")
            return None

    async def update_tag(self, old_name: str, new_name: str) -> bool:
        """Update a tag name.

        Args:
            old_name: Current tag name
            new_name: New tag name

        Returns:
            True if successful
        """
        try:
            # Create new tag
            new_tag = self.api.create_tag(new_name)
            if not new_tag:
                return False

            # Get contacts with old tag and migrate them
            contacts = self.api.get_contacts_by_tag(old_name)
            for contact in contacts:
                # Add new tag
                await self.add_tag_to_contact(contact["id"], new_name)
                # Remove old tag
                await self.remove_tag_from_contact(contact["id"], old_name)

            # Delete old tag
            return self.api.delete_tag(old_name)
        except Exception as e:
            logger.error(f"Failed to update tag '{old_name}' to '{new_name}': {e}")
            return False

    async def delete_tag(self, name: str) -> bool:
        """Delete a tag.

        Args:
            name: Tag name

        Returns:
            True if successful
        """
        try:
            return self.api.delete_tag(name)
        except Exception as e:
            logger.error(f"Failed to delete tag '{name}': {e}")
            return False

    async def remove_tag_from_contact(self, contact_id: int, tag_name: str) -> bool:
        """Remove a tag from a contact.

        Args:
            contact_id: Contact ID
            tag_name: Tag name

        Returns:
            True if successful
        """
        try:
            return self.api.remove_tag_from_contact(contact_id, tag_name)
        except Exception as e:
            logger.error(f"Failed to remove tag from contact {contact_id}: {e}")
            return False

    async def add_tag_to_contact(self, contact_id: int, tag_name: str) -> bool:
        """Add a tag to a contact.

        Args:
            contact_id: Contact ID
            tag_name: Tag name

        Returns:
            True if successful
        """
        try:
            return self.api.tag_contact(contact_id, tag_name)
        except Exception as e:
            logger.error(f"Failed to add tag to contact {contact_id}: {e}")
            return False

    # Note operations

    async def get_notes(self, contact_id: Optional[int] = None) -> List[Dict]:
        """Get notes.

        Args:
            contact_id: Optional contact ID to filter by

        Returns:
            List of note dictionaries
        """
        try:
            if contact_id:
                # TODO: Add get_contact_notes to PRTAPI
                pass
            return self.api.get_all_notes()
        except Exception as e:
            logger.error(f"Failed to get notes: {e}")
            return []

    async def create_note(
        self, title: str, content: str, contact_id: Optional[int] = None
    ) -> Optional[Dict]:
        """Create a note.

        Args:
            title: Note title
            content: Note content
            contact_id: Optional contact to associate with

        Returns:
            Created note dictionary or None
        """
        try:
            note = self.api.add_note(title, content)
            if note and contact_id:
                # TODO: Add note-contact association to PRTAPI
                pass
            return note
        except Exception as e:
            logger.error(f"Failed to create note: {e}")
            return None

    async def update_note(self, note_id: int, title: str, content: str) -> bool:
        """Update a note.

        Args:
            note_id: Note ID
            title: Updated title
            content: Updated content

        Returns:
            True if successful
        """
        try:
            # Get the existing note first
            all_notes = await self.get_notes()
            target_note = None
            for note in all_notes:
                if note.get("id") == note_id:
                    target_note = note
                    break

            if not target_note:
                logger.error(f"Note with ID {note_id} not found")
                return False

            # Update using direct database access
            from prt_src.models import Note

            note_obj = self.api.db.session.query(Note).filter(Note.id == note_id).first()
            if note_obj:
                note_obj.title = title
                note_obj.content = content
                self.api.db.session.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to update note {note_id}: {e}")
            return False

    async def delete_note(self, note_id: int) -> bool:
        """Delete a note.

        Args:
            note_id: Note ID

        Returns:
            True if successful
        """
        try:
            # Delete using direct database access
            from prt_src.models import Note

            note_obj = self.api.db.session.query(Note).filter(Note.id == note_id).first()
            if note_obj:
                self.api.db.session.delete(note_obj)
                self.api.db.session.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete note {note_id}: {e}")
            return False

    # Search operations

    async def unified_search(
        self, query: str, entity_types: Optional[List[str]] = None, limit: int = 100
    ) -> Dict[str, Any]:
        """Perform unified search across all entity types.

        Args:
            query: Search query string
            entity_types: List of entity types to search ('contacts', 'notes', 'tags', 'relationships')
            limit: Maximum number of results to return

        Returns:
            Dictionary with search results grouped by entity type
        """
        try:
            from prt_src.core.search_unified import EntityType, UnifiedSearchAPI

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
            search_api = UnifiedSearchAPI(self.api.db, max_results=limit)

            # Perform search
            results = search_api.search(query=query, entity_types=enum_types, limit=limit)

            return results

        except Exception as e:
            logger.error(f"Failed to perform unified search: {e}")
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

    # Statistics

    async def get_stats(self) -> Dict[str, int]:
        """Get database statistics.

        Returns:
            Dictionary with counts
        """
        try:
            return {
                "contacts": len(self.api.list_all_contacts()),
                "tags": len(self.api.get_all_tags()),
                "notes": len(self.api.get_all_notes()),
                "relationships": 0,  # TODO: Add to PRTAPI
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"contacts": 0, "tags": 0, "notes": 0, "relationships": 0}

    # Database management operations

    async def get_database_stats(self) -> Dict[str, int]:
        """Get comprehensive database statistics.

        Returns:
            Dictionary with database statistics
        """
        try:
            stats = self.api.get_database_stats()

            # Add additional stats
            stats["tags"] = len(self.api.list_all_tags())
            stats["notes"] = len(self.api.list_all_notes())

            return stats
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {"contacts": 0, "relationships": 0, "notes": 0, "tags": 0}

    async def get_database_size(self) -> int:
        """Get database file size in bytes.

        Returns:
            Database size in bytes
        """
        try:
            import os

            db_path = self.api.db.db_path
            if db_path and os.path.exists(db_path):
                return os.path.getsize(db_path)
            return 0
        except Exception as e:
            logger.error(f"Failed to get database size: {e}")
            return 0

    async def get_backup_history(self) -> List[Dict[str, Any]]:
        """Get list of available backups.

        Returns:
            List of backup dictionaries
        """
        try:
            return self.api.get_backup_history()
        except Exception as e:
            logger.error(f"Failed to get backup history: {e}")
            return []

    async def create_backup(self, comment: str = None) -> Optional[Dict[str, Any]]:
        """Create a database backup.

        Args:
            comment: Optional comment for the backup

        Returns:
            Backup information dictionary or None
        """
        try:
            if comment is None:
                comment = f"Manual backup - {self._get_timestamp()}"
            return self.api.create_backup_with_comment(comment)
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None

    async def restore_backup(self, backup_id: int) -> bool:
        """Restore from a backup.

        Args:
            backup_id: ID of the backup to restore

        Returns:
            True if successful
        """
        try:
            return self.api.restore_from_backup(backup_id)
        except Exception as e:
            logger.error(f"Failed to restore backup {backup_id}: {e}")
            return False

    async def export_data(self, format: str = "json") -> Optional[str]:
        """Export database data.

        Args:
            format: Export format ('json' or 'csv')

        Returns:
            Path to exported file or None
        """
        try:
            from datetime import datetime
            from pathlib import Path

            # Create exports directory
            export_dir = Path("exports")
            export_dir.mkdir(exist_ok=True)

            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if format.lower() == "csv":
                # Export relationships as CSV
                data = self.api.db.export_relationships(format="csv")
                filename = f"database_export_{timestamp}.csv"
            else:
                # Export as JSON (default)
                export_data = {
                    "export_info": {
                        "timestamp": datetime.now().isoformat(),
                        "format": "json",
                        "source": "PRT Database",
                    },
                    "contacts": self.api.list_all_contacts(),
                    "tags": self.api.list_all_tags(),
                    "notes": self.api.list_all_notes(),
                    "relationships": self.api.db.get_all_relationships(),
                }

                filename = f"database_export_{timestamp}.json"

                import json

                data = json.dumps(export_data, indent=2, default=str)

            export_path = export_dir / filename

            with open(export_path, "w", encoding="utf-8") as f:
                f.write(data)

            return str(export_path)

        except Exception as e:
            logger.error(f"Failed to export data: {e}")
            return None

    async def vacuum_database(self) -> bool:
        """Vacuum/optimize the database.

        Returns:
            True if successful
        """
        try:
            # Execute VACUUM command on SQLite database
            from sqlalchemy import text

            self.api.db.session.execute(text("VACUUM"))
            self.api.db.session.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to vacuum database: {e}")
            return False

    def _get_timestamp(self) -> str:
        """Get formatted timestamp string.

        Returns:
            Timestamp string
        """
        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
