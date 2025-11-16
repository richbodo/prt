"""
Supported LLM Models Registry for PRT

This module defines officially supported LLM models with metadata about
hardware requirements, descriptions, and support status. It provides
functions to validate model support and generate user guidance.
"""

from dataclasses import dataclass
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from .logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class SupportedModelInfo:
    """Information about an officially supported model."""

    # Model identification
    model_name: str  # Full model name (e.g., "gpt-oss:20b")
    friendly_name: str  # Alias (e.g., "gpt-oss-20b")
    display_name: str  # Human-readable name for display

    # Support status
    support_status: str  # "official", "experimental", "deprecated"
    provider: str  # "ollama", "llamacpp"

    # Hardware requirements
    min_ram_gb: int  # Minimum RAM required in GB
    recommended_ram_gb: int  # Recommended RAM in GB
    gpu_required: bool  # Whether GPU is required

    # Model characteristics
    parameter_count: str  # e.g., "20B", "7B", "13B"
    context_size: int  # Context window size

    # User guidance
    description: str  # Brief description for users
    use_cases: List[str]  # Recommended use cases

    # Optional fields (must come last)
    min_vram_gb: Optional[int] = None  # Minimum VRAM if GPU required
    quantization: Optional[str] = None  # e.g., "Q4_K_M", "Q8_0"
    notes: Optional[str] = None  # Additional notes or warnings


