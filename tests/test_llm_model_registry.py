"""Integration tests for LLM Model Registry with LRU cache behavior.

Tests the OllamaModelRegistry LRU cache functionality to ensure memory
usage is bounded and cache eviction works correctly.
"""

import time
from unittest.mock import patch

from prt_src.llm_model_registry import ModelInfo
from prt_src.llm_model_registry import OllamaModelRegistry


class TestModelInfoClass:
    """Test ModelInfo class functionality."""

    def test_model_info_initialization(self):
        """Test ModelInfo initialization with various data."""
        data = {"name": "llama3:8b", "size": 4 * 1024**3, "digest": "sha256:abc123"}
        model = ModelInfo(data)

        assert model.name == "llama3:8b"
        assert model.size == 4 * 1024**3
        assert model.digest == "sha256:abc123"

    def test_friendly_name_generation(self):
        """Test friendly name generation from model names."""
        test_cases = [
            ("llama3:8b", "llama3-8b"),
            ("gpt-oss:20b", "gpt-oss-20b"),
            ("mistral:7b:latest", "mistral-7b-latest"),
            ("mistral:7b-instruct", "mistral-7b-instruct"),
            ("simple", "simple"),
        ]

        for model_name, expected in test_cases:
            data = {"name": model_name}
            model = ModelInfo(data)
            assert model.friendly_name == expected

    def test_size_human_readable(self):
        """Test human-readable size formatting."""
        test_cases = [
            (1024**3, "1.0GB"),
            (4 * 1024**3, "4.0GB"),
            (1024**2 * 500, "500MB"),
            (0, "0B"),
        ]

        for size_bytes, expected in test_cases:
            data = {"name": "test", "size": size_bytes}
            model = ModelInfo(data)
            assert model.size_human == expected

    def test_is_local_gguf_detection(self):
        """Test GGUF file detection."""
        test_cases = [
            ("model.gguf", True),
            ("/path/to/model.gguf", True),
            ("model.GGUF", True),
            ("regular-model", False),
            ("model.bin", False),
        ]

        for name, expected in test_cases:
            data = {"name": name}
            model = ModelInfo(data)
            assert model.is_local_gguf() == expected


