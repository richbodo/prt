"""
LLM Memory/Cache System for Query Result Chaining

This module provides a simple persistent storage system that allows LLM tools
to save query results and reference them in subsequent operations.

Design principles:
- Simple file-based storage in temp directory
- JSON serialization for compatibility
- Automatic cleanup of old results
- Human-readable result IDs for LLM use
"""

import json
import tempfile
import uuid
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from .logging_config import get_logger

logger = get_logger(__name__)


class LLMMemory:
    """Manages persistent storage of query results for LLM tool chaining."""

    def __init__(self, base_dir: Optional[Path] = None, max_age_hours: int = 24):
        """Initialize the memory system.

        Args:
            base_dir: Directory for storing results (defaults to system temp)
            max_age_hours: Auto-cleanup results older than this (default 24h)
        """
        self.base_dir = base_dir or Path(tempfile.gettempdir()) / "prt_llm_memory"
        self.base_dir.mkdir(exist_ok=True)
        self.max_age = timedelta(hours=max_age_hours)

        # Clean up old results on initialization
        self._cleanup_old_results()

    def save_result(self, data: Any, result_type: str = "query", description: str = None) -> str:
        """Save query results and return a reference ID.

        Args:
            data: The data to save (will be JSON serialized)
            result_type: Type of result (e.g., 'query', 'search', 'contacts')
            description: Human-readable description

        Returns:
            String ID that can be used to retrieve the result
        """
        import time

        logger.info(f"[MEMORY_SAVE_START] Type: {result_type}, description: '{description}'")

        # Data analysis
        data_count = 0

        if isinstance(data, list):
            data_count = len(data)
            # Estimate size for contacts with images
            if data and isinstance(data[0], dict) and "profile_image" in data[0]:
                total_image_size = sum(len(item.get("profile_image", b"")) for item in data)
                logger.debug(
                    f"[MEMORY_DATA_ANALYSIS] {data_count} contacts, {total_image_size/1024/1024:.1f}MB images"
                )

            # Check for binary data issues
            binary_items = 0
            for item in data[:10]:  # Sample first 10
                if isinstance(item, dict) and "profile_image" in item:
                    if not isinstance(item["profile_image"], bytes):
                        logger.warning(
                            f"[MEMORY_DATA_TYPE] profile_image is not bytes: {type(item['profile_image'])}"
                        )
                    else:
                        binary_items += 1

            logger.debug(
                f"[MEMORY_BINARY_CHECK] {binary_items}/{min(10, len(data))} items have bytes profile_image"
            )

        # Generate ID
        timestamp = datetime.now().strftime("%H%M%S")
        short_uuid = str(uuid.uuid4())[:8]
        result_id = f"{result_type}_{timestamp}_{short_uuid}"

        logger.debug(f"[MEMORY_ID_GENERATED] {result_id}")

        try:
            # Prepare metadata
            metadata = {
                "id": result_id,
                "type": result_type,
                "description": description or f"{result_type} result",
                "created_at": datetime.now().isoformat(),
                "data_count": data_count,
                "data": data,
            }

            # JSON serialization attempt
            logger.debug("[MEMORY_JSON_START] Attempting JSON serialization")
            json_start = time.time()

            result_file = self.base_dir / f"{result_id}.json"
            with open(result_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, default=str)

            json_time = time.time() - json_start
            file_size = result_file.stat().st_size

            logger.info(
                f"[MEMORY_SAVE_SUCCESS] {result_id} saved in {json_time:.3f}s, file size: {file_size/1024/1024:.1f}MB"
            )

            return result_id

        except Exception as e:
            logger.error(f"[MEMORY_SAVE_ERROR] Failed to save {result_id}: {e}", exc_info=True)

            # Additional debugging for JSON errors
            if "not JSON serializable" in str(e):
                logger.error("[MEMORY_JSON_ERROR] Analyzing non-serializable data...")
                for i, item in enumerate(data[:5]):  # Sample first 5
                    try:
                        json.dumps(item, default=str)
                    except Exception as item_error:
                        logger.error(f"[MEMORY_JSON_ITEM_ERROR] Item {i}: {item_error}")

            raise

    def load_result(self, result_id: str) -> Optional[Dict[str, Any]]:
        """Load previously saved results by ID.

        Args:
            result_id: The ID returned by save_result()

        Returns:
            Dictionary with metadata and data, or None if not found
        """
        import time

        logger.debug(f"[MEMORY_LOAD_START] Loading {result_id}")

        result_file = self.base_dir / f"{result_id}.json"

        if not result_file.exists():
            logger.error(f"[MEMORY_LOAD_MISSING] File not found: {result_file}")
            return None

        file_size = result_file.stat().st_size
        logger.debug(f"[MEMORY_LOAD_FILE] File size: {file_size/1024/1024:.1f}MB")

        try:
            load_start = time.time()

            with open(result_file, encoding="utf-8") as f:
                result = json.load(f)

            load_time = time.time() - load_start

            # Calculate data count safely - use stored value or calculate for lists
            data_count = result.get("data_count", 0)
            if data_count == 0 and isinstance(result.get("data"), list):
                data_count = len(result["data"])

            logger.info(
                f"[MEMORY_LOAD_SUCCESS] {result_id} loaded in {load_time:.3f}s, {data_count} items"
            )

            return result

        except Exception as e:
            logger.error(f"[MEMORY_LOAD_ERROR] Failed to load {result_id}: {e}", exc_info=True)
            return None

    def list_results(self, result_type: str = None) -> List[Dict[str, Any]]:
        """List available results, optionally filtered by type.

        Args:
            result_type: Optional filter by result type

        Returns:
            List of result metadata (without full data)
        """
        results = []

        for result_file in self.base_dir.glob("*.json"):
            try:
                with open(result_file, encoding="utf-8") as f:
                    metadata = json.load(f)

                # Filter by type if specified
                if result_type and metadata.get("type") != result_type:
                    continue

                # Return metadata without full data for listing
                summary = {
                    "id": metadata.get("id"),
                    "type": metadata.get("type"),
                    "description": metadata.get("description"),
                    "created_at": metadata.get("created_at"),
                    "data_count": metadata.get("data_count"),
                }
                results.append(summary)

            except Exception as e:
                logger.warning(f"[LLM_MEMORY] Failed to read {result_file}: {e}")
                continue

        # Sort by creation time, newest first
        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return results

    def delete_result(self, result_id: str) -> bool:
        """Delete a stored result.

        Args:
            result_id: The ID of the result to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        result_file = self.base_dir / f"{result_id}.json"

        if not result_file.exists():
            logger.warning(f"[LLM_MEMORY] Cannot delete, result not found: {result_id}")
            return False

        try:
            result_file.unlink()
            logger.info(f"[LLM_MEMORY] Deleted result: {result_id}")
            return True

        except Exception as e:
            logger.error(f"[LLM_MEMORY] Failed to delete result {result_id}: {e}")
            return False

    def _cleanup_old_results(self) -> int:
        """Remove results older than max_age.

        Returns:
            Number of results cleaned up
        """
        cleaned_count = 0
        cutoff_time = datetime.now() - self.max_age

        for result_file in self.base_dir.glob("*.json"):
            try:
                # Check file modification time
                file_time = datetime.fromtimestamp(result_file.stat().st_mtime)

                if file_time < cutoff_time:
                    result_file.unlink()
                    cleaned_count += 1
                    logger.debug(f"[LLM_MEMORY] Cleaned up old result: {result_file.name}")

            except Exception as e:
                logger.warning(f"[LLM_MEMORY] Failed to clean up {result_file}: {e}")
                continue

        if cleaned_count > 0:
            logger.info(f"[LLM_MEMORY] Cleaned up {cleaned_count} old results")

        return cleaned_count

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about stored results.

        Returns:
            Dictionary with counts and storage info
        """
        results = self.list_results()

        stats = {
            "total_results": len(results),
            "storage_path": str(self.base_dir),
            "max_age_hours": self.max_age.total_seconds() / 3600,
            "types": {},
        }

        # Count by type
        for result in results:
            result_type = result.get("type", "unknown")
            stats["types"][result_type] = stats["types"].get(result_type, 0) + 1

        return stats


# Global instance for use by LLM tools
llm_memory = LLMMemory()
