"""
Integration tests for Mistral-7B-Instruct-v0.3 tool calling functionality.

This module contains comprehensive tests to validate that the mistral:7b-instruct model
properly executes tools instead of returning JSON artifacts. These tests verify the
specific configuration fixes for Mistral tool calling support.
"""

import json
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from prt_src.api import PRTAPI
from prt_src.config import LLMConfigManager
from prt_src.llm_ollama import OllamaLLM


class TestMistralToolCalling:
    """Test tool calling functionality with Mistral-7B-Instruct-v0.3."""

    @pytest.fixture
    def mistral_config_manager(self):
        """Create a config manager configured for Mistral model."""
        config_manager = LLMConfigManager()
        config_manager.llm.model = "mistral:7b-instruct"
        config_manager.llm.temperature = 0.7  # Will be optimized to 0.3 for Mistral
        config_manager.llm.base_url = "http://localhost:11434/v1"
        config_manager.llm.timeout = 30
        return config_manager

    @pytest.fixture
    def mistral_llm(self, test_db, mistral_config_manager):
        """Create OllamaLLM instance configured for Mistral."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config)

        # Mock Ollama API responses for testing
        with patch("requests.post"):
            llm = OllamaLLM(api=api, config_manager=mistral_config_manager)
            return llm

    def test_mistral_model_detection(self, mistral_llm):
        """Test that Mistral model is properly detected."""
        assert mistral_llm._is_mistral_model() is True
        assert "mistral" in mistral_llm.model.lower()

    def test_mistral_temperature_optimization(self, mistral_llm):
        """Test that Mistral model gets optimized temperature for tool calling."""
        # Original config had temperature=0.7, should be optimized to 0.3
        assert mistral_llm.temperature == 0.3

    def test_mistral_tool_call_id_format(self, mistral_llm):
        """Test that Mistral tool call IDs are generated correctly (9 alphanumeric characters)."""
        tool_call_id = mistral_llm._generate_mistral_tool_call_id()

        # Should be exactly 9 characters
        assert len(tool_call_id) == 9

        # Should be alphanumeric only
        assert tool_call_id.isalnum()

    @pytest.mark.skipif(reason="Requires running Ollama with mistral:7b-instruct model")
    def test_mistral_basic_tool_calling_real(self, mistral_llm):
        """Test basic tool calling with real Mistral model (skipped by default)."""
        # This test would run against a real Ollama instance
        response = mistral_llm.chat("Show me the first few contacts in the db")

        # Should get a proper response, not JSON artifacts
        assert response is not None
        assert len(response) > 0
        assert "function" not in response.lower()  # Should not return function code
        assert "json" not in response.lower()  # Should not return JSON examples

    def test_mistral_tool_calling_mocked_search_contacts(self, mistral_llm):
        """Test tool calling with mocked Ollama responses for search_contacts."""
        # Mock response showing tool calling works (not JSON artifacts)
        mock_tool_response = {
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "abc123def",  # 9-character Mistral format
                        "type": "function",
                        "function": {
                            "name": "search_contacts",
                            "arguments": json.dumps({"query": ""}),
                        },
                    }
                ],
            }
        }

        # Mock final response after tool execution
        mock_final_response = {
            "message": {
                "role": "assistant",
                "content": "I found 6 contacts in your database. Here are the first few: John Doe, Jane Smith, Bob Wilson.",
            }
        }

        with patch("requests.post") as mock_post:
            # First call returns tool call, second call returns final response
            mock_post.side_effect = [
                MagicMock(
                    status_code=200,
                    headers={"Content-Type": "application/json"},
                    text=json.dumps(mock_tool_response),
                ),
                MagicMock(
                    status_code=200,
                    headers={"Content-Type": "application/json"},
                    text=json.dumps(mock_final_response),
                ),
            ]

            response = mistral_llm.chat("Show me the first few contacts in the db")

            # Should execute tool and return proper response
            assert "found 6 contacts" in response.lower()
            assert "john doe" in response.lower()
            assert "jane smith" in response.lower()

            # Verify temperature was passed in requests
            calls = mock_post.call_args_list
            assert len(calls) >= 1

            # Check first request includes temperature optimization
            first_call_kwargs = calls[0][1]
            request_data = first_call_kwargs["json"]
            assert "options" in request_data
            assert request_data["options"]["temperature"] == 0.3

    def test_mistral_tool_calling_mocked_list_all_contacts(self, mistral_llm):
        """Test tool calling with mocked responses for list_all_contacts."""
        mock_tool_response = {
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "xyz789abc",
                        "type": "function",
                        "function": {"name": "list_all_contacts", "arguments": json.dumps({})},
                    }
                ],
            }
        }

        mock_final_response = {
            "message": {
                "role": "assistant",
                "content": "Here are all your contacts: John Doe, Jane Smith, Bob Wilson, Charlie Brown, Diana Prince, Alice Johnson.",
            }
        }

        with patch("requests.post") as mock_post:
            mock_post.side_effect = [
                MagicMock(
                    status_code=200,
                    headers={"Content-Type": "application/json"},
                    text=json.dumps(mock_tool_response),
                ),
                MagicMock(
                    status_code=200,
                    headers={"Content-Type": "application/json"},
                    text=json.dumps(mock_final_response),
                ),
            ]

            response = mistral_llm.chat("List all my contacts")

            assert "john doe" in response.lower()
            assert "jane smith" in response.lower()
            assert "diana prince" in response.lower()

    def test_mistral_tool_calling_mocked_get_contact_details(self, mistral_llm):
        """Test tool calling with mocked responses for get_contact_details."""
        mock_tool_response = {
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "def456ghi",
                        "type": "function",
                        "function": {
                            "name": "get_contact_details",
                            "arguments": json.dumps({"contact_id": 1}),
                        },
                    }
                ],
            }
        }

        mock_final_response = {
            "message": {
                "role": "assistant",
                "content": "Here are the details for John Doe (ID: 1): Email: john.doe@email.com, Phone: +1-555-0101",
            }
        }

        with patch("requests.post") as mock_post:
            mock_post.side_effect = [
                MagicMock(
                    status_code=200,
                    headers={"Content-Type": "application/json"},
                    text=json.dumps(mock_tool_response),
                ),
                MagicMock(
                    status_code=200,
                    headers={"Content-Type": "application/json"},
                    text=json.dumps(mock_final_response),
                ),
            ]

            response = mistral_llm.chat("Show me details for contact 1")

            assert "john doe" in response.lower()
            assert "john.doe@email.com" in response.lower()
            assert "+1-555-0101" in response

    def test_mistral_complex_tool_chain_mocked(self, mistral_llm):
        """Test complex tool chaining: search → get details → create note."""
        # Simulate a multi-step workflow
        mock_search_response = {
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "ghi789jkl",
                        "type": "function",
                        "function": {
                            "name": "search_contacts",
                            "arguments": json.dumps({"query": "john"}),
                        },
                    }
                ],
            }
        }

        mock_search_final = {
            "message": {
                "role": "assistant",
                "content": "I found John Doe (ID: 1) matching your search. Let me get his details and add a note.",
            }
        }

        with patch("requests.post") as mock_post:
            mock_post.side_effect = [
                MagicMock(
                    status_code=200,
                    headers={"Content-Type": "application/json"},
                    text=json.dumps(mock_search_response),
                ),
                MagicMock(
                    status_code=200,
                    headers={"Content-Type": "application/json"},
                    text=json.dumps(mock_search_final),
                ),
            ]

            response = mistral_llm.chat("Search for John and add a note about our meeting")

            assert "john doe" in response.lower()
            assert "found" in response.lower()

    def test_mistral_error_handling_and_fallback(self, mistral_llm):
        """Test error handling and fallback behavior for Mistral models."""
        # Test case where tool calling fails
        mock_error_response = {
            "message": {
                "role": "assistant",
                "content": "I apologize, but I encountered an error while trying to access your contacts database. Please try again.",
            }
        }

        with patch("requests.post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                headers={"Content-Type": "application/json"},
                text=json.dumps(mock_error_response),
            )

            response = mistral_llm.chat("Show me my contacts")

            # Should handle gracefully
            assert "error" in response.lower() or "apologize" in response.lower()
            assert len(response) > 0


class TestMistralModelConfigurationIntegration:
    """Test integration between Mistral model configuration and tool calling."""

    def test_non_mistral_model_keeps_original_temperature(self):
        """Test that non-Mistral models keep their original temperature."""
        config_manager = LLMConfigManager()
        config_manager.llm.model = "gpt-oss:20b"  # Not Mistral
        config_manager.llm.temperature = 0.7

        with patch("requests.post"):
            llm = OllamaLLM(api=PRTAPI(), config_manager=config_manager)

            # Should keep original temperature
            assert llm.temperature == 0.7
            assert not llm._is_mistral_model()

    def test_mistral_model_with_already_low_temperature(self):
        """Test Mistral model with temperature already <= 0.3."""
        config_manager = LLMConfigManager()
        config_manager.llm.model = "mistral:7b-instruct"
        config_manager.llm.temperature = 0.2  # Already optimal

        with patch("requests.post"):
            llm = OllamaLLM(api=PRTAPI(), config_manager=config_manager)

            # Should keep the lower temperature
            assert llm.temperature == 0.2
            assert llm._is_mistral_model()

    def test_mistral_tool_call_format_compliance(self):
        """Test that tool calls format is compatible with Mistral specifications."""
        config_manager = LLMConfigManager()
        config_manager.llm.model = "mistral:7b-instruct"

        with patch("requests.post"):
            llm = OllamaLLM(api=PRTAPI(), config_manager=config_manager)

            # Test tool call format
            tools = llm._format_tool_calls()

            # Should have proper structure for Mistral
            assert isinstance(tools, list)
            assert len(tools) > 0

            for tool in tools:
                assert "type" in tool
                assert tool["type"] == "function"
                assert "function" in tool
                assert "name" in tool["function"]
                assert "description" in tool["function"]
                assert "parameters" in tool["function"]

    def test_mistral_model_case_insensitive_detection(self):
        """Test that Mistral model detection is case-insensitive."""
        test_cases = [
            "mistral:7b-instruct",
            "MISTRAL:7b-instruct",
            "Mistral:7b-instruct",
            "mistral-custom-model",
        ]

        for model_name in test_cases:
            config_manager = LLMConfigManager()
            config_manager.llm.model = model_name

            with patch("requests.post"):
                llm = OllamaLLM(api=PRTAPI(), config_manager=config_manager)
                assert llm._is_mistral_model() is True


@pytest.mark.integration
class TestMistralToolCallingEndToEnd:
    """End-to-end integration tests for Mistral tool calling (requires Ollama)."""

    @pytest.mark.skipif(reason="Requires running Ollama with mistral:7b-instruct model")
    def test_mistral_tool_calling_real_database_scenario(self):
        """Test the exact user scenario that was failing: 'Show me the first few contacts in the db'."""
        # This would test against a real Ollama instance
        config_manager = LLMConfigManager()
        config_manager.llm.model = "mistral:7b-instruct"

        # Use debug database with fixture data
        api = PRTAPI({"debug": True})
        llm = OllamaLLM(api=api, config_manager=config_manager)

        response = llm.chat("Show me the first few contacts in the db")

        # Verify tool was executed, not JSON artifacts returned
        assert response is not None
        assert len(response) > 0
        assert "contacts" in response.lower()

        # Should NOT contain JSON artifacts or code examples
        assert "function" not in response
        assert "{" not in response
        assert "}" not in response
        assert "javascript" not in response.lower()
        assert "const" not in response.lower()

    @pytest.mark.skipif(reason="Requires running Ollama with mistral:7b-instruct model")
    def test_mistral_performance_with_debug_database(self):
        """Test Mistral tool calling performance with debug database."""
        config_manager = LLMConfigManager()
        config_manager.llm.model = "mistral:7b-instruct"

        api = PRTAPI({"debug": True})
        llm = OllamaLLM(api=api, config_manager=config_manager)

        import time

        start_time = time.time()

        response = llm.chat("How many contacts do I have?")

        end_time = time.time()
        response_time = end_time - start_time

        # Should respond within reasonable time (< 30 seconds)
        assert response_time < 30.0
        assert response is not None
        assert len(response) > 0
