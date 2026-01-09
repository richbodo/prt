"""Contact-related business operations."""

from typing import Any


class ContactOperations:
    """Handles all contact-related business logic."""

    def __init__(self, api):
        """Initialize with API instance.

        Args:
            api: PRTAPI instance for database access
        """
        self.api = api

    def list_contacts(self, page: int = 0, page_size: int = 20) -> dict[str, Any]:
        """Returns paginated contact list with metadata.

        Args:
            page: Page number (0-indexed)
            page_size: Number of contacts per page

        Returns:
            Dict containing contacts, pagination info, and total count
        """
        try:
            all_contacts = self.api.list_all_contacts()
            total = len(all_contacts)

            # Calculate pagination
            start_idx = page * page_size
            end_idx = min(start_idx + page_size, total)

            # Get page of contacts
            contacts = all_contacts[start_idx:end_idx] if start_idx < total else []

            return {
                "success": True,
                "contacts": contacts,
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
                "has_next": end_idx < total,
                "has_prev": page > 0,
            }
        except Exception as e:
            return {"success": False, "error": str(e), "contacts": [], "total": 0}

    def get_contact_details(self, contact_id: int) -> dict[str, Any] | None:
        """Returns full contact info including relationships, tags, notes.

        Args:
            contact_id: ID of the contact

        Returns:
            Dict with contact details or None if not found
        """
        try:
            # Get basic contact info
            contacts = self.api.list_all_contacts()
            contact = next((c for c in contacts if c["id"] == contact_id), None)

            if not contact:
                return None

            # Enrich with relationships
            relationships = self.api.db.get_contact_relationships(contact_id)

            # Get associated tags and notes through metadata
            metadata = self.api.db.get_contact_metadata(contact_id)

            return {
                "id": contact["id"],
                "name": contact["name"],
                "email": contact.get("email"),
                "phone": contact.get("phone"),
                "relationships": relationships,
                "tags": metadata.get("tags", []) if metadata else [],
                "notes": metadata.get("notes", []) if metadata else [],
                "created_at": contact.get("created_at"),
                "updated_at": contact.get("updated_at"),
            }
        except Exception as e:
            return {"error": str(e)}

    def search_contacts(self, query: str, limit: int = 50) -> list[dict[str, Any]]:
        """Full-text search across name, email, phone.

        Args:
            query: Search query string
            limit: Maximum results to return

        Returns:
            List of matching contacts with relevance scores
        """
        try:
            if not query:
                return []

            # Use existing search functionality
            results = self.api.search_contacts(query)

            # Add relevance scoring
            query_lower = query.lower()
            for contact in results:
                score = 0
                name_lower = contact.get("name", "").lower()

                # Exact match scores highest
                if query_lower == name_lower:
                    score = 100
                # Starts with query
                elif name_lower.startswith(query_lower):
                    score = 80
                # Contains query
                elif query_lower in name_lower:
                    score = 60
                # Email match
                elif query_lower in contact.get("email", "").lower():
                    score = 40
                # Phone match
                elif query_lower in contact.get("phone", "").lower():
                    score = 30

                contact["relevance_score"] = score

            # Sort by relevance and limit
            results.sort(key=lambda x: x["relevance_score"], reverse=True)
            return results[:limit]

        except Exception:
            return []

    def get_contacts_by_letter(self, letter: str) -> list[dict[str, Any]]:
        """Returns contacts whose name starts with given letter.

        Args:
            letter: Single letter to filter by

        Returns:
            List of contacts starting with the letter
        """
        try:
            if not letter or len(letter) != 1:
                return []

            letter_upper = letter.upper()
            all_contacts = self.api.list_all_contacts()

            # Filter contacts by first letter
            filtered = [
                c for c in all_contacts if c.get("name", "").upper().startswith(letter_upper)
            ]

            # Sort alphabetically
            filtered.sort(key=lambda x: x.get("name", "").upper())

            return filtered

        except Exception:
            return []

    def get_contact_metadata(self, contact_id: int) -> dict[str, Any] | None:
        """Helper method to get contact metadata.

        Args:
            contact_id: ID of the contact

        Returns:
            Dict with tags and notes or None
        """
        try:
            return self.api.db.get_contact_metadata(contact_id)
        except Exception:
            return None
