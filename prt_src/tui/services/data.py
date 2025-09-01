"""Data service for PRT TUI screens.

Wraps PRTAPI to provide data access for screens.
"""

from typing import Dict, List, Optional

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
            contacts = self.api.get_all_contacts()
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
                return self.api.get_contact_relationships(contact_id)
            # TODO: Add get_all_relationships to PRTAPI
            return []
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

    # Tag operations

    async def get_tags(self) -> List[Dict]:
        """Get all tags.

        Returns:
            List of tag dictionaries
        """
        try:
            return self.api.get_all_tags()
        except Exception as e:
            logger.error(f"Failed to get tags: {e}")
            return []

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

    async def create_note(self, title: str, content: str, contact_id: Optional[int] = None) -> bool:
        """Create a note.

        Args:
            title: Note title
            content: Note content
            contact_id: Optional contact to associate with

        Returns:
            True if successful
        """
        try:
            note = self.api.add_note(title, content)
            if note and contact_id:
                # TODO: Add note-contact association to PRTAPI
                pass
            return bool(note)
        except Exception as e:
            logger.error(f"Failed to create note: {e}")
            return False

    # Statistics

    async def get_stats(self) -> Dict[str, int]:
        """Get database statistics.

        Returns:
            Dictionary with counts
        """
        try:
            return {
                "contacts": len(self.api.get_all_contacts()),
                "tags": len(self.api.get_all_tags()),
                "notes": len(self.api.get_all_notes()),
                "relationships": 0,  # TODO: Add to PRTAPI
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"contacts": 0, "tags": 0, "notes": 0, "relationships": 0}
