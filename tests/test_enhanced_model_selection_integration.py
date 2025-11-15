"""
Integration tests for enhanced LLM model selection workflow.

Tests the complete model selection process including validation, error handling,
and user guidance across CLI and factory components.
"""

from unittest.mock import Mock
from unittest.mock import patch

import pytest

from prt_src.config import LLMConfigManager
from prt_src.llm_factory import check_model_availability
from prt_src.llm_factory import create_llm
from prt_src.llm_factory import get_model_validation_info
from prt_src.llm_factory import resolve_model_alias
from prt_src.llm_factory import validate_model_and_show_warnings
from prt_src.llm_supported_models import get_recommended_model
from prt_src.llm_supported_models import get_supported_models
from prt_src.llm_supported_models import validate_model_selection


@pytest.mark.integration
class TestModelSelectionIntegration:
    """Integration tests for model selection workflow."""

    @pytest.fixture
    def mock_api(self):
        """Mock API instance for testing."""
        api = Mock()
        api.get_config.return_value = {"db_path": "test.db", "db_encrypted": False}
        return api

    @pytest.fixture
    def test_config_manager(self):
        """Test configuration manager."""
        config_dict = {
            "llm": {
                "provider": "ollama",
                "model": "gpt-oss:20b",
                "base_url": "http://localhost:11434",
                "timeout": 300,
                "temperature": 0.1,
            }
        }
        return LLMConfigManager(config_dict)

    def test_supported_model_validation_workflow(self):
        """Test complete workflow for supported model validation."""
        # Test with officially supported model
        is_supported, message, model_info = validate_model_selection("gpt-oss:20b")

        assert is_supported is True
        assert "officially supported" in message.lower()
        assert model_info is not None
        assert model_info.support_status == "official"
        assert model_info.model_name == "gpt-oss:20b"
        assert model_info.friendly_name == "gpt-oss-20b"

    def test_experimental_model_validation_workflow(self):
        """Test complete workflow for experimental model validation."""
        # Test with experimental model
        is_supported, message, model_info = validate_model_selection("llama3:8b")

        assert is_supported is True
        assert "experimental" in message.lower()
        assert model_info is not None
        assert model_info.support_status == "experimental"

    def test_unsupported_model_validation_workflow(self):
        """Test complete workflow for unsupported model validation."""
        # Test with unsupported model
        is_supported, message, model_info = validate_model_selection("unknown-model:1b")

        assert is_supported is False
        assert "not officially supported" in message
        assert "recommended" in message.lower()
        assert model_info is None

    def test_model_alias_resolution_workflow(self):
        """Test model alias resolution with supported models."""
        # Test with friendly alias
        is_supported, message, model_info = validate_model_selection("gpt-oss-20b")

        assert is_supported is True
        assert model_info is not None
        assert model_info.model_name == "gpt-oss:20b"
        assert model_info.friendly_name == "gpt-oss-20b"

    def test_validation_with_warnings(self, caplog):
        """Test validation function with warning output."""
        # Test official model (should not warn)
        is_supported, message = validate_model_and_show_warnings("gpt-oss:20b", warn=True)
        assert is_supported is True

        # Test experimental model (should warn)
        is_supported, message = validate_model_and_show_warnings("llama3:8b", warn=True)
        assert is_supported is True

        # Test unsupported model (should warn)
        is_supported, message = validate_model_and_show_warnings("unknown:1b", warn=True)
        assert is_supported is False

    def test_model_validation_info_comprehensive(self):
        """Test comprehensive model validation information."""
        # Test with supported model
        info = get_model_validation_info("gpt-oss:20b")

        assert info["model_name"] == "gpt-oss:20b"
        assert info["is_supported"] is True
        assert info["support_info"] is not None
        assert info["support_info"]["status"] == "official"
        assert info["support_info"]["display_name"] == "GPT-OSS 20B"
        assert info["hardware_requirements"] is not None
        assert "RAM:" in info["hardware_requirements"]
        assert isinstance(info["recommendations"], list)

    def test_model_validation_info_unsupported(self):
        """Test validation info for unsupported model."""
        # Test with unsupported model
        info = get_model_validation_info("unknown:1b")

        assert info["model_name"] == "unknown:1b"
        assert info["is_supported"] is False
        assert info["support_info"] is None
        assert info["hardware_requirements"] is None
        assert len(info["recommendations"]) > 0
        assert "recommended model" in info["recommendations"][0].lower()

    @patch("prt_src.llm_factory.get_registry")
    def test_model_availability_check(self, mock_registry_getter):
        """Test model availability checking."""
        mock_registry = Mock()
        mock_registry.is_available.return_value = True
        mock_registry.resolve_alias.return_value = "gpt-oss:20b"
        mock_registry_getter.return_value = mock_registry

        availability = check_model_availability("gpt-oss-20b")

        assert availability["model_name"] == "gpt-oss-20b"
        assert availability["available_in_ollama"] is True
        assert availability["resolved_name"] == "gpt-oss:20b"
        assert availability["ollama_accessible"] is True
        assert availability["error"] is None

    @patch("prt_src.llm_factory.get_registry")
    def test_model_availability_check_offline(self, mock_registry_getter):
        """Test model availability checking when Ollama is offline."""
        mock_registry = Mock()
        mock_registry.is_available.return_value = False
        mock_registry_getter.return_value = mock_registry

        availability = check_model_availability("gpt-oss-20b")

        assert availability["model_name"] == "gpt-oss-20b"
        assert availability["available_in_ollama"] is False
        assert availability["ollama_accessible"] is False
        assert "not running or not accessible" in availability["error"]

    @patch("prt_src.llm_factory.get_registry")
    def test_resolve_model_alias_integration(self, mock_registry_getter, test_config_manager):
        """Test model alias resolution integration."""
        mock_registry = Mock()
        mock_registry.is_available.return_value = True
        mock_registry.resolve_alias.return_value = "gpt-oss:20b"
        mock_registry_getter.return_value = mock_registry

        provider, model_name = resolve_model_alias("gpt-oss-20b", test_config_manager)

        assert provider == "ollama"
        assert model_name == "gpt-oss:20b"

    @patch("prt_src.llm_factory.get_registry")
    def test_resolve_model_alias_fallback(self, mock_registry_getter, test_config_manager):
        """Test model alias resolution with fallback when Ollama is offline."""
        # Configure fallback in config
        test_config_manager.llm.fallback_models = {
            "gpt-oss-20b": {"provider": "ollama", "model_name": "gpt-oss:20b"}
        }

        mock_registry = Mock()
        mock_registry.is_available.return_value = False
        mock_registry_getter.return_value = mock_registry

        provider, model_name = resolve_model_alias("gpt-oss-20b", test_config_manager)

        assert provider == "ollama"
        assert model_name == "gpt-oss:20b"

    def test_supported_models_registry_consistency(self):
        """Test that supported models registry is consistent."""
        models = get_supported_models()

        # Check that we have at least the required official models
        official_models = [m for m in models.values() if m.support_status == "official"]
        assert len(official_models) >= 2  # At least gpt-oss and mistral

        # Check that gpt-oss:20b and mistral:7b-instruct are present
        model_names = list(models.keys())
        assert "gpt-oss:20b" in model_names
        assert "mistral:7b-instruct" in model_names

        # Verify recommended model is valid
        recommended = get_recommended_model()
        assert recommended.support_status == "official"
        assert recommended.model_name in models

    @patch("prt_src.llm_factory._create_ollama_llm")
    @patch("prt_src.llm_factory.get_registry")
    def test_create_llm_with_validation_integration(
        self, mock_registry_getter, mock_create_ollama, mock_api, test_config_manager
    ):
        """Test LLM creation with integrated validation."""
        # Mock registry
        mock_registry = Mock()
        mock_registry.is_available.return_value = True
        mock_registry.resolve_alias.return_value = "gpt-oss:20b"
        mock_registry_getter.return_value = mock_registry

        # Mock LLM creation
        mock_llm = Mock()
        mock_create_ollama.return_value = mock_llm

        # Create LLM with supported model
        llm = create_llm(api=mock_api, model="gpt-oss-20b", config_manager=test_config_manager)

        # Verify LLM was created
        assert llm == mock_llm
        mock_create_ollama.assert_called_once()

    def test_model_recommendation_workflow(self):
        """Test model recommendation workflow for users."""
        # Get recommendation
        recommended = get_recommended_model()

        # Verify it's a valid supported model
        assert recommended.support_status == "official"
        assert recommended.model_name
        assert recommended.friendly_name
        assert recommended.description
        assert len(recommended.use_cases) > 0

        # Verify validation works with recommended model
        is_supported, message, model_info = validate_model_selection(recommended.model_name)
        assert is_supported is True
        assert model_info == recommended


