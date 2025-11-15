"""
Functional tests for LLM Memory System

Tests memory operations independently with focus on data integrity,
serialization/deserialization, and cleanup mechanisms.
"""

import tempfile
import time
from datetime import datetime
from datetime import timedelta
from pathlib import Path

import pytest

from prt_src.llm_memory import LLMMemory


@pytest.fixture
def temp_memory_dir():
    """Create a temporary directory for memory tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def memory_instance(temp_memory_dir):
    """Create an isolated memory instance for testing."""
    return LLMMemory(base_dir=temp_memory_dir / "test_memory", max_age_hours=1)


@pytest.mark.unit
def test_memory_initialization(temp_memory_dir):
    """Test memory system initialization and directory creation."""
    memory_dir = temp_memory_dir / "test_init"
    assert not memory_dir.exists()

    memory = LLMMemory(base_dir=memory_dir, max_age_hours=12)

    assert memory.base_dir == memory_dir
    assert memory_dir.exists()
    assert memory.max_age == timedelta(hours=12)


@pytest.mark.unit
def test_memory_id_generation_uniqueness(memory_instance):
    """Test that memory IDs are unique and properly formatted."""
    ids = set()

    # Generate multiple IDs quickly to test uniqueness
    for i in range(10):
        memory_id = memory_instance.save_result(
            {"test": f"data_{i}"}, "test", f"test description {i}"
        )

        assert memory_id not in ids, f"Duplicate ID generated: {memory_id}"
        ids.add(memory_id)

        # Validate ID format: type_timestamp_uuid
        parts = memory_id.split("_")
        assert len(parts) == 3, f"Invalid ID format: {memory_id}"
        assert parts[0] == "test", f"Wrong type prefix: {parts[0]}"
        assert len(parts[1]) == 6, f"Invalid timestamp format: {parts[1]}"
        assert parts[1].isdigit(), f"Timestamp not numeric: {parts[1]}"
        assert len(parts[2]) == 8, f"Invalid UUID fragment: {parts[2]}"


@pytest.mark.unit
def test_memory_data_integrity_simple(memory_instance):
    """Test data integrity for simple data types."""
    test_cases = [
        ({"simple": "data"}, "dict"),
        ([1, 2, 3, 4, 5], "list"),
        ("simple string", "string"),
        (42, "number"),
        (True, "boolean"),
        (None, "null"),
        ({"nested": {"data": [1, 2, {"deep": "value"}]}}, "nested"),
    ]

    for data, description in test_cases:
        memory_id = memory_instance.save_result(data, "integrity", description)
        assert memory_id is not None, f"Failed to save {description} data"

        loaded = memory_instance.load_result(memory_id)
        assert loaded is not None, f"Failed to load {description} data for ID {memory_id}"
        assert loaded["data"] == data, f"Data corruption for {description}"
        assert loaded["type"] == "integrity"
        assert loaded["description"] == description
        assert "created_at" in loaded
        assert "data_count" in loaded


@pytest.mark.unit
def test_memory_data_integrity_large_dataset(memory_instance):
    """Test data integrity with large datasets."""
    # Create a large dataset
    large_data = []
    for i in range(1000):
        large_data.append(
            {
                "id": i,
                "name": f"Test Contact {i}",
                "email": f"test{i}@example.com",
                "metadata": {"score": i * 0.1, "tags": [f"tag_{j}" for j in range(i % 5)]},
            }
        )

    memory_id = memory_instance.save_result(large_data, "large", "large dataset test")
    loaded = memory_instance.load_result(memory_id)

    assert loaded is not None
    assert len(loaded["data"]) == 1000
    assert loaded["data_count"] == 1000

    # Verify random samples
    for i in [0, 100, 500, 999]:
        assert loaded["data"][i]["id"] == i
        assert loaded["data"][i]["name"] == f"Test Contact {i}"
        assert loaded["data"][i]["metadata"]["score"] == i * 0.1


@pytest.mark.unit
def test_memory_empty_data_handling(memory_instance):
    """Test handling of empty data structures."""
    test_cases = [
        ([], "empty list"),
        ({}, "empty dict"),
        ("", "empty string"),
    ]

    for data, description in test_cases:
        memory_id = memory_instance.save_result(data, "empty", description)
        loaded = memory_instance.load_result(memory_id)

        assert loaded is not None
        assert loaded["data"] == data
        assert loaded["data_count"] == 0  # Should be 0 for empty containers


@pytest.mark.unit
def test_memory_corrupted_data_recovery(memory_instance, temp_memory_dir):
    """Test behavior when memory files are corrupted."""
    # Create a valid result first
    memory_id = memory_instance.save_result({"test": "data"}, "corruption", "test data")

    # Verify it loads correctly
    loaded = memory_instance.load_result(memory_id)
    assert loaded is not None

    # Corrupt the file
    result_file = memory_instance.base_dir / f"{memory_id}.json"
    with open(result_file, "w") as f:
        f.write("invalid json content {")

    # Should return None gracefully
    corrupted_loaded = memory_instance.load_result(memory_id)
    assert corrupted_loaded is None


@pytest.mark.unit
def test_memory_concurrent_access_safety(memory_instance):
    """Test memory system behavior under simulated concurrent access."""
    import threading
    import time

    results = []
    errors = []

    def save_data(thread_id):
        try:
            for i in range(5):
                data = {"thread": thread_id, "iteration": i, "timestamp": time.time()}
                memory_id = memory_instance.save_result(data, "concurrent", f"thread {thread_id}")
                results.append(memory_id)
                time.sleep(0.001)  # Small delay to increase contention
        except Exception as e:
            errors.append(e)

    # Start multiple threads
    threads = []
    for i in range(3):
        thread = threading.Thread(target=save_data, args=(i,))
        threads.append(thread)
        thread.start()

    # Wait for all threads
    for thread in threads:
        thread.join()

    # Verify results
    assert len(errors) == 0, f"Concurrent access errors: {errors}"
    assert len(results) == 15  # 3 threads * 5 iterations
    assert len(set(results)) == 15  # All IDs should be unique

    # Verify all data can be loaded
    for memory_id in results:
        loaded = memory_instance.load_result(memory_id)
        assert loaded is not None


@pytest.mark.unit
def test_memory_cleanup_mechanisms(memory_instance):
    """Test cleanup of old results and file system error handling."""
    # Create some test data
    old_ids = []
    new_ids = []

    # Save some "old" data (we'll manually age these)
    for i in range(3):
        memory_id = memory_instance.save_result({"old_data": i}, "cleanup", f"old data {i}")
        old_ids.append(memory_id)

    # Manually age the files by modifying their timestamps
    import os

    cutoff_time = datetime.now() - timedelta(hours=2)  # 2 hours ago
    for memory_id in old_ids:
        result_file = memory_instance.base_dir / f"{memory_id}.json"
        old_timestamp = cutoff_time.timestamp()
        os.utime(result_file, (old_timestamp, old_timestamp))

    # Save some "new" data
    for i in range(2):
        memory_id = memory_instance.save_result({"new_data": i}, "cleanup", f"new data {i}")
        new_ids.append(memory_id)

    # Run cleanup
    cleaned_count = memory_instance._cleanup_old_results()

    assert cleaned_count == 3, f"Expected 3 cleaned results, got {cleaned_count}"

    # Verify old data is gone
    for memory_id in old_ids:
        loaded = memory_instance.load_result(memory_id)
        assert loaded is None, f"Old data should be cleaned up: {memory_id}"

    # Verify new data remains
    for memory_id in new_ids:
        loaded = memory_instance.load_result(memory_id)
        assert loaded is not None, f"New data should remain: {memory_id}"


@pytest.mark.unit
def test_memory_file_permission_errors(temp_memory_dir):
    """Test behavior when file permissions prevent operations."""
    memory_dir = temp_memory_dir / "readonly"
    memory = LLMMemory(base_dir=memory_dir)

    # Save some data first
    memory.save_result({"test": "data"}, "permission", "test")

    # Make directory read-only (Unix only)
    import stat

    try:
        memory_dir.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

        # Should fail gracefully when trying to save
        with pytest.raises(Exception):
            memory.save_result({"fail": "test"}, "permission", "should fail")

    finally:
        # Restore permissions for cleanup
        memory_dir.chmod(stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)


@pytest.mark.unit
def test_memory_list_and_stats_functionality(memory_instance):
    """Test list_results and get_stats methods thoroughly."""
    # Create diverse data
    test_data = [
        ({"contacts": [1, 2, 3]}, "contacts", "test contacts"),
        ({"search": ["a", "b"]}, "search", "test search"),
        ({"queries": []}, "contacts", "empty contacts"),  # Same type as first
        ({"other": "data"}, "other", "different type"),
    ]

    memory_ids = []
    for data, result_type, description in test_data:
        memory_id = memory_instance.save_result(data, result_type, description)
        memory_ids.append(memory_id)

    # Test listing all results
    all_results = memory_instance.list_results()
    assert len(all_results) == 4

    # Results should be sorted by creation time (newest first)
    timestamps = [r["created_at"] for r in all_results]
    assert timestamps == sorted(timestamps, reverse=True)

    # Test filtering by type
    contacts_results = memory_instance.list_results(result_type="contacts")
    assert len(contacts_results) == 2  # Two contacts type results

    search_results = memory_instance.list_results(result_type="search")
    assert len(search_results) == 1

    # Test stats
    stats = memory_instance.get_stats()
    assert stats["total_results"] == 4
    assert stats["types"]["contacts"] == 2
    assert stats["types"]["search"] == 1
    assert stats["types"]["other"] == 1
    assert "storage_path" in stats
    assert stats["max_age_hours"] == 1.0


@pytest.mark.unit
def test_memory_performance_targets(memory_instance):
    """Test that memory operations meet performance targets."""
    # Test data of various sizes
    small_data = {"small": "test"}
    medium_data = [{"item": i} for i in range(100)]
    large_data = [{"item": i, "data": "x" * 1000} for i in range(500)]

    # Test save performance
    start_time = time.time()
    small_id = memory_instance.save_result(small_data, "perf", "small test")
    small_save_time = time.time() - start_time

    start_time = time.time()
    medium_id = memory_instance.save_result(medium_data, "perf", "medium test")
    medium_save_time = time.time() - start_time

    start_time = time.time()
    large_id = memory_instance.save_result(large_data, "perf", "large test")
    large_save_time = time.time() - start_time

    # Test load performance
    start_time = time.time()
    memory_instance.load_result(small_id)
    small_load_time = time.time() - start_time

    start_time = time.time()
    memory_instance.load_result(medium_id)
    medium_load_time = time.time() - start_time

    start_time = time.time()
    memory_instance.load_result(large_id)
    large_load_time = time.time() - start_time

    # Performance assertions (target: < 50ms for individual operations)
    assert small_save_time < 0.05, f"Small save took {small_save_time:.3f}s"
    assert small_load_time < 0.05, f"Small load took {small_load_time:.3f}s"

    assert medium_save_time < 0.1, f"Medium save took {medium_save_time:.3f}s"
    assert medium_load_time < 0.1, f"Medium load took {medium_load_time:.3f}s"

    # Large data gets more time but should still be reasonable
    assert large_save_time < 0.5, f"Large save took {large_save_time:.3f}s"
    assert large_load_time < 0.5, f"Large load took {large_load_time:.3f}s"

    print("Performance results:")
    print(f"  Small: save {small_save_time:.3f}s, load {small_load_time:.3f}s")
    print(f"  Medium: save {medium_save_time:.3f}s, load {medium_load_time:.3f}s")
    print(f"  Large: save {large_save_time:.3f}s, load {large_load_time:.3f}s")


@pytest.mark.unit
def test_memory_cleanup_no_persistent_files(memory_instance):
    """Test that memory system doesn't leave persistent files after cleanup."""
    # Save some data
    memory_ids = []
    for i in range(5):
        memory_id = memory_instance.save_result({"test": f"data_{i}"}, "cleanup_test", f"test {i}")
        memory_ids.append(memory_id)

    # Verify files exist
    for memory_id in memory_ids:
        result_file = memory_instance.base_dir / f"{memory_id}.json"
        assert result_file.exists()

    # Delete all results
    for memory_id in memory_ids:
        deleted = memory_instance.delete_result(memory_id)
        assert deleted is True

    # Verify files are gone
    for memory_id in memory_ids:
        result_file = memory_instance.base_dir / f"{memory_id}.json"
        assert not result_file.exists()

    # Verify directory is empty (except for .gitkeep or similar)
    remaining_files = list(memory_instance.base_dir.glob("*.json"))
    assert len(remaining_files) == 0, f"Unexpected files remain: {remaining_files}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
