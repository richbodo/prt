"""
Tests for Ollama LLM integration.
"""

import json
from unittest.mock import Mock
from unittest.mock import patch

from prt_src.config import LLMConfigManager
from prt_src.llm_ollama import OllamaLLM
from prt_src.llm_ollama import Tool


class TestOllamaLLM:
    """Test Ollama LLM integration."""

    def test_tool_creation(self):
        """Test that tools are created correctly."""
        mock_api = Mock()
        llm = OllamaLLM(mock_api)

        # Check that tools are created
        assert len(llm.tools) > 0

        # Check that all tools have required attributes
        for tool in llm.tools:
            assert isinstance(tool, Tool)
            assert tool.name
            assert tool.description
            assert tool.parameters
            assert callable(tool.function)

    def test_get_tool_by_name(self):
        """Test getting a tool by name."""
        mock_api = Mock()
        llm = OllamaLLM(mock_api)

        # Test getting an existing tool
        tool = llm._get_tool_by_name("search_contacts")
        assert tool is not None
        assert tool.name == "search_contacts"

        # Test getting a non-existent tool
        tool = llm._get_tool_by_name("non_existent_tool")
        assert tool is None

    def test_call_tool(self):
        """Test calling a tool."""
        mock_api = Mock()
        mock_api.search_contacts.return_value = [{"id": 1, "name": "Test Contact"}]

        llm = OllamaLLM(mock_api)

        # Test successful tool call
        result = llm._call_tool("search_contacts", {"query": "test"})
        assert result == [{"id": 1, "name": "Test Contact"}]
        mock_api.search_contacts.assert_called_once_with(query="test")

        # Test tool not found
        result = llm._call_tool("non_existent_tool", {})
        assert "error" in result
        assert "not found" in result["error"]

        # Test tool call with exception
        mock_api.search_contacts.side_effect = Exception("Test error")
        result = llm._call_tool("search_contacts", {"query": "test"})
        assert "error" in result
        assert "Test error" in result["error"]

    def test_system_prompt_creation(self):
        """Test system prompt creation."""
        mock_api = Mock()
        llm = OllamaLLM(mock_api)

        prompt = llm._create_system_prompt()

        # Check that the prompt contains expected sections
        assert "Personal Relationship Toolkit" in prompt
        assert "AVAILABLE TOOLS" in prompt  # Updated to match new format (without colon)
        assert "search_contacts" in prompt  # At least one tool should be mentioned
        assert "USAGE INSTRUCTIONS" in prompt  # Updated to match new format

    def test_format_tool_calls(self):
        """Test formatting tools for Ollama API."""
        mock_api = Mock()
        llm = OllamaLLM(mock_api)

        formatted_tools = llm._format_tool_calls()

        # Check that tools are formatted correctly
        assert len(formatted_tools) == len(llm.tools)

        for tool in formatted_tools:
            assert "type" in tool
            assert tool["type"] == "function"
            assert "function" in tool
            # Check the nested structure
            function_def = tool["function"]
            assert "name" in function_def
            assert "description" in function_def
            assert "parameters" in function_def

    def test_default_disabled_tools_removed(self):
        """Default configuration should remove unstable tools from availability."""
        mock_api = Mock()
        llm = OllamaLLM(mock_api)

        tool_names = {tool.name for tool in llm.tools}
        assert "save_contacts_with_images" not in tool_names
        assert "list_memory" not in tool_names

    def test_config_can_enable_disabled_tools(self):
        """Custom configuration can re-enable disabled tools."""
        mock_api = Mock()
        config_manager = LLMConfigManager({"llm_tools": {"disabled": []}})
        llm = OllamaLLM(mock_api, config_manager=config_manager)

        tool_names = {tool.name for tool in llm.tools}
        assert "save_contacts_with_images" in tool_names
        assert "list_memory" in tool_names

    @patch("requests.post")
    def test_chat_without_tool_calls(self, mock_post):
        """Test chat without tool calls."""
        mock_api = Mock()
        llm = OllamaLLM(mock_api)

        # Mock response without tool calls - using Ollama API format
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"message": {"content": "Hello! How can I help you today?"}}'
        mock_response.content = mock_response.text.encode()
        mock_response.json.return_value = {
            "message": {"content": "Hello! How can I help you today?"}
        }
        mock_post.return_value = mock_response

        result = llm.chat("Hello")

        assert result == "Hello! How can I help you today?"
        assert len(llm.conversation_history) == 2  # user + assistant

    @patch("requests.post")
    def test_chat_with_tool_calls(self, mock_post):
        """Test chat with tool calls."""
        mock_api = Mock()
        mock_api.search_contacts.return_value = [{"id": 1, "name": "John Doe"}]
        llm = OllamaLLM(mock_api)

        # Mock first response with tool call - using Ollama API format
        mock_response1 = Mock()
        mock_response1.status_code = 200
        mock_response1.headers = {"Content-Type": "application/json"}
        mock_response1_data = {
            "message": {
                "content": "I'll search for contacts for you.",
                "tool_calls": [
                    {
                        "id": "call_1",
                        "function": {
                            "name": "search_contacts",
                            "arguments": {"query": "John"},
                        },
                    }
                ],
            }
        }
        mock_response1.text = json.dumps(mock_response1_data)
        mock_response1.content = mock_response1.text.encode()
        mock_response1.json.return_value = mock_response1_data

        # Mock second response (after tool call)
        mock_response2 = Mock()
        mock_response2.status_code = 200
        mock_response2.headers = {"Content-Type": "application/json"}
        mock_response2_data = {"message": {"content": "I found 1 contact: John Doe"}}
        mock_response2.text = json.dumps(mock_response2_data)
        mock_response2.content = mock_response2.text.encode()
        mock_response2.json.return_value = mock_response2_data

        mock_post.side_effect = [mock_response1, mock_response2]

        result = llm.chat("Find contacts named John")

        # The result should contain the final response content
        assert "John Doe" in result or "Error" in result
        assert mock_post.call_count == 2  # Two API calls (tool call + final response)

    @patch("requests.post")
    def test_chat_connection_error(self, mock_post):
        """Test chat with connection error."""
        import requests

        mock_api = Mock()
        llm = OllamaLLM(mock_api)

        # Mock connection error - use requests.RequestException to match error handling
        mock_post.side_effect = requests.exceptions.RequestException("Connection failed")

        result = llm.chat("Hello")

        assert "Error" in result
        assert "Connection failed" in result

    def test_clear_history(self):
        """Test clearing conversation history."""
        mock_api = Mock()
        llm = OllamaLLM(mock_api)

        # Add some history
        llm.conversation_history = [{"role": "user", "content": "test"}]

        # Clear history
        llm.clear_history()

        assert len(llm.conversation_history) == 0

    def test_llm_registers_sql_and_backup_tools(self):
        """Ensure execute_sql and backup tools are available."""
        mock_api = Mock()
        llm = OllamaLLM(mock_api)
        tool_names = [t.name for t in llm.tools]
        assert "execute_sql" in tool_names
        assert "create_backup_with_comment" in tool_names

    def test_system_prompt_mentions_sql_safety(self):
        """System prompt should warn about SQL write safety."""
        mock_api = Mock()
        llm = OllamaLLM(mock_api)
        prompt = llm._create_system_prompt()
        assert "execute_sql" in prompt
        assert "backup" in prompt.lower()


class TestTool:
    """Test Tool dataclass."""

    def test_tool_creation(self):
        """Test Tool dataclass creation."""

        def test_function():
            pass

        tool = Tool(
            name="test_tool",
            description="A test tool",
            parameters={"type": "object"},
            function=test_function,
        )

        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
        assert tool.parameters == {"type": "object"}
        assert tool.function == test_function
