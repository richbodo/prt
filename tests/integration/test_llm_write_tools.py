"""Integration tests for LLM write tools with automatic backups.

Tests that write operations:
1. Create automatic backups before modifying data
2. Execute successfully
3. Return proper result structure with backup_id
4. Handle errors gracefully
"""

from prt_src.api import PRTAPI
from prt_src.llm_ollama import OllamaLLM


class TestLLMWriteTools:
    """Test write tools create automatic backups and modify data correctly."""

    def test_add_tag_creates_backup(self, test_db):
        """Test that add_tag_to_contact creates automatic backup."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config)
        llm = OllamaLLM(api=api)

        # Get initial backup count
        initial_backups = api.get_backup_history()
        initial_count = len(initial_backups)

        # Add tag to contact using LLM tool
        result = llm._call_tool("add_tag_to_contact", {"contact_id": 1, "tag_name": "test-tag"})

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
        latest_backup = final_backups[0]  # Most recent first
        assert latest_backup["is_auto"] is True
        assert "add_tag_to_contact" in latest_backup["comment"]

    def test_remove_tag_creates_backup(self, test_db):
        """Test that remove_tag_from_contact creates automatic backup."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config)
        llm = OllamaLLM(api=api)

        # First add a tag
        api.add_tag_to_contact(1, "temp-tag")

        # Get backup count after add
        initial_backups = api.get_backup_history()
        initial_count = len(initial_backups)

        # Remove tag using LLM tool
        result = llm._call_tool(
            "remove_tag_from_contact", {"contact_id": 1, "tag_name": "temp-tag"}
        )

        # Verify result
        assert result["success"] is True
        assert "backup_id" in result

        # Verify backup was created
        final_backups = api.get_backup_history()
        assert len(final_backups) == initial_count + 1

        latest_backup = final_backups[0]
        assert "remove_tag_from_contact" in latest_backup["comment"]

    def test_create_tag_creates_backup(self, test_db):
        """Test that create_tag creates automatic backup."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config)
        llm = OllamaLLM(api=api)

        initial_backups = api.get_backup_history()
        initial_count = len(initial_backups)

        # Create tag using LLM tool
        result = llm._call_tool("create_tag", {"name": "new-test-tag"})

        # Verify result
        assert result["success"] is True
        assert "backup_id" in result

        # Verify backup was created
        final_backups = api.get_backup_history()
        assert len(final_backups) == initial_count + 1

        latest_backup = final_backups[0]
        assert "create_tag" in latest_backup["comment"]

    def test_delete_tag_creates_backup(self, test_db):
        """Test that delete_tag creates automatic backup."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config)
        llm = OllamaLLM(api=api)

        # Create tag to delete
        api.create_tag("tag-to-delete")

        initial_backups = api.get_backup_history()
        initial_count = len(initial_backups)

        # Delete tag using LLM tool
        result = llm._call_tool("delete_tag", {"name": "tag-to-delete"})

        # Verify result
        assert result["success"] is True
        assert "backup_id" in result

        # Verify backup was created
        final_backups = api.get_backup_history()
        assert len(final_backups) == initial_count + 1

        latest_backup = final_backups[0]
        assert "delete_tag" in latest_backup["comment"]

    def test_add_note_to_contact_creates_backup(self, test_db):
        """Test that add_note_to_contact creates automatic backup."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config)
        llm = OllamaLLM(api=api)

        initial_backups = api.get_backup_history()
        initial_count = len(initial_backups)

        # Add note using LLM tool
        result = llm._call_tool(
            "add_note_to_contact",
            {
                "contact_id": 1,
                "note_title": "Test Note",
                "note_content": "This is a test note",
            },
        )

        # Verify result
        assert result["success"] is True
        assert "backup_id" in result

        # Verify backup was created
        final_backups = api.get_backup_history()
        assert len(final_backups) == initial_count + 1

        latest_backup = final_backups[0]
        assert "add_note_to_contact" in latest_backup["comment"]

    def test_remove_note_from_contact_creates_backup(self, test_db):
        """Test that remove_note_from_contact creates automatic backup."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config)
        llm = OllamaLLM(api=api)

        # Add note first
        api.add_note_to_contact(1, "Temp Note", "Temporary content")

        initial_backups = api.get_backup_history()
        initial_count = len(initial_backups)

        # Remove note using LLM tool
        result = llm._call_tool(
            "remove_note_from_contact", {"contact_id": 1, "note_title": "Temp Note"}
        )

        # Verify result
        assert result["success"] is True
        assert "backup_id" in result

        # Verify backup was created
        final_backups = api.get_backup_history()
        assert len(final_backups) == initial_count + 1

        latest_backup = final_backups[0]
        assert "remove_note_from_contact" in latest_backup["comment"]

    def test_create_note_creates_backup(self, test_db):
        """Test that create_note creates automatic backup."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config)
        llm = OllamaLLM(api=api)

        initial_backups = api.get_backup_history()
        initial_count = len(initial_backups)

        # Create note using LLM tool
        result = llm._call_tool(
            "create_note", {"title": "New Test Note", "content": "Test content"}
        )

        # Verify result
        assert result["success"] is True
        assert "backup_id" in result

        # Verify backup was created
        final_backups = api.get_backup_history()
        assert len(final_backups) == initial_count + 1

        latest_backup = final_backups[0]
        assert "create_note" in latest_backup["comment"]

    def test_update_note_creates_backup(self, test_db):
        """Test that update_note creates automatic backup."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config)
        llm = OllamaLLM(api=api)

        # Create note to update
        api.create_note("Note to Update", "Original content")

        initial_backups = api.get_backup_history()
        initial_count = len(initial_backups)

        # Update note using LLM tool
        result = llm._call_tool(
            "update_note", {"title": "Note to Update", "content": "Updated content"}
        )

        # Verify result
        assert result["success"] is True
        assert "backup_id" in result

        # Verify backup was created
        final_backups = api.get_backup_history()
        assert len(final_backups) == initial_count + 1

        latest_backup = final_backups[0]
        assert "update_note" in latest_backup["comment"]

    def test_delete_note_creates_backup(self, test_db):
        """Test that delete_note creates automatic backup."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config)
        llm = OllamaLLM(api=api)

        # Create note to delete
        api.create_note("Note to Delete", "Will be deleted")

        initial_backups = api.get_backup_history()
        initial_count = len(initial_backups)

        # Delete note using LLM tool
        result = llm._call_tool("delete_note", {"title": "Note to Delete"})

        # Verify result
        assert result["success"] is True
        assert "backup_id" in result

        # Verify backup was created
        final_backups = api.get_backup_history()
        assert len(final_backups) == initial_count + 1

        latest_backup = final_backups[0]
        assert "delete_note" in latest_backup["comment"]

    def test_write_operation_error_handling(self, test_db):
        """Test that write operations handle errors gracefully."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config)
        llm = OllamaLLM(api=api)

        # Try to delete a non-existent tag (this should fail)
        result = llm._call_tool("delete_tag", {"name": "non-existent-tag-12345"})

        # Verify error structure
        assert isinstance(result, dict)
        # Note: Some operations may succeed even with invalid data (e.g., deleting non-existent tag is a no-op)
        # We're testing that the wrapper returns a proper structure
        assert "success" in result
        if not result["success"]:
            assert "error" in result
            assert "message" in result

    def test_read_only_tools_no_backup(self, test_db):
        """Test that read-only tools don't create backups."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config)
        llm = OllamaLLM(api=api)

        initial_backups = api.get_backup_history()
        initial_count = len(initial_backups)

        # Call read-only tool
        result = llm._call_tool("get_database_stats", {})

        # Verify no backup was created
        final_backups = api.get_backup_history()
        assert len(final_backups) == initial_count

        # Verify result doesn't have backup_id
        assert isinstance(result, dict)
        assert "backup_id" not in result

    def test_is_write_operation_detection(self, test_db):
        """Test that _is_write_operation correctly identifies write tools."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config)
        llm = OllamaLLM(api=api)

        # Write operations
        assert llm._is_write_operation("add_tag_to_contact") is True
        assert llm._is_write_operation("remove_tag_from_contact") is True
        assert llm._is_write_operation("create_tag") is True
        assert llm._is_write_operation("delete_tag") is True
        assert llm._is_write_operation("add_note_to_contact") is True
        assert llm._is_write_operation("remove_note_from_contact") is True
        assert llm._is_write_operation("create_note") is True
        assert llm._is_write_operation("update_note") is True
        assert llm._is_write_operation("delete_note") is True

        # Read operations
        assert llm._is_write_operation("search_contacts") is False
        assert llm._is_write_operation("list_all_contacts") is False
        assert llm._is_write_operation("get_database_stats") is False
        assert llm._is_write_operation("create_backup_with_comment") is False

    def test_manual_backup_tool(self, test_db):
        """Test manual backup tool works correctly."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config)
        llm = OllamaLLM(api=api)

        initial_backups = api.get_backup_history()
        initial_count = len(initial_backups)

        # Create manual backup
        result = llm._call_tool("create_backup_with_comment", {"comment": "Manual test backup"})

        # Verify result - manual backup tool returns the API result directly (not wrapped)
        assert isinstance(result, dict)
        # create_backup_with_comment returns 'id' not 'backup_id'
        assert "id" in result or "backup_id" in result

        # Verify backup was created
        final_backups = api.get_backup_history()
        assert len(final_backups) == initial_count + 1

        latest_backup = final_backups[0]
        assert latest_backup["is_auto"] is False
        assert "Manual test backup" in latest_backup["comment"]

    def test_multiple_write_operations_create_multiple_backups(self, test_db):
        """Test that multiple write operations each create their own backup.

        This verifies the backup system scales with operations.
        """
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config)
        llm = OllamaLLM(api=api)

        initial_backups = api.get_backup_history()
        initial_count = len(initial_backups)

        # Perform 3 write operations
        llm._call_tool("create_tag", {"name": "multi-test-1"})
        llm._call_tool("create_tag", {"name": "multi-test-2"})
        llm._call_tool("create_note", {"title": "Multi Test", "content": "Content"})

        # Verify 3 backups were created
        final_backups = api.get_backup_history()
        assert len(final_backups) == initial_count + 3

        # Verify all are automatic backups
        new_backups = final_backups[:3]  # Most recent 3
        for backup in new_backups:
            assert backup["is_auto"] is True
