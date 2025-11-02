"""
LLM Factory for PRT

This module provides a factory pattern for creating LLM instances based on provider type.
Supports both Ollama and llama-cpp-python providers.
"""

from typing import TYPE_CHECKING
from typing import Optional
from typing import Union

from .api import PRTAPI
from .config import LLMConfigManager
from .logging_config import get_logger

if TYPE_CHECKING:
    from .llm_llamacpp import LlamaCppLLM
    from .llm_ollama import OllamaLLM

logger = get_logger(__name__)


def create_llm(
    provider: Optional[str] = None,
    api: Optional[PRTAPI] = None,
    model: Optional[str] = None,
    config_manager: Optional[LLMConfigManager] = None,
    **kwargs,
) -> Union["OllamaLLM", "LlamaCppLLM"]:
    """Create an LLM instance based on provider type.

    Args:
        provider: LLM provider name ("ollama" or "llamacpp"). If None, uses config.
        api: PRTAPI instance for database operations. If None, creates a new instance.
        model: Model name or path override. If None, uses config.
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

    # Determine provider
    if provider is None:
        provider = config_manager.llm.provider

    provider = provider.lower()
    logger.info(f"[LLM Factory] Creating LLM provider: {provider}")

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
