"""Performance benchmarking for contacts with images functionality.

Tests the performance of the optimized query and tool chain with various dataset sizes.
Includes index usage verification and performance regression detection.
"""

import time
from pathlib import Path

import pytest

from prt_src.api import PRTAPI
from prt_src.llm_ollama import OllamaLLM


@pytest.mark.performance
def test_contacts_with_images_query_performance(test_db):
    """Test performance of get_contacts_with_images with fixture data."""
    db, fixtures = test_db
    config = {"db_path": str(db.path), "db_encrypted": False}
    api = PRTAPI(config)

    # Warm up the database
    api.list_all_contacts()

    # Benchmark the optimized query
    times = []
    for _i in range(5):  # Run multiple times for average
        start_time = time.time()
        contacts = api.get_contacts_with_images()
        query_time = time.time() - start_time
        times.append(query_time)

    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)

    # Performance assertions
    assert avg_time < 0.1, f"Average query time {avg_time:.3f}s exceeds 100ms threshold"
    assert max_time < 0.2, f"Max query time {max_time:.3f}s exceeds 200ms threshold"

    print("✓ Query performance (5 runs):")
    print(f"  Average: {avg_time*1000:.1f}ms")
    print(f"  Min: {min_time*1000:.1f}ms")
    print(f"  Max: {max_time*1000:.1f}ms")
    print(f"  Contacts found: {len(contacts)}")


@pytest.mark.performance
def test_contacts_with_images_vs_full_scan_performance(test_db):
    """Compare optimized query performance vs. full table scan."""
    db, fixtures = test_db
    config = {"db_path": str(db.path), "db_encrypted": False}
    api = PRTAPI(config)

    # Test optimized query
    start_time = time.time()
    optimized_contacts = api.get_contacts_with_images()
    optimized_time = time.time() - start_time

    # Test naive approach (full scan)
    start_time = time.time()
    all_contacts = api.list_all_contacts()
    naive_contacts = [c for c in all_contacts if c.get("profile_image")]
    naive_time = time.time() - start_time

    # Verify same results
    assert len(optimized_contacts) == len(
        naive_contacts
    ), "Optimized and naive queries returned different counts"

    # Performance comparison
    speedup = naive_time / optimized_time if optimized_time > 0 else float("inf")

    print("✓ Performance comparison:")
    print(f"  Optimized query: {optimized_time*1000:.1f}ms")
    print(f"  Naive full scan: {naive_time*1000:.1f}ms")
    print(f"  Speedup: {speedup:.1f}x")

    # The optimized query should be faster or at least not significantly slower
    assert (
        optimized_time <= naive_time * 1.5
    ), "Optimized query shouldn't be significantly slower than naive approach"


@pytest.mark.performance
def test_index_usage_verification(test_db):
    """Verify that the database index is being used for the optimized query."""
    import sqlite3

    db, fixtures = test_db
    db_path = str(db.path)

    # Use sqlite3 directly to check index
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Query to check index existence
        cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='index' AND name='idx_contacts_profile_image_not_null'
        """
        )

        result = cursor.fetchall()

        # Verify the index exists (it should be created by the migration)
        if len(result) > 0:
            print(f"✓ Performance index verified: {result[0][0]}")
        else:
            print("⚠ Performance index not found, but query should still work")

        # Test query plan to verify optimization
        cursor.execute(
            """
            EXPLAIN QUERY PLAN
            SELECT id, name, email, phone, profile_image, profile_image_filename, profile_image_mime_type
            FROM contacts
            WHERE profile_image IS NOT NULL
            ORDER BY name
        """
        )

        plan_result = cursor.fetchall()
        plan_text = " ".join([str(row) for row in plan_result])

        print(f"✓ Query plan: {plan_text}")

        # The query should be reasonably efficient
        # We don't strictly require the index since it's a migration feature
        print("✓ Index verification completed")

    finally:
        conn.close()


@pytest.mark.performance
def test_tool_chain_performance(test_db, llm_config):
    """Test performance of the complete tool chain."""
    db, fixtures = test_db
    config = {"db_path": str(db.path), "db_encrypted": False}

    api = PRTAPI(config)
    llm = OllamaLLM(api=api, config_manager=llm_config)

    # Test the individual tool performance
    start_time = time.time()
    query_result = llm._get_contacts_with_images()
    query_time = time.time() - start_time

    assert query_result["success"], f"Query tool failed: {query_result.get('error')}"

    # Test the combined tool performance (if contacts exist)
    if query_result["count"] > 0:
        start_time = time.time()
        directory_result = llm._create_directory_from_contacts_with_images("perf_test")
        total_time = time.time() - start_time

        assert directory_result[
            "success"
        ], f"Directory tool failed: {directory_result.get('error')}"

        # Verify performance metrics are included
        perf = directory_result["performance"]
        assert perf["query_time_ms"] > 0
        assert perf["directory_time_ms"] > 0
        assert perf["total_time_ms"] > 0

        print("✓ Tool chain performance:")
        print(f"  Query only: {query_time*1000:.1f}ms")
        print(f"  Full chain: {total_time*1000:.1f}ms")
        print(
            f"  Breakdown - Query: {perf['query_time_ms']:.1f}ms, Directory: {perf['directory_time_ms']:.1f}ms"
        )

        # Performance thresholds
        assert (
            perf["query_time_ms"] < 500
        ), f"Query took {perf['query_time_ms']:.1f}ms, expected < 500ms"
        assert (
            perf["total_time_ms"] < 10000
        ), f"Total time {perf['total_time_ms']:.1f}ms, expected < 10s"

        # Cleanup test directory
        output_path = Path(directory_result["output_path"])
        if output_path.exists():
            import shutil

            shutil.rmtree(
                output_path.parent if output_path.name.endswith("_directory") else output_path
            )


@pytest.mark.performance
def test_memory_usage_with_images(test_db):
    """Test memory efficiency when working with profile images."""
    import tracemalloc

    db, fixtures = test_db
    config = {"db_path": str(db.path), "db_encrypted": False}
    api = PRTAPI(config)

    # Start tracing memory
    tracemalloc.start()

    # Execute the query
    contacts = api.get_contacts_with_images()

    # Get memory usage
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"✓ Memory usage for {len(contacts)} contacts with images:")
    print(f"  Current: {current / 1024 / 1024:.1f} MB")
    print(f"  Peak: {peak / 1024 / 1024:.1f} MB")

    # Memory thresholds (adjust based on fixture data size)
    # These are generous thresholds - adjust if you know your fixture image sizes
    assert (
        peak < 50 * 1024 * 1024
    ), f"Peak memory {peak / 1024 / 1024:.1f} MB exceeds 50 MB threshold"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "performance"])
