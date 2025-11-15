"""
Unit tests for LLM supported models registry.
"""

from prt_src.llm_supported_models import SupportedModelInfo
from prt_src.llm_supported_models import get_hardware_guidance
from prt_src.llm_supported_models import get_model_support_info
from prt_src.llm_supported_models import get_models_by_status
from prt_src.llm_supported_models import get_recommended_model
from prt_src.llm_supported_models import get_supported_models
from prt_src.llm_supported_models import is_model_supported
from prt_src.llm_supported_models import suggest_models_for_hardware
from prt_src.llm_supported_models import validate_model_selection


class TestSupportedModelsRegistry:
    """Test the supported models registry functionality."""

    def test_get_supported_models_returns_dict(self):
        """Test that get_supported_models returns a dictionary."""
        models = get_supported_models()
        assert isinstance(models, dict)
        assert len(models) > 0

        # Should contain our officially supported models
        assert "gpt-oss:20b" in models
        assert "mistral:7b-instruct" in models

    def test_get_supported_models_returns_copy(self):
        """Test that get_supported_models returns a copy (immutable)."""
        models1 = get_supported_models()
        models2 = get_supported_models()

        # Should be equal but not the same object
        assert models1 == models2
        assert models1 is not models2

    def test_is_model_supported_with_full_name(self):
        """Test is_model_supported with full model names."""
        assert is_model_supported("gpt-oss:20b") is True
        assert is_model_supported("mistral:7b-instruct") is True
        assert is_model_supported("nonexistent-model:1b") is False

    def test_is_model_supported_with_friendly_name(self):
        """Test is_model_supported with friendly aliases."""
        assert is_model_supported("gpt-oss-20b") is True
        assert is_model_supported("mistral-7b-instruct") is True
        assert is_model_supported("nonexistent-model") is False

    def test_get_model_support_info_with_full_name(self):
        """Test get_model_support_info with full model names."""
        info = get_model_support_info("gpt-oss:20b")
        assert info is not None
        assert isinstance(info, SupportedModelInfo)
        assert info.model_name == "gpt-oss:20b"
        assert info.friendly_name == "gpt-oss-20b"
        assert info.support_status == "official"

    def test_get_model_support_info_with_friendly_name(self):
        """Test get_model_support_info with friendly aliases."""
        info = get_model_support_info("mistral-7b-instruct")
        assert info is not None
        assert isinstance(info, SupportedModelInfo)
        assert info.model_name == "mistral:7b-instruct"
        assert info.friendly_name == "mistral-7b-instruct"

    def test_get_model_support_info_nonexistent(self):
        """Test get_model_support_info with nonexistent model."""
        info = get_model_support_info("nonexistent-model")
        assert info is None

    def test_get_models_by_status(self):
        """Test filtering models by support status."""
        official_models = get_models_by_status("official")
        assert len(official_models) >= 2  # At least gpt-oss and mistral
        assert all(model.support_status == "official" for model in official_models)

        experimental_models = get_models_by_status("experimental")
        assert all(model.support_status == "experimental" for model in experimental_models)

        deprecated_models = get_models_by_status("deprecated")
        assert all(model.support_status == "deprecated" for model in deprecated_models)

    def test_get_recommended_model(self):
        """Test getting the recommended default model."""
        recommended = get_recommended_model()
        assert isinstance(recommended, SupportedModelInfo)
        assert recommended.support_status == "official"  # Should prioritize official models

    def test_validate_model_selection_official(self):
        """Test validation of officially supported model."""
        is_valid, message, model_info = validate_model_selection("gpt-oss:20b")
        assert is_valid is True
        assert "officially supported" in message.lower()
        assert model_info is not None
        assert model_info.support_status == "official"

    def test_validate_model_selection_experimental(self):
        """Test validation of experimental model."""
        is_valid, message, model_info = validate_model_selection("llama3:8b")
        assert is_valid is True
        assert "experimental" in message.lower()
        assert model_info is not None
        assert model_info.support_status == "experimental"

    def test_validate_model_selection_unsupported(self):
        """Test validation of unsupported model."""
        is_valid, message, model_info = validate_model_selection("unknown-model:1b")
        assert is_valid is False
        assert "not officially supported" in message
        assert "recommended" in message.lower()
        assert model_info is None

    def test_validate_model_selection_with_alias(self):
        """Test validation works with friendly aliases."""
        is_valid, message, model_info = validate_model_selection("mistral-7b-instruct")
        assert is_valid is True
        assert model_info is not None
        assert model_info.model_name == "mistral:7b-instruct"

    def test_mistral_model_tool_calling_support(self):
        """Test that Mistral model indicates tool calling support."""
        info = get_model_support_info("mistral:7b-instruct")
        assert info is not None
        assert "Tool calling" in info.use_cases
        assert "Mistral-7B-Instruct-v0.3" in info.description

    def test_mistral_model_updated_specifications(self):
        """Test that Mistral model has updated specifications."""
        info = get_model_support_info("mistral:7b-instruct")
        assert info is not None
        assert info.display_name == "Mistral 7B Instruct v0.3"
        assert info.context_size == 32768  # Updated context size
        assert info.quantization == "Q4_K_M"  # Added quantization info
        assert "4.4GB" in info.notes  # Model size information

    def test_get_hardware_guidance(self):
        """Test hardware guidance generation."""
        info = get_model_support_info("gpt-oss:20b")
        assert info is not None

        guidance = get_hardware_guidance(info)
        assert isinstance(guidance, str)
        assert "RAM:" in guidance
        assert "GPU:" in guidance
        assert "Context:" in guidance
        assert str(info.min_ram_gb) in guidance
        assert str(info.recommended_ram_gb) in guidance

    def test_suggest_models_for_hardware_sufficient_ram(self):
        """Test model suggestions with sufficient RAM."""
        # High-end hardware should get all models
        models = suggest_models_for_hardware(available_ram_gb=64, has_gpu=True, gpu_vram_gb=24)
        assert len(models) > 0

        # Should include official models first
        official_count = sum(1 for m in models if m.support_status == "official")
        assert official_count > 0

    def test_suggest_models_for_hardware_limited_ram(self):
        """Test model suggestions with limited RAM."""
        # Low RAM should filter out large models
        models = suggest_models_for_hardware(available_ram_gb=8, has_gpu=False, gpu_vram_gb=None)

        # All suggested models should fit in 8GB
        for model in models:
            assert model.min_ram_gb <= 8

    def test_suggest_models_for_hardware_no_gpu(self):
        """Test model suggestions without GPU."""
        models = suggest_models_for_hardware(available_ram_gb=32, has_gpu=False, gpu_vram_gb=None)

        # Should not include GPU-required models
        for model in models:
            assert not model.gpu_required

    def test_suggest_models_for_hardware_sorts_correctly(self):
        """Test that model suggestions are sorted correctly."""
        models = suggest_models_for_hardware(available_ram_gb=64, has_gpu=True, gpu_vram_gb=24)

        if len(models) >= 2:
            # Official models should come before experimental
            first_official_idx = next(
                (i for i, m in enumerate(models) if m.support_status == "official"), len(models)
            )
            first_experimental_idx = next(
                (i for i, m in enumerate(models) if m.support_status == "experimental"), len(models)
            )

            if first_official_idx < len(models) and first_experimental_idx < len(models):
                assert first_official_idx < first_experimental_idx


