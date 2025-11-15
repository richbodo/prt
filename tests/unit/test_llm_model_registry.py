"""Unit tests for LLM Model Registry.

These tests cover the OllamaModelRegistry class and ModelInfo class with mocked
HTTP calls to ensure fast, deterministic testing without external dependencies.
"""

import json
import time
from datetime import datetime
from datetime import timedelta
from unittest.mock import Mock
from unittest.mock import patch

import pytest
import requests

from prt_src.llm_model_registry import ModelInfo
from prt_src.llm_model_registry import OllamaModelRegistry


class TestModelInfo:
    """Test the ModelInfo class properties and methods."""

    def test_init_basic(self):
        """Test basic ModelInfo initialization."""
        data = {"name": "test-model", "size": 1024**3}
        model = ModelInfo(data)
        assert model.name == "test-model"
        assert model.size == 1024**3

    def test_init_with_all_fields(self):
        """Test ModelInfo initialization with all fields."""
        data = {
            "name": "test-model:latest",
            "size": 2 * 1024**3,
            "digest": "sha256:abc123",
            "details": {"family": "llama", "parameter_size": "7B", "quantization_level": "Q4_K_M"},
            "modified_at": "2024-01-15T10:30:00Z",
        }
        model = ModelInfo(data)
        assert model.name == "test-model:latest"
        assert model.size == 2 * 1024**3
        assert model.digest == "sha256:abc123"
        assert model.details == data["details"]
        assert model.modified_at == "2024-01-15T10:30:00Z"

    def test_friendly_name_basic(self):
        """Test friendly name generation from model names."""
        test_cases = [
            ("gpt-oss:20b", "gpt-oss-20b"),
            ("llama3:latest", "llama3"),
            ("mistral:7b", "mistral-7b"),
            ("phi3:3.8b-mini-instruct-4k-fp16", "phi3-3-8b-mini-instruct-4k-fp16"),
            ("simple-name", "simple-name"),
            ("model:with:multiple:colons", "model-with-multiple-colons"),
        ]

        for input_name, expected in test_cases:
            data = {"name": input_name}
            model = ModelInfo(data)
            assert model.friendly_name == expected, f"Input: {input_name}"

    def test_friendly_name_edge_cases(self):
        """Test friendly name generation with edge cases."""
        test_cases = [
            ("model:", "model"),  # Trailing colon
            (":model", "model"),  # Leading colon
            ("::model::", "model"),  # Multiple colons
            ("", ""),  # Empty string
            ("a:b:c:d:e", "a-b-c-d-e"),  # Many segments
        ]

        for input_name, expected in test_cases:
            data = {"name": input_name}
            model = ModelInfo(data)
            assert model.friendly_name == expected, f"Input: {input_name}"

    def test_size_human_formatting(self):
        """Test human-readable size formatting."""
        test_cases = [
            (0, "0B"),
            (512, "512B"),
            (1024, "1.0KB"),
            (1536, "1.5KB"),
            (1024**2, "1.0MB"),
            (1024**2 * 1.5, "1.5MB"),
            (1024**3, "1.0GB"),
            (1024**3 * 2.5, "2.5GB"),
            (1024**4, "1.0TB"),
            (1024**4 * 1.2, "1.2TB"),
        ]

        for size_bytes, expected in test_cases:
            data = {"name": "test", "size": size_bytes}
            model = ModelInfo(data)
            assert model.size_human == expected, f"Size: {size_bytes}"

    def test_size_human_none(self):
        """Test size formatting when size is None or missing."""
        data = {"name": "test"}
        model = ModelInfo(data)
        assert model.size_human == "Unknown"

        data = {"name": "test", "size": None}
        model = ModelInfo(data)
        assert model.size_human == "Unknown"

    def test_is_local_gguf_detection(self):
        """Test detection of local GGUF models."""
        test_cases = [
            ("model.gguf", True),
            ("path/to/model.gguf", True),
            ("/absolute/path/model.gguf", True),
            ("model.GGUF", True),  # Case insensitive
            ("model.gguf.backup", False),
            ("gguf-model", False),
            ("regular-model", False),
            ("model.bin", False),
        ]

        for name, expected in test_cases:
            data = {"name": name}
            model = ModelInfo(data)
            assert model.is_local_gguf() == expected, f"Name: {name}"

    def test_get_description_with_details(self):
        """Test description generation with model details."""
        data = {
            "name": "llama3:8b",
            "details": {"family": "llama", "parameter_size": "8B", "quantization_level": "Q4_K_M"},
        }
        model = ModelInfo(data)
        description = model.get_description()
        assert "llama" in description.lower()
        assert "8B" in description
        assert "Q4_K_M" in description

    def test_get_description_without_details(self):
        """Test description generation without model details."""
        data = {"name": "simple-model"}
        model = ModelInfo(data)
        description = model.get_description()
        assert description == "simple-model"


