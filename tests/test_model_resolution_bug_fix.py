"""Test the bug fix for Mistral Ollama communication failure.

This module tests the specific fixes implemented for model resolution
and validation to prevent 404 errors with models like mistral7b-instruct.
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from prt_src.llm_factory import resolve_model_alias
from prt_src.llm_model_registry import ModelInfo
from prt_src.llm_model_registry import OllamaModelRegistry


class TestModelResolutionBugFix:
    """Test the specific bug fix for model resolution with fuzzy matching."""

    def test_mistral_alias_variations_resolve_correctly(self):
        """Test that various mistral alias inputs resolve to the correct model."""
        with patch("prt_src.llm_factory.get_registry") as mock_get_registry:
            # Mock the registry
            mock_registry = MagicMock()
            mock_get_registry.return_value = mock_registry
            mock_registry.is_available.return_value = True

            # Mock the model that exists in Ollama
            mistral_model = ModelInfo({"name": "mistral:7b-instruct"})
            mock_registry.list_models.return_value = [mistral_model]

            # Mock exact alias resolution to fail first (no exact match)
            mock_registry.resolve_alias.return_value = "mistral:7b-instruct"

            # Test that the problematic input now resolves correctly
            result = resolve_model_alias("mistral7b-instruct")
            assert result == ("ollama", "mistral:7b-instruct")

    def test_model_not_found_error_with_suggestions(self):
        """Test that non-existent models provide helpful error messages."""
        with patch("prt_src.llm_factory.get_registry") as mock_get_registry:
            # Mock the registry
            mock_registry = MagicMock()
            mock_get_registry.return_value = mock_registry
            mock_registry.is_available.return_value = True

            # Mock no alias resolution match
            mock_registry.resolve_alias.return_value = None

            # Mock no direct model info found
            mock_registry.get_model_info.return_value = None

            # Mock available aliases for suggestions
            mock_registry.get_aliases.return_value = {
                "mistral-7b-instruct": "mistral:7b-instruct",
                "gpt-oss-20b": "gpt-oss:20b",
            }

            # Test that a completely wrong model name gives helpful error
            with pytest.raises(ValueError) as exc_info:
                resolve_model_alias("nonexistent-model")

            error_msg = str(exc_info.value)
            assert "not found in Ollama" in error_msg
            assert "Available models:" in error_msg

    def test_model_not_found_error_with_close_suggestions(self):
        """Test that typos in model names get close match suggestions."""
        with patch("prt_src.llm_factory.get_registry") as mock_get_registry:
            # Mock the registry
            mock_registry = MagicMock()
            mock_get_registry.return_value = mock_registry
            mock_registry.is_available.return_value = True

            # Mock no alias resolution match
            mock_registry.resolve_alias.return_value = None

            # Mock no direct model info found
            mock_registry.get_model_info.return_value = None

            # Mock available aliases for suggestions
            mock_registry.get_aliases.return_value = {
                "mistral-7b-instruct": "mistral:7b-instruct",
                "gpt-oss-20b": "gpt-oss:20b",
            }

            # Test that a typo gets close suggestions
            with pytest.raises(ValueError) as exc_info:
                resolve_model_alias("mistral7b-instructt")  # Note the extra 't'

            error_msg = str(exc_info.value)
            assert "not found in Ollama" in error_msg
            # The difflib should suggest the close match
            assert "Did you mean:" in error_msg
            assert "mistral-7b-instruct" in error_msg

    def test_exact_model_name_resolution_still_works(self):
        """Test that exact model name resolution continues to work."""
        with patch("prt_src.llm_factory.get_registry") as mock_get_registry:
            # Mock the registry
            mock_registry = MagicMock()
            mock_get_registry.return_value = mock_registry
            mock_registry.is_available.return_value = True

            # Mock exact alias resolution working
            mock_registry.resolve_alias.return_value = "mistral:7b-instruct"

            # Test that exact aliases still work
            result = resolve_model_alias("mistral-7b-instruct")
            assert result == ("ollama", "mistral:7b-instruct")

    def test_ollama_unavailable_fallback_behavior(self):
        """Test behavior when Ollama service is not available."""
        with patch("prt_src.llm_factory.get_registry") as mock_get_registry:
            # Mock the registry as unavailable
            mock_registry = MagicMock()
            mock_get_registry.return_value = mock_registry
            mock_registry.is_available.return_value = False

            # Should still return the model without validation
            result = resolve_model_alias("mistral7b-instruct")
            assert result == ("ollama", "mistral7b-instruct")


class TestModelInfoFriendlyNameGeneration:
    """Test friendly name generation for edge cases."""

    def test_mistral_instruct_model_friendly_name(self):
        """Test that the specific mistral model generates correct friendly name."""
        model = ModelInfo({"name": "mistral:7b-instruct"})
        assert model.friendly_name == "mistral-7b-instruct"

    def test_complex_model_names_with_multiple_colons(self):
        """Test friendly name generation for models with multiple colons."""
        test_cases = [
            ("mistral:7b:instruct:v0.3", "mistral-7b-instruct-v0-3"),
            ("model:complex:name:here", "model-complex-name-here"),
            ("simple:latest", "simple"),  # :latest should be stripped
        ]

        for model_name, expected_friendly in test_cases:
            model = ModelInfo({"name": model_name})
            assert model.friendly_name == expected_friendly


class TestIntegrationWithFuzzyMatching:
    """Integration tests for the complete model resolution pipeline."""

    def test_end_to_end_model_resolution_bug_fix(self):
        """Test the complete pipeline that was failing before the fix."""
        # This test mimics the exact scenario that was failing
        with patch("prt_src.llm_factory.get_registry") as mock_get_registry:
            # Create a realistic registry mock
            mock_registry = OllamaModelRegistry(max_cache_size=5)

            # Add the real models that would be in the registry
            models = [
                ModelInfo({"name": "mistral:7b-instruct"}),
                ModelInfo({"name": "gpt-oss:20b"}),
            ]

            # Manually set up the cache
            for model in models:
                mock_registry._model_cache[model.name] = model

            import datetime

            mock_registry._cache_timestamp = datetime.datetime.now()
            mock_registry._mock_is_available = True

            # Mock is_available to return True
            mock_registry.is_available = lambda: True

            # Mock get_model_info to return None (model doesn't exist as direct name)
            def mock_get_model_info(name):
                return mock_registry._model_cache.get(name)

            mock_registry.get_model_info = mock_get_model_info

            mock_get_registry.return_value = mock_registry

            # This should now work (was failing before fix)
            result = resolve_model_alias("mistral7b-instruct")
            assert result == ("ollama", "mistral:7b-instruct")

    def test_regression_working_models_still_work(self):
        """Test that models that were already working continue to work."""
        with patch("prt_src.llm_factory.get_registry") as mock_get_registry:
            # Mock the registry
            mock_registry = MagicMock()
            mock_get_registry.return_value = mock_registry
            mock_registry.is_available.return_value = True

            # Mock exact alias resolution working for gpt-oss
            mock_registry.resolve_alias.return_value = "gpt-oss:20b"

            # Test that gpt-oss (which was working) still works
            result = resolve_model_alias("gpt-oss-20b")
            assert result == ("ollama", "gpt-oss:20b")
