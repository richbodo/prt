"""Relationship management operations."""

from datetime import date
from typing import Any


class RelationshipOperations:
    """Handles all relationship-related business logic."""

    def __init__(self, api):
        """Initialize with API instance.

        Args:
            api: PRTAPI instance for database access
        """
        self.api = api

    def list_relationship_types(self) -> list[dict[str, Any]]:
        """Returns all relationship types with descriptions.

        Returns:
            List of relationship type dictionaries
        """
        try:
            types = self.api.db.list_relationship_types()
            # Ensure each type has required fields
            for rel_type in types:
                rel_type.setdefault("is_symmetrical", False)
                rel_type.setdefault("inverse_type_key", None)
            return types
        except Exception:
            return []

    def create_relationship(
        self, from_id: int, to_id: int, type_key: str, start_date: date | None = None
    ) -> dict[str, Any]:
        """Creates relationship, returns success/error status.

        Args:
            from_id: Source contact ID
            to_id: Target contact ID
            type_key: Relationship type key
            start_date: Optional start date

        Returns:
            Dict with success status and message
        """
        try:
            # Validate inputs
            if from_id == to_id:
                return {"success": False, "error": "Cannot create relationship with same contact"}

            # Validate contact IDs exist
            contacts = self.api.list_all_contacts()
            contact_ids = {c["id"] for c in contacts}

            if from_id not in contact_ids:
                return {"success": False, "error": f"Contact ID {from_id} not found"}

            if to_id not in contact_ids:
                return {"success": False, "error": f"Contact ID {to_id} not found"}

            # Validate relationship type
            rel_types = self.api.db.list_relationship_types()
            valid_types = {rt["type_key"] for rt in rel_types}

            if type_key not in valid_types:
                return {"success": False, "error": f"Invalid relationship type: {type_key}"}

            # Create the relationship
            self.api.db.create_contact_relationship(from_id, to_id, type_key, start_date=start_date)

            return {
                "success": True,
                "message": "Relationship created successfully",
                "from_id": from_id,
                "to_id": to_id,
                "type_key": type_key,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_contact_relationships(self, contact_id: int) -> list[dict[str, Any]]:
        """Returns all relationships for a contact.

        Args:
            contact_id: ID of the contact

        Returns:
            List of relationships grouped by type
        """
        try:
            relationships = self.api.db.get_contact_relationships(contact_id)

            # Group by relationship type
            grouped = {}
            for rel in relationships:
                type_key = rel.get("type", "unknown")
                if type_key not in grouped:
                    grouped[type_key] = []
                grouped[type_key].append(rel)

            # Convert to list format
            result = []
            for type_key, rels in grouped.items():
                result.append(
                    {
                        "type": type_key,
                        "description": rels[0].get("description", type_key) if rels else type_key,
                        "relationships": rels,
                        "count": len(rels),
                    }
                )

            return result

        except Exception:
            return []

    def delete_relationship(self, from_id: int, to_id: int, type_key: str) -> dict[str, Any]:
        """Deletes specific relationship.

        Args:
            from_id: Source contact ID
            to_id: Target contact ID
            type_key: Relationship type key

        Returns:
            Dict with success status
        """
        try:
            # Check if relationship exists
            relationships = self.find_relationships_between(from_id, to_id)
            exists = any(r for r in relationships if r.get("type") == type_key)

            if not exists:
                return {"success": False, "error": "Relationship not found"}

            # Delete the relationship
            self.api.db.delete_contact_relationship(from_id, to_id, type_key)

            return {"success": True, "message": "Relationship deleted successfully"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def find_relationships_between(
        self, contact1_id: int, contact2_id: int
    ) -> list[dict[str, Any]]:
        """Returns all relationships between two contacts.

        Args:
            contact1_id: First contact ID
            contact2_id: Second contact ID

        Returns:
            List of relationships in both directions
        """
        try:
            relationships = []

            # Get relationships from contact1 to contact2
            contact1_rels = self.api.db.get_contact_relationships(contact1_id)
            for rel in contact1_rels:
                if rel.get("other_contact_id") == contact2_id:
                    rel["from_contact_id"] = contact1_id
                    rel["to_contact_id"] = contact2_id
                    relationships.append(rel)

            # Get relationships from contact2 to contact1
            contact2_rels = self.api.db.get_contact_relationships(contact2_id)
            for rel in contact2_rels:
                if rel.get("other_contact_id") == contact1_id:
                    rel["from_contact_id"] = contact2_id
                    rel["to_contact_id"] = contact1_id
                    relationships.append(rel)

            return relationships

        except Exception:
            return []

    def get_relationship_type_info(self, type_key: str) -> dict[str, Any] | None:
        """Get detailed info about a relationship type.

        Args:
            type_key: Relationship type key

        Returns:
            Dict with type information or None
        """
        try:
            types = self.api.db.list_relationship_types()
            for rel_type in types:
                if rel_type.get("type_key") == type_key:
                    return rel_type
            return None
        except Exception:
            return None