class TestOllamaModelRegistryAvailability:
    """Test the is_available() method."""

    @patch("requests.get")
    def test_is_available_success(self, mock_get):
        """Test is_available returns True when Ollama responds."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        registry = OllamaModelRegistry()
        assert registry.is_available() is True

        mock_get.assert_called_once_with("http://localhost:11434/api/tags", timeout=2)

    @patch("requests.get")
    def test_is_available_connection_error(self, mock_get):
        """Test is_available returns False on connection error."""
        mock_get.side_effect = requests.ConnectionError("Connection refused")

        registry = OllamaModelRegistry()
        assert registry.is_available() is False

    @patch("requests.get")
    def test_is_available_timeout(self, mock_get):
        """Test is_available returns False on timeout."""
        mock_get.side_effect = requests.Timeout("Request timed out")

        registry = OllamaModelRegistry()
        assert registry.is_available() is False

    @patch("requests.get")
    def test_is_available_non_200_status(self, mock_get):
        """Test is_available returns False on non-200 status."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        registry = OllamaModelRegistry()
        assert registry.is_available() is False


class TestOllamaModelRegistryListModels:
    """Test the list_models() method."""

    @pytest.fixture
    def mock_models_response(self):
        """Fixture providing mock models API response."""
        return {
            "models": [
                {
                    "name": "llama3:8b",
                    "size": 4 * 1024**3,
                    "digest": "sha256:abc123",
                    "modified_at": "2024-01-15T10:30:00Z",
                },
                {
                    "name": "gpt-oss:20b",
                    "size": 12 * 1024**3,
                    "digest": "sha256:def456",
                    "modified_at": "2024-01-14T15:45:00Z",
                },
            ]
        }

    @patch("requests.get")
    def test_list_models_success(self, mock_get, mock_models_response):
        """Test successful model listing."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_models_response
        mock_get.return_value = mock_response

        registry = OllamaModelRegistry()
        models = registry.list_models()

        assert len(models) == 2
        assert models[0].name == "llama3:8b"
        assert models[0].friendly_name == "llama3-8b"
        assert models[1].name == "gpt-oss:20b"
        assert models[1].friendly_name == "gpt-oss-20b"

    @patch("requests.get")
    def test_list_models_caching(self, mock_get, mock_models_response):
        """Test that list_models caches results."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_models_response
        mock_get.return_value = mock_response

        registry = OllamaModelRegistry()

        # First call
        models1 = registry.list_models()
        assert len(models1) == 2

        # Second call should use cache
        models2 = registry.list_models()
        assert len(models2) == 2

        # Should only have made one HTTP request
        assert mock_get.call_count == 1

    @patch("requests.get")
    def test_list_models_cache_expiry(self, mock_get, mock_models_response):
        """Test that cache expires after TTL."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_models_response
        mock_get.return_value = mock_response

        registry = OllamaModelRegistry(cache_ttl=1)  # 1 second TTL

        # First call
        models1 = registry.list_models()
        assert len(models1) == 2

        # Wait for cache to expire
        time.sleep(1.1)

        # Second call should refresh cache
        models2 = registry.list_models()
        assert len(models2) == 2

        # Should have made two HTTP requests
        assert mock_get.call_count == 2

    @patch("requests.get")
    def test_list_models_force_refresh(self, mock_get, mock_models_response):
        """Test force refresh bypasses cache."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_models_response
        mock_get.return_value = mock_response

        registry = OllamaModelRegistry()

        # First call
        models1 = registry.list_models()
        assert len(models1) == 2

        # Force refresh should bypass cache
        models2 = registry.list_models(force_refresh=True)
        assert len(models2) == 2

        # Should have made two HTTP requests
        assert mock_get.call_count == 2

    @patch("requests.get")
    def test_list_models_connection_error(self, mock_get):
        """Test list_models returns empty list on connection error."""
        mock_get.side_effect = requests.ConnectionError("Connection refused")

        registry = OllamaModelRegistry()
        models = registry.list_models()

        assert models == []

    @patch("requests.get")
    def test_list_models_timeout(self, mock_get):
        """Test list_models returns empty list on timeout."""
        mock_get.side_effect = requests.Timeout("Request timed out")

        registry = OllamaModelRegistry()
        models = registry.list_models()

        assert models == []

    @patch("requests.get")
    def test_list_models_invalid_json(self, mock_get):
        """Test list_models handles invalid JSON gracefully."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_get.return_value = mock_response

        registry = OllamaModelRegistry()
        models = registry.list_models()

        assert models == []


class TestOllamaModelRegistryGetModelInfo:
    """Test the get_model_info() method."""

    @pytest.fixture
    def mock_show_response(self):
        """Fixture providing mock model show API response."""
        return {
            "modelfile": "FROM llama3:8b\nSYSTEM You are a helpful assistant.",
            "parameters": {"temperature": 0.7, "top_p": 0.9},
            "template": "{{ .System }}{{ .Prompt }}",
            "details": {"family": "llama", "parameter_size": "8B", "quantization_level": "Q4_K_M"},
        }

    @patch("requests.post")
    def test_get_model_info_success(self, mock_post, mock_show_response):
        """Test successful model info retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_show_response
        mock_post.return_value = mock_response

        registry = OllamaModelRegistry()
        info = registry.get_model_info("llama3:8b")

        assert info is not None
        assert info.name == "llama3:8b"
        assert "llama3:8b" in registry._model_cache

    @patch("requests.post")
    def test_get_model_info_caching(self, mock_post, mock_show_response):
        """Test that get_model_info caches results."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_show_response
        mock_post.return_value = mock_response

        registry = OllamaModelRegistry()

        # First call
        info1 = registry.get_model_info("llama3:8b")
        assert info1 is not None

        # Second call should use cache
        info2 = registry.get_model_info("llama3:8b")
        assert info2 is not None

        # Should only have made one HTTP request
        assert mock_post.call_count == 1

    @patch("requests.post")
    def test_get_model_info_force_refresh(self, mock_post, mock_show_response):
        """Test force refresh bypasses cache."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_show_response
        mock_post.return_value = mock_response

        registry = OllamaModelRegistry()

        # First call
        info1 = registry.get_model_info("llama3:8b")
        assert info1 is not None

        # Force refresh should bypass cache
        info2 = registry.get_model_info("llama3:8b", force_refresh=True)
        assert info2 is not None

        # Should have made two HTTP requests
        assert mock_post.call_count == 2

    @patch("requests.post")
    def test_get_model_info_404_error(self, mock_post):
        """Test get_model_info returns None on 404."""
        mock_response = Mock()
        mock_response.status_code = 404

        # Create HTTPError with response attribute
        http_error = requests.HTTPError("Not found")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_post.return_value = mock_response

        registry = OllamaModelRegistry()
        info = registry.get_model_info("nonexistent:model")

        assert info is None

    @patch("requests.post")
    def test_get_model_info_connection_error(self, mock_post):
        """Test get_model_info returns None on connection error."""
        mock_post.side_effect = requests.ConnectionError("Connection refused")

        registry = OllamaModelRegistry()
        info = registry.get_model_info("llama3:8b")

        assert info is None

    @patch("requests.post")
    def test_get_model_info_http_error(self, mock_post):
        """Test get_model_info returns None on HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 500

        # Create HTTPError with response attribute
        http_error = requests.HTTPError("Server error")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_post.return_value = mock_response

        registry = OllamaModelRegistry()
        info = registry.get_model_info("llama3:8b")

        assert info is None


class TestOllamaModelRegistryResolveAlias:
    """Test the resolve_alias() method."""

    @pytest.fixture
    def registry_with_models(self):
        """Fixture providing registry with cached models."""
        registry = OllamaModelRegistry()
        # Mock cached models
        model1 = ModelInfo({"name": "llama3:8b"})
        model2 = ModelInfo({"name": "gpt-oss:20b"})
        registry._model_cache["llama3:8b"] = model1
        registry._model_cache["gpt-oss:20b"] = model2
        registry._cache_timestamp = datetime.now()
        return registry

    def test_resolve_alias_exact_match(self, registry_with_models):
        """Test resolve_alias with exact alias match."""
        result = registry_with_models.resolve_alias("llama3-8b")
        assert result == "llama3:8b"

    def test_resolve_alias_full_name(self, registry_with_models):
        """Test resolve_alias with full model name."""
        result = registry_with_models.resolve_alias("llama3:8b")
        assert result == "llama3:8b"

    def test_resolve_alias_not_found(self, registry_with_models):
        """Test resolve_alias returns None when not found."""
        result = registry_with_models.resolve_alias("nonexistent-model")
        assert result is None

    @patch.object(OllamaModelRegistry, "list_models")
    def test_resolve_alias_triggers_cache(self, mock_list_models):
        """Test resolve_alias triggers model list when cache empty."""
        mock_list_models.return_value = [ModelInfo({"name": "llama3:8b"})]

        registry = OllamaModelRegistry()
        result = registry.resolve_alias("llama3-8b")

        mock_list_models.assert_called_once()
        assert result == "llama3:8b"


class TestOllamaModelRegistryHelperMethods:
    """Test helper methods like get_aliases() and get_default_model()."""

    @pytest.fixture
    def registry_with_models(self):
        """Fixture providing registry with cached models."""
        registry = OllamaModelRegistry()
        model1 = ModelInfo({"name": "llama3:8b"})
        model2 = ModelInfo({"name": "gpt-oss:20b"})
        model3 = ModelInfo({"name": "mistral:7b"})
        registry._model_cache["llama3:8b"] = model1
        registry._model_cache["gpt-oss:20b"] = model2
        registry._model_cache["mistral:7b"] = model3
        registry._cache_timestamp = datetime.now()
        return registry

    def test_get_aliases(self, registry_with_models):
        """Test get_aliases returns correct mapping."""
        aliases = registry_with_models.get_aliases()

        expected = {
            "llama3-8b": "llama3:8b",
            "gpt-oss-20b": "gpt-oss:20b",
            "mistral-7b": "mistral:7b",
        }
        assert aliases == expected

    def test_get_default_model_first_available(self, registry_with_models):
        """Test get_default_model returns first model when available."""
        default = registry_with_models.get_default_model()

        # Should return one of the cached models
        cached_models = list(registry_with_models._model_cache.keys())
        assert default in cached_models

    @patch.object(OllamaModelRegistry, "list_models")
    def test_get_default_model_empty_cache(self, mock_list_models):
        """Test get_default_model returns None when no models."""
        mock_list_models.return_value = []

        registry = OllamaModelRegistry()
        default = registry.get_default_model()

        assert default is None

    @patch.object(OllamaModelRegistry, "list_models")
    def test_get_default_model_triggers_list(self, mock_list_models):
        """Test get_default_model triggers model list when cache empty."""
        mock_list_models.return_value = [ModelInfo({"name": "llama3:8b"})]

        registry = OllamaModelRegistry()
        default = registry.get_default_model()

        mock_list_models.assert_called_once()
        assert default == "llama3:8b"


class TestOllamaModelRegistryCacheBehavior:
    """Test cache behavior and TTL logic."""

    def test_cache_initialization(self):
        """Test cache is properly initialized."""
        registry = OllamaModelRegistry()
        assert len(registry._model_cache) == 0
        assert registry._cache_timestamp is None

    def test_cache_ttl_validation_fresh(self):
        """Test cache TTL validation for fresh cache."""
        registry = OllamaModelRegistry(cache_ttl=300)
        registry._cache_timestamp = datetime.now()

        assert registry._is_cache_valid() is True

    def test_cache_ttl_validation_expired(self):
        """Test cache TTL validation for expired cache."""
        registry = OllamaModelRegistry(cache_ttl=300)
        registry._cache_timestamp = datetime.now() - timedelta(seconds=400)

        assert registry._is_cache_valid() is False

    def test_cache_ttl_validation_no_timestamp(self):
        """Test cache TTL validation with no timestamp."""
        registry = OllamaModelRegistry()
        assert registry._is_cache_valid() is False

    @patch("requests.get")
    def test_cache_population(self, mock_get):
        """Test cache gets populated after list_models call."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": [{"name": "llama3:8b", "size": 1024**3}]}
        mock_get.return_value = mock_response

        registry = OllamaModelRegistry()
        assert len(registry._model_cache) == 0

        registry.list_models()

        assert len(registry._model_cache) == 1
        assert "llama3:8b" in registry._model_cache
        assert registry._cache_timestamp is not None

    @patch("requests.get")
    def test_cache_force_refresh_clears_timestamp(self, mock_get):
        """Test force refresh updates cache timestamp."""
        # Mock a successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": []}
        mock_get.return_value = mock_response

        registry = OllamaModelRegistry()
        old_timestamp = datetime.now() - timedelta(seconds=100)
        registry._cache_timestamp = old_timestamp

        registry.list_models(force_refresh=True)

        # Timestamp should be refreshed (newer than the old one)
        assert registry._cache_timestamp is not None
        assert registry._cache_timestamp > old_timestamp


