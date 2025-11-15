"""
LLM Factory for PRT

This module provides a factory pattern for creating LLM instances based on provider type.
Supports both Ollama and llama-cpp-python providers.
"""

import threading
from typing import TYPE_CHECKING
from typing import Optional
from typing import Union

from .api import PRTAPI
from .config import LLMConfigManager
from .llm_model_registry import OllamaModelRegistry
from .llm_supported_models import validate_model_selection
from .logging_config import get_logger

if TYPE_CHECKING:
    from .llm_llamacpp import LlamaCppLLM
    from .llm_ollama import OllamaLLM

logger = get_logger(__name__)

# Legacy default model alias for backward compatibility
# This constant represents the historical default model identifier used
# when no model is specified in configuration or via CLI arguments.
DEFAULT_LEGACY_MODEL_ALIAS = "llama8"

# Global registry instance (cached) with thread-safe initialization
_registry: Optional[OllamaModelRegistry] = None
_registry_lock = threading.Lock()


def get_registry() -> OllamaModelRegistry:
    """Get or create the global model registry instance.

    This function implements thread-safe lazy initialization using double-checked
    locking to ensure only one registry instance is created even when called
    concurrently from multiple threads.

    Returns:
        Shared OllamaModelRegistry instance
    """
    global _registry
    # First check (no lock) - fast path for already initialized registry
    if _registry is None:
        # Acquire lock for initialization
        with _registry_lock:
            # Second check (with lock) - ensure only one thread creates the registry
            if _registry is None:
                _registry = OllamaModelRegistry()
    return _registry


def resolve_model_alias(
    model_alias: Optional[str] = None, config_manager: Optional[LLMConfigManager] = None
) -> tuple[str, str]:
    """Resolve a model alias to (provider, model_name).

    Strategy:
    1. If no alias provided, use config default_model or legacy default
    2. Check if alias is in Ollama registry
    3. If in registry, prefer 'ollama' provider
    4. If not in registry but ends with .gguf, use 'llamacpp'
    5. Fall back to config if Ollama offline

    Args:
        model_alias: Model alias or full name (e.g., "llama8", "gpt-oss-20b")
        config_manager: Config manager instance

    Returns:
        Tuple of (provider, resolved_model_name)
    """
    if config_manager is None:
        config_manager = LLMConfigManager()

    # Get the model to use
    if model_alias is None:
        # Try config first
        model_alias = getattr(config_manager.llm, "default_model", None)
        if model_alias:
            logger.debug(f"Using default_model from config: {model_alias}")
        else:
            # Use config's model setting (defaults to gpt-oss:20b)
            model_alias = config_manager.llm.model
            logger.debug(f"No model specified, using config model: {model_alias}")

    logger.info(f"[Model Resolution] Resolving alias: {model_alias}")

    # Try Ollama registry first
    registry = get_registry()
    ollama_available = registry.is_available()

    if ollama_available:
        # Check if it's a known alias
        resolved_name = registry.resolve_alias(model_alias)

        if resolved_name:
            logger.info(f"[Model Resolution] Found in Ollama: {model_alias} -> {resolved_name}")
            return ("ollama", resolved_name)
        else:
            # Not in registry - check if it's a direct model name in Ollama
            model_info = registry.get_model_info(model_alias)
            if model_info:
                logger.info(f"[Model Resolution] Direct match in Ollama: {model_alias}")
                return ("ollama", model_alias)
    else:
        logger.warning("[Model Resolution] Ollama not available, checking config fallback")

    # Ollama offline or model not found - check config fallback
    fallback_models = getattr(config_manager.llm, "fallback_models", {}) or {}

    if fallback_models and model_alias in fallback_models:
        fallback = fallback_models[model_alias]
        provider = fallback.get("provider", "ollama")
        model_name = fallback.get("model_name", model_alias)
        logger.info(
            f"[Model Resolution] Using config fallback: {model_alias} -> {provider}/{model_name}"
        )
        return (provider, model_name)

    # Special case: if we're using the default legacy model and Ollama is available,
    # use the registry's default model instead of assuming the legacy model exists
    if model_alias == DEFAULT_LEGACY_MODEL_ALIAS and ollama_available:
        default_model = registry.get_default_model()
        if default_model:
            logger.info(f"[Model Resolution] Using registry default model: {default_model}")
            return ("ollama", default_model)

    # Check if it looks like a .gguf path
    if model_alias.endswith(".gguf"):
        logger.info(f"[Model Resolution] Detected .gguf file: {model_alias}")
        return ("llamacpp", model_alias)

    # Last resort - assume it's an Ollama model name
    logger.warning(
        f"[Model Resolution] Could not resolve '{model_alias}', " f"assuming Ollama model"
    )
    return ("ollama", model_alias)


