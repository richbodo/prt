"""
Integration tests for Ollama-specific memory chaining behavior.

Tests Ollama interface reliability with memory operations, including
timeout handling, network error recovery, and response validation.
"""

import time
from pathlib import Path

import pytest

from prt_src.api import PRTAPI
from prt_src.llm_ollama import OllamaLLM


@pytest.mark.integration
def test_ollama_timeout_handling_with_memory(test_db, isolated_memory_context):
    """Test that memory operations work correctly with Ollama timeout settings."""
    db, fixtures = test_db
    config = {"db_path": str(db.path), "db_encrypted": False}
    mock_memory = isolated_memory_context

    # Initialize API and LLM
    api = PRTAPI(config)
    llm = OllamaLLM(api=api)

    # Test saving contacts works within timeout constraints
    start_time = time.time()
    result = llm._save_contacts_with_images("timeout test contacts")
    save_time = time.time() - start_time

    assert result["success"] is True
    assert "memory_id" in result
    memory_id = result["memory_id"]

    # Verify the operation completed in reasonable time
    assert save_time < 30.0, f"Save operation took {save_time:.1f}s, too slow"

    # Test that memory can be loaded quickly
    start_time = time.time()
    loaded = mock_memory.load_result(memory_id)
    load_time = time.time() - start_time

    assert loaded is not None
    assert load_time < 5.0, f"Load operation took {load_time:.1f}s, too slow"

    # Verify isolation
    assert loaded["test_name"] == "test_ollama_timeout_handling_with_memory"


@pytest.mark.integration
def test_ollama_memory_response_size_limits(test_db, isolated_memory_context):
    """Test memory operations with various data sizes that could affect Ollama responses."""
    db, fixtures = test_db
    config = {"db_path": str(db.path), "db_encrypted": False}

    # Initialize API and LLM
    api = PRTAPI(config)
    llm = OllamaLLM(api=api)

    # Test with normal-sized contact set
    normal_result = llm._save_contacts_with_images("normal size test")
    assert normal_result["success"] is True
    normal_memory_id = normal_result["memory_id"]

    # Test listing memory (should be fast regardless of individual result sizes)
    list_result = llm._list_memory()
    assert list_result["success"] is True
    assert list_result["total_count"] >= 1

    # Verify the listing includes our normal result
    found = any(r["id"] == normal_memory_id for r in list_result["results"])
    assert found, f"Normal memory result {normal_memory_id} not found in list"

    # Verify all results have reasonable metadata sizes
    for result in list_result["results"]:
        assert "id" in result
        assert "type" in result
        assert "data_count" in result
        # Metadata should be small and manageable
        assert len(str(result)) < 1000, "Result metadata too large"

    # Verify isolation
    assert list_result["stats"]["test_name"] == "test_ollama_memory_response_size_limits"


@pytest.mark.integration
def test_ollama_memory_tool_chaining_parameters(test_db, isolated_memory_context):
    """Test that tool parameters and return values match expected schemas in memory operations."""
    db, fixtures = test_db
    config = {"db_path": str(db.path), "db_encrypted": False}
    mock_memory = isolated_memory_context

    # Initialize API and LLM
    api = PRTAPI(config)
    llm = OllamaLLM(api=api)

    # Test save_contacts_with_images tool schema
    save_result = llm._save_contacts_with_images("schema validation test")

    # Verify save result schema
    assert isinstance(save_result, dict), "Save result must be dict"
    required_save_fields = ["success", "memory_id", "count", "usage"]
    for field in required_save_fields:
        assert field in save_result, f"Missing required field: {field}"

    assert isinstance(save_result["success"], bool)
    assert isinstance(save_result["memory_id"], str)
    assert isinstance(save_result["count"], int)
    assert isinstance(save_result["usage"], str)
    assert save_result["count"] > 0, "Should have saved some contacts"

    memory_id = save_result["memory_id"]

    # Test list_memory tool schema
    list_result = llm._list_memory()

    # Verify list result schema
    assert isinstance(list_result, dict), "List result must be dict"
    required_list_fields = ["success", "results", "total_count", "stats"]
    for field in required_list_fields:
        assert field in list_result, f"Missing required field: {field}"

    assert isinstance(list_result["success"], bool)
    assert isinstance(list_result["results"], list)
    assert isinstance(list_result["total_count"], int)
    assert isinstance(list_result["stats"], dict)

    # Verify individual result schema in list
    for result in list_result["results"]:
        result_fields = ["id", "type", "description", "created_at", "data_count"]
        for field in result_fields:
            assert field in result, f"Missing result field: {field}"

    # Test generate_directory tool schema
    directory_result = llm._generate_directory(memory_id=memory_id, output_name="schema_test")

    # Verify directory result schema
    assert isinstance(directory_result, dict), "Directory result must be dict"
    required_dir_fields = ["success"]
    for field in required_dir_fields:
        assert field in directory_result, f"Missing required field: {field}"

    if directory_result["success"]:
        success_fields = ["output_path", "url", "contact_count"]
        for field in success_fields:
            assert field in directory_result, f"Missing success field: {field}"
        assert isinstance(directory_result["contact_count"], int)
    else:
        # If failed, should have error information
        assert "error" in directory_result or "message" in directory_result

    # Verify isolation
    loaded = mock_memory.load_result(memory_id)
    assert loaded["test_name"] == "test_ollama_memory_tool_chaining_parameters"

    # Cleanup if directory was created
    if directory_result["success"]:
        output_path = Path(directory_result["output_path"])
        if output_path.exists():
            import shutil

            shutil.rmtree(output_path, ignore_errors=True)