class TestOllamaModelRegistryErrorHandling:
    """Test error handling and edge cases."""

    def test_custom_base_url(self):
        """Test initialization with custom base URL."""
        custom_url = "http://custom-ollama:11434"
        registry = OllamaModelRegistry(base_url=custom_url)
        assert registry.base_url == custom_url

    def test_custom_cache_ttl(self):
        """Test initialization with custom cache TTL."""
        registry = OllamaModelRegistry(cache_ttl=600)
        assert registry.cache_ttl == 600

    def test_url_normalization(self):
        """Test base URL normalization removes trailing slash."""
        registry = OllamaModelRegistry(base_url="http://localhost:11434/")
        assert registry.base_url == "http://localhost:11434"

    @patch("requests.get")
    def test_malformed_models_response(self, mock_get):
        """Test handling of malformed models API response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"invalid": "response"}
        mock_get.return_value = mock_response

        registry = OllamaModelRegistry()
        models = registry.list_models()

        assert models == []

    @patch("requests.get")
    def test_missing_models_field(self, mock_get):
        """Test handling of response missing 'models' field."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response

        registry = OllamaModelRegistry()
        models = registry.list_models()

        assert models == []

    def test_model_info_missing_fields(self):
        """Test ModelInfo handles missing fields gracefully."""
        minimal_data = {"name": "test-model"}
        model = ModelInfo(minimal_data)

        assert model.name == "test-model"
        assert model.size is None
        assert model.size_human == "Unknown"
        assert model.digest is None
        assert model.details is None
        assert model.modified_at is None

    @patch("prt_src.llm_model_registry.logger")
    def test_logging_on_errors(self, mock_logger):
        """Test that errors are properly logged."""
        with patch("requests.get") as mock_get:
            mock_get.side_effect = requests.ConnectionError("Connection failed")

            registry = OllamaModelRegistry()
            registry.list_models()

            # Should log the error
            mock_logger.debug.assert_called()