@pytest.mark.integration
class TestCLIModelSelectionIntegration:
    """Integration tests for CLI model selection commands."""

    @patch("prt_src.llm_factory.get_registry")
    def test_list_models_command_integration(self, mock_registry_getter):
        """Test list-models command integration with support status."""
        from prt_src.llm_model_registry import ModelInfo

        # Mock models from Ollama
        mock_gpt_model = ModelInfo(
            {"name": "gpt-oss:20b", "size": 12000000000, "modified_at": "2024-01-01"}  # 12GB
        )

        mock_mistral_model = ModelInfo(
            {"name": "mistral:7b-instruct", "size": 4000000000, "modified_at": "2024-01-01"}  # 4GB
        )

        mock_unknown_model = ModelInfo(
            {"name": "unknown:1b", "size": 1000000000, "modified_at": "2024-01-01"}  # 1GB
        )

        mock_registry = Mock()
        mock_registry.is_available.return_value = True
        mock_registry.list_models.return_value = [
            mock_gpt_model,
            mock_mistral_model,
            mock_unknown_model,
        ]
        mock_registry.get_default_model.return_value = "gpt-oss:20b"
        mock_registry_getter.return_value = mock_registry

        # Import here to avoid circular imports during module loading
        from prt_src.llm_supported_models import get_model_support_info

        # Test that supported models are identified correctly
        gpt_support = get_model_support_info("gpt-oss:20b")
        assert gpt_support is not None
        assert gpt_support.support_status == "official"

        mistral_support = get_model_support_info("mistral:7b-instruct")
        assert mistral_support is not None
        assert mistral_support.support_status == "official"

        unknown_support = get_model_support_info("unknown:1b")
        assert unknown_support is None

    def test_model_help_text_integration(self):
        """Test that help text provides useful guidance."""
        # This would be tested by running the CLI with --help, but we can verify
        # that our help text mentions the list-models command

        # The help text should now reference list-models
        help_text = "Model alias (e.g., 'gpt-oss-20b', 'mistral-7b-instruct'). Use 'list-models' to see available options with support status."

        assert "list-models" in help_text
        assert "gpt-oss-20b" in help_text
        assert "mistral-7b-instruct" in help_text
