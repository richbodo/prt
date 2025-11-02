"""Thread safety tests for LLM factory.

Tests that the global registry initialization is thread-safe and that
concurrent access to get_registry() doesn't create race conditions.
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed

from prt_src.llm_factory import get_registry


class TestLLMFactoryThreadSafety:
    """Test thread safety of LLM factory global registry."""

    def setup_method(self):
        """Reset global registry before each test."""
        import prt_src.llm_factory as factory_module
        factory_module._registry = None

    def test_get_registry_singleton(self):
        """Test that get_registry returns the same instance."""
        registry1 = get_registry()
        registry2 = get_registry()

        assert registry1 is registry2
        assert id(registry1) == id(registry2)

    def test_get_registry_concurrent_access(self):
        """Test that concurrent access to get_registry is thread-safe."""
        results = []
        num_threads = 20

        def get_registry_worker():
            """Worker function that gets registry and stores result."""
            registry = get_registry()
            results.append(id(registry))
            return registry

        # Launch multiple threads concurrently
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(get_registry_worker) for _ in range(num_threads)]

            # Wait for all to complete
            registries = [future.result() for future in as_completed(futures)]

        # All threads should get the same registry instance
        assert (
            len(set(results)) == 1
        ), f"Got {len(set(results))} different instances: {set(results)}"

        # All returned registries should be the same object
        first_registry = registries[0]
        for registry in registries[1:]:
            assert registry is first_registry

    def test_get_registry_thread_safe_initialization(self):
        """Test thread-safe initialization with timing collision."""
        results = []
        barrier = threading.Barrier(10)  # Synchronize 10 threads

        def synchronized_get_registry():
            """Worker that waits for all threads, then gets registry."""
            barrier.wait()  # All threads start at exactly the same time
            registry = get_registry()
            results.append(id(registry))
            return registry

        threads = []
        for _ in range(10):
            thread = threading.Thread(target=synchronized_get_registry)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Should have created exactly one registry instance
        assert len(set(results)) == 1, f"Created {len(set(results))} instances in race condition"

    def test_get_registry_lock_exists(self):
        """Test that the registry lock exists and is a threading.Lock."""
        from prt_src.llm_factory import _registry_lock

        assert _registry_lock is not None
        assert isinstance(_registry_lock, threading.Lock)

    def test_get_registry_idempotent(self):
        """Test that get_registry is idempotent after initialization."""
        # First call initializes
        registry1 = get_registry()

        # Subsequent calls should be fast and return same instance
        start_time = time.time()
        for _ in range(100):
            registry = get_registry()
            assert registry is registry1

        elapsed = time.time() - start_time
        # 100 calls should be very fast (< 0.01 seconds) since no lock needed
        assert elapsed < 0.01, f"get_registry too slow after initialization: {elapsed}s"
