"""Timeout protection utilities for contract tests."""

import signal
from contextlib import contextmanager
from typing import Generator

import pytest

from prt_src.logging_config import get_logger

logger = get_logger(__name__)


class TimeoutError(Exception):
    """Raised when a test exceeds its timeout."""


@contextmanager
def timeout_context(seconds: int) -> Generator[None, None, None]:
    """
    Provide timeout context for long-running tests.

    Args:
        seconds: Maximum time to allow for the test

    Raises:
        TimeoutError: If the test exceeds the specified timeout

    Usage:
        with timeout_context(300):
            # Test code that should complete within 5 minutes
            result = long_running_operation()
    """

    def timeout_handler(signum, frame):
        raise TimeoutError(f"Test exceeded {seconds}s timeout")

    # Store original handler
    original_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

    try:
        logger.debug(f"Starting timeout context for {seconds}s")
        yield
        logger.debug("Timeout context completed successfully")
    except TimeoutError:
        logger.warning(f"Test timed out after {seconds}s")
        raise
    except Exception as e:
        logger.warning(f"Test failed with exception: {e}")
        raise
    finally:
        # Always clean up the alarm
        signal.alarm(0)
        signal.signal(signal.SIGALRM, original_handler)


def contract_test_timeout(seconds: int = 300):
    """
    Decorator for contract tests that need timeout protection.

    Args:
        seconds: Maximum time to allow for the test (default: 5 minutes)

    Usage:
        @contract_test_timeout(300)
        def test_real_llm_contract():
            # Test implementation
            pass
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            with timeout_context(seconds):
                return func(*args, **kwargs)

        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper

    return decorator


def is_ollama_available() -> bool:
    """
    Check if Ollama is available and responding with models.

    This provides a tiered availability check:
    1. Basic connectivity via /api/version
    2. Model availability via /api/tags
    3. At least one model is available

    Returns:
        True if Ollama is available with models, False otherwise
    """
    try:
        import requests

        # Test basic connectivity
        version_response = requests.get("http://localhost:11434/api/version", timeout=2)
        if version_response.status_code != 200:
            return False

        # Test model availability
        tags_response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if tags_response.status_code != 200:
            return False

        # Check if any models are available
        tags_data = tags_response.json()
        models = tags_data.get("models", [])
        return len(models) > 0

    except Exception:
        return False


def is_ollama_inference_ready() -> bool:
    """
    Check if Ollama can actually perform inference (more thorough than just availability).

    This tests actual inference capability with a simple prompt.
    Use this for tests that need to verify LLM functionality, not just connectivity.

    Returns:
        True if Ollama can perform inference, False otherwise
    """
    try:
        import requests

        if not is_ollama_available():
            return False

        # Test with a simple inference call - try multiple models if available
        # Get available models
        tags_response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if tags_response.status_code != 200:
            return False

        models_data = tags_response.json()
        available_models = [model["name"] for model in models_data.get("models", [])]

        # Prefer faster/smaller models for the inference test
        preferred_models = [
            "phi4-mini:latest",
            "phi3-mini-local:latest",
            "mistral:7b-instruct",
            "gpt-oss:20b",
        ]
        test_model = None

        for preferred in preferred_models:
            if preferred in available_models:
                test_model = preferred
                break

        if not test_model and available_models:
            # Use the first available model as fallback
            test_model = available_models[0]

        if not test_model:
            return False

        # Test with a simple inference call
        test_data = {"model": test_model, "prompt": "Hi", "stream": False}
        response = requests.post(
            "http://localhost:11434/api/generate", json=test_data, timeout=20
        )  # Increased timeout
        if response.status_code != 200:
            return False

        result = response.json()
        response_text = result.get("response", "").strip()
        return len(response_text) > 0

    except Exception:
        return False


def requires_llm(func):
    """
    Decorator to mark tests that require a real LLM service.

    Usage:
        @requires_llm
        def test_real_llm_functionality():
            # Test implementation
            pass
    """
    return pytest.mark.skipif(
        not is_ollama_available(), reason="Ollama not available - skipping real LLM test"
    )(func)


def contract_test(timeout_seconds: int = 300):
    """
    Combined decorator for contract tests with LLM requirement and timeout.

    Args:
        timeout_seconds: Maximum time to allow for the test

    Usage:
        @contract_test(300)
        def test_llm_contract():
            # Test implementation
            pass
    """

    def decorator(func):
        # Apply multiple decorators in sequence
        func = pytest.mark.contract(func)
        func = pytest.mark.requires_llm(func)
        func = pytest.mark.timeout(timeout_seconds)(func)
        func = requires_llm(func)
        func = contract_test_timeout(timeout_seconds)(func)
        return func

    return decorator


def flaky_contract_test(max_runs: int = 3, min_passes: int = 1, timeout_seconds: int = 300):
    """
    Decorator for flaky contract tests with retry logic and timeout.

    Args:
        max_runs: Maximum number of times the test will be run
        min_passes: Minimum number of times the test must pass to be a success
        timeout_seconds: Maximum time to allow for each test run

    Usage:
        @flaky_contract_test(max_runs=3, min_passes=1)
        def test_flaky_llm_behavior():
            # Test implementation
            pass
    """

    def decorator(func):
        # Apply decorators in sequence
        func = pytest.mark.flaky(max_runs=max_runs, min_passes=min_passes)(func)
        func = contract_test(timeout_seconds)(func)
        return func

    return decorator
