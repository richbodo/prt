"""
Integration tests for the LLM Memory System.

These tests verify memory system integration with real file operations,
JSON serialization, and system cleanup while maintaining test isolation.
"""

import json
import shutil
import tempfile
import time
from pathlib import Path

import pytest

from tests.mocks.mock_llm_memory import MockLLMMemory


@pytest.mark.integration
class TestLLMMemoryIntegration:
    """Integration tests for memory system with real file operations."""

    @pytest.fixture
    def temp_memory_dir(self):
        """Create a temporary directory for memory system testing."""
        temp_dir = Path(tempfile.mkdtemp(prefix="prt_memory_integration_"))
        yield temp_dir
        # Cleanup
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

    @pytest.fixture
    def file_based_memory(self, temp_memory_dir):
        """Memory system using real file storage."""
        memory = MockLLMMemory("integration_test", use_temp_files=True)
        memory.base_dir = temp_memory_dir
        return memory

    def test_memory_file_persistence(self, file_based_memory):
        """Test memory persistence to actual files."""
        test_data = {"contacts": [{"name": "Test User", "id": 1}]}
        memory_id = file_based_memory.save_result(test_data, "contacts", "integration test")

        # Verify file was created
        expected_file = file_based_memory.base_dir / f"{memory_id}.json"
        assert expected_file.exists()

        # Verify file contents
        with open(expected_file) as f:
            file_data = json.load(f)

        assert file_data["id"] == memory_id
        assert file_data["type"] == "contacts"
        assert file_data["data"] == test_data

        # Test loading from file
        loaded = file_based_memory.load_result(memory_id)
        assert loaded is not None
        assert loaded["data"] == test_data

    def test_large_dataset_serialization(self, file_based_memory):
        """Test memory system with large contact datasets."""
        # Generate large dataset
        large_dataset = []
        for i in range(100):
            contact = {
                "id": i,
                "name": f"Contact {i}",
                "email": f"contact{i}@example.com",
                "phone": f"+1-555-{i:04d}",
                "profile_image": b"x" * 1024,  # 1KB fake image data per contact
                "has_profile_image": True,
                "tags": [f"tag{j}" for j in range(5)],  # Multiple tags per contact
                "notes": f"This is a longer note for contact {i} " * 10,  # Longer text
            }
            large_dataset.append(contact)

        start_time = time.time()
        memory_id = file_based_memory.save_result(large_dataset, "contacts", "large dataset test")
        save_time = time.time() - start_time

        # Verify performance (should handle 100 contacts with 1KB images in reasonable time)
        assert save_time < 5.0, f"Large save took {save_time:.1f}s, expected < 5s"

        # Test loading performance
        start_time = time.time()
        loaded = file_based_memory.load_result(memory_id)
        load_time = time.time() - start_time

        assert load_time < 2.0, f"Large load took {load_time:.1f}s, expected < 2s"
        assert len(loaded["data"]) == 100
        assert loaded["data"][0]["name"] == "Contact 0"
        assert loaded["data"][99]["name"] == "Contact 99"

    def test_memory_file_cleanup(self, file_based_memory):
        """Test automatic cleanup of memory files."""
        # Create multiple memory entries
        memory_ids = []
        for i in range(5):
            memory_id = file_based_memory.save_result(
                {"data": f"test {i}"}, "test", f"cleanup test {i}"
            )
            memory_ids.append(memory_id)

        # Verify all files exist
        for memory_id in memory_ids:
            file_path = file_based_memory.base_dir / f"{memory_id}.json"
            assert file_path.exists()

        # Cleanup
        file_based_memory.cleanup()

        # Verify all files are gone
        for memory_id in memory_ids:
            file_path = file_based_memory.base_dir / f"{memory_id}.json"
            assert not file_path.exists()

    def test_corrupted_file_handling(self, file_based_memory):
        """Test handling of corrupted memory files."""
        # Create a valid memory entry
        memory_id = file_based_memory.save_result({"data": "valid"}, "test", "corruption test")

        # Corrupt the file
        file_path = file_based_memory.base_dir / f"{memory_id}.json"
        with open(file_path, "w") as f:
            f.write("invalid json content{")

        # Loading should return None without crashing
        result = file_based_memory.load_result(memory_id)
        assert result is None

        # Listing should skip corrupted files
        results = file_based_memory.list_results()
        assert not any(r["id"] == memory_id for r in results)

    def test_memory_directory_permissions(self, file_based_memory):
        """Test memory system handles directory permission issues gracefully."""
        # Create read-only directory after memory creation
        file_based_memory.base_dir.chmod(0o444)

        try:
            # Attempt to save should fail gracefully
            with pytest.raises(PermissionError):
                file_based_memory.save_result({"data": "test"}, "test", "permission test")
        finally:
            # Restore write permissions for cleanup
            file_based_memory.base_dir.chmod(0o755)

    def test_concurrent_file_access(self, file_based_memory):
        """Test concurrent file access safety."""
        import threading

        results = []
        errors = []

        def save_worker(worker_id):
            try:
                for i in range(3):
                    memory_id = file_based_memory.save_result(
                        {"worker": worker_id, "iteration": i},
                        "concurrent",
                        f"Worker {worker_id} iteration {i}",
                    )
                    results.append(memory_id)
            except Exception as e:
                errors.append(e)

        # Run concurrent workers
        threads = []
        for worker_id in range(3):
            thread = threading.Thread(target=save_worker, args=(worker_id,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify all operations succeeded
        assert len(errors) == 0, f"Concurrent errors: {errors}"
        assert len(results) == 9  # 3 workers * 3 iterations

        # Verify all files exist and are unique
        unique_ids = set(results)
        assert len(unique_ids) == 9

        for memory_id in results:
            file_path = file_based_memory.base_dir / f"{memory_id}.json"
            assert file_path.exists()

    def test_memory_json_serialization_edge_cases(self, file_based_memory):
        """Test JSON serialization of various data types."""
        edge_cases = [
            # Unicode and special characters
            {"data": {"name": "José García", "note": "Special chars: áéíóú ñ 中文"}},
            # Large integers and floats
            {"data": {"big_int": 2**63 - 1, "float": 3.141592653589793}},
            # Empty structures
            {"data": {"empty_list": [], "empty_dict": {}, "null_value": None}},
            # Nested structures
            {"data": {"nested": {"level1": {"level2": {"level3": "deep"}}}}},
            # Binary data (should be handled by default=str)
            {"data": {"binary": b"binary data", "has_binary": True}},
        ]

        for i, test_case in enumerate(edge_cases):
            memory_id = file_based_memory.save_result(
                test_case["data"], "edge_case", f"edge case {i}"
            )

            # Verify round-trip serialization
            loaded = file_based_memory.load_result(memory_id)
            assert loaded is not None
            assert loaded["type"] == "edge_case"

            # Note: Binary data will be converted to string representation
            # but structure should be preserved

    def test_memory_automatic_cleanup_age(self):
        """Test automatic cleanup based on file age."""
        # Create memory with very short max age
        memory = MockLLMMemory("cleanup_test", use_temp_files=True)
        from datetime import timedelta

        memory.max_age = timedelta(seconds=1)

        # Save a result
        memory_id = memory.save_result({"data": "old"}, "test", "age test")

        # Initially should be present
        assert memory.load_result(memory_id) is not None

        # Wait for expiration
        time.sleep(1.1)

        # Trigger cleanup by creating new memory instance
        new_memory = MockLLMMemory("cleanup_test", use_temp_files=True)
        new_memory.base_dir = memory.base_dir
        new_memory.max_age = timedelta(seconds=1)

        # Old result should be cleaned up
        cleaned_count = new_memory._cleanup_old_results()
        assert cleaned_count >= 1

        # Old result should no longer be loadable
        assert new_memory.load_result(memory_id) is None

        # Cleanup both memory instances
        memory.cleanup()
        new_memory.cleanup()

    def test_memory_stats_accuracy_with_files(self, file_based_memory):
        """Test memory statistics accuracy with file operations."""
        # Save various types of results
        contacts_id = file_based_memory.save_result(
            [{"name": "Contact"}], "contacts", "test contacts"
        )
        file_based_memory.save_result([{"query": "search"}], "search", "search results")
        file_based_memory.save_result([{"note": "test"}], "notes", "test notes")

        stats = file_based_memory.get_stats()

        assert stats["total_results"] == 3
        assert stats["types"]["contacts"] == 1
        assert stats["types"]["search"] == 1
        assert stats["types"]["notes"] == 1
        assert stats["use_temp_files"] is True

        # Delete one result and verify stats update
        assert file_based_memory.delete_result(contacts_id) is True

        updated_stats = file_based_memory.get_stats()
        assert updated_stats["total_results"] == 2
        assert "contacts" not in updated_stats["types"] or updated_stats["types"]["contacts"] == 0

    def test_memory_system_recovery_from_corruption(self, file_based_memory):
        """Test memory system recovery from various corruption scenarios."""
        # Create some valid entries
        valid_id1 = file_based_memory.save_result({"data": "valid1"}, "test", "valid 1")
        valid_id2 = file_based_memory.save_result({"data": "valid2"}, "test", "valid 2")

        # Create corrupted files
        corrupted_file = file_based_memory.base_dir / "corrupted.json"
        with open(corrupted_file, "w") as f:
            f.write("not json at all")

        empty_file = file_based_memory.base_dir / "empty.json"
        empty_file.touch()

        # System should still function
        results = file_based_memory.list_results()
        valid_results = [r for r in results if r["id"] in [valid_id1, valid_id2]]
        assert len(valid_results) == 2

        # Should still be able to load valid results
        assert file_based_memory.load_result(valid_id1) is not None
        assert file_based_memory.load_result(valid_id2) is not None

        # Should be able to save new results
        new_id = file_based_memory.save_result({"data": "new"}, "test", "new after corruption")
        assert file_based_memory.load_result(new_id) is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
