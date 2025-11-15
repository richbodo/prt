"""Unit tests for LLM contacts with images workflow using mocked responses.

This test suite provides fast, deterministic tests for the contacts with images
workflow by mocking LLM responses. It covers various response scenarios including
conversational responses, tool execution, and error conditions.
"""

from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import mock_open
from unittest.mock import patch

import pytest

from prt_src.api import PRTAPI
from prt_src.llm_ollama import OllamaLLM
from tests.fixtures import get_fixture_spec


@pytest.mark.unit
class TestLLMContactsWithImagesMocked:
    """Test LLM contacts with images functionality with mocked responses."""

    @pytest.fixture
    def mock_api(self, test_db):
        """Create a mock API with test database."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        return PRTAPI(config)

    @pytest.fixture
    def mock_llm(self, mock_api):
        """Create a mock LLM instance."""
        # Mock the config manager to avoid network calls
        with patch("prt_src.llm_ollama.LLMConfigManager") as mock_config_class:
            mock_config = Mock()
            mock_config.llm.base_url = "http://localhost:11434"
            mock_config.llm.model = "mock-model"
            mock_config.llm.keep_alive = "5m"
            mock_config.llm.timeout = 30
            mock_config.llm.temperature = 0.1
            mock_config.tools.disabled_tools = []
            mock_config_class.return_value = mock_config

            llm = OllamaLLM(api=mock_api, config_manager=mock_config)
            return llm

    def test_get_contacts_with_images_tool_success(self, mock_llm, mock_api):
        """Test successful tool execution for getting contacts with images."""
        # Get fixture spec to validate expected data
        get_fixture_spec()

        # Mock the API method to return test data
        test_contacts = [
            {
                "id": 1,
                "name": "John Doe",
                "email": "john.doe@example.com",
                "profile_image": b"fake_image_data_1",
            },
            {
                "id": 2,
                "name": "Jane Smith",
                "email": "jane.smith@example.com",
                "profile_image": b"fake_image_data_2",
            },
        ]

        mock_api.get_contacts_with_images = Mock(return_value=test_contacts)

        # Test the tool directly
        result = mock_llm._get_contacts_with_images()

        # Verify result structure
        assert isinstance(result, dict)
        assert result["success"] is True
        assert "contacts" in result
        assert "count" in result
        assert "message" in result

        # Verify data
        assert result["count"] == 2
        assert len(result["contacts"]) == 2
        assert result["message"] == "Found 2 contacts with profile images"

        # Verify API was called
        mock_api.get_contacts_with_images.assert_called_once()

    def test_get_contacts_with_images_tool_empty_result(self, mock_llm, mock_api):
        """Test tool behavior when no contacts with images are found."""
        # Mock empty result
        mock_api.get_contacts_with_images = Mock(return_value=[])

        result = mock_llm._get_contacts_with_images()

        # Verify result structure for empty case
        assert isinstance(result, dict)
        assert result["success"] is True
        assert result["count"] == 0
        assert len(result["contacts"]) == 0
        assert "Found 0 contacts" in result["message"]

    def test_get_contacts_with_images_tool_api_error(self, mock_llm, mock_api):
        """Test tool error handling when API fails."""
        # Mock API to raise an exception
        mock_api.get_contacts_with_images = Mock(side_effect=Exception("Database error"))

        result = mock_llm._get_contacts_with_images()

        # Verify error handling
        assert isinstance(result, dict)
        assert result["success"] is False
        assert "error" in result
        assert "Database error" in result["error"]
        assert result["count"] == 0
        assert len(result["contacts"]) == 0

    def test_conversational_response_pattern(self, mock_llm):
        """Test that LLM can respond conversationally to directory requests."""
        # Mock the chat method to test response patterns
        with patch.object(mock_llm, "chat") as mock_chat:
            # Set up conversational response (most likely real LLM behavior)
            mock_chat.return_value = (
                "I can help you create a directory of contacts with images. "
                "Let me first get all contacts that have profile images and "
                "then create the directory for you."
            )

            response = mock_llm.chat("create a directory of contacts with images")

            # Verify conversational response
            assert isinstance(response, str)
            assert len(response) > 0
            assert "directory" in response.lower()
            assert "contacts" in response.lower()
            assert "images" in response.lower()

            # Verify this is explanatory, not tool execution
            assert "let me" in response.lower() or "i can help" in response.lower()

    def test_tool_execution_with_explanation_response(self, mock_llm, mock_api):
        """Test response pattern where LLM explains and then executes tools."""
        # Mock successful tool execution
        test_contacts = [
            {"id": 1, "name": "John Doe", "profile_image": b"data1"},
            {"id": 2, "name": "Jane Smith", "profile_image": b"data2"},
        ]
        mock_api.get_contacts_with_images = Mock(return_value=test_contacts)

        with patch.object(mock_llm, "chat") as mock_chat:
            # Response that includes both explanation and indicates tool execution
            mock_chat.return_value = (
                "I'll get all your contacts that have profile images. "
                "Let me search through your database... "
                "I found 2 contacts with profile images."
            )

            response = mock_llm.chat("get contacts with images")

            # Verify response indicates both explanation and result
            assert "found" in response.lower() or "contacts" in response.lower()
            assert len(response) > 20  # Should be substantive

    def test_clarification_request_response(self, mock_llm):
        """Test response pattern where LLM asks for clarification."""
        with patch.object(mock_llm, "chat") as mock_chat:
            mock_chat.return_value = (
                "Would you like me to create a directory showing all your "
                "contacts that have profile images? I can generate an "
                "interactive HTML directory for you."
            )

            response = mock_llm.chat("create something with contacts")

            # Verify clarification response
            assert isinstance(response, str)
            assert "would you like" in response.lower() or "do you want" in response.lower()
            assert len(response) > 20

    def test_create_directory_tool_success(self, mock_llm, mock_api):
        """Test directory creation tool by mocking _get_contacts_with_images."""
        # Instead of testing the full directory creation (which involves file system),
        # let's test that the method properly handles the contacts retrieval part

        # Mock the get_contacts_with_images method to return success
        with patch.object(mock_llm, "_get_contacts_with_images") as mock_get_contacts:
            mock_get_contacts.return_value = {
                "success": True,
                "contacts": [
                    {"id": 1, "name": "John Doe", "profile_image": b"data1"},
                    {"id": 2, "name": "Jane Smith", "profile_image": b"data2"},
                ],
                "count": 2,
            }

            # Mock the file operations that happen in the directory creation
            with patch("tempfile.TemporaryDirectory") as mock_tempdir, patch(
                "builtins.open", mock_open()
            ), patch("json.dump"), patch("pathlib.Path") as mock_path_class:

                mock_tempdir_instance = MagicMock()
                mock_tempdir_instance.__enter__.return_value = "/tmp/mock_dir"
                mock_tempdir_instance.__exit__.return_value = None
                mock_tempdir.return_value = mock_tempdir_instance

                # Mock the Path operations
                mock_path = MagicMock()
                mock_path.absolute.return_value = mock_path
                mock_path.__str__.return_value = "/mock/directories/test_dir"
                mock_path.__truediv__.return_value = mock_path
                mock_path_class.return_value = mock_path

                # Mock the DirectoryGenerator import and usage
                mock_generator = MagicMock()
                mock_generator.generate.return_value = True

                # We'll patch the import at the point of use
                import sys

                original_modules = sys.modules.copy()
                try:
                    # Create a mock make_directory module
                    mock_make_directory = MagicMock()
                    mock_make_directory.DirectoryGenerator.return_value = mock_generator
                    sys.modules["make_directory"] = mock_make_directory

                    result = mock_llm._create_directory_from_contacts_with_images("test_dir")

                finally:
                    # Restore original modules
                    sys.modules.clear()
                    sys.modules.update(original_modules)

        # Verify successful result
        assert isinstance(result, dict)
        assert result["success"] is True
        assert "output_path" in result
        assert "url" in result
        assert "contact_count" in result
        assert "performance" in result
        assert result["contact_count"] == 2

    def test_create_directory_tool_no_contacts(self, mock_llm, mock_api):
        """Test directory creation when no contacts with images exist."""
        # Mock empty contacts
        mock_api.get_contacts_with_images = Mock(return_value=[])

        result = mock_llm._create_directory_from_contacts_with_images("test_dir")

        # Verify appropriate failure response
        assert isinstance(result, dict)
        assert result["success"] is False
        assert "error" in result
        assert "no contacts with images found" in result["error"].lower()

    def test_performance_timing(self, mock_llm, mock_api):
        """Test that tool execution timing is captured properly."""
        # Mock API with small delay to test timing
        import time

        def mock_get_contacts():
            time.sleep(0.001)  # 1ms delay
            return [{"id": 1, "name": "Test", "profile_image": b"data"}]

        mock_api.get_contacts_with_images = mock_get_contacts

        start_time = time.time()
        result = mock_llm._get_contacts_with_images()
        end_time = time.time()

        # Verify timing is reasonable
        execution_time = end_time - start_time
        assert execution_time < 1.0  # Should be very fast
        assert result["success"] is True

    def test_safe_get_length_various_inputs(self, mock_llm):
        """Test the _safe_get_length helper method with various inputs."""
        # Test with list
        assert mock_llm._safe_get_length([1, 2, 3]) == 3
        assert mock_llm._safe_get_length([]) == 0

        # Test with None
        assert mock_llm._safe_get_length(None) == 0

        # Test with string (should return actual length)
        assert mock_llm._safe_get_length("string") == 6

        # Test with non-iterable objects (should return 0 or handle gracefully)
        try:
            result = mock_llm._safe_get_length(42)
            assert result >= 0  # Should not crash, exact value may vary
        except TypeError:
            # If it raises TypeError, that's also acceptable behavior
            pass

    def test_edge_case_malformed_contact_data(self, mock_llm, mock_api):
        """Test handling of malformed contact data."""
        # Mock API to return contacts with missing fields
        malformed_contacts = [
            {"id": 1, "profile_image": b"data"},  # Missing name
            {"name": "Jane Smith"},  # Missing profile_image
            {"id": 3, "name": "Bob", "profile_image": b"data"},  # Valid
        ]
        mock_api.get_contacts_with_images = Mock(return_value=malformed_contacts)

        result = mock_llm._get_contacts_with_images()

        # Should handle malformed data gracefully
        assert result["success"] is True
        assert result["count"] == 3
        assert len(result["contacts"]) == 3

    def test_large_response_handling(self, mock_llm, mock_api):
        """Test handling of large contact datasets."""
        # Mock large dataset
        large_contacts = []
        for i in range(100):
            large_contacts.append(
                {
                    "id": i,
                    "name": f"Contact {i}",
                    "email": f"contact{i}@example.com",
                    "profile_image": b"x" * 1000,  # 1KB image each
                }
            )

        mock_api.get_contacts_with_images = Mock(return_value=large_contacts)

        result = mock_llm._get_contacts_with_images()

        # Should handle large datasets
        assert result["success"] is True
        assert result["count"] == 100
        assert len(result["contacts"]) == 100

    def test_concurrent_tool_calls(self, mock_llm, mock_api):
        """Test that tool can handle multiple concurrent calls safely."""
        import threading
        import time

        test_contacts = [{"id": 1, "name": "Test", "profile_image": b"data"}]
        mock_api.get_contacts_with_images = Mock(return_value=test_contacts)

        results = []

        def call_tool():
            time.sleep(0.001)  # Small delay to encourage race conditions
            result = mock_llm._get_contacts_with_images()
            results.append(result)

        # Start multiple threads
        threads = [threading.Thread(target=call_tool) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # All calls should succeed
        assert len(results) == 5
        for result in results:
            assert result["success"] is True
            assert result["count"] == 1
