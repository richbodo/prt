"""
Ollama Model Registry for PRT

This module provides model discovery and management via Ollama's REST API.
It discovers available models, generates friendly aliases, and provides model information.
"""

import re
from datetime import datetime
from datetime import timedelta
from typing import Any

import requests
from lru import LRU

from .logging_config import get_logger

logger = get_logger(__name__)


class ModelInfo:
    """Information about a discovered model."""

    def __init__(self, data: dict[str, Any]):
        """Initialize from Ollama API response.

        Args:
            data: Model data from /api/tags or /api/show
        """
        self.name = data.get("name", "")
        self.model = data.get("model", self.name)
        self.size = data.get("size")
        self.modified_at = data.get("modified_at")
        self.digest = data.get("digest")
        self.details = data.get("details")

        # Extended info from /api/show
        self.modelfile = data.get("modelfile", "")
        self.template = data.get("template", "")
        self.system = data.get("system", "")
        self.parameters = data.get("parameters", "")

    @property
    def friendly_name(self) -> str:
        """Generate a friendly alias from model name.

        Examples:
            gpt-oss:20b -> gpt-oss-20b
            llama3-8b-local:latest -> llama3-8b-local
            mistral:latest -> mistral
            mistral:7b:latest -> mistral-7b-latest
        """
        # Special case: if name ends with :latest and has no other colons, remove :latest
        if self.name.endswith(":latest") and self.name.count(":") == 1:
            name = self.name[:-7]  # Remove ":latest" (7 characters)
        else:
            # Otherwise, replace all : with -
            name = self.name.replace(":", "-")

        # Replace dots with dashes for consistency (e.g., "3.8b" -> "3-8b")
        name = name.replace(".", "-")

        # Clean up leading/trailing dashes and multiple consecutive dashes
        name = name.strip("-")
        name = re.sub(r"-+", "-", name)

        return name

    @property
    def size_human(self) -> str:
        """Human-readable size string."""
        if self.size is None:
            return "Unknown"
        if self.size == 0:
            return "0B"

        tb = self.size / (1024**4)
        if tb >= 1:
            # Always show 1 decimal place for TB
            return f"{tb:.1f}TB"

        gb = self.size / (1024**3)
        if gb >= 1:
            # Always show 1 decimal place for GB
            return f"{gb:.1f}GB"

        mb = self.size / (1024**2)
        if mb >= 1:
            # Show as integer if whole number, otherwise 1 decimal place for MB
            return f"{int(mb)}MB" if mb == int(mb) else f"{mb:.1f}MB"

        kb = self.size / 1024
        if kb >= 1:
            # Show as integer if whole number, otherwise 1 decimal place for KB
            return f"{int(kb)}KB" if kb == int(kb) else f"{kb:.1f}KB"

        return f"{self.size}B"

    def is_local_gguf(self) -> bool:
        """Check if this model was created from a local .gguf file.

        Returns:
            True if model name ends with .gguf or modelfile contains FROM with a .gguf path
        """
        # Check if the model name itself ends with .gguf
        if self.name.lower().endswith(".gguf"):
            return True

        # Check if modelfile indicates it was created from a .gguf file
        if self.modelfile:
            # Look for "FROM ./*.gguf" or "FROM /path/to/*.gguf"
            from_match = re.search(r"FROM\s+([^\s]+\.gguf)", self.modelfile, re.IGNORECASE)
            return from_match is not None

        return False

    def get_description(self) -> str:
        """Generate a description for this model."""
        if self.details:
            # Build description from details
            parts = []
            if "family" in self.details:
                parts.append(self.details["family"])
            if "parameter_size" in self.details:
                parts.append(self.details["parameter_size"])
            if "quantization_level" in self.details:
                parts.append(self.details["quantization_level"])

            if parts:
                return " ".join(parts)

        # Fallback to model name if no details
        return self.name


