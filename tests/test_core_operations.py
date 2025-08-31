"""Tests for core business operations."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from prt_src.core import (
    ContactOperations,
    DatabaseOperations,
    Operations,
    RelationshipOperations,
    SearchOperations,
)


@pytest.fixture
def mock_api():
    """Create a mock API with test data."""
    api = MagicMock()

    # Mock contacts
    api.list_all_contacts.return_value = [
        {"id": 1, "name": "Alice Smith", "email": "alice@example.com", "phone": "555-0001"},
        {"id": 2, "name": "Bob Jones", "email": "bob@example.com", "phone": "555-0002"},
        {"id": 3, "name": "Charlie Brown", "email": "charlie@example.com", "phone": "555-0003"},
        {"id": 4, "name": "Diana Prince", "email": "diana@example.com", "phone": "555-0004"},
        {"id": 5, "name": "Eve Adams", "email": "eve@example.com", "phone": "555-0005"},
    ]

    # Mock search results
    api.search_contacts.return_value = [
        {"id": 1, "name": "Alice Smith", "email": "alice@example.com"},
        {"id": 5, "name": "Eve Adams", "email": "eve@example.com"},
    ]

    # Mock tags
    api.list_all_tags.return_value = [
        {"id": 1, "name": "family", "contact_count": 2},
        {"id": 2, "name": "work", "contact_count": 3},
        {"id": 3, "name": "friends", "contact_count": 4},
    ]

    api.search_tags.return_value = [{"id": 1, "name": "family", "contact_count": 2}]

    # Mock notes
    api.list_all_notes.return_value = [
        {"id": 1, "title": "Meeting Notes", "content": "Important discussion"},
        {"id": 2, "title": "Project Ideas", "content": "New features to implement"},
    ]

    api.search_notes.return_value = [
        {"id": 1, "title": "Meeting Notes", "content": "Important discussion"}
    ]

    # Mock database
    api.db.path = Path("/tmp/test.db")
    api.db.count_contacts.return_value = 5
    api.db.test_connection.return_value = True

    # Mock relationship types
    api.db.list_relationship_types.return_value = [
        {
            "id": 1,
            "type_key": "mother",
            "description": "Is the mother of",
            "inverse_type_key": None,
            "is_symmetrical": False,
        },
        {
            "id": 2,
            "type_key": "friend",
            "description": "Is a friend of",
            "inverse_type_key": "friend",
            "is_symmetrical": True,
        },
        {
            "id": 3,
            "type_key": "coworker",
            "description": "Is a coworker of",
            "inverse_type_key": "coworker",
            "is_symmetrical": True,
        },
    ]

    # Mock relationships
    api.db.get_contact_relationships.return_value = [
        {
            "relationship_id": 1,
            "type": "mother",
            "description": "Is the mother of",
            "other_contact_id": 2,
            "other_contact_name": "Bob Jones",
            "other_contact_email": "bob@example.com",
            "direction": "from",
            "start_date": None,
            "end_date": None,
        }
    ]

    # Mock metadata
    api.db.get_contact_metadata.return_value = {
        "tags": [{"id": 1, "name": "family"}],
        "notes": [{"id": 1, "title": "Meeting Notes"}],
    }

    # Mock backups
    api.get_backup_history.return_value = [
        {
            "id": 1,
            "filename": "backup_20240101_120000.db",
            "path": "/tmp/backup_20240101_120000.db",
            "comment": "Before major update",
            "created_at": "2024-01-01 12:00:00",
            "size": 1024 * 1024,  # 1MB
            "is_auto": False,
            "exists": True,
            "schema_version": 4,
        },
        {
            "id": 2,
            "filename": "backup_20240102_120000.db",
            "path": "/tmp/backup_20240102_120000.db",
            "comment": "Auto backup",
            "created_at": "2024-01-02 12:00:00",
            "size": 1024 * 1024,
            "is_auto": True,
            "exists": True,
            "schema_version": 4,
        },
    ]

    api.create_backup_with_comment.return_value = {
        "id": 3,
        "filename": "backup_20240103_120000.db",
        "path": "/tmp/backup_20240103_120000.db",
        "comment": "Test backup",
        "created_at": "2024-01-03 12:00:00",
        "size": 1024 * 1024,
    }

    return api


@pytest.fixture
def operations(mock_api):
    """Create Operations instance with mock API."""
    return Operations(mock_api)


class TestContactOperations:
    """Test contact-related operations."""

    def test_list_contacts_pagination(self, mock_api):
        """Verify page size and offset work correctly."""
        ops = ContactOperations(mock_api)

        # Test first page
        result = ops.list_contacts(page=0, page_size=2)
        assert result["success"] is True
        assert len(result["contacts"]) == 2
        assert result["page"] == 0
        assert result["total"] == 5
        assert result["total_pages"] == 3
        assert result["has_next"] is True
        assert result["has_prev"] is False

        # Test second page
        result = ops.list_contacts(page=1, page_size=2)
        assert len(result["contacts"]) == 2
        assert result["page"] == 1
        assert result["has_next"] is True
        assert result["has_prev"] is True

        # Test last page
        result = ops.list_contacts(page=2, page_size=2)
        assert len(result["contacts"]) == 1
        assert result["has_next"] is False
        assert result["has_prev"] is True

    def test_search_contacts_all_fields(self, mock_api):
        """Search matches name, email, phone fields."""
        ops = ContactOperations(mock_api)

        # Search by name
        results = ops.search_contacts("alice")
        assert len(results) > 0
        assert all("relevance_score" in r for r in results)

        # Empty search returns empty list
        results = ops.search_contacts("")
        assert results == []

    def test_get_contact_details_complete(self, mock_api):
        """Returns all associated data for a contact."""
        ops = ContactOperations(mock_api)

        # Get existing contact
        details = ops.get_contact_details(1)
        assert details is not None
        assert details["id"] == 1
        assert details["name"] == "Alice Smith"
        assert "relationships" in details
        assert "tags" in details
        assert "notes" in details

        # Non-existent contact returns None
        details = ops.get_contact_details(999)
        assert details is None

    def test_contacts_by_letter_case_insensitive(self, mock_api):
        """Letter jump works case-insensitively."""
        ops = ContactOperations(mock_api)

        # Test with 'A'
        results = ops.get_contacts_by_letter("A")
        assert len(results) == 1
        assert results[0]["name"] == "Alice Smith"

        # Test with lowercase 'a'
        results = ops.get_contacts_by_letter("a")
        assert len(results) == 1
        assert results[0]["name"] == "Alice Smith"

        # Test with 'B'
        results = ops.get_contacts_by_letter("B")
        assert len(results) == 1
        assert results[0]["name"] == "Bob Jones"

        # Invalid input returns empty
        assert ops.get_contacts_by_letter("") == []
        assert ops.get_contacts_by_letter("AB") == []


class TestRelationshipOperations:
    """Test relationship operations."""

    def test_create_relationship_validation(self, mock_api):
        """Invalid IDs rejected properly."""
        ops = RelationshipOperations(mock_api)

        # Same contact ID
        result = ops.create_relationship(1, 1, "friend")
        assert result["success"] is False
        assert "same contact" in result["error"].lower()

        # Invalid from_id
        result = ops.create_relationship(999, 2, "friend")
        assert result["success"] is False
        assert "999" in result["error"]

        # Invalid to_id
        result = ops.create_relationship(1, 999, "friend")
        assert result["success"] is False
        assert "999" in result["error"]

        # Invalid relationship type
        result = ops.create_relationship(1, 2, "invalid_type")
        assert result["success"] is False
        assert "invalid_type" in result["error"].lower()

        # Valid relationship
        result = ops.create_relationship(1, 2, "friend")
        assert result["success"] is True

    def test_delete_relationship_exists(self, mock_api):
        """Only deletes existing relationships."""
        ops = RelationshipOperations(mock_api)

        # Delete existing relationship
        result = ops.delete_relationship(1, 2, "mother")
        assert result["success"] is True

        # Delete non-existent relationship
        result = ops.delete_relationship(1, 3, "mother")
        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_find_relationships_bidirectional(self, mock_api):
        """Finds relationships in both directions."""
        ops = RelationshipOperations(mock_api)

        # Find relationships between two contacts
        relationships = ops.find_relationships_between(1, 2)
        assert len(relationships) > 0
        assert relationships[0]["from_contact_id"] == 1
        assert relationships[0]["to_contact_id"] == 2

    def test_relationship_types_complete(self, mock_api):
        """All relationship types returned with required fields."""
        ops = RelationshipOperations(mock_api)

        types = ops.list_relationship_types()
        assert len(types) == 3
        for rel_type in types:
            assert "type_key" in rel_type
            assert "description" in rel_type
            assert "is_symmetrical" in rel_type


class TestSearchOperations:
    """Test search operations."""

    def test_unified_search_grouping(self, mock_api):
        """Results grouped by type correctly."""
        ops = SearchOperations(mock_api)

        result = ops.unified_search("test")
        assert "contacts" in result
        assert "tags" in result
        assert "notes" in result
        assert "total" in result
        assert "counts" in result

        # Empty query returns empty results
        result = ops.unified_search("")
        assert result["total"] == 0

    def test_search_by_relationship_from_user(self, mock_api):
        """Filters relationships from user correctly."""
        ops = SearchOperations(mock_api)

        # Search for contacts with specific relationship type
        results = ops.search_by_relationship_type("mother", from_user=True)
        assert isinstance(results, list)

        # Each result should have relationship info
        for contact in results:
            assert "relationship_type" in contact
            assert contact["relationship_type"] == "mother"

    def test_search_empty_query(self, mock_api):
        """Handles empty string gracefully."""
        ops = SearchOperations(mock_api)

        # Unified search with empty query
        result = ops.unified_search("")
        assert result["total"] == 0

        # Search by note with empty query
        results = ops.search_by_note("")
        # Empty query to search_notes returns results, but we handle it
        assert isinstance(results, list)


class TestDatabaseOperations:
    """Test database operations."""

    def test_backup_with_comment(self, mock_api):
        """Comment stored correctly in backup."""
        ops = DatabaseOperations(mock_api)

        # Update mock to return the correct comment
        mock_api.create_backup_with_comment.return_value = {
            "id": 3,
            "filename": "backup_20240103_120000.db",
            "path": "/tmp/backup_20240103_120000.db",
            "comment": "Test comment",  # Match what we're testing
            "created_at": "2024-01-03 12:00:00",
            "size": 1024 * 1024,
        }

        result = ops.create_backup("Test comment")
        assert result["success"] is True
        assert result["backup"]["comment"] == "Test comment"
        assert "filename" in result["backup"]
        assert "size_mb" in result["backup"]

    def test_restore_backup_validation(self, mock_api):
        """Invalid backup ID rejected."""
        ops = DatabaseOperations(mock_api)

        # Valid backup ID
        result = ops.restore_backup(1)
        assert result["success"] is True

        # Invalid backup ID
        result = ops.restore_backup(999)
        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_list_backups_pagination(self, mock_api):
        """Pagination works correctly for backups."""
        ops = DatabaseOperations(mock_api)

        # First page
        result = ops.list_backups(limit=1, offset=0)
        assert result["success"] is True
        assert len(result["backups"]) == 1
        assert result["total"] == 2
        assert result["has_more"] is True

        # Second page
        result = ops.list_backups(limit=1, offset=1)
        assert len(result["backups"]) == 1
        assert result["has_more"] is False

    def test_database_status_complete(self, mock_api):
        """Database status includes all required info."""
        ops = DatabaseOperations(mock_api)

        status = ops.get_database_status()
        assert status["healthy"] is True
        assert "counts" in status
        assert status["counts"]["contacts"] == 5
        assert "database_size_mb" in status
        assert "last_backup" in status


class TestOperationsOrchestrator:
    """Test main operations orchestrator."""

    def test_validate_operation(self, operations):
        """Operation validation works correctly."""
        # Valid create_relationship
        result = operations.validate_operation(
            "create_relationship", {"from_id": 1, "to_id": 2, "type_key": "friend"}
        )
        assert result["valid"] is True
        assert len(result["errors"]) == 0

        # Invalid - same contact
        result = operations.validate_operation(
            "create_relationship", {"from_id": 1, "to_id": 1, "type_key": "friend"}
        )
        assert result["valid"] is False
        assert "same contact" in result["errors"][0].lower()

        # Missing required field
        result = operations.validate_operation("create_relationship", {"from_id": 1, "to_id": 2})
        assert result["valid"] is False
        assert "type_key" in result["errors"][0]

    def test_execute_batch(self, operations):
        """Batch execution processes multiple operations."""
        batch = [
            {"type": "list_contacts", "params": {"page": 0, "page_size": 2}},
            {"type": "list_relationship_types", "params": {}},
            {"type": "database_status", "params": {}},
        ]

        results = operations.execute_batch(batch)
        assert len(results) == 3
        assert results[0]["success"] is True
        assert results[1]["success"] is True
        assert results[2]["success"] is True

    def test_get_available_operations(self, operations):
        """Lists all available operations."""
        ops = operations.get_available_operations()
        assert "list_contacts" in ops
        assert "create_relationship" in ops
        assert "unified_search" in ops
        assert "create_backup" in ops
        assert len(ops) > 10  # Should have many operations


class TestPlatformAbstraction:
    """Test platform abstraction functionality."""

    def test_platform_capabilities(self):
        """Platform capabilities properly defined."""
        from prt_src.platforms import PlatformCapabilities

        caps = PlatformCapabilities()
        assert caps.can_export_files is True
        assert caps.can_import_files is True
        assert caps.has_persistent_storage is True
        assert caps.max_display_width == 120

    def test_pagination_helper(self):
        """Pagination helper works correctly."""
        from prt_src.platforms.base import Platform, PlatformCapabilities

        # Create a concrete test implementation
        class TestPlatform(Platform):
            def get_capabilities(self):
                return PlatformCapabilities()

            def get_input(self, prompt, choices=None, default=None, password=False):
                return "test"

            def display_output(self, content, style=None, format="text"):
                pass

            def get_file_path(self, title="", file_types=None, save=False):
                return None

            def get_export_path(self, default_name, extension=".json"):
                return None

            def show_progress(self, message, current=0, total=100):
                pass

            def confirm(self, message, default=False):
                return True

            def clear_screen(self):
                pass

        platform = TestPlatform()
        items = list(range(25))

        # Test first page
        page_items, info = platform.paginate(items, page=0, page_size=10)
        assert len(page_items) == 10
        assert info["page"] == 0
        assert info["total"] == 25
        assert info["total_pages"] == 3
        assert info["has_next"] is True
        assert info["has_prev"] is False

        # Test last page
        page_items, info = platform.paginate(items, page=2, page_size=10)
        assert len(page_items) == 5
        assert info["has_next"] is False
        assert info["has_prev"] is True
