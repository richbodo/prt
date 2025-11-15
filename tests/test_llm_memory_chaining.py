"""Test the new memory-based LLM tool chaining functionality."""

import time
from pathlib import Path

import pytest

from prt_src.api import PRTAPI
from prt_src.llm_ollama import OllamaLLM


@pytest.mark.integration
def test_memory_system_basic_operations(isolated_memory_context):
    """Test basic memory system operations with isolated memory."""
    mock_memory = isolated_memory_context

    # Test save and load
    test_data = {"test": "data", "count": 5}
    memory_id = mock_memory.save_result(test_data, "test", "test data")

    assert memory_id is not None
    assert memory_id.startswith("test_")

    # Test load
    loaded = mock_memory.load_result(memory_id)
    assert loaded is not None
    assert loaded["data"] == test_data
    assert loaded["type"] == "test"
    assert loaded["test_name"] == "test_memory_system_basic_operations"

    # Test list
    results = mock_memory.list_results()
    assert len(results) >= 1
    assert any(r["id"] == memory_id for r in results)

    # Verify isolation - no persistent files outside test context
    stats = mock_memory.get_stats()
    assert stats["test_name"] == "test_memory_system_basic_operations"
    assert not stats["use_temp_files"]  # Using in-memory storage

    # Test cleanup (handled automatically by fixture)


@pytest.mark.integration
def test_save_contacts_with_images_tool(test_db, isolated_memory_context, llm_config):
    """Test the save_contacts_with_images tool with isolated memory."""
    db, fixtures = test_db
    config = {"db_path": str(db.path), "db_encrypted": False}
    mock_memory = isolated_memory_context

    # Initialize API and LLM with test config
    api = PRTAPI(config)
    llm = OllamaLLM(api=api, config_manager=llm_config)

    # Test saving contacts to memory
    result = llm._save_contacts_with_images("test contacts with images")

    assert result["success"] is True
    assert "memory_id" in result
    assert result["count"] > 0
    assert "usage" in result

    memory_id = result["memory_id"]

    # Verify the memory was actually saved (using the patched global memory)
    loaded = mock_memory.load_result(memory_id)
    assert loaded is not None
    assert len(loaded["data"]) == result["count"]

    # Verify test isolation
    assert loaded["test_name"] == "test_save_contacts_with_images_tool"

    # Test that all loaded contacts have images
    for contact in loaded["data"]:
        # Note: profile_image is removed during serialization, but we can check the flag
        assert contact.get("has_profile_image") is True or contact.get("profile_image") is not None

    print(f"✓ Saved {result['count']} contacts to isolated memory: {memory_id}")

    # Verify no global memory pollution
    stats = mock_memory.get_stats()
    assert stats["total_results"] >= 1


@pytest.mark.integration
def test_list_memory_tool(test_db, isolated_memory_context, llm_config):
    """Test the list_memory tool with isolated memory."""
    db, fixtures = test_db
    config = {"db_path": str(db.path), "db_encrypted": False}

    # Initialize API and LLM with test config
    api = PRTAPI(config)
    llm = OllamaLLM(api=api, config_manager=llm_config)

    # First save some data
    save_result = llm._save_contacts_with_images("test memory listing")
    assert save_result["success"] is True

    # Test listing memory
    list_result = llm._list_memory()

    assert list_result["success"] is True
    assert "results" in list_result
    assert list_result["total_count"] >= 1
    assert "stats" in list_result

    # Check that our saved result appears in the list
    memory_id = save_result["memory_id"]
    found = any(r["id"] == memory_id for r in list_result["results"])
    assert found, f"Memory ID {memory_id} not found in list"

    # Verify test isolation
    assert list_result["stats"]["test_name"] == "test_list_memory_tool"

    print(f"✓ Listed {list_result['total_count']} isolated memory results")


@pytest.mark.integration
def test_generate_directory_with_memory_id(test_db, isolated_memory_context, llm_config):
    """Test generating directory using memory ID with isolated memory."""
    db, fixtures = test_db
    config = {"db_path": str(db.path), "db_encrypted": False}
    mock_memory = isolated_memory_context

    # Initialize API and LLM with test config
    api = PRTAPI(config)
    llm = OllamaLLM(api=api, config_manager=llm_config)

    # Step 1: Save contacts to memory
    save_result = llm._save_contacts_with_images("contacts for directory test")
    assert save_result["success"] is True

    memory_id = save_result["memory_id"]
    contact_count = save_result["count"]

    # Verify memory was saved in isolated context
    loaded = mock_memory.load_result(memory_id)
    assert loaded is not None
    assert loaded["test_name"] == "test_generate_directory_with_memory_id"

    # Step 2: Generate directory using memory ID
    directory_result = llm._generate_directory(
        memory_id=memory_id, output_name="test_isolated_memory"
    )

    assert (
        directory_result["success"] is True
    ), f"Directory generation failed: {directory_result.get('error')}"
    assert "output_path" in directory_result
    assert "url" in directory_result
    assert "contact_count" in directory_result

    # Verify the directory was actually created
    output_path = Path(directory_result["output_path"])
    assert output_path.exists(), f"Directory not created at {output_path}"

    # Verify HTML file exists
    index_file = output_path / "index.html"
    assert index_file.exists(), "index.html not found in directory"

    print(f"✓ Created directory from isolated memory with {contact_count} contacts")
    print(f"  Memory ID: {memory_id}")
    print(f"  Output: {directory_result['output_path']}")

    # Cleanup test directory
    if output_path.exists():
        import shutil

        shutil.rmtree(output_path, ignore_errors=True)


