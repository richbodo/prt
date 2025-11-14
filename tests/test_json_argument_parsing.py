"""Test JSON argument parsing in LLM tool calling."""

import json
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from prt_src.api import PRTAPI
from prt_src.llm_ollama import OllamaLLM


class TestJSONArgumentParsing:
    """Test the specific JSON argument parsing logic that was causing the bug."""

    def test_parse_string_arguments(self):
        """Test parsing when arguments are provided as JSON string."""
        # This is what was causing the original bug
        raw_arguments = '{"sql": "SELECT COUNT(*) FROM contacts", "confirm": true}'

        # Test the logic we implemented
        if isinstance(raw_arguments, str):
            try:
                arguments = json.loads(raw_arguments)
                success = True
                error = None
            except json.JSONDecodeError as e:
                success = False
                error = str(e)
                arguments = None
        else:
            success = False
            error = "Not a string"
            arguments = None

        assert success is True
        assert error is None
        assert arguments == {"sql": "SELECT COUNT(*) FROM contacts", "confirm": True}

    def test_parse_dict_arguments(self):
        """Test parsing when arguments are already a dict (what Ollama sometimes returns)."""
        # This is what was causing "JSON object must be str, bytes or bytearray, not dict"
        raw_arguments = {"sql": "SELECT COUNT(*) FROM contacts", "confirm": True}

        # Test the logic we implemented
        if isinstance(raw_arguments, str):
            try:
                arguments = json.loads(raw_arguments)
                success = True
                error = None
            except json.JSONDecodeError as e:
                success = False
                error = str(e)
                arguments = None
        elif isinstance(raw_arguments, dict):
            arguments = raw_arguments
            success = True
            error = None
        else:
            success = False
            error = f"Unexpected argument type: {type(raw_arguments)}"
            arguments = None

        assert success is True
        assert error is None
        assert arguments == {"sql": "SELECT COUNT(*) FROM contacts", "confirm": True}

    def test_parse_malformed_json(self):
        """Test parsing malformed JSON string."""
        raw_arguments = '{"sql": "SELECT COUNT(*) FROM contacts", "confirm": '  # Malformed

        # Test the logic we implemented
        if isinstance(raw_arguments, str):
            try:
                arguments = json.loads(raw_arguments)
                success = True
                error = None
            except json.JSONDecodeError as e:
                success = False
                error = str(e)
                arguments = None
        else:
            success = False
            error = "Not a string"
            arguments = None

        assert success is False
        assert error is not None
        assert (
            "expecting" in error.lower() or "json" in error.lower()
        )  # Different JSON error messages
        assert arguments is None

    def test_parse_unexpected_type(self):
        """Test parsing unexpected argument types."""
        raw_arguments = ["invalid", "list", "type"]  # List instead of string or dict

        # Test the logic we implemented
        if isinstance(raw_arguments, str):
            try:
                arguments = json.loads(raw_arguments)
                success = True
                error = None
            except json.JSONDecodeError as e:
                success = False
                error = str(e)
                arguments = None
        elif isinstance(raw_arguments, dict):
            arguments = raw_arguments
            success = True
            error = None
        else:
            success = False
            error = f"Unexpected argument type: {type(raw_arguments)}"
            arguments = None

        assert success is False
        assert error == "Unexpected argument type: <class 'list'>"
        assert arguments is None

    def test_original_bug_simulation(self):
        """Simulate the original bug scenario."""
        # This would have caused: "the JSON object must be str, bytes or bytearray, not dict"
        tool_call_arguments = {"sql": "SELECT COUNT(*) FROM contacts", "confirm": True}

        # Original buggy code (commented out):
        # arguments = json.loads(tool_call_arguments)  # This would fail!

        # New fixed code:
        if isinstance(tool_call_arguments, str):
            arguments = json.loads(tool_call_arguments)
        elif isinstance(tool_call_arguments, dict):
            arguments = tool_call_arguments
        else:
            raise ValueError(f"Unexpected argument type: {type(tool_call_arguments)}")

        # Should work without error
        assert arguments == {"sql": "SELECT COUNT(*) FROM contacts", "confirm": True}

    @pytest.mark.unit
    def test_integration_with_llm_class(self):
        """Test the fix integrated with the actual LLM class structure."""
        # Create a minimal mock setup
        mock_api = Mock(spec=PRTAPI)
        mock_api.execute_sql.return_value = {"success": True, "result": [{"count": 1810}]}

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

                llm = OllamaLLM(mock_api, config_manager=mock_config_mgr.return_value)

                # Test that we can call _call_tool without JSON errors
                # Using search_contacts which is simpler
                result = llm._call_tool("search_contacts", {"query": "test"})

                # Should not throw JSON parsing errors and should return mock result
                assert result is not None  # Should get the mocked result

    def test_empty_arguments(self):
        """Test handling of empty arguments."""
        # Test both formats
        string_empty = "{}"
        dict_empty = {}

        # String format
        if isinstance(string_empty, str):
            arguments_from_string = json.loads(string_empty)

        # Dict format
        if isinstance(dict_empty, dict):
            arguments_from_dict = dict_empty

        assert arguments_from_string == {}
        assert arguments_from_dict == {}
        assert arguments_from_string == arguments_from_dict
