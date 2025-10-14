"""Data service for PRT TUI screens.

Wraps PRTAPI to provide data access for screens.
"""

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

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

    async def search_tags(self, query: str) -> List[Dict]:
        """Search tags.

        Args:
            query: Search query

        Returns:
            List of matching tags
        """
        try:
            return self.api.search_tags(query)
        except Exception as e:
            logger.error(f"Failed to search tags: {e}")
            return []

    async def search_notes(self, query: str) -> List[Dict]:
        """Search notes.

        Args:
            query: Search query

        Returns:
            List of matching notes
        """
        try:
            return self.api.search_notes(query)
        except Exception as e:
            logger.error(f"Failed to search notes: {e}")
            return []

    async def search_relationships(self, query: str) -> List[Dict]:
        """Search contact-to-contact relationships.

        Args:
            query: Search query (matches contact name or relationship type)

        Returns:
            List of matching relationships
        """
        try:
            return self.api.search_relationships(query)
        except Exception as e:
            logger.error(f"Failed to search relationships: {e}")
            return []

    async def search_relationship_types(self, query: str) -> List[Dict]:
        """Search relationship types.

        Args:
            query: Search query (matches type key or description)

        Returns:
            List of matching relationship types
        """
        try:
            return self.api.search_relationship_types(query)
        except Exception as e:
            logger.error(f"Failed to search relationship types: {e}")
            return []

    async def list_all_contacts(self) -> List[Dict]:
        """List all contacts.

        Returns:
            List of all contacts
        """
        try:
            return self.api.list_all_contacts()
        except Exception as e:
            logger.error(f"Failed to list all contacts: {e}")
            return []

    async def list_all_tags(self) -> List[Dict]:
        """List all tags.

        Returns:
            List of all tags
        """
        try:
            return self.api.list_all_tags()
        except Exception as e:
            logger.error(f"Failed to list all tags: {e}")
            return []

    async def list_all_notes(self) -> List[Dict]:
        """List all notes.

        Returns:
            List of all notes
        """
        try:
            return self.api.list_all_notes()
        except Exception as e:
            logger.error(f"Failed to list all notes: {e}")
            return []

    async def list_all_relationships(self) -> List[Dict]:
        """List all contact-to-contact relationships.

        Returns:
            List of all relationships
        """
        try:
            return self.api.list_all_relationships()
        except Exception as e:
            logger.error(f"Failed to list all relationships: {e}")
            return []

    async def list_all_relationship_types(self) -> List[Dict]:
        """List all relationship types.

        Returns:
            List of all relationship types
        """
        try:
            return self.api.list_all_relationship_types()
        except Exception as e:
            logger.error(f"Failed to list all relationship types: {e}")
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
            from prt_src.core.search_unified import EntityType
            from prt_src.core.search_unified import UnifiedSearchAPI

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

    # Relationship types initialization

    async def seed_default_relationship_types(self) -> bool:
        """Seed the database with default relationship types.

        Creates standard relationship types with their inverses:
        - parent/child
        - sibling/sibling (symmetrical)
        - spouse/spouse (symmetrical)
        - friend/friend (symmetrical)
        - colleague/colleague (symmetrical)
        - grandparent/grandchild
        - aunt_uncle/niece_nephew
        - cousin/cousin (symmetrical)
        - mentor/mentee
        - reports_to/manages

        Returns:
            True if successful
        """
        try:
            # Check if relationship types already exist
            existing_types = self.api.list_all_relationship_types()
            if existing_types:
                logger.info("Relationship types already exist, skipping seeding")
                return True

            # Define default relationship types
            default_types = [
                {
                    "type_key": "parent",
                    "description": "Is the parent of",
                    "inverse_key": "child",
                    "is_symmetrical": False,
                },
                {
                    "type_key": "child",
                    "description": "Is the child of",
                    "inverse_key": "parent",
                    "is_symmetrical": False,
                },
                {
                    "type_key": "sibling",
                    "description": "Is the sibling of",
                    "inverse_key": "sibling",
                    "is_symmetrical": True,
                },
                {
                    "type_key": "spouse",
                    "description": "Is the spouse of",
                    "inverse_key": "spouse",
                    "is_symmetrical": True,
                },
                {
                    "type_key": "friend",
                    "description": "Is a friend of",
                    "inverse_key": "friend",
                    "is_symmetrical": True,
                },
                {
                    "type_key": "colleague",
                    "description": "Is a colleague of",
                    "inverse_key": "colleague",
                    "is_symmetrical": True,
                },
                {
                    "type_key": "grandparent",
                    "description": "Is the grandparent of",
                    "inverse_key": "grandchild",
                    "is_symmetrical": False,
                },
                {
                    "type_key": "grandchild",
                    "description": "Is the grandchild of",
                    "inverse_key": "grandparent",
                    "is_symmetrical": False,
                },
                {
                    "type_key": "aunt_uncle",
                    "description": "Is the aunt/uncle of",
                    "inverse_key": "niece_nephew",
                    "is_symmetrical": False,
                },
                {
                    "type_key": "niece_nephew",
                    "description": "Is the niece/nephew of",
                    "inverse_key": "aunt_uncle",
                    "is_symmetrical": False,
                },
                {
                    "type_key": "cousin",
                    "description": "Is a cousin of",
                    "inverse_key": "cousin",
                    "is_symmetrical": True,
                },
                {
                    "type_key": "mentor",
                    "description": "Is the mentor of",
                    "inverse_key": "mentee",
                    "is_symmetrical": False,
                },
                {
                    "type_key": "mentee",
                    "description": "Is the mentee of",
                    "inverse_key": "mentor",
                    "is_symmetrical": False,
                },
                {
                    "type_key": "reports_to",
                    "description": "Reports to",
                    "inverse_key": "manages",
                    "is_symmetrical": False,
                },
                {
                    "type_key": "manages",
                    "description": "Manages",
                    "inverse_key": "reports_to",
                    "is_symmetrical": False,
                },
            ]

            # Create each relationship type
            success_count = 0
            for rel_type in default_types:
                try:
                    success = self.api.create_relationship_type(
                        type_key=rel_type["type_key"],
                        description=rel_type["description"],
                        inverse_key=rel_type["inverse_key"],
                        is_symmetrical=rel_type["is_symmetrical"],
                    )
                    if success:
                        success_count += 1
                    else:
                        logger.warning(
                            f"Failed to create relationship type: {rel_type['type_key']}"
                        )
                except Exception as e:
                    logger.error(f"Error creating relationship type {rel_type['type_key']}: {e}")

            logger.info(
                f"Successfully created {success_count}/{len(default_types)} relationship types"
            )
            return success_count > 0

        except Exception as e:
            logger.error(f"Failed to seed default relationship types: {e}")
            return False

    # Relationship type management operations

    async def get_relationship_types(self) -> List[Dict]:
        """Get all relationship types.

        Returns:
            List of relationship type dictionaries
        """
        try:
            return self.api.list_all_relationship_types()
        except Exception as e:
            logger.error(f"Failed to get relationship types: {e}")
            return []

    async def create_relationship_type(
        self,
        type_key: str,
        description: str,
        inverse_key: Optional[str] = None,
        is_symmetrical: bool = False,
    ) -> Optional[Dict]:
        """Create a new relationship type.

        Args:
            type_key: Unique key for the relationship type
            description: Human-readable description
            inverse_key: Key for the inverse relationship type
            is_symmetrical: Whether the relationship is symmetrical

        Returns:
            Created relationship type dictionary or None
        """
        try:
            success = self.api.create_relationship_type(
                type_key=type_key,
                description=description,
                inverse_key=inverse_key,
                is_symmetrical=is_symmetrical,
            )
            if success:
                # Return the created relationship type
                rel_types = await self.get_relationship_types()
                for rel_type in rel_types:
                    if rel_type.get("type_key") == type_key:
                        return rel_type
            return None
        except Exception as e:
            logger.error(f"Failed to create relationship type '{type_key}': {e}")
            return None

    async def update_relationship_type(
        self,
        type_key: str,
        description: Optional[str] = None,
        inverse_key: Optional[str] = None,
        is_symmetrical: Optional[bool] = None,
    ) -> bool:
        """Update a relationship type.

        Args:
            type_key: Key of the relationship type to update
            description: New description (if provided)
            inverse_key: New inverse key (if provided)
            is_symmetrical: New symmetrical flag (if provided)

        Returns:
            True if successful
        """
        try:
            # Get current relationship type
            rel_types = await self.get_relationship_types()
            current_type = None
            for rel_type in rel_types:
                if rel_type.get("type_key") == type_key:
                    current_type = rel_type
                    break

            if not current_type:
                logger.error(f"Relationship type '{type_key}' not found")
                return False

            # For now, we'll need to delete and recreate since the API doesn't have update method
            # This is a simplification - in production you'd want proper update methods
            if description is None:
                description = current_type.get("description", "")
            if inverse_key is None:
                inverse_key = current_type.get("inverse_type_key")
            if is_symmetrical is None:
                is_symmetrical = bool(current_type.get("is_symmetrical", False))

            # Delete old type
            delete_success = self.api.delete_relationship_type(type_key)
            if not delete_success:
                return False

            # Create new type
            create_success = self.api.create_relationship_type(
                type_key=type_key,
                description=description,
                inverse_key=inverse_key,
                is_symmetrical=is_symmetrical,
            )
            return create_success

        except Exception as e:
            logger.error(f"Failed to update relationship type '{type_key}': {e}")
            return False

    async def delete_relationship_type(self, type_key: str) -> bool:
        """Delete a relationship type.

        Args:
            type_key: Key of the relationship type to delete

        Returns:
            True if successful
        """
        try:
            return self.api.delete_relationship_type(type_key)
        except Exception as e:
            logger.error(f"Failed to delete relationship type '{type_key}': {e}")
            return False

    async def get_relationship_type_usage_count(self, type_key: str) -> int:
        """Get the usage count for a relationship type.

        Args:
            type_key: Key of the relationship type

        Returns:
            Number of relationships using this type
        """
        try:
            all_relationships = await self.get_relationships()
            usage_count = 0
            for rel in all_relationships:
                if rel.get("type_key") == type_key:
                    usage_count += 1
            return usage_count
        except Exception as e:
            logger.error(f"Failed to get usage count for relationship type '{type_key}': {e}")
            return 0

    async def create_relationship_with_details(
        self,
        from_contact_id: int,
        to_contact_id: int,
        type_key: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> bool:
        """Create a relationship with detailed information.

        Args:
            from_contact_id: Source contact ID
            to_contact_id: Target contact ID
            type_key: Relationship type key
            start_date: Optional start date (ISO format)
            end_date: Optional end date (ISO format)

        Returns:
            True if successful
        """
        try:
            # Convert date strings to date objects if provided
            start_date_obj = None
            if start_date:
                from datetime import datetime

                try:
                    start_date_obj = datetime.fromisoformat(start_date).date()
                except ValueError:
                    logger.warning(f"Invalid start_date format: {start_date}")

            if end_date:
                from datetime import datetime

                try:
                    # Convert to date object (currently not used, but may be needed for validation)
                    datetime.fromisoformat(end_date).date()
                except ValueError:
                    logger.warning(f"Invalid end_date format: {end_date}")

            # Create the relationship using the core operations
            from prt_src.core.relationships import RelationshipOperations

            rel_ops = RelationshipOperations(self.api)

            result = rel_ops.create_relationship(
                from_id=from_contact_id,
                to_id=to_contact_id,
                type_key=type_key,
                start_date=start_date_obj,
            )

            return result.get("success", False)

        except Exception as e:
            logger.error(f"Failed to create relationship with details: {e}")
            return False

    async def get_relationship_details(self, relationship_id: int) -> Optional[Dict]:
        """Get detailed information about a relationship.

        Args:
            relationship_id: ID of the relationship

        Returns:
            Relationship details dictionary or None
        """
        try:
            all_relationships = await self.get_relationships()
            for rel in all_relationships:
                if rel.get("relationship_id") == relationship_id:
                    return rel
            return None
        except Exception as e:
            logger.error(f"Failed to get relationship details for {relationship_id}: {e}")
            return None

    async def update_relationship(
        self,
        relationship_id: int,
        type_key: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> bool:
        """Update a relationship.

        Args:
            relationship_id: ID of the relationship to update
            type_key: New relationship type key (if provided)
            start_date: New start date (if provided)
            end_date: New end date (if provided)

        Returns:
            True if successful
        """
        try:
            # This is a simplified implementation
            # In a full implementation, you would update the relationship directly in the database
            # For now, we'll indicate that this functionality needs to be implemented
            logger.warning("Update relationship functionality not fully implemented")
            return False

        except Exception as e:
            logger.error(f"Failed to update relationship {relationship_id}: {e}")
            return False