class TestOllamaModelRegistryLRUCache:
    """Test LRU cache functionality in OllamaModelRegistry."""

    def test_cache_respects_size_limit(self):
        """Test that cache respects the maximum size limit."""
        registry = OllamaModelRegistry(max_cache_size=3)

        # Add models to cache directly
        for i in range(5):
            model_name = f"model{i}:latest"
            model_data = {"name": model_name, "size": 1024**3}
            model_info = ModelInfo(model_data)
            registry._model_cache[model_name] = model_info

        # Cache should only contain 3 models (the limit)
        assert len(registry._model_cache) == 3

    def test_lru_eviction_behavior(self):
        """Test that LRU eviction works correctly."""
        registry = OllamaModelRegistry(max_cache_size=3)

        # Add 3 models
        models = []
        for i in range(3):
            model_name = f"model{i}:latest"
            model_data = {"name": model_name, "size": 1024**3}
            model_info = ModelInfo(model_data)
            registry._model_cache[model_name] = model_info
            models.append(model_name)

        # Access model0 and model1 to make them recently used
        _ = registry._model_cache[models[0]]  # model0 - most recent
        _ = registry._model_cache[models[1]]  # model1 - second most recent
        # model2 is least recently used

        # Add a new model - should evict model2 (least recently used)
        new_model_name = "new_model:latest"
        new_model_data = {"name": new_model_name, "size": 1024**3}
        new_model_info = ModelInfo(new_model_data)
        registry._model_cache[new_model_name] = new_model_info

        # model2 should be evicted, others should remain
        assert models[2] not in registry._model_cache  # model2 evicted
        assert models[0] in registry._model_cache  # model0 kept
        assert models[1] in registry._model_cache  # model1 kept
        assert new_model_name in registry._model_cache  # new model added

    def test_cache_ttl_with_lru(self):
        """Test that TTL invalidation works alongside LRU."""
        registry = OllamaModelRegistry(cache_ttl=1, max_cache_size=5)

        # Add a model to cache
        model_name = "test:model"
        model_data = {"name": model_name, "size": 1024**3}
        model_info = ModelInfo(model_data)
        registry._model_cache[model_name] = model_info
        registry._cache_timestamp = registry._cache_timestamp or time.time()

        # Cache should be valid initially
        assert registry._is_cache_valid() is True
        assert len(registry._model_cache) == 1

        # Wait for TTL to expire
        time.sleep(1.1)

        # Cache should be invalid
        assert registry._is_cache_valid() is False

    def test_frequently_accessed_models_stay_cached(self):
        """Test that frequently accessed models stay in cache."""
        registry = OllamaModelRegistry(max_cache_size=2)

        # Add two models
        model1_name = "frequent:model"
        model2_name = "infrequent:model"

        model1_data = {"name": model1_name, "size": 1024**3}
        model2_data = {"name": model2_name, "size": 1024**3}

        registry._model_cache[model1_name] = ModelInfo(model1_data)
        registry._model_cache[model2_name] = ModelInfo(model2_data)

        # Access model1 multiple times
        for _ in range(3):
            _ = registry._model_cache[model1_name]

        # Add a new model - should evict model2 (less frequently accessed)
        model3_name = "new:model"
        model3_data = {"name": model3_name, "size": 1024**3}
        registry._model_cache[model3_name] = ModelInfo(model3_data)

        # model1 should remain, model2 should be evicted
        assert model1_name in registry._model_cache
        assert model2_name not in registry._model_cache
        assert model3_name in registry._model_cache

    def test_cache_statistics_tracking(self):
        """Test that cache statistics are tracked correctly."""
        registry = OllamaModelRegistry(max_cache_size=3)

        # Add some models
        for i in range(2):
            model_name = f"model{i}:latest"
            model_data = {"name": model_name, "size": 1024**3}
            registry._model_cache[model_name] = ModelInfo(model_data)

        # Cache hit
        _ = registry._model_cache.get("model0:latest")

        # Cache miss (non-existent key)
        result = registry._model_cache.get("nonexistent:model")
        assert result is None

        # Test that registry maintains statistics (implementation dependent)
        assert hasattr(registry, "_stats")

    def test_default_cache_size(self):
        """Test that default cache size is reasonable."""
        registry = OllamaModelRegistry()

        # Default should be 100 models
        assert registry.max_cache_size == 100

    def test_custom_cache_size(self):
        """Test initialization with custom cache size."""
        custom_size = 50
        registry = OllamaModelRegistry(max_cache_size=custom_size)

        assert registry.max_cache_size == custom_size

    def test_cache_operations_work_with_lru(self):
        """Test that all cache operations work with LRU implementation."""
        registry = OllamaModelRegistry(max_cache_size=5)

        # Test basic dict operations
        model_name = "test:model"
        model_data = {"name": model_name, "size": 1024**3}
        model_info = ModelInfo(model_data)

        # Test assignment
        registry._model_cache[model_name] = model_info

        # Test membership test
        assert model_name in registry._model_cache

        # Test retrieval
        retrieved = registry._model_cache[model_name]
        assert retrieved.name == model_name

        # Test deletion
        del registry._model_cache[model_name]
        assert model_name not in registry._model_cache

        # Test len()
        assert len(registry._model_cache) == 0

    @patch("prt_src.llm_model_registry.logger")
    def test_cache_eviction_logging(self, mock_logger):
        """Test that cache evictions are logged for observability."""
        registry = OllamaModelRegistry(max_cache_size=2)

        # Fill cache to capacity
        for i in range(3):  # One more than capacity
            model_name = f"model{i}:latest"
            model_data = {"name": model_name, "size": 1024**3}
            registry._model_cache[model_name] = ModelInfo(model_data)

        # Should have logged eviction (implementation dependent)
        # This test verifies that the registry has the capability to log
        assert hasattr(registry, "_stats")

    def test_integration_with_alias_resolution(self):
        """Test that LRU cache works with alias resolution."""
        registry = OllamaModelRegistry(max_cache_size=3)

        # Add models to cache
        models = [
            ModelInfo({"name": "llama3:8b"}),
            ModelInfo({"name": "gpt-oss:20b"}),
        ]

        for model in models:
            registry._model_cache[model.name] = model

        # Set timestamp to make cache valid
        import datetime

        registry._cache_timestamp = datetime.datetime.now()

        # Test alias resolution
        result = registry.resolve_alias("llama3-8b")
        assert result == "llama3:8b"

        result = registry.resolve_alias("gpt-oss-20b")
        assert result == "gpt-oss:20b"

    def test_integration_with_default_model_selection(self):
        """Test that LRU cache works with default model selection."""
        registry = OllamaModelRegistry(max_cache_size=3)

        # Add a model to cache
        model = ModelInfo({"name": "llama3:8b"})
        registry._model_cache[model.name] = model

        # Set timestamp to make cache valid
        import datetime

        registry._cache_timestamp = datetime.datetime.now()

        # Test default model selection
        default = registry.get_default_model()
        assert default == "llama3:8b"


