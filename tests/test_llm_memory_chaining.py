"""Test the new memory-based LLM tool chaining functionality."""

import time
from pathlib import Path

import pytest

from prt_src.api import PRTAPI
from prt_src.llm_memory import llm_memory
from prt_src.llm_ollama import OllamaLLM


@pytest.mark.integration
def test_memory_system_basic_operations():
    """Test basic memory system operations."""
    # Test save and load
    test_data = {"test": "data", "count": 5}
    memory_id = llm_memory.save_result(test_data, "test", "test data")

    assert memory_id is not None
    assert memory_id.startswith("test_")

    # Test load
    loaded = llm_memory.load_result(memory_id)
    assert loaded is not None
    assert loaded["data"] == test_data
    assert loaded["type"] == "test"

    # Test list
    results = llm_memory.list_results()
    assert len(results) >= 1
    assert any(r["id"] == memory_id for r in results)

    # Cleanup
    llm_memory.delete_result(memory_id)


@pytest.mark.integration
def test_save_contacts_with_images_tool(test_db):
    """Test the save_contacts_with_images tool."""
    db, fixtures = test_db
    config = {"db_path": str(db.path), "db_encrypted": False}

    # Initialize API and LLM
    api = PRTAPI(config)
    llm = OllamaLLM(api=api)

    # Test saving contacts to memory
    result = llm._save_contacts_with_images("test contacts with images")

    assert result["success"] is True
    assert "memory_id" in result
    assert result["count"] > 0
    assert "usage" in result

    memory_id = result["memory_id"]

    # Verify the memory was actually saved
    loaded = llm_memory.load_result(memory_id)
    assert loaded is not None
    assert len(loaded["data"]) == result["count"]

    # Test that all loaded contacts have images
    for contact in loaded["data"]:
        # Note: profile_image is removed during serialization, but we can check the flag
        assert contact.get("has_profile_image") is True or contact.get("profile_image") is not None

    print(f"✓ Saved {result['count']} contacts to memory: {memory_id}")


@pytest.mark.integration
def test_list_memory_tool(test_db):
    """Test the list_memory tool."""
    db, fixtures = test_db
    config = {"db_path": str(db.path), "db_encrypted": False}

    # Initialize API and LLM
    api = PRTAPI(config)
    llm = OllamaLLM(api=api)

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

    print(f"✓ Listed {list_result['total_count']} memory results")


@pytest.mark.integration
def test_generate_directory_with_memory_id(test_db):
    """Test generating directory using memory ID instead of search query."""
    db, fixtures = test_db
    config = {"db_path": str(db.path), "db_encrypted": False}

    # Initialize API and LLM
    api = PRTAPI(config)
    llm = OllamaLLM(api=api)

    # Step 1: Save contacts to memory
    save_result = llm._save_contacts_with_images("contacts for directory test")
    assert save_result["success"] is True

    memory_id = save_result["memory_id"]
    contact_count = save_result["count"]

    # Step 2: Generate directory using memory ID
    directory_result = llm._generate_directory(memory_id=memory_id, output_name="memory_chain_test")

    assert (
        directory_result["success"] is True
    ), f"Directory generation failed: {directory_result.get('error')}"
    assert "output_path" in directory_result
    assert "url" in directory_result

    # Verify the directory was created
    output_path = Path(directory_result["output_path"])
    assert output_path.exists(), f"Directory not created at {output_path}"

    # Check for key files
    index_file = output_path / "index.html"
    assert index_file.exists(), "index.html not found in directory"

    # Check for images directory (should contain copied images)
    images_dir = output_path / "images"
    if contact_count > 0:
        assert images_dir.exists(), "Images directory not created"

    print(f"✓ Created directory from memory with {contact_count} contacts")
    print(f"  Memory ID: {memory_id}")
    print(f"  Output: {directory_result['output_path']}")

    # Cleanup test directory
    if output_path.exists():
        import shutil

        shutil.rmtree(
            output_path.parent if output_path.name.endswith("_directory") else output_path
        )


@pytest.mark.integration
def test_memory_chaining_workflow_complete(test_db):
    """Test the complete chaining workflow: save -> list -> generate."""
    db, fixtures = test_db
    config = {"db_path": str(db.path), "db_encrypted": False}

    # Initialize API and LLM
    api = PRTAPI(config)
    llm = OllamaLLM(api=api)

    start_time = time.time()

    # Step 1: Save contacts with images
    print("Step 1: Saving contacts with images...")
    save_result = llm._save_contacts_with_images("workflow test contacts")

    assert save_result["success"] is True
    memory_id = save_result["memory_id"]
    save_time = time.time() - start_time

    # Step 2: List memory to verify
    print("Step 2: Listing memory...")
    list_result = llm._list_memory(result_type="contacts")

    assert list_result["success"] is True
    assert any(r["id"] == memory_id for r in list_result["results"])
    list_time = time.time() - start_time

    # Step 3: Generate directory from memory
    print("Step 3: Generating directory from memory...")
    directory_result = llm._generate_directory(
        memory_id=memory_id, output_name="complete_workflow_test"
    )

    assert directory_result["success"] is True
    total_time = time.time() - start_time

    # Performance verification
    print("✓ Complete workflow performance:")
    print(f"  Save step: {save_time:.2f}s")
    print(f"  List step: {(list_time - save_time):.2f}s")
    print(f"  Directory step: {(total_time - list_time):.2f}s")
    print(f"  Total time: {total_time:.2f}s")

    # The workflow should be reasonably fast
    assert total_time < 30.0, f"Workflow took {total_time:.1f}s, expected < 30s"

    # Cleanup
    output_path = Path(directory_result["output_path"])
    if output_path.exists():
        import shutil

        shutil.rmtree(
            output_path.parent if output_path.name.endswith("_directory") else output_path
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
