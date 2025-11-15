"""
Performance and reliability tests for LLM Memory System.

These tests verify system behavior under stress, performance targets,
and reliability conditions to ensure production readiness.
"""

import threading
import time

import pytest

from tests.mocks.mock_llm_memory import TestMemoryContext


@pytest.mark.integration
class TestLLMMemoryReliability:
    """Performance and reliability tests for memory system."""

    def test_memory_performance_benchmarks(self, isolated_memory_context):
        """Test memory system performance meets targets."""
        mock_memory = isolated_memory_context

        # Performance targets from spec:
        # - Memory operations < 50ms
        # - Full test suite < 2 seconds

        # Benchmark save operations
        save_times = []
        for i in range(10):
            test_data = {"iteration": i, "data": "x" * 100}  # Small dataset

            start_time = time.time()
            memory_id = mock_memory.save_result(test_data, "benchmark", f"save {i}")
            save_time = time.time() - start_time

            save_times.append(save_time)

        avg_save_time = sum(save_times) / len(save_times)
        max_save_time = max(save_times)

        assert avg_save_time < 0.05, f"Average save time {avg_save_time*1000:.1f}ms > 50ms"
        assert max_save_time < 0.1, f"Max save time {max_save_time*1000:.1f}ms > 100ms"

        # Benchmark load operations
        load_times = []
        for i in range(10):
            memory_id = f"test_benchmark_{i:06d}_12345678"  # Simulate realistic ID

            start_time = time.time()
            mock_memory.load_result(memory_id)  # Will be None, but still measures lookup
            load_time = time.time() - start_time

            load_times.append(load_time)

        avg_load_time = sum(load_times) / len(load_times)
        max_load_time = max(load_times)

        assert avg_load_time < 0.01, f"Average load time {avg_load_time*1000:.1f}ms > 10ms"
        assert max_load_time < 0.05, f"Max load time {max_load_time*1000:.1f}ms > 50ms"

        print(
            f"✓ Performance: avg save {avg_save_time*1000:.1f}ms, avg load {avg_load_time*1000:.1f}ms"
        )

    def test_memory_system_stress_test(self, isolated_memory_context):
        """Test memory system under stress conditions."""
        mock_memory = isolated_memory_context

        # Stress test: rapid save/load cycles
        memory_ids = []
        start_time = time.time()

        for i in range(50):
            # Vary data sizes
            data_size = (i % 5 + 1) * 100  # 100-500 chars
            test_data = {"iteration": i, "data": "x" * data_size, "timestamp": time.time()}

            memory_id = mock_memory.save_result(test_data, "stress", f"stress {i}")
            memory_ids.append(memory_id)

            # Verify immediate load
            loaded = mock_memory.load_result(memory_id)
            assert loaded is not None
            assert loaded["data"]["iteration"] == i

        total_time = time.time() - start_time
        operations_per_second = (50 * 2) / total_time  # 50 saves + 50 loads

        assert (
            operations_per_second > 200
        ), f"Performance: {operations_per_second:.1f} ops/sec < 200"
        print(f"✓ Stress test: {operations_per_second:.1f} operations/second")

        # Verify data integrity after stress
        for i, memory_id in enumerate(memory_ids):
            loaded = mock_memory.load_result(memory_id)
            assert loaded is not None
            assert loaded["data"]["iteration"] == i

    def test_concurrent_memory_operations(self, isolated_memory_context):
        """Test memory system reliability under concurrent access."""
        mock_memory = isolated_memory_context
        results = []
        errors = []
        lock = threading.Lock()

        def worker_save_and_load(worker_id, operations_per_worker=10):
            """Worker function for concurrent testing."""
            worker_results = []
            try:
                for i in range(operations_per_worker):
                    # Save operation
                    test_data = {"worker_id": worker_id, "operation": i, "timestamp": time.time()}

                    memory_id = mock_memory.save_result(
                        test_data, "concurrent", f"worker_{worker_id}_op_{i}"
                    )

                    # Immediate load verification
                    loaded = mock_memory.load_result(memory_id)
                    assert loaded is not None
                    assert loaded["data"]["worker_id"] == worker_id

                    worker_results.append(memory_id)

                    # Small delay to encourage race conditions
                    time.sleep(0.001)

                with lock:
                    results.extend(worker_results)

            except Exception as e:
                with lock:
                    errors.append(f"Worker {worker_id}: {e}")

        # Start multiple concurrent workers
        threads = []
        num_workers = 5
        operations_per_worker = 8

        start_time = time.time()

        for worker_id in range(num_workers):
            thread = threading.Thread(
                target=worker_save_and_load, args=(worker_id, operations_per_worker)
            )
            threads.append(thread)
            thread.start()

        # Wait for all workers to complete
        for thread in threads:
            thread.join()

        total_time = time.time() - start_time

        # Verify no errors occurred
        assert len(errors) == 0, f"Concurrent access errors: {errors}"

        # Verify expected number of results
        expected_operations = num_workers * operations_per_worker
        assert len(results) == expected_operations

        # Verify all memory IDs are unique (no race condition corruption)
        unique_results = set(results)
        assert len(unique_results) == len(results), "Race condition: duplicate memory IDs"

        concurrent_ops_per_sec = expected_operations / total_time
        print(f"✓ Concurrent test: {concurrent_ops_per_sec:.1f} ops/sec with {num_workers} workers")

    def test_memory_system_recovery_after_errors(self, isolated_memory_context):
        """Test memory system recovery after various error conditions."""
        mock_memory = isolated_memory_context

        # Save some valid data first
        valid_id = mock_memory.save_result(
            {"data": "valid before error"}, "recovery", "valid before"
        )

        # Simulate various error conditions
        error_scenarios = [
            # JSON serialization error (handled by default=str)
            {"data": object(), "should_fail": False},  # Will be converted to string
            # Very large data (should still work with in-memory storage)
            {"data": "x" * 100000, "should_fail": False},
            # Empty data (should work fine)
            {"data": {}, "should_fail": False},
        ]

        for i, scenario in enumerate(error_scenarios):
            try:
                memory_id = mock_memory.save_result(
                    scenario["data"], "recovery", f"error scenario {i}"
                )
                if scenario["should_fail"]:
                    pytest.fail(f"Expected scenario {i} to fail but it succeeded")
                else:
                    # Verify successful save
                    loaded = mock_memory.load_result(memory_id)
                    assert loaded is not None
            except Exception as e:
                if not scenario["should_fail"]:
                    pytest.fail(f"Unexpected failure in scenario {i}: {e}")

        # Verify system still works after errors
        recovery_id = mock_memory.save_result(
            {"data": "valid after errors"}, "recovery", "valid after"
        )

        # Verify both original and recovery data are accessible
        original_data = mock_memory.load_result(valid_id)
        recovery_data = mock_memory.load_result(recovery_id)

        assert original_data is not None
        assert recovery_data is not None
        assert original_data["data"]["data"] == "valid before error"
        assert recovery_data["data"]["data"] == "valid after errors"

    def test_memory_system_with_large_datasets(self, isolated_memory_context):
        """Test memory system performance with large datasets."""
        mock_memory = isolated_memory_context

        # Test with progressively larger datasets
        dataset_sizes = [10, 100, 500]  # Number of contacts
        performance_results = []

        for size in dataset_sizes:
            # Generate large contact dataset
            large_dataset = []
            for i in range(size):
                contact = {
                    "id": i,
                    "name": f"Contact {i}",
                    "email": f"contact{i}@example.com",
                    "phone": f"+1-555-{i:04d}",
                    "profile_image": b"x" * 512,  # 512 bytes per image
                    "has_profile_image": True,
                    "notes": f"Long note for contact {i} " * 20,  # ~400 chars per note
                }
                large_dataset.append(contact)

            # Measure save performance
            start_time = time.time()
            memory_id = mock_memory.save_result(large_dataset, "large", f"dataset size {size}")
            save_time = time.time() - start_time

            # Measure load performance
            start_time = time.time()
            loaded = mock_memory.load_result(memory_id)
            load_time = time.time() - start_time

            assert loaded is not None
            assert len(loaded["data"]) == size

            performance_results.append(
                {
                    "size": size,
                    "save_time": save_time,
                    "load_time": load_time,
                    "total_time": save_time + load_time,
                }
            )

            # Performance targets scale with size
            max_save_time = min(5.0, size * 0.01)  # 10ms per contact, max 5s
            max_load_time = min(2.0, size * 0.005)  # 5ms per contact, max 2s

            assert (
                save_time < max_save_time
            ), f"Save {size} contacts: {save_time:.2f}s > {max_save_time:.2f}s"
            assert (
                load_time < max_load_time
            ), f"Load {size} contacts: {load_time:.2f}s > {max_load_time:.2f}s"

        # Print performance summary
        print("✓ Large dataset performance:")
        for result in performance_results:
            print(
                f"  {result['size']} contacts: save {result['save_time']*1000:.0f}ms, load {result['load_time']*1000:.0f}ms"
            )

    def test_memory_test_suite_performance(self):
        """Test that memory-related tests complete within target time."""
        # This test measures the performance of the test suite itself
        start_time = time.time()

        # Simulate running multiple memory tests
        test_scenarios = [
            # Basic operations
            lambda: TestMemoryContext("perf_test_1", use_temp_files=False)
            .__enter__()
            .__exit__(None, None, None),
            lambda: TestMemoryContext("perf_test_2", use_temp_files=False)
            .__enter__()
            .__exit__(None, None, None),
            lambda: TestMemoryContext("perf_test_3", use_temp_files=False)
            .__enter__()
            .__exit__(None, None, None),
        ]

        for scenario in test_scenarios:
            scenario()

        total_time = time.time() - start_time

        # Target: Memory test overhead should be minimal
        assert total_time < 1.0, f"Memory test suite overhead: {total_time:.2f}s > 1.0s"
        print(f"✓ Test suite performance: {total_time*1000:.0f}ms overhead")

    def test_memory_isolation_reliability(self):
        """Test reliability of memory isolation between tests."""
        # Test that multiple isolated contexts don't interfere
        context_results = {}

        test_names = [f"isolation_test_{i}" for i in range(5)]

        for test_name in test_names:
            with TestMemoryContext(test_name, use_temp_files=False, patch_global=False) as memory:
                # Save test-specific data
                memory_id = memory.save_result(
                    {"test_name": test_name, "data": f"data for {test_name}"},
                    "isolation",
                    f"isolation test {test_name}",
                )

                # Verify isolation
                results = memory.list_results()
                assert len(results) == 1
                assert results[0]["id"] == memory_id

                context_results[test_name] = memory_id

        # Verify each context was truly isolated
        assert len(set(context_results.values())) == len(
            context_results
        ), "Context isolation failed"

    @pytest.mark.skipif(True, reason="Network test - run manually for full validation")
    def test_memory_system_under_resource_pressure(self):
        """Test memory system behavior under resource pressure."""
        # This test would simulate low memory conditions, disk space issues, etc.
        # Skipped by default as it requires special system setup

    def test_memory_cleanup_performance(self, isolated_memory_context):
        """Test performance of memory cleanup operations."""
        mock_memory = isolated_memory_context

        # Create many memory entries
        num_entries = 100
        for i in range(num_entries):
            mock_memory.save_result({"data": f"cleanup test {i}"}, "cleanup", f"cleanup {i}")

        # Measure cleanup performance
        start_time = time.time()
        mock_memory.cleanup()
        cleanup_time = time.time() - start_time

        # Cleanup should be fast even with many entries
        max_cleanup_time = max(1.0, num_entries * 0.005)  # 5ms per entry, max 1s
        assert (
            cleanup_time < max_cleanup_time
        ), f"Cleanup {num_entries} entries: {cleanup_time:.2f}s > {max_cleanup_time:.2f}s"

        # Verify cleanup was complete
        stats = mock_memory.get_stats()
        assert stats["total_results"] == 0

        print(f"✓ Cleanup performance: {num_entries} entries in {cleanup_time*1000:.0f}ms")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