def create_llm(
    provider: Optional[str] = None,
    api: Optional[PRTAPI] = None,
    model: Optional[str] = None,
    config_manager: Optional[LLMConfigManager] = None,
    **kwargs,
) -> Union["OllamaLLM", "LlamaCppLLM"]:
    """Create an LLM instance based on provider type.

    Args:
        provider: LLM provider name ("ollama" or "llamacpp"). If None, auto-detects from model.
        api: PRTAPI instance for database operations. If None, creates a new instance.
        model: Model alias or name (e.g., "llama8", "gpt-oss-20b"). If None, uses config default.
        config_manager: LLMConfigManager instance. If None, loads from config.
        **kwargs: Additional provider-specific arguments

    Returns:
        LLM instance (OllamaLLM or LlamaCppLLM)

    Raises:
        ValueError: If provider is unknown or required parameters are missing
        ImportError: If required dependencies are not installed
    """
    # Load config if not provided
    if config_manager is None:
        config_manager = LLMConfigManager()

    # Create API if not provided
    if api is None:
        api = PRTAPI()

    # Determine provider and resolve model name
    if provider is None:
        # Auto-detect provider based on model alias
        resolved_provider, resolved_model = resolve_model_alias(model, config_manager)
        provider = resolved_provider
        model = resolved_model
        logger.info(f"[LLM Factory] Auto-detected provider: {provider}, resolved model: {model}")
    else:
        # Explicit provider given - use it directly
        logger.info(f"[LLM Factory] Using explicit provider: {provider}")
        # If model is None, resolve_model_alias will use config default
        if model is None:
            _, model = resolve_model_alias(None, config_manager)
            logger.info(f"[LLM Factory] Resolved model from config: {model}")

    provider = provider.lower()
    logger.info(f"[LLM Factory] Creating LLM with provider={provider}, model={model}")

    # Validate model selection and show warnings
    if model:
        validate_model_and_show_warnings(model, warn=True)

    if provider == "ollama":
        return _create_ollama_llm(api, model, config_manager, **kwargs)
    elif provider == "llamacpp":
        return _create_llamacpp_llm(api, model, config_manager, **kwargs)
    else:
        raise ValueError(
            f"Unknown LLM provider: {provider}. Supported providers: 'ollama', 'llamacpp'"
        )


def _create_ollama_llm(
    api: PRTAPI,
    model: Optional[str] = None,
    config_manager: Optional[LLMConfigManager] = None,
    **kwargs,
) -> "OllamaLLM":
    """Create an Ollama LLM instance.

    Args:
        api: PRTAPI instance
        model: Model name override
        config_manager: LLMConfigManager instance
        **kwargs: Additional Ollama-specific arguments

    Returns:
        OllamaLLM instance

    Raises:
        ImportError: If llm_ollama module cannot be imported
    """
    try:
        from .llm_ollama import OllamaLLM
    except ImportError as e:
        logger.error(f"[LLM Factory] Failed to import OllamaLLM: {e}")
        raise ImportError(
            "OllamaLLM is not available. Make sure prt_src.llm_ollama is installed."
        ) from e

    # Override model if provided
    if model and config_manager:
        original_model = config_manager.llm.model
        config_manager.llm.model = model
        logger.info(f"[LLM Factory] Overriding Ollama model: {original_model} -> {model}")

    logger.info(
        f"[LLM Factory] Creating OllamaLLM: model={config_manager.llm.model}, "
        f"base_url={config_manager.llm.base_url}"
    )

    return OllamaLLM(api=api, config_manager=config_manager, **kwargs)


def _create_llamacpp_llm(
    api: PRTAPI,
    model: Optional[str] = None,
    config_manager: Optional[LLMConfigManager] = None,
    **kwargs,
) -> "LlamaCppLLM":
    """Create a LlamaCpp LLM instance.

    Args:
        api: PRTAPI instance
        model: Model path override (path to .gguf file)
        config_manager: LLMConfigManager instance
        **kwargs: Additional llama-cpp-python specific arguments

    Returns:
        LlamaCppLLM instance

    Raises:
        ImportError: If llama-cpp-python is not installed
        ValueError: If model_path is not provided
        FileNotFoundError: If model file doesn't exist
    """
    try:
        from .llm_llamacpp import LlamaCppLLM
    except ImportError as e:
        logger.error(f"[LLM Factory] Failed to import LlamaCppLLM: {e}")
        raise ImportError(
            "llama-cpp-python is not installed. Install it with: pip install llama-cpp-python"
        ) from e

    # Override model path if provided
    model_path = model or getattr(config_manager.llm, "model_path", None)

    if not model_path:
        raise ValueError(
            "model_path is required for llamacpp provider. "
            "Either provide it via --llm-model CLI flag or set it in config: "
            "llm.model_path in prt_config.json"
        )

    if model and config_manager:
        original_path = getattr(config_manager.llm, "model_path", None)
        config_manager.llm.model_path = model
        logger.info(f"[LLM Factory] Overriding model path: {original_path} -> {model}")

    logger.info(f"[LLM Factory] Creating LlamaCppLLM: model_path={model_path}")

    # Extract llama-cpp-python specific parameters
    n_ctx = kwargs.pop("n_ctx", getattr(config_manager.llm, "n_ctx", 4096))
    n_gpu_layers = kwargs.pop("n_gpu_layers", getattr(config_manager.llm, "n_gpu_layers", 0))
    n_threads = kwargs.pop("n_threads", getattr(config_manager.llm, "n_threads", None))

    logger.info(
        f"[LLM Factory] LlamaCpp config: n_ctx={n_ctx}, "
        f"n_gpu_layers={n_gpu_layers}, n_threads={n_threads}"
    )

    return LlamaCppLLM(
        api=api,
        model_path=model_path,
        n_ctx=n_ctx,
        n_gpu_layers=n_gpu_layers,
        n_threads=n_threads,
        config_manager=config_manager,
        **kwargs,
    )


