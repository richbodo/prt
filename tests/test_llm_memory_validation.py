"""
Validation and coverage tests for LLM Memory System.

These tests focus on validation, edge cases, and ensuring comprehensive
coverage of memory system functionality and error conditions.
"""

from unittest.mock import Mock
from unittest.mock import patch

import pytest

from prt_src.api import PRTAPI
from prt_src.llm_ollama import OllamaLLM
from tests.mocks.mock_llm_memory import TestMemoryContext


@pytest.mark.integration
class TestLLMMemoryValidation:
    """Validation tests for memory system reliability and coverage."""

    def test_memory_id_format_validation(self, isolated_memory_context):
        """Test memory ID format consistency and validation."""
        mock_memory = isolated_memory_context

        # Test various result types
        result_types = ["contacts", "search", "notes", "tags", "query"]

        for result_type in result_types:
            memory_id = mock_memory.save_result(
                {"data": "test"}, result_type, f"test {result_type}"
            )

            # Validate ID format: test_{type}_{timestamp}_{uuid}
            parts = memory_id.split("_")
            assert parts[0] == "test"  # test prefix for mock
            assert parts[1] == result_type
            assert len(parts) >= 4  # test, type, timestamp, uuid

            # Timestamp should be 6 digits (HHMMSS)
            assert len(parts[2]) == 6
            assert parts[2].isdigit()

            # UUID part should be 8 characters
            assert len(parts[3]) == 8

    def test_contact_data_consistency_validation(self, test_db, isolated_memory_context):
        """Test contact data consistency through save/load cycles."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}

        api = PRTAPI(config)
        llm = OllamaLLM(api=api)

        # Save contacts with images
        result = llm._save_contacts_with_images("validation test contacts")
        assert result["success"] is True

        memory_id = result["memory_id"]
        mock_memory = isolated_memory_context

        # Load and validate data structure
        loaded = mock_memory.load_result(memory_id)
        assert loaded is not None

        contacts = loaded["data"]
        assert isinstance(contacts, list)
        assert len(contacts) > 0

        # Validate each contact structure
        for contact in contacts:
            # Required fields
            assert "id" in contact
            assert "name" in contact
            assert isinstance(contact["id"], int)
            assert isinstance(contact["name"], str)

            # Image handling validation
            if "profile_image" in contact:
                # Profile images should be either bytes or None
                assert contact["profile_image"] is None or isinstance(
                    contact["profile_image"], bytes
                )

            # has_profile_image flag should be boolean
            if "has_profile_image" in contact:
                assert isinstance(contact["has_profile_image"], bool)

    def test_directory_generation_validation(self, test_db, isolated_memory_context):
        """Test directory generation with memory ID validation."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}

        api = PRTAPI(config)
        llm = OllamaLLM(api=api)

        # Test with valid memory ID
        save_result = llm._save_contacts_with_images("directory validation test")
        memory_id = save_result["memory_id"]

        # Test directory generation
        directory_result = llm._generate_directory(
            memory_id=memory_id, output_name="validation_test_dir"
        )

        assert directory_result["success"] is True
        assert "output_path" in directory_result
        assert "url" in directory_result

        # Cleanup
        import shutil
        from pathlib import Path

        output_path = Path(directory_result["output_path"])
        if output_path.exists():
            shutil.rmtree(
                output_path.parent if output_path.name.endswith("_directory") else output_path
            )

    def test_memory_error_conditions(self, isolated_memory_context):
        """Test memory system error handling and edge cases."""
        mock_memory = isolated_memory_context

        # Test loading non-existent memory ID
        result = mock_memory.load_result("nonexistent_id")
        assert result is None

        # Test deleting non-existent memory ID
        deleted = mock_memory.delete_result("nonexistent_id")
        assert deleted is False

        # Test listing with no results
        initial_results = mock_memory.list_results()
        assert isinstance(initial_results, list)

        # Test listing with filter that matches nothing
        filtered_results = mock_memory.list_results(result_type="nonexistent_type")
        assert isinstance(filtered_results, list)
        assert len(filtered_results) == 0

    def test_api_test_environment_detection(self, test_db):
        """Test that PRTAPI correctly detects test environment."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}

        api = PRTAPI(config)

        # Should detect test environment
        assert api._is_test_environment() is True

        # Test the various detection methods

        # Test pytest module detection
        import sys

        assert "pytest" in sys.modules

        # Test database path detection
        db_path_str = str(api.db.path)
        test_indicators = ["test.db", "test_", "/tmp/", "debug.db", "empty_test"]
        assert any(indicator in db_path_str.lower() for indicator in test_indicators)

    def test_schema_migration_skipping_in_tests(self, test_db):
        """Test that schema migrations are skipped in test environment."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}

        # Mock schema manager to simulate migration needed
        with patch("prt_src.api.SchemaManager") as mock_schema_manager_class:
            mock_schema_manager = Mock()
            mock_schema_manager.get_schema_version.return_value = 5  # Simulate older version
            mock_schema_manager.check_migration_needed.return_value = True
            mock_schema_manager.migrate_safely.return_value = True
            mock_schema_manager_class.return_value = mock_schema_manager

            # Initialize API - should detect test environment and skip migration
            PRTAPI(config)

            # Migration should not have been called due to test environment
            mock_schema_manager.migrate_safely.assert_not_called()

    def test_memory_context_manager_isolation(self):
        """Test TestMemoryContext provides proper isolation."""
        # Test that different contexts are isolated
        with TestMemoryContext("test1", use_temp_files=False) as memory1:
            memory1_id = memory1.save_result({"data": "test1"}, "test", "context 1")

            with TestMemoryContext("test2", use_temp_files=False) as memory2:
                memory2_id = memory2.save_result({"data": "test2"}, "test", "context 2")

                # Each context should only see its own data
                assert memory1.load_result(memory1_id) is not None
                assert memory1.load_result(memory2_id) is None

                assert memory2.load_result(memory2_id) is not None
                assert memory2.load_result(memory1_id) is None

    def test_tool_usage_information_accuracy(self, test_db, isolated_memory_context):
        """Test accuracy of tool usage information."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}

        api = PRTAPI(config)
        llm = OllamaLLM(api=api)

        result = llm._save_contacts_with_images("usage info test")

        # Validate usage information
        assert "usage" in result
        usage = result["usage"]
        assert isinstance(usage, str)

        # Should contain helpful information
        assert "saved" in usage.lower()
        assert str(result["count"]) in usage
        assert result["memory_id"] in usage

    def test_memory_system_performance_targets(self, isolated_memory_context):
        """Test that memory system meets performance targets."""
        import time

        mock_memory = isolated_memory_context

        # Test save performance target: < 50ms per small operation
        test_data = {"small": "data", "count": 1}

        start_time = time.time()
        memory_id = mock_memory.save_result(test_data, "performance", "perf test")
        save_time = time.time() - start_time

        assert save_time < 0.05, f"Save took {save_time*1000:.1f}ms, expected < 50ms"

        # Test load performance target: < 10ms per small operation
        start_time = time.time()
        loaded = mock_memory.load_result(memory_id)
        load_time = time.time() - start_time

        assert load_time < 0.01, f"Load took {load_time*1000:.1f}ms, expected < 10ms"
        assert loaded is not None

    def test_list_memory_tool_comprehensive(self, test_db, isolated_memory_context):
        """Test comprehensive list_memory tool functionality."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}

        api = PRTAPI(config)
        llm = OllamaLLM(api=api)
        mock_memory = isolated_memory_context

        # Save multiple different types of results
        llm._save_contacts_with_images("list test contacts")
        mock_memory.save_result([{"query": "test"}], "search", "search results")

        # Test listing all results
        all_results = llm._list_memory()
        assert all_results["success"] is True
        assert all_results["total_count"] >= 2

        # Test listing filtered by type
        contacts_results = llm._list_memory(result_type="contacts")
        assert contacts_results["success"] is True
        assert len(contacts_results["results"]) >= 1
        assert all(r["type"] == "contacts" for r in contacts_results["results"])

        # Test stats accuracy
        stats = all_results["stats"]
        assert stats["total_results"] >= 2
        assert "contacts" in stats["types"]
        assert "search" in stats["types"]

    def test_memory_cleanup_completeness(self, isolated_memory_context):
        """Test that memory cleanup is complete and doesn't leave artifacts."""
        mock_memory = isolated_memory_context

        # Create some memory entries
        memory_ids = []
        for i in range(5):
            memory_id = mock_memory.save_result(
                {"data": f"cleanup test {i}"}, "cleanup", f"cleanup {i}"
            )
            memory_ids.append(memory_id)

        # Verify entries exist
        stats_before = mock_memory.get_stats()
        assert stats_before["total_results"] == 5

        # Test cleanup
        mock_memory.cleanup()

        # Verify complete cleanup
        stats_after = mock_memory.get_stats()
        assert stats_after["total_results"] == 0

        # Verify individual entries are gone
        for memory_id in memory_ids:
            assert mock_memory.load_result(memory_id) is None

    def test_edge_case_data_types(self, isolated_memory_context):
        """Test memory system with edge case data types."""
        mock_memory = isolated_memory_context

        edge_cases = [
            # Empty data structures
            {"empty_list": [], "empty_dict": {}, "empty_string": ""},
            # Very large strings
            {"large_string": "x" * 10000},
            # Nested structures
            {"nested": {"deep": {"very": {"deep": "value"}}}},
            # Mixed types
            {"mixed": [1, "string", True, None, {"nested": "dict"}]},
            # Special characters
            {"unicode": "Special chars: áéíóú ñ çã 中文 🌟"},
        ]

        for i, data in enumerate(edge_cases):
            memory_id = mock_memory.save_result(data, "edge", f"edge case {i}")

            # Verify round-trip integrity
            loaded = mock_memory.load_result(memory_id)
            assert loaded is not None
            assert loaded["data"] == data
            assert loaded["type"] == "edge"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