@pytest.mark.integration
def test_ollama_memory_error_propagation_and_recovery(test_db, isolated_memory_context):
    """Test error propagation and recovery mechanisms in memory chaining operations."""
    db, fixtures = test_db
    config = {"db_path": str(db.path), "db_encrypted": False}

    # Initialize API and LLM
    api = PRTAPI(config)
    llm = OllamaLLM(api=api)

    # Test 1: Generate directory with invalid memory ID
    invalid_result = llm._generate_directory(memory_id="invalid_id_12345", output_name="error_test")

    assert isinstance(invalid_result, dict), "Error result should be dict"
    assert invalid_result["success"] is False, "Should fail with invalid memory ID"
    assert "error" in invalid_result or "message" in invalid_result, "Should have error message"

    # Test 2: Generate directory with no parameters (should fail gracefully)
    no_params_result = llm._generate_directory()

    assert isinstance(no_params_result, dict), "No-params result should be dict"
    assert no_params_result["success"] is False, "Should fail with no parameters"
    assert "error" in no_params_result or "message" in no_params_result

    # Test 3: Successful operation after errors (recovery)
    save_result = llm._save_contacts_with_images("recovery test contacts")
    assert save_result["success"] is True, "Should succeed after previous errors"

    memory_id = save_result["memory_id"]
    list_result = llm._list_memory()
    assert list_result["success"] is True, "List should work after errors"

    # Verify the successful save appears in the list
    found = any(r["id"] == memory_id for r in list_result["results"])
    assert found, "Successful save should appear in list after error recovery"


@pytest.mark.integration
def test_ollama_memory_content_validation(test_db, isolated_memory_context):
    """Test that memory operations properly validate content types and data integrity."""
    db, fixtures = test_db
    config = {"db_path": str(db.path), "db_encrypted": False}
    mock_memory = isolated_memory_context

    # Initialize API and LLM
    api = PRTAPI(config)
    llm = OllamaLLM(api=api)

    # Test saving contacts with validation
    save_result = llm._save_contacts_with_images("content validation test")
    assert save_result["success"] is True
    memory_id = save_result["memory_id"]

    # Verify saved data has proper structure
    loaded = mock_memory.load_result(memory_id)
    assert loaded is not None
    assert isinstance(loaded["data"], list), "Saved contacts should be a list"
    assert len(loaded["data"]) > 0, "Should have saved some contacts"

    # Validate contact data structure
    for contact in loaded["data"]:
        assert isinstance(contact, dict), "Each contact should be a dict"
        assert "id" in contact, "Contact should have ID"
        assert "name" in contact, "Contact should have name"

        # Profile image should be handled correctly
        if "profile_image" in contact:
            # In memory, profile images might be base64 encoded or references
            assert contact["profile_image"] is not None

        # Check for profile image flag
        if "has_profile_image" in contact:
            assert isinstance(contact["has_profile_image"], bool)

    # Test that list operation returns valid content types
    list_result = llm._list_memory(result_type="contacts")
    assert list_result["success"] is True

    # All results should be of requested type
    for result in list_result["results"]:
        assert result["type"] == "contacts", f"Wrong type: {result['type']}"

    # Verify stats are properly formatted
    stats = list_result["stats"]
    assert isinstance(stats, dict)
    assert "total_results" in stats
    assert isinstance(stats["total_results"], int)

    # Verify isolation
    assert loaded["test_name"] == "test_ollama_memory_content_validation"


@pytest.mark.integration
def test_ollama_memory_performance_with_realistic_data(test_db, isolated_memory_context):
    """Test memory system performance with realistic data volumes for Ollama operations."""
    db, fixtures = test_db
    config = {"db_path": str(db.path), "db_encrypted": False}
    mock_memory = isolated_memory_context

    # Initialize API and LLM
    api = PRTAPI(config)
    llm = OllamaLLM(api=api)

    # Test performance targets for realistic operations
    operations_data = []

    # Test 1: Save operation performance
    start_time = time.time()
    save_result = llm._save_contacts_with_images("performance test contacts")
    save_time = time.time() - start_time

    assert save_result["success"] is True
    memory_id = save_result["memory_id"]
    operations_data.append(("save", save_time, save_result["count"]))

    # Test 2: List operation performance
    start_time = time.time()
    list_result = llm._list_memory()
    list_time = time.time() - start_time

    assert list_result["success"] is True
    operations_data.append(("list", list_time, list_result["total_count"]))

    # Test 3: Directory generation performance (with mock)
    start_time = time.time()
    directory_result = llm._generate_directory(memory_id=memory_id, output_name="perf_test")
    directory_time = time.time() - start_time

    operations_data.append(("directory", directory_time, save_result["count"]))

    # Performance assertions based on Ollama constraints
    # These should be reasonable for Ollama tool calling
    assert save_time < 10.0, f"Save operation took {save_time:.1f}s, too slow for Ollama"
    assert list_time < 2.0, f"List operation took {list_time:.1f}s, too slow for Ollama"
    assert directory_time < 15.0, f"Directory generation took {directory_time:.1f}s, too slow"

    # Total workflow time should be reasonable
    total_time = save_time + list_time + directory_time
    assert total_time < 25.0, f"Total workflow took {total_time:.1f}s, too slow for Ollama"

    # Print performance summary for debugging
    print("\nOllama Memory Performance Results:")
    for operation, duration, item_count in operations_data:
        print(f"  {operation}: {duration:.2f}s ({item_count} items)")
    print(f"  Total workflow: {total_time:.2f}s")

    # Verify isolation and cleanup
    loaded = mock_memory.load_result(memory_id)
    assert loaded["test_name"] == "test_ollama_memory_performance_with_realistic_data"

    # Cleanup directory if created
    if directory_result.get("success") and "output_path" in directory_result:
        output_path = Path(directory_result["output_path"])
        if output_path.exists():
            import shutil

            shutil.rmtree(output_path, ignore_errors=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