def validate_model_and_show_warnings(model_name: str, warn: bool = True) -> tuple[bool, str]:
    """Validate a model selection and optionally show warnings.

    Args:
        model_name: Model name to validate
        warn: Whether to log warnings for unsupported models

    Returns:
        Tuple of (is_supported, message)
    """
    is_supported, message, model_info = validate_model_selection(model_name)

    if warn:
        if is_supported and model_info:
            if model_info.support_status == "official":
                logger.info(f"✓ Using officially supported model: {model_info.display_name}")
            elif model_info.support_status == "experimental":
                logger.warning(
                    f"⚠️  Using experimental model: {model_info.display_name}. "
                    f"Some features may not work correctly."
                )
            elif model_info.support_status == "deprecated":
                logger.warning(
                    f"⚠️  Model '{model_info.display_name}' is deprecated. "
                    f"Consider upgrading to a newer model."
                )
        elif not is_supported:
            logger.warning(
                f"Model '{model_name}' is not officially supported. "
                f"You can still try to use it, but some features may not work correctly."
            )

    return is_supported, message


def get_model_validation_info(model_name: str) -> dict:
    """Get comprehensive validation information for a model.

    Args:
        model_name: Model name to check

    Returns:
        Dictionary with validation information
    """
    is_supported, message, model_info = validate_model_selection(model_name)

    result = {
        "model_name": model_name,
        "is_supported": is_supported,
        "message": message,
        "support_info": None,
        "hardware_requirements": None,
        "recommendations": [],
    }

    if model_info:
        from .llm_supported_models import get_hardware_guidance

        result["support_info"] = {
            "status": model_info.support_status,
            "display_name": model_info.display_name,
            "description": model_info.description,
            "use_cases": model_info.use_cases,
            "provider": model_info.provider,
            "parameter_count": model_info.parameter_count,
            "context_size": model_info.context_size,
            "notes": model_info.notes,
        }
        result["hardware_requirements"] = get_hardware_guidance(model_info)

        # Add recommendations based on status
        if model_info.support_status == "experimental":
            result["recommendations"].append(
                "Consider using an officially supported model for production use"
            )
        elif model_info.support_status == "deprecated":
            result["recommendations"].append(
                "This model is deprecated. Please upgrade to a newer model"
            )
    else:
        # Model not in supported list - suggest alternatives
        from .llm_supported_models import get_recommended_model

        recommended = get_recommended_model()
        result["recommendations"].append(
            f"Consider using the recommended model: {recommended.display_name} ({recommended.friendly_name})"
        )

    return result


def check_model_availability(model_name: str) -> dict:
    """Check if a model is available in the registry.

    Args:
        model_name: Model name to check

    Returns:
        Dictionary with availability information
    """
    registry = get_registry()
    result = {
        "model_name": model_name,
        "available_in_ollama": False,
        "resolved_name": None,
        "ollama_accessible": False,
        "error": None,
    }

    try:
        result["ollama_accessible"] = registry.is_available()

        if result["ollama_accessible"]:
            # Check if it's a known alias
            resolved_name = registry.resolve_alias(model_name)
            if resolved_name:
                result["available_in_ollama"] = True
                result["resolved_name"] = resolved_name
            else:
                # Check if it's a direct model name
                model_info = registry.get_model_info(model_name)
                if model_info:
                    result["available_in_ollama"] = True
                    result["resolved_name"] = model_name
        else:
            result["error"] = "Ollama is not running or not accessible"

    except Exception as e:
        result["error"] = str(e)

    return result


def get_available_providers() -> list[str]:
    """Get list of available LLM providers.

    Returns:
        List of provider names that can be used
    """
    providers = []

    # Check Ollama
    try:
        from .llm_ollama import OllamaLLM  # noqa: F401

        providers.append("ollama")
    except ImportError:
        pass

    # Check llama-cpp-python
    try:
        from .llm_llamacpp import LlamaCppLLM  # noqa: F401

        providers.append("llamacpp")
    except ImportError:
        pass

    return providers


def validate_provider(provider: str) -> bool:
    """Validate that a provider is available.

    Args:
        provider: Provider name to validate

    Returns:
        True if provider is available, False otherwise
    """
    return provider.lower() in get_available_providers()
