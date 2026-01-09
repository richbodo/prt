"""
Mock LLM Memory System for Test Isolation

This module provides an isolated memory system specifically for testing,
ensuring that tests don't interfere with each other or leave persistent state.

Key features:
- Test-specific temporary directories
- Automatic cleanup after tests
- Isolated from production memory system
- Fast in-memory fallback for unit tests
"""

import json
import tempfile
import uuid
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from typing import Any

from prt_src.logging_config import get_logger

logger = get_logger(__name__)


class MockLLMMemory:
    """Test-isolated memory system that cleans up automatically."""

    def __init__(self, test_name: str = None, use_temp_files: bool = True):
        """Initialize test memory system.

        Args:
            test_name: Name of the test for unique directory
            use_temp_files: If False, uses in-memory storage for speed
        """
        self.test_name = test_name or "unknown_test"
        self.use_temp_files = use_temp_files
        self.max_age = timedelta(hours=1)  # Shorter cleanup for tests

        if use_temp_files:
            # Create test-specific directory
            self.base_dir = Path(tempfile.mkdtemp(prefix=f"prt_test_memory_{self.test_name}_"))
            logger.debug(f"[MOCK_MEMORY] Created test memory dir: {self.base_dir}")
        else:
            # Use in-memory storage for speed
            self.base_dir = None
            self._memory_store = {}
            logger.debug(f"[MOCK_MEMORY] Using in-memory storage for {self.test_name}")

    def save_result(self, data: Any, result_type: str = "query", description: str = None) -> str:
        """Save result with test isolation."""
        # Generate test-specific ID
        timestamp = datetime.now().strftime("%H%M%S")
        short_uuid = str(uuid.uuid4())[:8]
        result_id = f"test_{result_type}_{timestamp}_{short_uuid}"

        logger.debug(f"[MOCK_MEMORY_SAVE] {result_id} for test {self.test_name}")

        metadata = {
            "id": result_id,
            "type": result_type,
            "description": description or f"{result_type} result",
            "created_at": datetime.now().isoformat(),
            "data_count": len(data) if isinstance(data, list) else 1,
            "data": data,
            "test_name": self.test_name,
        }

        if self.use_temp_files:
            # Save to temp file
            result_file = self.base_dir / f"{result_id}.json"
            try:
                with open(result_file, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, indent=2, default=str)
                logger.debug(f"[MOCK_MEMORY_SAVE] Saved to file: {result_file}")
            except Exception as e:
                logger.error(f"[MOCK_MEMORY_SAVE_ERROR] Failed to save {result_id}: {e}")
                raise
        else:
            # Save to memory
            self._memory_store[result_id] = metadata
            logger.debug("[MOCK_MEMORY_SAVE] Saved to memory store")

        return result_id

    def load_result(self, result_id: str) -> dict[str, Any] | None:
        """Load result with test isolation."""
        logger.debug(f"[MOCK_MEMORY_LOAD] Loading {result_id} for test {self.test_name}")

        if self.use_temp_files:
            result_file = self.base_dir / f"{result_id}.json"
            if not result_file.exists():
                logger.warning(f"[MOCK_MEMORY_LOAD] File not found: {result_file}")
                return None

            try:
                with open(result_file, encoding="utf-8") as f:
                    result = json.load(f)
                logger.debug("[MOCK_MEMORY_LOAD] Loaded from file successfully")
                return result
            except Exception as e:
                logger.error(f"[MOCK_MEMORY_LOAD_ERROR] Failed to load {result_id}: {e}")
                return None
        else:
            # Load from memory
            result = self._memory_store.get(result_id)
            if result:
                logger.debug("[MOCK_MEMORY_LOAD] Loaded from memory store successfully")
            else:
                logger.warning("[MOCK_MEMORY_LOAD] Not found in memory store")
            return result

    def list_results(self, result_type: str = None) -> list[dict[str, Any]]:
        """List results with test isolation."""
        results = []

        if self.use_temp_files:
            if not self.base_dir or not self.base_dir.exists():
                return results

            for result_file in self.base_dir.glob("*.json"):
                try:
                    with open(result_file, encoding="utf-8") as f:
                        metadata = json.load(f)

                    # Filter by type if specified
                    if result_type and metadata.get("type") != result_type:
                        continue

                    # Return summary without full data
                    summary = {
                        "id": metadata.get("id"),
                        "type": metadata.get("type"),
                        "description": metadata.get("description"),
                        "created_at": metadata.get("created_at"),
                        "data_count": metadata.get("data_count"),
                        "test_name": metadata.get("test_name"),
                    }
                    results.append(summary)
                except Exception as e:
                    logger.warning(f"[MOCK_MEMORY_LIST] Failed to read {result_file}: {e}")
        else:
            # List from memory
            for _result_id, metadata in self._memory_store.items():
                # Filter by type if specified
                if result_type and metadata.get("type") != result_type:
                    continue

                summary = {
                    "id": metadata.get("id"),
                    "type": metadata.get("type"),
                    "description": metadata.get("description"),
                    "created_at": metadata.get("created_at"),
                    "data_count": metadata.get("data_count"),
                    "test_name": metadata.get("test_name"),
                }
                results.append(summary)

        # Sort by creation time, newest first
        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return results

    def delete_result(self, result_id: str) -> bool:
        """Delete result with test isolation."""
        logger.debug(f"[MOCK_MEMORY_DELETE] Deleting {result_id} for test {self.test_name}")

        if self.use_temp_files:
            result_file = self.base_dir / f"{result_id}.json"
            if not result_file.exists():
                return False

            try:
                result_file.unlink()
                logger.debug(f"[MOCK_MEMORY_DELETE] Deleted file: {result_file}")
                return True
            except Exception as e:
                logger.error(f"[MOCK_MEMORY_DELETE_ERROR] Failed to delete {result_id}: {e}")
                return False
        else:
            # Delete from memory
            if result_id in self._memory_store:
                del self._memory_store[result_id]
                logger.debug("[MOCK_MEMORY_DELETE] Deleted from memory store")
                return True
            return False

    def get_stats(self) -> dict[str, Any]:
        """Get statistics for test memory system."""
        results = self.list_results()

        stats = {
            "total_results": len(results),
            "storage_path": str(self.base_dir) if self.base_dir else "in-memory",
            "max_age_hours": self.max_age.total_seconds() / 3600,
            "test_name": self.test_name,
            "use_temp_files": self.use_temp_files,
            "types": {},
        }

        # Count by type
        for result in results:
            result_type = result.get("type", "unknown")
            stats["types"][result_type] = stats["types"].get(result_type, 0) + 1

        return stats

    def _cleanup_old_results(self) -> int:
        """Clean up old results (for compatibility with real LLMMemory).

        Returns:
            Number of results cleaned up
        """
        if not self.use_temp_files:
            return 0

        from datetime import datetime

        cleaned_count = 0
        cutoff_time = datetime.now() - self.max_age

        if self.base_dir and self.base_dir.exists():
            for result_file in self.base_dir.glob("*.json"):
                try:
                    # Check file modification time
                    file_time = datetime.fromtimestamp(result_file.stat().st_mtime)

                    if file_time < cutoff_time:
                        result_file.unlink()
                        cleaned_count += 1
                        logger.debug(
                            f"[MOCK_MEMORY_CLEANUP] Cleaned up old result: {result_file.name}"
                        )

                except Exception as e:
                    logger.warning(f"[MOCK_MEMORY_CLEANUP] Failed to clean up {result_file}: {e}")
                    continue

        if cleaned_count > 0:
            logger.info(f"[MOCK_MEMORY_CLEANUP] Cleaned up {cleaned_count} old results")

        return cleaned_count

    def cleanup(self):
        """Clean up test memory system."""
        logger.debug(f"[MOCK_MEMORY_CLEANUP] Cleaning up test memory for {self.test_name}")

        if self.use_temp_files and self.base_dir and self.base_dir.exists():
            import shutil

            try:
                shutil.rmtree(self.base_dir)
                logger.debug(f"[MOCK_MEMORY_CLEANUP] Removed directory: {self.base_dir}")
            except Exception as e:
                logger.warning(f"[MOCK_MEMORY_CLEANUP] Failed to remove {self.base_dir}: {e}")
        elif not self.use_temp_files:
            self._memory_store.clear()
            logger.debug("[MOCK_MEMORY_CLEANUP] Cleared memory store")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with automatic cleanup."""
        self.cleanup()


def create_test_memory(test_name: str = None, use_temp_files: bool = True) -> MockLLMMemory:
    """Factory function to create test memory instances.

    Args:
        test_name: Name of the test for unique directory
        use_temp_files: If False, uses in-memory storage for speed

    Returns:
        MockLLMMemory instance
    """
    return MockLLMMemory(test_name=test_name, use_temp_files=use_temp_files)


class TestMemoryContext:
    """Context manager for test memory with automatic cleanup and LLM patching."""

    def __init__(self, test_name: str, use_temp_files: bool = True, patch_global: bool = True):
        """Initialize test memory context.

        Args:
            test_name: Name of the test
            use_temp_files: Whether to use temp files or in-memory storage
            patch_global: Whether to patch the global llm_memory instance
        """
        self.test_name = test_name
        self.use_temp_files = use_temp_files
        self.patch_global = patch_global
        self.mock_memory = None
        self.original_memory = None
        self.original_ollama_memory = None

    def __enter__(self) -> MockLLMMemory:
        """Enter context with memory setup and optional patching."""
        self.mock_memory = MockLLMMemory(self.test_name, self.use_temp_files)

        if self.patch_global:
            # Patch the global llm_memory instance in multiple modules
            import prt_src.llm_memory
            import prt_src.llm_ollama

            # Save original instances
            self.original_memory = prt_src.llm_memory.llm_memory
            self.original_ollama_memory = getattr(prt_src.llm_ollama, "llm_memory", None)

            # Patch both modules
            prt_src.llm_memory.llm_memory = self.mock_memory
            prt_src.llm_ollama.llm_memory = self.mock_memory

            logger.debug(f"[TEST_MEMORY_CONTEXT] Patched global llm_memory for {self.test_name}")

        return self.mock_memory

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context with cleanup and restoration."""
        if self.patch_global and self.original_memory:
            # Restore original global instances
            import prt_src.llm_memory
            import prt_src.llm_ollama

            prt_src.llm_memory.llm_memory = self.original_memory
            if self.original_ollama_memory:
                prt_src.llm_ollama.llm_memory = self.original_ollama_memory

            logger.debug(f"[TEST_MEMORY_CONTEXT] Restored global llm_memory for {self.test_name}")

        if self.mock_memory:
            self.mock_memory.cleanup()
