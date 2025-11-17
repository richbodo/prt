"""Tests for relationship deletion efficiency improvements (PR 157 follow-up)."""

from unittest.mock import Mock
from unittest.mock import patch

import pytest

from prt_src.api import PRTAPI
from prt_src.tui.services.data import DataService


class TestRelationshipDeletionEfficiency:
    """Test the efficiency improvements for relationship deletion."""

    def test_database_delete_relationship_by_id_success(self, test_db):
        """Test database layer delete_relationship_by_id method."""
        db_instance, fixtures = test_db

        # Create a test relationship first

        # Get existing contacts from fixtures
        contacts_raw = db_instance.list_contacts()
        contacts = [{"id": c[0], "name": c[1], "email": c[2]} for c in contacts_raw]
        assert len(contacts) >= 2, "Need at least 2 contacts for relationship test"

        from_contact = contacts[0]
        to_contact = contacts[1]

        # Create a relationship type if it doesn't exist
        rel_types = db_instance.list_relationship_types()
        if not rel_types:
            db_instance.create_relationship_type("friend", "Friend", True)
            rel_types = db_instance.list_relationship_types()

        type_key = rel_types[0]["type_key"]

        # Create a relationship
        db_instance.create_contact_relationship(from_contact["id"], to_contact["id"], type_key)

        # Get all relationships to find the one we just created
        relationships = db_instance.get_all_relationships()
        test_relationship = None
        for rel in relationships:
            if (
                rel["from_contact_id"] == from_contact["id"]
                and rel["to_contact_id"] == to_contact["id"]
                and rel["type_key"] == type_key
            ):
                test_relationship = rel
                break

        assert test_relationship is not None, "Test relationship should exist"
        relationship_id = test_relationship["relationship_id"]

        # Test deletion
        result = db_instance.delete_relationship_by_id(relationship_id)
        assert result is True, "Deletion should succeed"

        # Verify relationship is deleted
        updated_relationships = db_instance.get_all_relationships()
        for rel in updated_relationships:
            assert rel["relationship_id"] != relationship_id, "Relationship should be deleted"

    def test_database_delete_relationship_by_id_not_found(self, test_db):
        """Test database layer delete_relationship_by_id with non-existent ID."""
        db_instance, fixtures = test_db

        # Try to delete non-existent relationship
        result = db_instance.delete_relationship_by_id(99999)
        assert result is False, "Deletion should fail for non-existent relationship"

    def test_api_delete_relationship_by_id_success(self, test_db):
        """Test API layer delete_relationship_by_id method."""
        db_instance, fixtures = test_db
        config = {"db_path": str(db_instance.path), "db_encrypted": False}
        api = PRTAPI(config)

        # Get existing relationships from fixtures
        relationships = api.get_all_relationships()
        if not relationships:
            # Create a test relationship if none exist
            contacts = api.list_all_contacts()
            assert len(contacts) >= 2, "Need at least 2 contacts"

            # Create relationship type if needed
            rel_types = api.list_all_relationship_types()
            if not rel_types:
                api.create_relationship_type("friend", "Friend", True)
                rel_types = api.list_all_relationship_types()

            # Create a relationship
            api.add_contact_relationship(
                contacts[0]["name"], contacts[1]["name"], rel_types[0]["type_key"]
            )
            relationships = api.get_all_relationships()

        assert len(relationships) > 0, "Should have at least one relationship"
        test_relationship = relationships[0]
        relationship_id = test_relationship["relationship_id"]

        # Test deletion
        result = api.delete_relationship_by_id(relationship_id)
        assert result["success"] is True, "API deletion should succeed"
        assert "message" in result
        assert "relationship_id" in result
        assert result["relationship_id"] == relationship_id

    def test_api_delete_relationship_by_id_not_found(self, test_db):
        """Test API layer delete_relationship_by_id with non-existent ID."""
        db_instance, fixtures = test_db
        config = {"db_path": str(db_instance.path), "db_encrypted": False}
        api = PRTAPI(config)

        # Try to delete non-existent relationship
        result = api.delete_relationship_by_id(99999)
        assert result["success"] is False
        assert "not found" in result["error"].lower()

    async def test_data_service_delete_relationship_simplified(self, test_db):
        """Test that DataService delete_relationship is simplified."""
        db_instance, fixtures = test_db

        # Create a DataService instance
        data_service = DataService()
        data_service.api = Mock()

        # Mock the API response
        mock_result = {"success": True, "message": "Deleted"}
        data_service.api.delete_relationship_by_id.return_value = mock_result

        # Test the method (it's async)
        result = await data_service.delete_relationship(123)

        # Verify it calls the API method exactly once
        data_service.api.delete_relationship_by_id.assert_called_once_with(123)
        assert result is True

    async def test_delete_relationship_single_api_call(self, test_db):
        """Test that deleting a relationship makes exactly 1 API call."""
        db_instance, fixtures = test_db

        # Create a DataService instance with mocked API
        data_service = DataService()
        data_service.api = Mock()

        # Mock the API response
        mock_result = {"success": True}
        data_service.api.delete_relationship_by_id.return_value = mock_result

        # Call the delete method (it's async)
        result = await data_service.delete_relationship(123)

        # Verify exactly one API call was made
        assert data_service.api.delete_relationship_by_id.call_count == 1
        assert result is True

    @pytest.mark.integration
    def test_delete_relationship_performance(self, test_db):
        """Test that relationship deletion performance is acceptable."""
        import time

        db_instance, fixtures = test_db
        config = {"db_path": str(db_instance.path), "db_encrypted": False}

        # Create multiple relationships for performance testing
        api = PRTAPI(config)
        contacts = api.list_all_contacts()

        if len(contacts) >= 2:
            # Create relationship type if needed
            rel_types = api.list_all_relationship_types()
            if not rel_types:
                api.create_relationship_type("friend", "Friend", True)
                rel_types = api.list_all_relationship_types()

            type_key = rel_types[0]["type_key"]

            # Create a relationship
            api.add_contact_relationship(contacts[0]["name"], contacts[1]["name"], type_key)

            relationships = api.get_all_relationships()
            if relationships:
                relationship_id = relationships[-1]["relationship_id"]

                # Time the deletion
                start_time = time.time()
                result = api.delete_relationship_by_id(relationship_id)
                end_time = time.time()

                # Performance should be under 0.1 seconds
                deletion_time = end_time - start_time
                assert deletion_time < 0.1, f"Deletion took {deletion_time:.3f}s, should be < 0.1s"
                assert result["success"] is True

    async def test_data_service_error_handling(self, test_db):
        """Test error handling in DataService delete_relationship."""
        data_service = DataService()
        data_service.api = Mock()

        # Mock an exception
        data_service.api.delete_relationship_by_id.side_effect = Exception("API Error")

        # Test error handling (it's async)
        result = await data_service.delete_relationship(123)
        assert result is False

    def test_api_error_handling(self, test_db):
        """Test error handling in API delete_relationship_by_id."""
        db_instance, fixtures = test_db
        config = {"db_path": str(db_instance.path), "db_encrypted": False}
        api = PRTAPI(config)

        # Mock database to raise exception
        with patch.object(api.db, "delete_relationship_by_id", side_effect=Exception("DB Error")):
            result = api.delete_relationship_by_id(123)
            assert result["success"] is False
            assert "error" in result
