"""Test JSON handling in tool calling for chat screen functionality."""

import json
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from prt_src.api import PRTAPI
from prt_src.llm_ollama import OllamaLLM


class TestToolCallingJSONHandling:
    """Test proper JSON handling for tool call arguments."""

    @pytest.fixture
    def mock_api(self):
        """Mock PRTAPI for testing."""
        api = Mock(spec=PRTAPI)
        api.search_contacts.return_value = [
            {"id": 1, "name": "John Doe", "email": "john@example.com"},
            {"id": 2, "name": "Jane Smith", "email": "jane@example.com"},
        ]
        api.execute_sql.return_value = {"success": True, "result": [{"count": 1810}]}
        api.get_contacts_with_images.return_value = [
            {"id": 1, "name": "John Doe", "has_image": True},
            {"id": 2, "name": "Jane Smith", "has_image": True},
        ]
        api.create_backup_with_comment.return_value = {"backup_path": "/path/to/backup"}
        return api

    @pytest.fixture
    def ollama_llm(self, mock_api):
        """Create OllamaLLM instance for testing."""
        with patch("prt_src.llm_ollama.LLMConfigManager") as mock_config_mgr:
            mock_config = Mock()
            mock_config.llm.base_url = "http://localhost:11434"
            mock_config.llm.model = "gpt-oss:20b"
            mock_config.llm.keep_alive = "30m"
            mock_config.llm.timeout = 300
            mock_config.llm.temperature = 0.7
            mock_config.tools.disabled_tools = []
            mock_config_mgr.return_value = mock_config

            with patch("prt_src.llm_ollama.get_schema_for_llm") as mock_schema:
                mock_schema.return_value = "Mock schema info"
                return OllamaLLM(mock_api, config_manager=mock_config_mgr.return_value)

    def test_tool_call_with_string_arguments(self, ollama_llm, mock_api):
        """Test tool calling when arguments are provided as JSON string."""
        # Mock the HTTP response for tool calling
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = json.dumps(
            {
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "function": {
                                "name": "execute_sql",
                                "arguments": '{"sql": "SELECT COUNT(*) as count FROM contacts", "confirm": true, "reason": "Count contacts for user query"}',
                            },
                        }
                    ],
                }
            }
        )

        # Mock final response after tool calling
        mock_final_response = Mock()
        mock_final_response.raise_for_status.return_value = None
        mock_final_response.headers = {"Content-Type": "application/json"}
        mock_final_response.text = json.dumps(
            {
                "message": {
                    "role": "assistant",
                    "content": "You have 1810 contacts in your database.",
                }
            }
        )

        with patch("requests.post") as mock_post:
            mock_post.side_effect = [mock_response, mock_final_response]

            # Test that tool calling works with string arguments
            result = ollama_llm.chat("How many contacts are in the database?")

            # Verify the result
            assert "You have 1810 contacts in your database." in result
            assert "Error processing response" not in result
            assert "JSON object must be str" not in result

    def test_tool_call_with_dict_arguments(self, ollama_llm, mock_api):
        """Test tool calling when arguments are provided as already-parsed dict."""
        # Mock the HTTP response for tool calling with dict arguments
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = json.dumps(
            {
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "function": {
                                "name": "execute_sql",
                                "arguments": {
                                    "sql": "SELECT COUNT(*) as count FROM contacts",
                                    "confirm": True,
                                    "reason": "Count contacts for user query",
                                },
                            },
                        }
                    ],
                }
            }
        )

        # Mock final response after tool calling
        mock_final_response = Mock()
        mock_final_response.raise_for_status.return_value = None
        mock_final_response.headers = {"Content-Type": "application/json"}
        mock_final_response.text = json.dumps(
            {
                "message": {
                    "role": "assistant",
                    "content": "You have 1810 contacts in your database.",
                }
            }
        )

        with patch("requests.post") as mock_post:
            mock_post.side_effect = [mock_response, mock_final_response]

            # Test that tool calling works with dict arguments
            result = ollama_llm.chat("How many contacts are in the database?")

            # Verify the result
            assert "You have 1810 contacts in your database." in result
            assert "Error processing response" not in result
            assert "JSON object must be str" not in result

    def test_tool_call_with_malformed_json_arguments(self, ollama_llm, mock_api):
        """Test tool calling with malformed JSON string arguments."""
        # Mock the HTTP response for tool calling with malformed JSON
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = json.dumps(
            {
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "function": {
                                "name": "execute_sql",
                                "arguments": '{"sql": "SELECT COUNT(*) as count FROM contacts", "confirm": true, "reason": ',  # Malformed JSON
                            },
                        }
                    ],
                }
            }
        )

        # Mock final response after tool calling
        mock_final_response = Mock()
        mock_final_response.raise_for_status.return_value = None
        mock_final_response.headers = {"Content-Type": "application/json"}
        mock_final_response.text = json.dumps(
            {
                "message": {
                    "role": "assistant",
                    "content": "I encountered an error while processing your request.",
                }
            }
        )

        with patch("requests.post") as mock_post:
            mock_post.side_effect = [mock_response, mock_final_response]

            # Test that malformed JSON is handled gracefully
            result = ollama_llm.chat("How many contacts are in the database?")

            # Should not crash with JSON parsing error
            assert "Error processing response: the JSON object must be str" not in result
            assert isinstance(result, str)

    def test_tool_call_with_unexpected_argument_type(self, ollama_llm, mock_api):
        """Test tool calling with unexpected argument types (e.g., list, int)."""
        # Mock the HTTP response for tool calling with unexpected argument type
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = json.dumps(
            {
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "function": {
                                "name": "execute_sql",
                                "arguments": [
                                    "invalid",
                                    "argument",
                                    "list",
                                ],  # Unexpected list type
                            },
                        }
                    ],
                }
            }
        )

        # Mock final response after tool calling
        mock_final_response = Mock()
        mock_final_response.raise_for_status.return_value = None
        mock_final_response.headers = {"Content-Type": "application/json"}
        mock_final_response.text = json.dumps(
            {
                "message": {
                    "role": "assistant",
                    "content": "I encountered an error while processing your request.",
                }
            }
        )

        with patch("requests.post") as mock_post:
            mock_post.side_effect = [mock_response, mock_final_response]

            # Test that unexpected argument types are handled gracefully
            result = ollama_llm.chat("How many contacts are in the database?")

            # Should not crash with type error
            assert "Error processing response: the JSON object must be str" not in result
            assert isinstance(result, str)

    def test_tool_call_without_arguments(self, ollama_llm, mock_api):
        """Test tool calling when no arguments are provided."""
        # Mock the HTTP response for tool calling without arguments
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = json.dumps(
            {
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "function": {
                                "name": "get_contacts_with_images",
                                "arguments": "{}",  # Empty arguments
                            },
                        }
                    ],
                }
            }
        )

        # Mock final response after tool calling
        mock_final_response = Mock()
        mock_final_response.raise_for_status.return_value = None
        mock_final_response.headers = {"Content-Type": "application/json"}
        mock_final_response.text = json.dumps(
            {
                "message": {
                    "role": "assistant",
                    "content": "Here are the contacts with profile images.",
                }
            }
        )

        with patch("requests.post") as mock_post:
            mock_post.side_effect = [mock_response, mock_final_response]

            # Test that empty arguments work correctly
            result = ollama_llm.chat("Show me contacts with images")

            # Should work without issues
            assert "Error processing response" not in result
            assert isinstance(result, str)

    def test_multiple_tool_calls_mixed_argument_types(self, ollama_llm, mock_api):
        """Test multiple tool calls with mixed argument types."""
        # Mock the HTTP response for multiple tool calls
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = json.dumps(
            {
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "function": {
                                "name": "search_contacts",
                                "arguments": '{"query": "John"}',  # String format
                            },
                        },
                        {
                            "id": "call_2",
                            "function": {
                                "name": "execute_sql",
                                "arguments": {  # Dict format
                                    "sql": "SELECT COUNT(*) as count FROM contacts",
                                    "confirm": True,
                                    "reason": "Count total contacts",
                                },
                            },
                        },
                    ],
                }
            }
        )

        # Mock final response after tool calling
        mock_final_response = Mock()
        mock_final_response.raise_for_status.return_value = None
        mock_final_response.headers = {"Content-Type": "application/json"}
        mock_final_response.text = json.dumps(
            {
                "message": {
                    "role": "assistant",
                    "content": "I found some contacts named John and you have 1810 total contacts.",
                }
            }
        )

        with patch("requests.post") as mock_post:
            mock_post.side_effect = [mock_response, mock_final_response]

            # Test that mixed argument types work correctly
            result = ollama_llm.chat("Find John and tell me total contact count")

            # Should handle both argument types without issues
            assert "Error processing response" not in result
            assert "JSON object must be str" not in result
            assert isinstance(result, str)


