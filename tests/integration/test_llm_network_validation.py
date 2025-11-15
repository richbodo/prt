"""Integration tests for LLM network request validation.

Tests that the Ollama LLM client properly validates HTTP responses
and handles malicious or malformed responses safely.

These tests use mocks to avoid network dependencies and ensure fast execution.
"""

from unittest.mock import Mock
from unittest.mock import patch

import pytest

from prt_src.llm_ollama import ALLOWED_CONTENT_TYPES
from prt_src.llm_ollama import MAX_RESPONSE_SIZE_BYTES
from prt_src.llm_ollama import MAX_RESPONSE_SIZE_WARNING
from prt_src.llm_ollama import OllamaLLM


@pytest.mark.integration
class TestLLMNetworkValidation:
    """Test network request validation in OllamaLLM."""

    def setup_method(self):
        """Set up test instance."""
        # Create a mock API for testing
        mock_api = Mock()
        self.llm = OllamaLLM(mock_api)

    def test_validate_response_valid_json(self):
        """Test validation of valid JSON response."""
        mock_response = Mock()
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.content = b'{"test": "data"}'
        mock_response.text = '{"test": "data"}'
        mock_response.iter_content.return_value = [b'{"test": "data"}']

        result = self.llm._validate_and_parse_response(mock_response, "test")

        assert result == {"test": "data"}

    def test_validate_response_valid_json_with_charset(self):
        """Test validation of valid JSON response with charset."""
        mock_response = Mock()
        mock_response.headers = {"Content-Type": "application/json; charset=utf-8"}
        mock_response.content = b'{"test": "data"}'
        mock_response.text = '{"test": "data"}'
        mock_response.iter_content.return_value = [b'{"test": "data"}']

        result = self.llm._validate_and_parse_response(mock_response, "test")

        assert result == {"test": "data"}

    def test_validate_response_invalid_content_type_html(self):
        """Test rejection of HTML content type."""
        mock_response = Mock()
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.content = b"<html><body>Error</body></html>"
        mock_response.text = "<html><body>Error</body></html>"
        mock_response.iter_content.return_value = [b"<html><body>Error</body></html>"]

        with pytest.raises(ValueError, match="Invalid Content-Type"):
            self.llm._validate_and_parse_response(mock_response, "test")

    def test_validate_response_invalid_content_type_plain_text(self):
        """Test rejection of plain text content type."""
        mock_response = Mock()
        mock_response.headers = {"Content-Type": "text/plain"}
        mock_response.content = b"Error message"
        mock_response.text = "Error message"
        mock_response.iter_content.return_value = [b"Error message"]

        with pytest.raises(ValueError, match="Invalid Content-Type"):
            self.llm._validate_and_parse_response(mock_response, "test")

    def test_validate_response_missing_content_type(self):
        """Test handling of missing content-type header."""
        mock_response = Mock()
        mock_response.headers = {}
        mock_response.content = b'{"test": "data"}'
        mock_response.text = '{"test": "data"}'
        mock_response.iter_content.return_value = [b'{"test": "data"}']

        with pytest.raises(ValueError, match="Invalid Content-Type"):
            self.llm._validate_and_parse_response(mock_response, "test")

    def test_validate_response_oversized_content_length(self):
        """Test rejection of oversized response via Content-Length."""
        mock_response = Mock()
        mock_response.headers = {
            "Content-Type": "application/json",
            "Content-Length": str(11 * 1024 * 1024),  # 11MB > 10MB limit
        }
        # Content should simulate large size
        mock_response.content = b"x" * (11 * 1024 * 1024)
        mock_response.text = "x" * (11 * 1024 * 1024)

        with pytest.raises(ValueError, match="Response size.*exceeds maximum"):
            self.llm._validate_and_parse_response(mock_response, "test")

    def test_validate_response_oversized_while_reading(self):
        """Test rejection of oversized response while reading."""
        mock_response = Mock()
        mock_response.headers = {"Content-Type": "application/json"}

        # Simulate reading chunks that exceed the limit
        large_chunk = b"x" * (6 * 1024 * 1024)  # 6MB chunks
        mock_response.content = large_chunk + large_chunk  # Total: 12MB
        mock_response.text = (large_chunk + large_chunk).decode()
        mock_response.iter_content.return_value = [large_chunk, large_chunk]  # Total: 12MB

        with pytest.raises(ValueError, match="Response size.*exceeds maximum"):
            self.llm._validate_and_parse_response(mock_response, "test")

    def test_validate_response_large_response_warning(self):
        """Test warning for large but acceptable response."""
        mock_response = Mock()
        mock_response.headers = {
            "Content-Type": "application/json",  # Use proper case
            "Content-Length": str(6 * 1024 * 1024),  # 6MB (> 5MB warning threshold)
        }
        large_content = b'{"large": "' + b"x" * (6 * 1024 * 1024 - 20) + b'"}'
        mock_response.content = large_content
        mock_response.text = large_content.decode()
        mock_response.iter_content.return_value = [large_content]

        with patch("prt_src.llm_ollama.logger") as mock_logger:
            result = self.llm._validate_and_parse_response(mock_response, "test")

            # Should succeed but log warning
            assert result is not None
            mock_logger.warning.assert_called()

    def test_validate_response_malformed_json(self):
        """Test handling of malformed JSON."""
        mock_response = Mock()
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.content = b'{"invalid": json}'
        mock_response.text = '{"invalid": json}'
        mock_response.iter_content.return_value = [b'{"invalid": json}']

        with pytest.raises(ValueError, match="Invalid JSON response"):
            self.llm._validate_and_parse_response(mock_response, "test")

    def test_validate_response_truncated_json(self):
        """Test handling of truncated JSON."""
        mock_response = Mock()
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.content = b'{"incomplete":'
        mock_response.text = '{"incomplete":'
        mock_response.iter_content.return_value = [b'{"incomplete":']

        with pytest.raises(ValueError, match="Invalid JSON response"):
            self.llm._validate_and_parse_response(mock_response, "test")

    def test_validate_response_empty_response(self):
        """Test handling of empty response."""
        mock_response = Mock()
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.content = b""
        mock_response.text = ""
        mock_response.iter_content.return_value = [b""]

        with pytest.raises(ValueError, match="Invalid JSON response"):
            self.llm._validate_and_parse_response(mock_response, "test")

    @pytest.mark.asyncio
    async def test_health_check_with_validation(self):
        """Test health_check uses validation."""
        with (
            patch.object(self.llm, "_validate_and_parse_response") as mock_validate,
            patch("requests.get") as mock_get,
        ):
            mock_response = Mock()
            mock_response.status_code = 200  # Add missing status code
            mock_get.return_value = mock_response
            mock_validate.return_value = {"status": "ok"}

            result = await self.llm.health_check()

            assert result is True
            mock_validate.assert_called_once_with(mock_response, "health_check")

    @pytest.mark.asyncio
    async def test_health_check_validation_fails(self):
        """Test health_check when validation fails."""
        with (
            patch.object(self.llm, "_validate_and_parse_response") as mock_validate,
            patch("requests.get") as mock_get,
        ):
            mock_response = Mock()
            mock_response.status_code = 200  # Add missing status code
            mock_get.return_value = mock_response
            mock_validate.side_effect = ValueError(
                "Validation failed"
            )  # Make validation raise exception

            result = await self.llm.health_check()

            assert result is False

    @pytest.mark.asyncio
    async def test_preload_model_with_validation(self):
        """Test preload_model uses validation."""
        with (
            patch.object(self.llm, "_validate_and_parse_response") as mock_validate,
            patch("requests.post") as mock_post,
        ):
            mock_response = Mock()
            mock_response.status_code = 200  # Add missing status code
            mock_post.return_value = mock_response
            mock_validate.return_value = {"status": "success"}

            result = await self.llm.preload_model()

            assert result is True
            mock_validate.assert_called_once_with(mock_response, "preload_model")

    @pytest.mark.asyncio
    async def test_preload_model_validation_fails(self):
        """Test preload_model when validation fails."""
        with (
            patch.object(self.llm, "_validate_and_parse_response") as mock_validate,
            patch("requests.post") as mock_post,
        ):
            mock_response = Mock()
            mock_response.status_code = 200  # Add missing status code
            mock_post.return_value = mock_response
            mock_validate.side_effect = ValueError(
                "Validation failed"
            )  # Make validation raise exception

            result = await self.llm.preload_model()

            assert result is False

    def test_chat_with_validation(self):
        """Test chat method uses validation for main response."""
        with (
            patch.object(self.llm, "_validate_and_parse_response") as mock_validate,
            patch("requests.post") as mock_post,
        ):
            mock_response = Mock()
            mock_response.status_code = 200  # Add missing status code
            mock_response.raise_for_status.return_value = None  # Mock raise_for_status method
            mock_post.return_value = mock_response
            mock_validate.return_value = {"message": {"content": "Hello!"}, "done": True}

            response = self.llm.chat("Hello")

            assert "Hello!" in response
            mock_validate.assert_called_with(mock_response, "chat")

    def test_chat_validation_fails_main_response(self):
        """Test chat method when main response validation fails."""
        with (
            patch.object(self.llm, "_validate_and_parse_response") as mock_validate,
            patch("requests.post") as mock_post,
        ):
            mock_response = Mock()
            mock_response.status_code = 200  # Add missing status code
            mock_response.raise_for_status.return_value = None  # Mock raise_for_status method
            mock_post.return_value = mock_response
            mock_validate.side_effect = ValueError(
                "Validation failed"
            )  # Make validation raise exception

            result = self.llm.chat("Hello")
            # Chat method handles exceptions gracefully and returns error message
            assert "Error" in result

    def test_security_constants_defined(self):
        """Test that security constants are properly defined."""
        # Test module-level constants
        assert MAX_RESPONSE_SIZE_BYTES == 10 * 1024 * 1024  # 10MB
        assert MAX_RESPONSE_SIZE_WARNING == 5 * 1024 * 1024  # 5MB
        assert "application/json" in ALLOWED_CONTENT_TYPES

    def test_validation_prevents_memory_exhaustion(self):
        """Test that validation prevents memory exhaustion attacks."""
        mock_response = Mock()
        mock_response.headers = {
            "Content-Type": "application/json",
            "Content-Length": str(100 * 1024 * 1024),  # 100MB attack
        }
        # Large content to simulate memory exhaustion attack
        mock_response.content = b"x" * (100 * 1024 * 1024)
        mock_response.text = "x" * (100 * 1024 * 1024)

        with pytest.raises(ValueError, match="Response size.*exceeds maximum"):
            self.llm._validate_and_parse_response(mock_response, "test")

        # Should reject without trying to read the response
        mock_response.iter_content.assert_not_called()

    def test_validation_prevents_type_confusion(self):
        """Test that validation prevents type confusion attacks."""
        mock_response = Mock()
        mock_response.headers = {"Content-Type": "application/javascript"}
        mock_response.content = b'alert("xss")'
        mock_response.text = 'alert("xss")'
        mock_response.iter_content.return_value = [b'alert("xss")']

        with pytest.raises(ValueError, match="Invalid Content-Type"):
            self.llm._validate_and_parse_response(mock_response, "test")