# Registry of officially supported models
SUPPORTED_MODELS: Dict[str, SupportedModelInfo] = {
    "gpt-oss:20b": SupportedModelInfo(
        model_name="gpt-oss:20b",
        friendly_name="gpt-oss-20b",
        display_name="GPT-OSS 20B",
        support_status="official",
        provider="ollama",
        min_ram_gb=16,
        recommended_ram_gb=32,
        gpu_required=False,
        min_vram_gb=8,
        parameter_count="20B",
        context_size=4096,
        description="High-quality 20B parameter model with tool calling support",
        use_cases=["General chat", "Tool calling", "Contact queries", "Complex reasoning"],
        notes="Best model for PRT's tool calling features. Supports function calls.",
    ),
    "mistral:7b-instruct": SupportedModelInfo(
        model_name="mistral:7b-instruct",
        friendly_name="mistral-7b-instruct",
        display_name="Mistral 7B Instruct v0.3",
        support_status="official",
        provider="ollama",
        min_ram_gb=8,
        recommended_ram_gb=16,
        gpu_required=False,
        min_vram_gb=4,
        parameter_count="7B",
        context_size=32768,
        quantization="Q4_K_M",
        description="Efficient 7B instruction-tuned model with tool calling support (Mistral-7B-Instruct-v0.3)",
        use_cases=["General chat", "Contact queries", "Tool calling", "Moderate hardware"],
        notes="Good alternative for systems with limited RAM. Supports function calling with v3 tokenizer. Model size: 4.4GB.",
    ),
    "llama3:8b": SupportedModelInfo(
        model_name="llama3:8b",
        friendly_name="llama3-8b",
        display_name="Llama 3 8B",
        support_status="experimental",
        provider="ollama",
        min_ram_gb=8,
        recommended_ram_gb=16,
        gpu_required=False,
        min_vram_gb=4,
        parameter_count="8B",
        context_size=8192,
        description="Meta's Llama 3 8B model for general purposes",
        use_cases=["General chat", "Contact queries"],
        notes="Limited tool calling support. May not work with all PRT features.",
    ),
    "codestral:22b": SupportedModelInfo(
        model_name="codestral:22b",
        friendly_name="codestral-22b",
        display_name="Codestral 22B",
        support_status="experimental",
        provider="ollama",
        min_ram_gb=16,
        recommended_ram_gb=32,
        gpu_required=False,
        min_vram_gb=8,
        parameter_count="22B",
        context_size=32768,
        description="Code-focused model with large context window",
        use_cases=["Code analysis", "Database queries", "Large context tasks"],
        notes="Experimental support. Large context window but limited tool calling.",
    ),
    # ============================================================
    # LLAMACPP GGUF MODELS
    # ============================================================
    "llama-3.2-8b-instruct-q4_k_m.gguf": SupportedModelInfo(
        model_name="llama-3.2-8b-instruct-q4_k_m.gguf",
        friendly_name="llama3.2-8b-q4",
        display_name="Llama 3.2 8B Instruct (Q4_K_M)",
        support_status="official",
        provider="llamacpp",
        min_ram_gb=6,
        recommended_ram_gb=12,
        gpu_required=False,
        min_vram_gb=4,
        parameter_count="8B",
        context_size=131072,  # 128k context
        quantization="Q4_K_M",
        description="Latest Llama 3.2 8B model with enhanced instruction following (Q4_K_M quantization)",
        use_cases=["General chat", "Contact queries", "Tool calling", "Efficient inference"],
        notes="Best balance of quality and performance. GGUF format for direct model execution. File size: ~4.9GB.",
    ),
    "mistral-7b-instruct-v0.3-q4_k_m.gguf": SupportedModelInfo(
        model_name="mistral-7b-instruct-v0.3-q4_k_m.gguf",
        friendly_name="mistral-7b-q4",
        display_name="Mistral 7B Instruct v0.3 (Q4_K_M)",
        support_status="official",
        provider="llamacpp",
        min_ram_gb=5,
        recommended_ram_gb=10,
        gpu_required=False,
        min_vram_gb=3,
        parameter_count="7B",
        context_size=32768,
        quantization="Q4_K_M",
        description="Efficient Mistral 7B with excellent tool calling capabilities (Q4_K_M quantization)",
        use_cases=["Tool calling", "General chat", "Contact queries", "Low resource systems"],
        notes="Excellent for tool calling. Highly compatible with PRT features. File size: ~4.1GB.",
    ),
    "codellama-13b-instruct-q4_k_m.gguf": SupportedModelInfo(
        model_name="codellama-13b-instruct-q4_k_m.gguf",
        friendly_name="codellama-13b-q4",
        display_name="CodeLlama 13B Instruct (Q4_K_M)",
        support_status="experimental",
        provider="llamacpp",
        min_ram_gb=10,
        recommended_ram_gb=18,
        gpu_required=False,
        min_vram_gb=6,
        parameter_count="13B",
        context_size=16384,
        quantization="Q4_K_M",
        description="Code-specialized Llama model with instruction tuning (Q4_K_M quantization)",
        use_cases=["SQL queries", "Database analysis", "Complex reasoning", "Code-related tasks"],
        notes="Good for complex SQL queries and database operations. File size: ~7.9GB.",
    ),
    "phi-3.5-mini-instruct-q4_k_m.gguf": SupportedModelInfo(
        model_name="phi-3.5-mini-instruct-q4_k_m.gguf",
        friendly_name="phi3.5-mini-q4",
        display_name="Phi-3.5 Mini Instruct (Q4_K_M)",
        support_status="experimental",
        provider="llamacpp",
        min_ram_gb=3,
        recommended_ram_gb=6,
        gpu_required=False,
        min_vram_gb=2,
        parameter_count="3.8B",
        context_size=128000,  # 128k context
        quantization="Q4_K_M",
        description="Ultra-efficient Microsoft Phi-3.5 model with large context (Q4_K_M quantization)",
        use_cases=[
            "Low resource systems",
            "General chat",
            "Quick queries",
            "Mobile/edge deployment",
        ],
        notes="Very small but capable. Good for systems with limited resources. File size: ~2.2GB.",
    ),
    "llama-3.1-70b-instruct-q4_k_m.gguf": SupportedModelInfo(
        model_name="llama-3.1-70b-instruct-q4_k_m.gguf",
        friendly_name="llama3.1-70b-q4",
        display_name="Llama 3.1 70B Instruct (Q4_K_M)",
        support_status="experimental",
        provider="llamacpp",
        min_ram_gb=48,
        recommended_ram_gb=64,
        gpu_required=False,
        min_vram_gb=24,
        parameter_count="70B",
        context_size=131072,  # 128k context
        quantization="Q4_K_M",
        description="High-performance Llama 3.1 70B model for complex reasoning (Q4_K_M quantization)",
        use_cases=[
            "Complex reasoning",
            "Advanced tool calling",
            "High-quality responses",
            "Professional use",
        ],
        notes="Requires significant resources. Excellent quality but slow inference on CPU. File size: ~42GB.",
    ),
}


def get_supported_models() -> Dict[str, SupportedModelInfo]:
    """Get the registry of supported models.

    Returns:
        Dictionary mapping model names to SupportedModelInfo
    """
    return SUPPORTED_MODELS.copy()


def is_model_supported(model_name: str) -> bool:
    """Check if a model is officially supported.

    Args:
        model_name: Model name to check (can be full name or alias)

    Returns:
        True if model is officially supported
    """
    # Check direct model name
    if model_name in SUPPORTED_MODELS:
        return True

    # Check friendly names
    return any(model_info.friendly_name == model_name for model_info in SUPPORTED_MODELS.values())


def get_model_support_info(model_name: str) -> Optional[SupportedModelInfo]:
    """Get support information for a model.

    Args:
        model_name: Model name to lookup (can be full name or alias)

    Returns:
        SupportedModelInfo if found, None otherwise
    """
    # Check direct model name
    if model_name in SUPPORTED_MODELS:
        return SUPPORTED_MODELS[model_name]

    # Check friendly names
    for model_info in SUPPORTED_MODELS.values():
        if model_info.friendly_name == model_name:
            return model_info

    return None


