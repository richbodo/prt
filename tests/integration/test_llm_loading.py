"""Integration tests for LLM model loading and initialization.

Tests that model loading works correctly for both Ollama and LlamaCpp providers.
"""

import pytest

from prt_src.api import PRTAPI
from prt_src.config import LLMConfigManager
from prt_src.llm_factory import DEFAULT_LEGACY_MODEL_ALIAS
from prt_src.llm_factory import create_llm
from prt_src.llm_factory import resolve_model_alias


class TestLLMModelLoading:
    """Test LLM model loading for different providers."""

    def test_resolve_default_model_alias(self):
        """Test that default model alias resolves correctly."""
        config = LLMConfigManager()

        # When no model specified, should default to "llama8" or registry default
        provider, model = resolve_model_alias(None, config)

        assert provider in ["ollama", "llamacpp"]
        assert model is not None
        assert len(model) > 0

    def test_resolve_explicit_alias(self):
        """Test that explicit model aliases resolve correctly."""
        config = LLMConfigManager()

        # Try to resolve an alias - if Ollama is offline, this will fall back
        provider, model = resolve_model_alias("llama8", config)

        assert provider in ["ollama", "llamacpp"]
        assert model is not None

    def test_resolve_gguf_path(self):
        """Test that .gguf paths are detected correctly."""
        config = LLMConfigManager()

        # .gguf files should always resolve to llamacpp provider
        provider, model = resolve_model_alias("MODELS/test.gguf", config)

        assert provider == "llamacpp"
        assert model == "MODELS/test.gguf"

    def test_create_llm_with_default(self, test_db):
        """Test creating LLM with default model."""
        db, fixtures = test_db
        config_dict = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config_dict)

        # Create LLM without specifying model (should use default)
        llm = create_llm(api=api)

        assert llm is not None
        assert hasattr(llm, "model")
        assert hasattr(llm, "chat")

    def test_create_llm_with_explicit_model(self, test_db):
        """Test creating LLM with explicit model specification."""
        db, fixtures = test_db
        config_dict = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config_dict)

        # Create LLM with explicit model
        llm = create_llm(api=api, model="llama8")

        assert llm is not None
        assert hasattr(llm, "model")

    def test_ollama_llm_initialization(self, test_db):
        """Test OllamaLLM initializes with correct base_url."""
        db, fixtures = test_db
        config_dict = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config_dict)

        try:
            from prt_src.llm_ollama import OllamaLLM

            llm = OllamaLLM(api=api)

            # Should use native API URL (not /v1)
            assert llm.base_url == "http://localhost:11434"
            assert not llm.base_url.endswith("/v1")

            # Should have keep_alive parameter
            assert hasattr(llm, "keep_alive")
            assert llm.keep_alive is not None
        except ImportError:
            pytest.skip("OllamaLLM not available")

    def test_llama_cpp_llm_initialization(self, test_db):
        """Test LlamaCppLLM initializes correctly."""
        db, fixtures = test_db
        config_dict = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config_dict)

        try:
            from prt_src.llm_llamacpp import LlamaCppLLM

            # LlamaCppLLM requires model_path
            # This will fail if file doesn't exist, but we're testing initialization
            with pytest.raises((ValueError, FileNotFoundError)):
                LlamaCppLLM(api=api, model_path=None)
        except ImportError:
            pytest.skip("LlamaCppLLM not available")

    def test_create_llm_handles_missing_provider(self, test_db):
        """Test that create_llm handles invalid provider gracefully."""
        db, fixtures = test_db
        config_dict = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config_dict)

        # Invalid provider should raise ValueError
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            create_llm(api=api, provider="invalid_provider")

    def test_model_resolution_with_ollama_offline(self):
        """Test that model resolution works when Ollama is offline."""
        config = LLMConfigManager()

        # Even if Ollama is offline, resolution should not crash
        # It should fall back to config or assumptions
        try:
            provider, model = resolve_model_alias("test-model", config)
            assert provider in ["ollama", "llamacpp"]
            assert model is not None
        except Exception as e:
            # Should not raise exceptions, should fallback gracefully
            pytest.fail(f"Model resolution should not crash when Ollama offline: {e}")

    def test_default_legacy_model_constant_defined(self):
        """Test that DEFAULT_LEGACY_MODEL_ALIAS constant is defined and usable."""
        # Verify constant exists and has expected value
        assert DEFAULT_LEGACY_MODEL_ALIAS == "llama8"

        # Verify it can be used with resolve_model_alias
        config = LLMConfigManager()
        provider, model = resolve_model_alias(DEFAULT_LEGACY_MODEL_ALIAS, config)

        # Should resolve successfully (exact model depends on Ollama availability)
        assert provider in ["ollama", "llamacpp"]
        assert model is not None
        assert len(model) > 0
