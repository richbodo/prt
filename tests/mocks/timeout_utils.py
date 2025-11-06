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
    Check if Ollama is available and responding.

    Returns:
        True if Ollama is available, False otherwise
    """
    try:
        import requests

        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        return response.status_code == 200
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


def flaky_contract_test(reruns: int = 2, reruns_delay: int = 5, timeout_seconds: int = 300):
    """
    Decorator for flaky contract tests with retry logic and timeout.

    Args:
        reruns: Number of times to retry on failure
        reruns_delay: Delay between retries in seconds
        timeout_seconds: Maximum time to allow for each test run

    Usage:
        @flaky_contract_test(reruns=3, reruns_delay=10)
        def test_flaky_llm_behavior():
            # Test implementation
            pass
    """

    def decorator(func):
        # Apply decorators in sequence
        func = pytest.mark.flaky(reruns=reruns, reruns_delay=reruns_delay)(func)
        func = contract_test(timeout_seconds)(func)
        return func

    return decorator