@pytest.mark.integration
def test_generate_directory_error_handling(test_db, isolated_memory_context, llm_config):
    """Test directory generation error handling with invalid memory IDs."""
    db, fixtures = test_db
    config = {"db_path": str(db.path), "db_encrypted": False}

    # Initialize API and LLM with test config
    api = PRTAPI(config)
    llm = OllamaLLM(api=api, config_manager=llm_config)

    # Test with invalid memory ID
    directory_result = llm._generate_directory(
        memory_id="invalid_memory_id", output_name="error_test"
    )

    assert (
        directory_result["success"] is False
    ), "Expected directory generation to fail with invalid memory ID"
    assert "error" in directory_result or "message" in directory_result
    assert "not found" in directory_result.get("error", "") or "not found" in directory_result.get(
        "message", ""
    )

    # Test with no parameters
    directory_result2 = llm._generate_directory()

    assert (
        directory_result2["success"] is False
    ), "Expected directory generation to fail with no parameters"
    assert "error" in directory_result2 or "message" in directory_result2

    print("✓ Error handling test: Directory generation errors handled correctly")


@pytest.mark.integration
def test_memory_chaining_edge_cases(isolated_memory_context):
    """Test edge cases in memory chaining workflow."""
    mock_memory = isolated_memory_context

    # Test invalid memory ID handling
    fake_memory_id = "test_invalid_123456_abcdef12"
    loaded = mock_memory.load_result(fake_memory_id)
    assert loaded is None, "Should return None for invalid memory ID"

    # Test empty data handling
    empty_memory_id = mock_memory.save_result([], "empty", "empty dataset")
    loaded_empty = mock_memory.load_result(empty_memory_id)
    assert loaded_empty is not None
    assert loaded_empty["data"] == []
    assert loaded_empty["data_count"] == 0

    # Test memory ID format validation
    test_memory_id = mock_memory.save_result({"test": "data"}, "format", "format test")
    parts = test_memory_id.split("_")
    assert parts[0] == "test"  # test prefix for mock
    assert parts[1] == "format"  # result type
    assert len(parts[2]) == 6  # timestamp (HHMMSS)
    assert len(parts[3]) == 8  # UUID fragment
    assert parts[2].isdigit()  # timestamp is numeric

    print("✓ Edge cases test: All edge cases handled correctly")


@pytest.mark.integration
def test_memory_chaining_workflow_complete(test_db, isolated_memory_context, llm_config):
    """Test the complete chaining workflow: save -> list -> generate with isolated memory."""
    db, fixtures = test_db
    config = {"db_path": str(db.path), "db_encrypted": False}
    mock_memory = isolated_memory_context

    # Initialize API and LLM with test config
    api = PRTAPI(config)
    llm = OllamaLLM(api=api, config_manager=llm_config)

    start_time = time.time()

    # Step 1: Save contacts with images
    print("Step 1: Saving contacts with images to isolated memory...")
    save_result = llm._save_contacts_with_images("isolated workflow test contacts")

    assert save_result["success"] is True
    memory_id = save_result["memory_id"]
    save_time = time.time() - start_time

    # Verify isolation
    loaded = mock_memory.load_result(memory_id)
    assert loaded["test_name"] == "test_memory_chaining_workflow_complete"

    # Step 2: List memory to verify
    print("Step 2: Listing isolated memory...")
    list_result = llm._list_memory(result_type="contacts")

    assert list_result["success"] is True
    assert any(r["id"] == memory_id for r in list_result["results"])
    assert list_result["stats"]["test_name"] == "test_memory_chaining_workflow_complete"
    list_time = time.time() - start_time

    # Step 3: Generate directory from memory
    print("Step 3: Generating directory from isolated memory...")
    directory_result = llm._generate_directory(
        memory_id=memory_id, output_name="test_workflow_complete"
    )

    assert directory_result["success"] is True
    total_time = time.time() - start_time

    # Verify directory was created
    output_path = Path(directory_result["output_path"])
    assert output_path.exists(), "Directory should have been created"

    # Performance verification
    print("✓ Complete isolated workflow performance:")
    print(f"  Save step: {save_time:.2f}s")
    print(f"  List step: {(list_time - save_time):.2f}s")
    print(f"  Directory step: {(total_time - list_time):.2f}s")
    print(f"  Total time: {total_time:.2f}s")

    # Reasonable performance target
    assert total_time < 30.0, f"Isolated workflow took {total_time:.1f}s, expected < 30s"

    # Verify clean isolation - only our test results
    stats = mock_memory.get_stats()
    assert stats["total_results"] >= 1

    # Verify data integrity through the entire workflow
    saved_data = loaded["data"]
    assert isinstance(saved_data, list), "Saved data should be a list"
    assert len(saved_data) > 0, "Should have saved some contacts"

    # Validate contact data structure
    for contact in saved_data:
        assert "id" in contact, "Contact should have ID"
        assert "name" in contact, "Contact should have name"
        if "has_profile_image" in contact:
            assert isinstance(
                contact["has_profile_image"], bool
            ), "has_profile_image should be boolean"

    print("✓ Complete workflow: All steps passed with proper isolation")

    # Cleanup test directory
    if output_path.exists():
        import shutil

        shutil.rmtree(output_path, ignore_errors=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
