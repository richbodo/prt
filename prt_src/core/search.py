"""Search operations across all entities."""

from typing import Any


class SearchOperations:
    """Handles all search-related business logic."""

    def __init__(self, api):
        """Initialize with API instance.

        Args:
            api: PRTAPI instance for database access
        """
        self.api = api

    def unified_search(self, query: str) -> dict[str, Any]:
        """Searches contacts, tags, notes simultaneously.

        Args:
            query: Search query string

        Returns:
            Dict with results grouped by type
        """
        try:
            if not query:
                return {"contacts": [], "tags": [], "notes": [], "total": 0}

            # Search each entity type
            contacts = self.api.search_contacts(query)
            tags = self.api.search_tags(query)
            notes = self.api.search_notes(query)

            # Count total results
            total = len(contacts) + len(tags) + len(notes)

            return {
                "query": query,
                "contacts": contacts,
                "tags": tags,
                "notes": notes,
                "total": total,
                "counts": {"contacts": len(contacts), "tags": len(tags), "notes": len(notes)},
            }

        except Exception as e:
            return {"error": str(e), "contacts": [], "tags": [], "notes": [], "total": 0}

    def search_by_tag(self, tag_name: str) -> list[dict[str, Any]]:
        """Returns contacts associated with tag.

        Args:
            tag_name: Name of the tag to search for

        Returns:
            List of contacts with the tag
        """
        try:
            # First find the tag
            tags = self.api.search_tags(tag_name)
            if not tags:
                return []

            # Get exact match if possible
            tag = next((t for t in tags if t["name"].lower() == tag_name.lower()), tags[0])

            # Get contacts for this tag
            contacts_with_tag = []
            all_contacts = self.api.list_all_contacts()

            for contact in all_contacts:
                # Check if contact has this tag via metadata
                metadata = self.api.db.get_contact_metadata(contact["id"])
                if (
                    metadata
                    and metadata.get("tags")
                    and any(t["id"] == tag["id"] for t in metadata["tags"])
                ):
                    contacts_with_tag.append(
                        {
                            "id": contact["id"],
                            "name": contact["name"],
                            "email": contact.get("email"),
                            "phone": contact.get("phone"),
                            "tag": tag["name"],
                        }
                    )

            return contacts_with_tag

        except Exception:
            return []

    def search_by_note(self, query: str) -> list[dict[str, Any]]:
        """Searches note content and titles.

        Args:
            query: Search query for notes

        Returns:
            List of notes with associated contacts
        """
        try:
            # Search notes
            notes = self.api.search_notes(query)

            # Enhance with associated contacts
            results = []
            for note in notes:
                # Get contacts associated with this note
                associated_contacts = []
                all_contacts = self.api.list_all_contacts()

                for contact in all_contacts:
                    metadata = self.api.db.get_contact_metadata(contact["id"])
                    if (
                        metadata
                        and metadata.get("notes")
                        and any(n["id"] == note["id"] for n in metadata["notes"])
                    ):
                        associated_contacts.append(
                            {
                                "id": contact["id"],
                                "name": contact["name"],
                                "email": contact.get("email"),
                            }
                        )

                results.append(
                    {
                        "note": note,
                        "associated_contacts": associated_contacts,
                        "contact_count": len(associated_contacts),
                    }
                )

            return results

        except Exception:
            return []

    def search_by_relationship_type(
        self, type_key: str, from_user: bool = True
    ) -> list[dict[str, Any]]:
        """Returns contacts with specific relationship type.

        Args:
            type_key: Relationship type key
            from_user: If True, searches relationships FROM the user (contact ID 1)

        Returns:
            List of contacts with this relationship type
        """
        try:
            # Get all contacts
            all_contacts = self.api.list_all_contacts()

            # Determine the "user" contact (usually ID 1 or first contact)
            user_contact_id = 1  # Default to ID 1
            if all_contacts and not any(c["id"] == 1 for c in all_contacts):
                # If no contact with ID 1, use the first contact as "user"
                user_contact_id = all_contacts[0]["id"]

            # Get relationships for the user
            relationships = self.api.db.get_contact_relationships(user_contact_id)

            # Filter by relationship type
            matching_contacts = []
            for rel in relationships:
                if rel.get("type") == type_key:
                    # Get the other contact's details
                    other_id = rel.get("other_contact_id")
                    other_contact = next((c for c in all_contacts if c["id"] == other_id), None)

                    if other_contact:
                        matching_contacts.append(
                            {
                                "id": other_contact["id"],
                                "name": other_contact["name"],
                                "email": other_contact.get("email"),
                                "phone": other_contact.get("phone"),
                                "relationship_type": type_key,
                                "relationship_description": rel.get("description", type_key),
                                "start_date": rel.get("start_date"),
                                "end_date": rel.get("end_date"),
                            }
                        )

            return matching_contacts

        except Exception:
            return []

    def get_recent_searches(self, limit: int = 10) -> list[str]:
        """Get recently used search queries.

        Args:
            limit: Maximum number of recent searches

        Returns:
            List of recent search strings
        """
        # This would typically be stored in a cache or database
        # For now, return empty list
        return []

    def get_search_suggestions(self, partial: str) -> list[str]:
        """Get search suggestions based on partial input.

        Args:
            partial: Partial search string

        Returns:
            List of suggested search terms
        """
        try:
            suggestions = []

            if len(partial) < 2:
                return suggestions

            # Get contact name suggestions
            contacts = self.api.list_all_contacts()
            for contact in contacts[:20]:  # Limit to prevent too many suggestions
                name = contact.get("name", "")
                if partial.lower() in name.lower():
                    suggestions.append(name)

            # Get tag suggestions
            tags = self.api.list_all_tags()
            for tag in tags[:10]:
                if partial.lower() in tag["name"].lower():
                    suggestions.append(f"tag:{tag['name']}")

            return suggestions[:10]  # Limit total suggestions

        except Exception:
            return []
