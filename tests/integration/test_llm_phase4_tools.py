"""Integration tests for LLM Phase 4 tools (SQL, directory generation, relationships).

Tests that Phase 4 tools:
1. SQL execution requires confirmation for ALL queries
2. SQL write operations create automatic backups
3. Directory generation creates D3.js visualizations
4. Relationship management tools create backups
5. Error handling works correctly

These tests call tool methods directly (not chat()) so they remain fast integration tests.
"""

from pathlib import Path

import pytest

from prt_src.api import PRTAPI
from prt_src.llm_ollama import OllamaLLM


@pytest.mark.integration
class TestLLMPhase4Tools:
    """Test Phase 4 advanced tools (SQL, directory, relationships)."""

    def test_execute_sql_requires_confirmation(self, test_db):
        """Test that SQL execution requires confirm=true for ALL queries."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config)
        llm = OllamaLLM(api=api)

        # Try to execute SQL without confirmation
        result = llm._call_tool(
            "execute_sql",
            {"sql": "SELECT COUNT(*) FROM contacts", "confirm": False},
        )

        # Verify rejection
        assert isinstance(result, dict)
        assert result["success"] is False
        assert "Confirmation required" in result["error"]
        assert "confirm=true" in result["message"]

    def test_execute_sql_read_query_with_confirmation(self, test_db):
        """Test that SQL read queries work when confirmed."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config)
        llm = OllamaLLM(api=api)

        # Execute SELECT query with confirmation
        result = llm._call_tool(
            "execute_sql",
            {
                "sql": "SELECT id, name FROM contacts LIMIT 2",
                "confirm": True,
                "reason": "Testing read query",
            },
        )

        # Verify success
        assert isinstance(result, dict)
        assert result["success"] is True
        assert "rows" in result
        assert "rowcount" in result
        assert len(result["rows"]) <= 2
        # Each row should have id and name
        if result["rows"]:
            assert "id" in result["rows"][0]
            assert "name" in result["rows"][0]

    def test_execute_sql_write_query_creates_backup(self, test_db):
        """Test that SQL write queries create automatic backups."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config)
        llm = OllamaLLM(api=api)

        # Get initial backup count
        initial_backups = api.get_backup_history()
        initial_count = len(initial_backups)

        # Execute write query with confirmation
        result = llm._call_tool(
            "execute_sql",
            {
                "sql": "INSERT INTO tags (name) VALUES ('sql-test-tag')",
                "confirm": True,
                "reason": "Testing write query backup",
            },
        )

        # Verify success
        assert result["success"] is True
        assert result["rowcount"] == 1

        # Verify backup was created
        final_backups = api.get_backup_history()
        assert len(final_backups) == initial_count + 1

        latest_backup = final_backups[0]
        assert latest_backup["is_auto"] is True
        assert "execute_sql" in latest_backup["comment"]

    def test_generate_directory(self, test_db):
        """Test directory generation creates D3.js visualization."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config)
        llm = OllamaLLM(api=api)

        # First check what contacts exist in the test database
        contacts = api.list_all_contacts()
        if not contacts:
            pytest.skip("Test requires contacts in database")

        # Use name from first contact to ensure we find something
        first_contact_name = contacts[0]["name"].split()[0]  # Use first name only

        # Generate directory for all contacts
        result = llm._call_tool(
            "generate_directory",
            {"search_query": first_contact_name, "output_name": "test_directory"},
        )

        # Verify success
        assert isinstance(result, dict)
        if not result["success"]:
            print(f"Error: {result.get('error')}")
            print(f"Message: {result.get('message')}")
        assert result["success"] is True
        assert "output_path" in result
        assert "url" in result
        assert "contact_count" in result
        assert result["contact_count"] > 0

        # Verify output directory exists
        output_path = Path(result["output_path"])
        assert output_path.exists()
        assert (output_path / "index.html").exists()
        assert (output_path / "data.js").exists()

    def test_generate_directory_with_search_query(self, test_db):
        """Test directory generation with specific search query."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config)
        llm = OllamaLLM(api=api)

        # Search for specific contact
        contacts = api.search_contacts("Alice")
        if not contacts:
            pytest.skip("Test requires contact named Alice")

        # Generate directory with search query
        result = llm._call_tool(
            "generate_directory",
            {"search_query": "Alice", "output_name": "test_alice"},
        )

        # Verify success
        assert result["success"] is True
        assert result["contact_count"] >= 1

        # Verify output exists
        output_path = Path(result["output_path"])
        assert output_path.exists()

    def test_generate_directory_no_results(self, test_db):
        """Test directory generation with no matching contacts."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config)
        llm = OllamaLLM(api=api)

        # Search for non-existent contact
        result = llm._call_tool(
            "generate_directory",
            {"search_query": "NonExistentContact12345", "output_name": "test_empty"},
        )

        # Verify failure
        assert result["success"] is False
        assert "No contacts found" in result["message"]

    def test_add_contact_relationship_creates_backup(self, test_db):
        """Test that add_contact_relationship creates automatic backup."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config)
        llm = OllamaLLM(api=api)

        # Get two contact names from fixtures
        contacts = api.list_all_contacts()
        if len(contacts) < 2:
            pytest.skip("Test requires at least 2 contacts")

        contact1_name = contacts[0]["name"]
        contact2_name = contacts[1]["name"]

        # Get initial backup count
        initial_backups = api.get_backup_history()
        initial_count = len(initial_backups)

        # Add relationship using LLM tool
        result = llm._call_tool(
            "add_contact_relationship",
            {
                "from_contact_name": contact1_name,
                "to_contact_name": contact2_name,
                "type_key": "friend",
            },
        )

        # Verify result structure
        assert isinstance(result, dict)
        assert result["success"] is True
        assert "backup_id" in result
        assert "message" in result
        assert "Backup #" in result["message"]

        # Verify backup was created
        final_backups = api.get_backup_history()
        assert len(final_backups) == initial_count + 1

        # Verify backup metadata
        latest_backup = final_backups[0]
        assert latest_backup["is_auto"] is True
        assert "add_contact_relationship" in latest_backup["comment"]

    def test_remove_contact_relationship_creates_backup(self, test_db):
        """Test that remove_contact_relationship creates automatic backup."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config)
        llm = OllamaLLM(api=api)

        # Get two contact names
        contacts = api.list_all_contacts()
        if len(contacts) < 2:
            pytest.skip("Test requires at least 2 contacts")

        contact1_name = contacts[0]["name"]
        contact2_name = contacts[1]["name"]

        # First add a relationship using an available relationship type
        relationship_types = api.list_all_relationship_types()
        if not relationship_types:
            pytest.skip("Test requires at least one relationship type")

        test_type = relationship_types[0]["type_key"]  # Use first available type
        api.add_contact_relationship(contact1_name, contact2_name, test_type)

        # Get backup count after add
        initial_backups = api.get_backup_history()
        initial_count = len(initial_backups)

        # Remove relationship using LLM tool
        result = llm._call_tool(
            "remove_contact_relationship",
            {
                "from_contact_name": contact1_name,
                "to_contact_name": contact2_name,
                "type_key": test_type,
            },
        )

        # Verify result
        assert result["success"] is True
        assert "backup_id" in result

        # Verify backup was created
        final_backups = api.get_backup_history()
        assert len(final_backups) == initial_count + 1

        latest_backup = final_backups[0]
        assert "remove_contact_relationship" in latest_backup["comment"]

    def test_is_write_operation_includes_phase4_tools(self, test_db):
        """Test that _is_write_operation correctly identifies Phase 4 write tools."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config)
        llm = OllamaLLM(api=api)

        # Phase 4 write operations (relationships)
        assert llm._is_write_operation("add_contact_relationship") is True
        assert llm._is_write_operation("remove_contact_relationship") is True

        # Phase 4 non-write operations (SQL and directory are special, handled separately)
        assert llm._is_write_operation("execute_sql") is False
        assert llm._is_write_operation("generate_directory") is False

    def test_sql_error_handling(self, test_db):
        """Test that SQL errors are handled gracefully."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config)
        llm = OllamaLLM(api=api)

        # Execute invalid SQL with confirmation
        result = llm._call_tool(
            "execute_sql",
            {
                "sql": "SELECT * FROM nonexistent_table_12345",
                "confirm": True,
                "reason": "Testing error handling",
            },
        )

        # Verify error structure
        assert isinstance(result, dict)
        assert result["success"] is False
        assert "error" in result
        assert "message" in result

    def test_relationship_error_handling(self, test_db):
        """Test that relationship operations handle errors gracefully."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config)
        llm = OllamaLLM(api=api)

        # Try to add relationship with non-existent contacts
        result = llm._call_tool(
            "add_contact_relationship",
            {
                "from_contact_name": "NonExistentContact12345",
                "to_contact_name": "AlsoNonExistent67890",
                "type_key": "friend",
            },
        )

        # Verify error structure (should fail before creating backup)
        assert isinstance(result, dict)
        # This might succeed or fail depending on API implementation
        # We're testing that the wrapper returns a proper structure
        assert "success" in result
        if not result["success"]:
            assert "error" in result
            assert "message" in result

    def test_execute_sql_with_profile_images_no_json_error(self, test_db):
        """Test that execute_sql with profile images doesn't cause JSON serialization errors."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config)
        llm = OllamaLLM(api=api)

        # Execute SQL query that returns profile images (binary data)
        # This simulates the exact scenario from the bug report
        result = llm._call_tool(
            "execute_sql",
            {
                "sql": "SELECT id, name, profile_image FROM contacts WHERE profile_image IS NOT NULL LIMIT 2",
                "confirm": True,
                "reason": "Testing profile image query without JSON errors",
            },
        )

        # Verify the tool executes successfully without JSON serialization errors
        assert isinstance(result, dict)
        assert result["success"] is True
        assert "rows" in result
        assert "rowcount" in result
        assert result["rowcount"] > 0  # Should have contacts with profile images

        # Verify that rows contain profile image data as bytes
        for row in result["rows"]:
            assert "id" in row
            assert "name" in row
            assert "profile_image" in row
            # Profile image should be binary data
            assert isinstance(row["profile_image"], bytes)
            assert len(row["profile_image"]) > 0

        # Most importantly: this test passing means no JSON serialization error occurred
        # The enhanced logging should handle bytes data properly with the custom serializer