def get_models_by_status(status: str) -> List[SupportedModelInfo]:
    """Get all models with a specific support status.

    Args:
        status: Support status ("official", "experimental", "deprecated")

    Returns:
        List of models with the given status
    """
    return [model for model in SUPPORTED_MODELS.values() if model.support_status == status]


def get_recommended_model() -> SupportedModelInfo:
    """Get the recommended default model.

    Returns:
        SupportedModelInfo for the recommended model
    """
    # Return the first official model
    official_models = get_models_by_status("official")
    if official_models:
        return official_models[0]

    # Fallback to any supported model
    if SUPPORTED_MODELS:
        return list(SUPPORTED_MODELS.values())[0]

    raise RuntimeError("No supported models defined")


def validate_model_selection(model_name: str) -> Tuple[bool, str, Optional[SupportedModelInfo]]:
    """Validate a user's model selection and provide guidance.

    Args:
        model_name: Model name selected by user

    Returns:
        Tuple of (is_valid, message, model_info)
        - is_valid: True if model is supported
        - message: User-friendly message about the model
        - model_info: SupportedModelInfo if supported, None otherwise
    """
    model_info = get_model_support_info(model_name)

    if model_info is None:
        # Model not in supported list
        recommended = get_recommended_model()
        message = (
            f"Model '{model_name}' is not officially supported. "
            f"Recommended model: {recommended.display_name} ({recommended.friendly_name}). "
            f"You can still try to use this model, but features may not work correctly."
        )
        return False, message, None

    elif model_info.support_status == "official":
        message = f"✓ Using officially supported model: {model_info.display_name}"
        return True, message, model_info

    elif model_info.support_status == "experimental":
        message = (
            f"⚠️  Using experimental model: {model_info.display_name}. "
            f"Some features may not work correctly. {model_info.notes or ''}"
        )
        return True, message, model_info

    elif model_info.support_status == "deprecated":
        recommended = get_recommended_model()
        message = (
            f"⚠️  Model '{model_info.display_name}' is deprecated. "
            f"Consider using: {recommended.display_name} ({recommended.friendly_name})"
        )
        return True, message, model_info

    else:
        message = f"Unknown support status for model: {model_info.display_name}"
        return True, message, model_info


def get_hardware_guidance(model_info: SupportedModelInfo) -> str:
    """Generate hardware requirement guidance for a model.

    Args:
        model_info: Model to generate guidance for

    Returns:
        Human-readable hardware guidance string
    """
    parts = []

    # RAM requirements
    parts.append(
        f"RAM: {model_info.min_ram_gb}GB minimum, {model_info.recommended_ram_gb}GB recommended"
    )

    # GPU requirements
    if model_info.gpu_required:
        if model_info.min_vram_gb:
            parts.append(f"GPU: Required ({model_info.min_vram_gb}GB+ VRAM)")
        else:
            parts.append("GPU: Required")
    else:
        if model_info.min_vram_gb:
            parts.append(f"GPU: Optional ({model_info.min_vram_gb}GB+ VRAM for acceleration)")
        else:
            parts.append("GPU: Optional (for acceleration)")

    # Additional info
    parts.append(f"Context: {model_info.context_size:,} tokens")
    if model_info.quantization:
        parts.append(f"Quantization: {model_info.quantization}")

    return " | ".join(parts)


def suggest_models_for_hardware(
    available_ram_gb: Optional[int] = None, has_gpu: bool = False, gpu_vram_gb: Optional[int] = None
) -> List[SupportedModelInfo]:
    """Suggest appropriate models based on hardware specs.

    Args:
        available_ram_gb: Available system RAM in GB
        has_gpu: Whether GPU is available
        gpu_vram_gb: Available GPU VRAM in GB

    Returns:
        List of suitable models, ordered by preference
    """
    suitable_models = []

    for model_info in SUPPORTED_MODELS.values():
        # Skip if insufficient RAM
        if available_ram_gb and available_ram_gb < model_info.min_ram_gb:
            continue

        # Skip if GPU required but not available
        if model_info.gpu_required and not has_gpu:
            continue

        # Skip if insufficient VRAM
        if model_info.min_vram_gb and gpu_vram_gb and gpu_vram_gb < model_info.min_vram_gb:
            continue

        suitable_models.append(model_info)

    # Sort by preference: official first, then by parameter count (larger is better)
    def sort_key(model):
        status_priority = {"official": 0, "experimental": 1, "deprecated": 2}
        param_size = int("".join(filter(str.isdigit, model.parameter_count)) or "0")
        return (status_priority.get(model.support_status, 3), -param_size)

    return sorted(suitable_models, key=sort_key)
