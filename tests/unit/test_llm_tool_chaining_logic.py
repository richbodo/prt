"""
Focused unit tests for LLM tool chaining logic.

These tests isolate the tool chaining functionality from the full system,
using mocks for dependencies to ensure fast, reliable, and focused testing.
"""

from unittest.mock import Mock
from unittest.mock import patch

import pytest

from prt_src.llm_ollama import OllamaLLM
from tests.mocks.mock_llm_memory import MockLLMMemory


@pytest.mark.unit
class TestLLMToolChainingLogic:
    """Unit tests for LLM tool chaining without full system dependencies."""

    @pytest.fixture
    def mock_api(self):
        """Mock PRTAPI for unit testing."""
        mock_api = Mock()
        mock_api.get_contacts_with_images.return_value = [
            {
                "id": 1,
                "name": "John Doe",
                "email": "john@example.com",
                "profile_image": b"fake_image_data",
                "has_profile_image": True,
            },
            {
                "id": 2,
                "name": "Jane Smith",
                "email": "jane@example.com",
                "profile_image": b"more_fake_image_data",
                "has_profile_image": True,
            },
        ]
        return mock_api

    @pytest.fixture
    def mock_memory(self):
        """Mock memory system for unit testing."""
        return MockLLMMemory("test_tool_chaining", use_temp_files=False)

    @pytest.fixture
    def llm_with_mocks(self, mock_api, mock_memory):
        """LLM instance with mocked dependencies."""
        # Patch both llm_memory module and ollama module references
        with patch.multiple("prt_src.llm_ollama", llm_memory=mock_memory):
            llm = OllamaLLM(api=mock_api)
            yield llm

    def test_save_contacts_tool_parameter_handling(self, llm_with_mocks, mock_api):
        """Test save_contacts_with_images tool parameter handling."""
        # Test with valid query
        result = llm_with_mocks._save_contacts_with_images("test contacts")

        assert result["success"] is True
        assert "memory_id" in result
        assert result["count"] == 2
        assert "usage" in result

        # Verify the API was called correctly
        mock_api.get_contacts_with_images.assert_called_once()

    def test_save_contacts_tool_empty_results(self, llm_with_mocks, mock_api):
        """Test save_contacts_with_images with no results."""
        mock_api.get_contacts_with_images.return_value = []

        result = llm_with_mocks._save_contacts_with_images("no results query")

        assert result["success"] is False
        assert result["count"] == 0
        assert "No contacts" in result["error"]

    def test_save_contacts_tool_error_handling(self, llm_with_mocks, mock_api):
        """Test save_contacts_with_images error handling."""
        mock_api.get_contacts_with_images.side_effect = Exception("Database error")

        result = llm_with_mocks._save_contacts_with_images("error query")

        assert result["success"] is False
        assert "error" in result
        assert "Database error" in result["error"]

    def test_list_memory_tool_basic(self, llm_with_mocks, mock_memory):
        """Test list_memory tool basic functionality."""
        # Pre-populate memory
        mock_memory.save_result([{"name": "Test Contact"}], "contacts", "test description")

        result = llm_with_mocks._list_memory()

        assert result["success"] is True
        assert "results" in result
        assert result["total_count"] >= 1
        assert "stats" in result
        assert result["stats"]["total_results"] >= 1

    def test_list_memory_tool_filtered(self, llm_with_mocks, mock_memory):
        """Test list_memory tool with type filtering."""
        # Add different types
        mock_memory.save_result([{"data": "contacts"}], "contacts", "contacts")
        mock_memory.save_result([{"data": "search"}], "search", "search results")

        # Test filtering by type
        result = llm_with_mocks._list_memory(result_type="contacts")

        assert result["success"] is True
        contacts_results = [r for r in result["results"] if r["type"] == "contacts"]
        assert len(contacts_results) >= 1

    def test_list_memory_tool_empty(self, llm_with_mocks, mock_memory):
        """Test list_memory tool with empty memory."""
        result = llm_with_mocks._list_memory()

        assert result["success"] is True
        assert result["total_count"] == 0
        assert len(result["results"]) == 0

    def test_memory_id_generation_uniqueness(self, llm_with_mocks, mock_api):
        """Test that memory IDs are unique across multiple saves."""
        memory_ids = []

        for i in range(5):
            result = llm_with_mocks._save_contacts_with_images(f"query {i}")
            assert result["success"] is True
            memory_ids.append(result["memory_id"])

        # All IDs should be unique
        assert len(set(memory_ids)) == len(memory_ids)

        # All IDs should follow expected format
        for memory_id in memory_ids:
            assert memory_id.startswith("test_contacts_")
            assert len(memory_id.split("_")) >= 3

    def test_memory_data_integrity(self, llm_with_mocks, mock_api, mock_memory):
        """Test data integrity through save/load cycle."""
        # Save contacts
        result = llm_with_mocks._save_contacts_with_images("integrity test")
        memory_id = result["memory_id"]

        # Load and verify
        loaded = mock_memory.load_result(memory_id)
        assert loaded is not None
        assert loaded["type"] == "contacts"
        assert loaded["data_count"] == 2
        assert len(loaded["data"]) == 2

        # Verify contact data structure
        for contact in loaded["data"]:
            assert "id" in contact
            assert "name" in contact
            assert "email" in contact
            assert "has_profile_image" in contact

    def test_contact_image_handling(self, llm_with_mocks, mock_api, mock_memory):
        """Test proper handling of contact profile images."""
        # Modify mock to have contacts with and without images
        mock_api.get_contacts_with_images.return_value = [
            {
                "id": 1,
                "name": "With Image",
                "profile_image": b"image_data",
                "has_profile_image": True,
            },
            {
                "id": 2,
                "name": "Without Image",
                "profile_image": None,
                "has_profile_image": False,
            },
        ]

        result = llm_with_mocks._save_contacts_with_images("image test")
        memory_id = result["memory_id"]

        loaded = mock_memory.load_result(memory_id)
        contacts = loaded["data"]

        # Check image handling
        with_image = next(c for c in contacts if c["name"] == "With Image")
        without_image = next(c for c in contacts if c["name"] == "Without Image")

        assert with_image["has_profile_image"] is True
        assert without_image["has_profile_image"] is False

    @patch("prt_src.llm_ollama.OllamaLLM._generate_directory")
    def test_tool_chaining_workflow(self, mock_generate, llm_with_mocks, mock_api):
        """Test complete tool chaining workflow."""
        # Mock directory generation
        mock_generate.return_value = {
            "success": True,
            "output_path": "/tmp/test_directory",
            "url": "file:///tmp/test_directory/index.html",
        }

        # Step 1: Save contacts
        save_result = llm_with_mocks._save_contacts_with_images("workflow test")
        assert save_result["success"] is True
        memory_id = save_result["memory_id"]

        # Step 2: List memory (verify it appears)
        list_result = llm_with_mocks._list_memory()
        assert list_result["success"] is True
        assert any(r["id"] == memory_id for r in list_result["results"])

        # Step 3: Generate directory (mocked)
        directory_result = llm_with_mocks._generate_directory(
            memory_id=memory_id, output_name="test_workflow"
        )
        assert directory_result["success"] is True

        # Verify directory generation was called with correct memory_id
        mock_generate.assert_called_once()
        call_args = mock_generate.call_args
        assert call_args[1]["memory_id"] == memory_id

    def test_error_propagation_in_tool_chain(self, llm_with_mocks, mock_api, mock_memory):
        """Test error propagation through tool chains."""
        # Cause memory save to fail by making data unserializable
        mock_api.get_contacts_with_images.return_value = [
            {"id": 1, "name": "Test", "circular": None}
        ]

        # Create circular reference to break JSON serialization
        contact = mock_api.get_contacts_with_images.return_value[0]
        contact["circular"] = contact

        # Mock memory to simulate JSON error
        with patch.object(mock_memory, "save_result") as mock_save:
            mock_save.side_effect = TypeError("Object is not JSON serializable")

            result = llm_with_mocks._save_contacts_with_images("error test")

            assert result["success"] is False
            assert "error" in result

    def test_memory_statistics_accuracy(self, llm_with_mocks, mock_api, mock_memory):
        """Test accuracy of memory statistics."""
        # Save multiple results of different types
        llm_with_mocks._save_contacts_with_images("contacts 1")
        llm_with_mocks._save_contacts_with_images("contacts 2")

        # Add non-contacts result manually
        mock_memory.save_result({"data": "search"}, "search", "search result")

        result = llm_with_mocks._list_memory()
        stats = result["stats"]

        assert stats["total_results"] >= 3
        assert "contacts" in stats["types"]
        assert "search" in stats["types"]
        assert stats["types"]["contacts"] >= 2
        assert stats["types"]["search"] >= 1

    def test_memory_cleanup_isolation(self, mock_memory):
        """Test memory cleanup doesn't affect other tests."""
        # Add some data
        memory_id = mock_memory.save_result({"test": "data"}, "test", "cleanup test")
        assert mock_memory.load_result(memory_id) is not None

        # Cleanup should remove data
        mock_memory.cleanup()

        # Data should be gone
        stats = mock_memory.get_stats()
        assert stats["total_results"] == 0

    def test_performance_memory_operations(self, llm_with_mocks, mock_api, mock_memory):
        """Test performance of memory operations meets targets."""
        import time

        # Test save performance
        start_time = time.time()
        result = llm_with_mocks._save_contacts_with_images("performance test")
        save_time = time.time() - start_time

        assert result["success"] is True
        assert save_time < 1.0, f"Save took {save_time:.3f}s, expected < 1s"

        # Test load performance
        memory_id = result["memory_id"]
        start_time = time.time()
        loaded = mock_memory.load_result(memory_id)
        load_time = time.time() - start_time

        assert loaded is not None
        assert load_time < 0.1, f"Load took {load_time:.3f}s, expected < 0.1s"

        # Test list performance
        start_time = time.time()
        list_result = llm_with_mocks._list_memory()
        list_time = time.time() - start_time

        assert list_result["success"] is True
        assert list_time < 0.1, f"List took {list_time:.3f}s, expected < 0.1s"

    def test_concurrent_memory_access_safety(self, mock_memory):
        """Test memory system handles concurrent access safely."""
        import threading
        import time

        results = []
        errors = []

        def save_worker(worker_id):
            try:
                for i in range(5):
                    memory_id = mock_memory.save_result(
                        {"worker": worker_id, "iteration": i},
                        "concurrent",
                        f"Worker {worker_id} iteration {i}",
                    )
                    results.append(memory_id)
                    time.sleep(0.01)  # Small delay to encourage race conditions
            except Exception as e:
                errors.append(e)

        # Run multiple workers concurrently
        threads = []
        for worker_id in range(3):
            thread = threading.Thread(target=save_worker, args=(worker_id,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Verify no errors and all saves succeeded
        assert len(errors) == 0, f"Concurrent access errors: {errors}"
        assert len(results) == 15  # 3 workers * 5 iterations
        assert len(set(results)) == 15  # All IDs should be unique


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