class OllamaModelRegistry:
    """Discovers and manages Ollama models via REST API."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        cache_ttl: int = 300,
        max_cache_size: int = 100,
    ):
        """Initialize the model registry.

        Args:
            base_url: Ollama API base URL
            cache_ttl: Cache time-to-live in seconds (default: 5 minutes)
            max_cache_size: Maximum number of models to cache (default: 100)
        """
        self.base_url = base_url.rstrip("/")
        self.cache_ttl = cache_ttl
        self.max_cache_size = max_cache_size
        self._model_cache = LRU(max_cache_size)
        self._cache_timestamp: datetime | None = None

        # Cache statistics
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "refreshes": 0,
        }
        self._operation_count = 0

    def is_available(self) -> bool:
        """Check if Ollama is running and accessible.

        Returns:
            True if Ollama API is reachable
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Ollama not available: {e}")
            return False

    def _is_cache_valid(self) -> bool:
        """Check if the model cache is still valid.

        Returns:
            True if cache exists and hasn't expired
        """
        if not self._cache_timestamp:
            return False

        age = datetime.now() - self._cache_timestamp
        return age < timedelta(seconds=self.cache_ttl)

    def list_models(self, force_refresh: bool = False) -> list[ModelInfo]:
        """List all available models from Ollama.

        Args:
            force_refresh: Force cache refresh even if valid

        Returns:
            List of ModelInfo objects
        """
        # Return cached results if valid
        if not force_refresh and self._is_cache_valid():
            self._stats["hits"] += 1
            logger.debug(f"Returning {len(self._model_cache)} models from cache")
            # Return cached models (order may not be preserved from original response)
            return list(self._model_cache.values())

        self._stats["refreshes"] += 1
        logger.info("Fetching model list from Ollama API...")

        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()

            data = response.json()
            models = data.get("models", [])

            # Clear cache and rebuild
            self._model_cache.clear()
            model_list = []

            for model_data in models:
                model_info = ModelInfo(model_data)
                self._model_cache[model_info.name] = model_info
                model_list.append(model_info)
                logger.debug(f"Discovered model: {model_info.name} ({model_info.size_human})")

            self._cache_timestamp = datetime.now()
            logger.info(f"Discovered {len(self._model_cache)} models from Ollama")

            # Log statistics periodically
            self._operation_count += 1
            if self._operation_count % 100 == 0:
                logger.debug(
                    f"Cache stats: {self._stats}, current size: {len(self._model_cache)}/{self.max_cache_size}"
                )

            return model_list

        except requests.exceptions.ConnectionError:
            logger.warning("Cannot connect to Ollama - is it running?")
            return []
        except requests.exceptions.Timeout:
            logger.warning("Ollama API request timed out")
            return []
        except Exception as e:
            logger.error(f"Error fetching models from Ollama: {e}")
            return []

    def get_model_info(self, model_name: str, force_refresh: bool = False) -> ModelInfo | None:
        """Get detailed information about a specific model.

        Args:
            model_name: Name of the model (can be alias or full name)
            force_refresh: Force fresh data from API

        Returns:
            ModelInfo with extended details, or None if not found
        """
        # Check cache first
        if not force_refresh and model_name in self._model_cache:
            cached = self._model_cache[model_name]
            # If we already have extended info, return it
            if cached.modelfile:
                self._stats["hits"] += 1
                logger.debug(f"Returning cached extended info for {model_name}")
                return cached

        self._stats["misses"] += 1
        logger.debug(f"Fetching extended info for model: {model_name}")

        try:
            response = requests.post(
                f"{self.base_url}/api/show",
                json={"name": model_name},
                timeout=10,
            )
            response.raise_for_status()

            data = response.json()

            # Track cache size before insertion to detect evictions
            cache_size_before = len(self._model_cache)

            # Merge with existing cache entry if present
            if model_name in self._model_cache:
                # Update existing entry with extended info
                existing = self._model_cache[model_name]
                existing.modelfile = data.get("modelfile", "")
                existing.template = data.get("template", "")
                existing.system = data.get("system", "")
                existing.parameters = data.get("parameters", "")
                model_info = existing
            else:
                # Create new entry
                model_info = ModelInfo(data)
                model_info.name = model_name
                self._model_cache[model_name] = model_info

                # Check if an eviction occurred
                cache_size_after = len(self._model_cache)
                if (
                    cache_size_before >= self.max_cache_size
                    and cache_size_after == self.max_cache_size
                ):
                    self._stats["evictions"] += 1
                    logger.debug(
                        f"Cache at max size ({self.max_cache_size}), LRU eviction occurred"
                    )

            logger.debug(f"Retrieved extended info for {model_name}")

            # Log statistics periodically
            self._operation_count += 1
            if self._operation_count % 100 == 0:
                logger.debug(
                    f"Cache stats: {self._stats}, current size: {len(self._model_cache)}/{self.max_cache_size}"
                )

            return model_info

        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code == 404:
                logger.warning(f"Model not found: {model_name}")
            else:
                logger.error(f"HTTP error getting model info: {e}")
            return None
        except requests.exceptions.ConnectionError:
            logger.warning("Cannot connect to Ollama")
            return None
        except Exception as e:
            logger.error(f"Error getting model info for {model_name}: {e}")
            return None

    def resolve_alias(self, alias: str) -> str | None:
        """Resolve a friendly alias to the full model name.

        Args:
            alias: Friendly alias (e.g., "gpt-oss-20b", "llama3-8b-local")

        Returns:
            Full model name, or None if not found
        """
        # First check if it's already a full model name
        if alias in self._model_cache:
            return alias

        # Check if it matches any friendly names exactly
        models = self.list_models()
        for model in models:
            if model.friendly_name == alias:
                return model.name

        # If no exact match, try fuzzy matching for common variations
        # Normalize the input alias by handling dash variations
        normalized_alias = self._normalize_alias(alias)

        for model in models:
            normalized_friendly = self._normalize_alias(model.friendly_name)
            if normalized_friendly == normalized_alias:
                logger.info(
                    f"Found fuzzy match: '{alias}' -> '{model.friendly_name}' -> '{model.name}'"
                )
                return model.name

        # Not found
        logger.debug(f"Alias '{alias}' not found in registry")
        return None

    def _normalize_alias(self, alias: str) -> str:
        """Normalize an alias for fuzzy matching.

        Removes dashes and converts to lowercase for comparison.
        Examples:
            'mistral-7b-instruct' -> 'mistral7binstruct'
            'mistral7b-instruct' -> 'mistral7binstruct'
            'mistral7binstruct' -> 'mistral7binstruct'
        """
        return alias.lower().replace("-", "").replace("_", "")

    def get_aliases(self) -> dict[str, str]:
        """Get all available aliases and their full names.

        Returns:
            Dictionary mapping friendly aliases to full model names
        """
        models = self.list_models()
        return {model.friendly_name: model.name for model in models}

    def get_default_model(self) -> str | None:
        """Get a sensible default model.

        Priority:
        1. gpt-oss:20b (preferred default)
        2. Any officially supported model
        3. Any available model

        Returns:
            Model name, or None if no models available
        """
        from prt_src.llm_supported_models import get_supported_models

        models = self.list_models()
        if not models:
            return None

        model_names = {model.name for model in models}

        # Priority 1: Check for gpt-oss:20b specifically
        if "gpt-oss:20b" in model_names:
            logger.debug("Found preferred default model: gpt-oss:20b")
            return "gpt-oss:20b"

        # Priority 2: Look for any officially supported model
        supported_models = get_supported_models()
        for model_name in supported_models:
            if model_name in model_names:
                logger.debug(f"Found supported default model: {model_name}")
                return model_name

        # Priority 3: Return first available model
        logger.debug(f"Using first available model: {models[0].name}")
        return models[0].name