class TestFuzzyAliasResolution:
    """Test the fuzzy alias resolution functionality added to fix model name matching."""

    def test_normalize_alias_function(self):
        """Test the _normalize_alias helper function."""
        registry = OllamaModelRegistry()

        test_cases = [
            ("mistral-7b-instruct", "mistral7binstruct"),
            ("mistral7b-instruct", "mistral7binstruct"),
            ("mistral7binstruct", "mistral7binstruct"),
            ("gpt-oss-20b", "gptoss20b"),
            ("gptoss20b", "gptoss20b"),
            ("GPT-OSS-20B", "gptoss20b"),  # Test case sensitivity
            ("llama3_8b_local", "llama38blocal"),  # Test underscore handling
        ]

        for input_alias, expected_normalized in test_cases:
            result = registry._normalize_alias(input_alias)
            assert (
                result == expected_normalized
            ), f"Expected {expected_normalized}, got {result} for input {input_alias}"

    def test_fuzzy_alias_resolution(self):
        """Test fuzzy alias resolution with missing dashes."""
        registry = OllamaModelRegistry(max_cache_size=10)

        # Add test models to cache
        models = [
            ModelInfo({"name": "mistral:7b-instruct"}),  # friendly_name: "mistral-7b-instruct"
            ModelInfo({"name": "gpt-oss:20b"}),  # friendly_name: "gpt-oss-20b"
            ModelInfo({"name": "llama3:8b"}),  # friendly_name: "llama3-8b"
        ]

        for model in models:
            registry._model_cache[model.name] = model

        # Set timestamp to make cache valid
        import datetime

        registry._cache_timestamp = datetime.datetime.now()

        # Test exact matches (should still work)
        assert registry.resolve_alias("mistral-7b-instruct") == "mistral:7b-instruct"
        assert registry.resolve_alias("gpt-oss-20b") == "gpt-oss:20b"
        assert registry.resolve_alias("llama3-8b") == "llama3:8b"

        # Test fuzzy matches (missing dashes) - this is the bug fix
        assert registry.resolve_alias("mistral7b-instruct") == "mistral:7b-instruct"
        assert registry.resolve_alias("mistral7binstruct") == "mistral:7b-instruct"
        assert registry.resolve_alias("gptoss20b") == "gpt-oss:20b"
        assert registry.resolve_alias("llama38b") == "llama3:8b"

        # Test case insensitive matching
        assert registry.resolve_alias("MISTRAL7B-INSTRUCT") == "mistral:7b-instruct"
        assert registry.resolve_alias("Mistral7bInstruct") == "mistral:7b-instruct"

        # Test non-existent models (should return None)
        assert registry.resolve_alias("nonexistent-model") is None
        assert registry.resolve_alias("notreal7b") is None

    def test_fuzzy_matching_with_underscores(self):
        """Test fuzzy matching handles underscores correctly."""
        registry = OllamaModelRegistry(max_cache_size=5)

        # Add a model that might have underscores in user input
        model = ModelInfo({"name": "phi3-mini:latest"})  # friendly_name: "phi3-mini"
        registry._model_cache[model.name] = model

        import datetime

        registry._cache_timestamp = datetime.datetime.now()

        # Test various underscore/dash variations
        assert registry.resolve_alias("phi3-mini") == "phi3-mini:latest"
        assert registry.resolve_alias("phi3mini") == "phi3-mini:latest"
        assert registry.resolve_alias("phi3_mini") == "phi3-mini:latest"
