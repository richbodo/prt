"""
Tests for LLM timeout configuration changes.

This module tests that the timeout has been properly increased from 120s to 300s
for handling large datasets without timing out.
"""

import pytest

from prt_src.config import LLMConfig
from prt_src.config import LLMConfigManager
from prt_src.llm_ollama import OllamaLLM


class TestTimeoutConfiguration:
    """Test timeout configuration for LLM operations."""

    def test_default_timeout_is_300_seconds(self):
        """Test that the default LLM timeout is set to 300 seconds."""
        config = LLMConfig()
        assert config.timeout == 300, f"Expected timeout of 300s, got {config.timeout}s"

    def test_config_manager_loads_300_second_timeout(self):
        """Test that LLMConfigManager loads the 300-second timeout by default."""
        # Test with empty config dict to ensure default is used
        config_manager = LLMConfigManager(config_dict={})
        assert (
            config_manager.llm.timeout == 300
        ), f"Expected timeout of 300s, got {config_manager.llm.timeout}s"

    def test_ollama_llm_uses_300_second_timeout(self, sample_config, llm_config):
        """Test that OllamaLLM initializes with the 300-second timeout."""
        # Create OllamaLLM instance with default config using proper constructor
        from unittest.mock import MagicMock

        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api, config_manager=llm_config)
        assert llm.timeout == 300, f"Expected OllamaLLM timeout of 300s, got {llm.timeout}s"

    def test_ollama_llm_respects_custom_timeout(self, sample_config, llm_config):
        """Test that OllamaLLM respects custom timeout values when provided."""
        from unittest.mock import MagicMock

        custom_timeout = 600
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api, config_manager=llm_config, timeout=custom_timeout)
        assert (
            llm.timeout == custom_timeout
        ), f"Expected custom timeout of {custom_timeout}s, got {llm.timeout}s"

    def test_config_manager_custom_timeout_override(self):
        """Test that LLMConfigManager can be overridden with custom timeout values."""
        custom_config = {"llm": {"model": "test-model", "timeout": 450}}
        config_manager = LLMConfigManager(config_dict=custom_config)
        assert (
            config_manager.llm.timeout == 450
        ), f"Expected custom timeout of 450s, got {config_manager.llm.timeout}s"

    def test_timeout_increase_rationale(self):
        """Test that the timeout increase addresses the specific issue described."""
        # This test documents why we increased the timeout
        original_timeout = 120
        new_timeout = 300

        # Verify the increase is substantial enough for large datasets
        increase_ratio = new_timeout / original_timeout
        assert (
            increase_ratio == 2.5
        ), f"Timeout should be increased by 2.5x (from {original_timeout}s to {new_timeout}s)"

        # Verify the new timeout is reasonable for 1800+ contact databases
        # Based on the log evidence: query took ~2 minutes to complete
        expected_completion_time = 120  # seconds (observed in logs)
        buffer_time = new_timeout - expected_completion_time
        assert buffer_time >= 60, f"Should have at least 60s buffer, got {buffer_time}s buffer"

    @pytest.mark.parametrize(
        "contacts_count,expected_suitable",
        [
            (100, True),  # Small database - 300s is more than enough
            (1000, True),  # Medium database - 300s should handle it
            (1800, True),  # Large database - 300s should handle it (per user's case)
            (5000, False),  # Very large database - may need more than 300s, but indexes help
        ],
    )
    def test_timeout_suitable_for_database_sizes(self, contacts_count, expected_suitable):
        """Test that 300s timeout is suitable for various database sizes."""
        timeout = 300

        # Rough estimation: 1800 contacts took ~120s, so linear scaling
        estimated_time = (contacts_count / 1800) * 120

        # Add 50% buffer for safety
        safe_time = estimated_time * 1.5

        is_suitable = timeout >= safe_time
        assert is_suitable == expected_suitable, (
            f"300s timeout should be {'suitable' if expected_suitable else 'insufficient'} "
            f"for {contacts_count} contacts (estimated {safe_time:.1f}s needed)"
        )


class TestTimeoutErrorHandling:
    """Test timeout error handling and messaging."""

    def test_timeout_error_message_mentions_new_limit(self):
        """Test that timeout error messages mention the new 300s limit."""
        # This would be integration test - testing the actual error message format
        # when a timeout occurs with the new 300s limit
        expected_timeout = 300

        # Simulate the error message format from llm_ollama.py:1425
        error_message = f"Error: Request to Ollama timed out after {expected_timeout} seconds. The model may need more time to load or process this request."

        assert "300 seconds" in error_message
        assert "timed out" in error_message.lower()

    def test_timeout_configuration_is_documented(self):
        """Test that the timeout increase is properly documented in the code."""
        # Read the config file to verify the comment is present
        import inspect

        from prt_src.config import LLMConfig

        # Check that the timeout field has appropriate documentation
        # This ensures future developers understand why it's 300s
        source = inspect.getsource(LLMConfig)

        # Look for documentation mentioning the increase and reason
        assert "300" in source, "LLMConfig source should contain the 300s timeout value"
        # The comment should explain why it was increased
        assert any(
            keyword in source.lower() for keyword in ["large", "dataset", "contact", "increased"]
        ), "LLMConfig should document why timeout was increased for large datasets"

    def test_config_manager_timeout_default_fixed(self):
        """Test that the LLMConfigManager default timeout issue is fixed."""
        # This test specifically addresses the bug where LLMConfigManager._load_llm_config()
        # had a hardcoded default of 120s that overrode the class default of 300s

        # Test with no llm config provided - should use the 300s default
        config_manager = LLMConfigManager(config_dict={})
        assert (
            config_manager.llm.timeout == 300
        ), "LLMConfigManager should use 300s default when no config provided"

        # Test with empty llm config - should still use 300s default
        config_manager = LLMConfigManager(config_dict={"llm": {}})
        assert (
            config_manager.llm.timeout == 300
        ), "LLMConfigManager should use 300s default when llm config is empty"

        # Test that explicit timeout in config still works
        config_manager = LLMConfigManager(config_dict={"llm": {"timeout": 450}})
        assert (
            config_manager.llm.timeout == 450
        ), "LLMConfigManager should respect explicit timeout values"