class TestSupportedModelInfo:
    """Test the SupportedModelInfo dataclass."""

    def test_supported_model_info_creation(self):
        """Test creating a SupportedModelInfo instance."""
        model = SupportedModelInfo(
            model_name="test:1b",
            friendly_name="test-1b",
            display_name="Test 1B",
            support_status="experimental",
            provider="ollama",
            min_ram_gb=4,
            recommended_ram_gb=8,
            gpu_required=False,
            parameter_count="1B",
            context_size=2048,
            description="Test model",
            use_cases=["Testing"],
        )

        assert model.model_name == "test:1b"
        assert model.friendly_name == "test-1b"
        assert model.support_status == "experimental"
        assert model.min_ram_gb == 4
        assert model.gpu_required is False
        assert model.use_cases == ["Testing"]

    def test_supported_model_info_optional_fields(self):
        """Test that optional fields work correctly."""
        model = SupportedModelInfo(
            model_name="test:1b",
            friendly_name="test-1b",
            display_name="Test 1B",
            support_status="official",
            provider="ollama",
            min_ram_gb=4,
            recommended_ram_gb=8,
            gpu_required=True,
            min_vram_gb=6,  # Optional field
            parameter_count="1B",
            context_size=2048,
            quantization="Q4_K_M",  # Optional field
            description="Test model",
            use_cases=["Testing"],
            notes="Test notes",  # Optional field
        )

        assert model.min_vram_gb == 6
        assert model.quantization == "Q4_K_M"
        assert model.notes == "Test notes"


class TestModelRegistryIntegration:
    """Integration tests for the model registry."""

    def test_all_supported_models_have_required_fields(self):
        """Test that all models in the registry have required fields."""
        models = get_supported_models()

        for _model_name, model_info in models.items():
            # Required fields should not be None or empty
            assert model_info.model_name
            assert model_info.friendly_name
            assert model_info.display_name
            assert model_info.support_status in ["official", "experimental", "deprecated"]
            assert model_info.provider in ["ollama", "llamacpp"]
            assert model_info.min_ram_gb > 0
            assert model_info.recommended_ram_gb > 0
            assert model_info.parameter_count
            assert model_info.context_size > 0
            assert model_info.description
            assert isinstance(model_info.use_cases, list)
            assert len(model_info.use_cases) > 0

    def test_friendly_names_are_unique(self):
        """Test that all friendly names are unique."""
        models = get_supported_models()
        friendly_names = [model.friendly_name for model in models.values()]
        assert len(friendly_names) == len(set(friendly_names))

    def test_model_names_are_unique(self):
        """Test that all model names are unique (this should be guaranteed by dict keys)."""
        models = get_supported_models()
        model_names = list(models.keys())
        assert len(model_names) == len(set(model_names))

    def test_recommended_ram_not_less_than_minimum(self):
        """Test that recommended RAM is not less than minimum RAM."""
        models = get_supported_models()

        for model_info in models.values():
            assert model_info.recommended_ram_gb >= model_info.min_ram_gb

    def test_at_least_one_official_model_exists(self):
        """Test that there is at least one officially supported model."""
        official_models = get_models_by_status("official")
        assert len(official_models) >= 1