@pytest.mark.integration
class TestChatScreenToolCalling:
    """Integration tests for chat screen tool calling functionality."""

    def test_database_query_integration(self, test_db):
        """Test actual database queries through chat interface."""
        db, fixtures = test_db

        # This would require setting up the actual TUI chat screen
        # For now, we'll test the core LLM functionality
        config = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config)

        with patch("prt_src.llm_ollama.LLMConfigManager") as mock_config_mgr:
            mock_config = Mock()
            mock_config.llm.base_url = "http://localhost:11434"
            mock_config.llm.model = "gpt-oss:20b"
            mock_config.llm.keep_alive = "30m"
            mock_config.llm.timeout = 300
            mock_config.llm.temperature = 0.7
            mock_config.tools.disabled_tools = []
            mock_config_mgr.return_value = mock_config

            ollama_llm = OllamaLLM(api, config_manager=mock_config_mgr.return_value)

            # Test that database queries can be processed
            # (This would actually call Ollama if running, so we mock it)
            with patch("requests.post") as mock_post:
                mock_response = Mock()
                mock_response.raise_for_status.return_value = None
                mock_response.headers = {"Content-Type": "application/json"}
                mock_response.text = json.dumps(
                    {
                        "message": {
                            "role": "assistant",
                            "content": "You have 6 contacts in your database.",
                        }
                    }
                )
                mock_post.return_value = mock_response

                result = ollama_llm.chat("How many contacts are in the database?")

                # Verify no JSON parsing errors
                assert "Error processing response" not in result
                assert "JSON object must be str" not in result
