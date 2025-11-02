"""Integration tests for LLM network request validation.

Tests that the Ollama LLM client properly validates HTTP responses
and handles malicious or malformed responses safely.
"""

from unittest.mock import Mock
from unittest.mock import patch

import pytest

from prt_src.llm_ollama import OllamaLLM


class TestLLMNetworkValidation:
    """Test network request validation in OllamaLLM."""

    def setup_method(self):
        """Set up test instance."""
        self.llm = OllamaLLM()

    def test_validate_response_valid_json(self):
        """Test validation of valid JSON response."""
        mock_response = Mock()
        mock_response.headers = {"content-type": "application/json"}
        mock_response.iter_content.return_value = [b'{"test": "data"}']

        result = self.llm._validate_and_parse_response(mock_response, "test")

        assert result == {"test": "data"}

    def test_validate_response_valid_json_with_charset(self):
        """Test validation of valid JSON response with charset."""
        mock_response = Mock()
        mock_response.headers = {"content-type": "application/json; charset=utf-8"}
        mock_response.iter_content.return_value = [b'{"test": "data"}']

        result = self.llm._validate_and_parse_response(mock_response, "test")

        assert result == {"test": "data"}

    def test_validate_response_invalid_content_type_html(self):
        """Test rejection of HTML content type."""
        mock_response = Mock()
        mock_response.headers = {"content-type": "text/html"}
        mock_response.iter_content.return_value = [b"<html><body>Error</body></html>"]

        result = self.llm._validate_and_parse_response(mock_response, "test")

        assert result is None

    def test_validate_response_invalid_content_type_plain_text(self):
        """Test rejection of plain text content type."""
        mock_response = Mock()
        mock_response.headers = {"content-type": "text/plain"}
        mock_response.iter_content.return_value = [b"Error message"]

        result = self.llm._validate_and_parse_response(mock_response, "test")

        assert result is None

    def test_validate_response_missing_content_type(self):
        """Test handling of missing content-type header."""
        mock_response = Mock()
        mock_response.headers = {}
        mock_response.iter_content.return_value = [b'{"test": "data"}']

        result = self.llm._validate_and_parse_response(mock_response, "test")

        assert result is None

    def test_validate_response_oversized_content_length(self):
        """Test rejection of oversized response via Content-Length."""
        mock_response = Mock()
        mock_response.headers = {
            "content-type": "application/json",
            "content-length": str(11 * 1024 * 1024),  # 11MB > 10MB limit
        }

        result = self.llm._validate_and_parse_response(mock_response, "test")

        assert result is None

    def test_validate_response_oversized_while_reading(self):
        """Test rejection of oversized response while reading."""
        mock_response = Mock()
        mock_response.headers = {"content-type": "application/json"}

        # Simulate reading chunks that exceed the limit
        large_chunk = b"x" * (6 * 1024 * 1024)  # 6MB chunks
        mock_response.iter_content.return_value = [large_chunk, large_chunk]  # Total: 12MB

        result = self.llm._validate_and_parse_response(mock_response, "test")

        assert result is None

    def test_validate_response_large_response_warning(self):
        """Test warning for large but acceptable response."""
        mock_response = Mock()
        mock_response.headers = {
            "content-type": "application/json",
            "content-length": str(6 * 1024 * 1024),  # 6MB (> 5MB warning threshold)
        }
        mock_response.iter_content.return_value = [
            b'{"large": "' + b"x" * (6 * 1024 * 1024 - 20) + b'"}'
        ]

        with patch("prt_src.llm_ollama.logger") as mock_logger:
            result = self.llm._validate_and_parse_response(mock_response, "test")

            # Should succeed but log warning
            assert result is not None
            mock_logger.warning.assert_called()

    def test_validate_response_malformed_json(self):
        """Test handling of malformed JSON."""
        mock_response = Mock()
        mock_response.headers = {"content-type": "application/json"}
        mock_response.iter_content.return_value = [b'{"invalid": json}']

        result = self.llm._validate_and_parse_response(mock_response, "test")

        assert result is None

    def test_validate_response_truncated_json(self):
        """Test handling of truncated JSON."""
        mock_response = Mock()
        mock_response.headers = {"content-type": "application/json"}
        mock_response.iter_content.return_value = [b'{"incomplete":']

        result = self.llm._validate_and_parse_response(mock_response, "test")

        assert result is None

    def test_validate_response_empty_response(self):
        """Test handling of empty response."""
        mock_response = Mock()
        mock_response.headers = {"content-type": "application/json"}
        mock_response.iter_content.return_value = [b""]

        result = self.llm._validate_and_parse_response(mock_response, "test")

        assert result is None

    def test_health_check_with_validation(self):
        """Test health_check uses validation."""
        with patch.object(self.llm, "_validate_and_parse_response") as mock_validate:
            with patch("requests.get") as mock_get:
                mock_response = Mock()
                mock_get.return_value = mock_response
                mock_validate.return_value = {"status": "ok"}

                result = self.llm.health_check()

                assert result is True
                mock_validate.assert_called_once_with(mock_response, "health_check")

    def test_health_check_validation_fails(self):
        """Test health_check when validation fails."""
        with patch.object(self.llm, "_validate_and_parse_response") as mock_validate:
            with patch("requests.get") as mock_get:
                mock_response = Mock()
                mock_get.return_value = mock_response
                mock_validate.return_value = None  # Validation failure

                result = self.llm.health_check()

                assert result is False

    def test_preload_model_with_validation(self):
        """Test preload_model uses validation."""
        with patch.object(self.llm, "_validate_and_parse_response") as mock_validate:
            with patch("requests.post") as mock_post:
                mock_response = Mock()
                mock_post.return_value = mock_response
                mock_validate.return_value = {"status": "success"}

                result = self.llm.preload_model("test-model")

                assert result is True
                mock_validate.assert_called_once_with(mock_response, "preload_model")

    def test_preload_model_validation_fails(self):
        """Test preload_model when validation fails."""
        with patch.object(self.llm, "_validate_and_parse_response") as mock_validate:
            with patch("requests.post") as mock_post:
                mock_response = Mock()
                mock_post.return_value = mock_response
                mock_validate.return_value = None  # Validation failure

                result = self.llm.preload_model("test-model")

                assert result is False

    def test_chat_with_validation(self):
        """Test chat method uses validation for main response."""
        messages = [{"role": "user", "content": "Hello"}]

        with patch.object(self.llm, "_validate_and_parse_response") as mock_validate:
            with patch("requests.post") as mock_post:
                mock_response = Mock()
                mock_post.return_value = mock_response
                mock_validate.return_value = {"message": {"content": "Hello!"}, "done": True}

                response = self.llm.chat(messages, "test-model")

                assert response["message"]["content"] == "Hello!"
                mock_validate.assert_called_with(mock_response, "chat")

    def test_chat_validation_fails_main_response(self):
        """Test chat method when main response validation fails."""
        messages = [{"role": "user", "content": "Hello"}]

        with patch.object(self.llm, "_validate_and_parse_response") as mock_validate:
            with patch("requests.post") as mock_post:
                mock_response = Mock()
                mock_post.return_value = mock_response
                mock_validate.return_value = None  # Validation failure

                with pytest.raises(Exception):
                    self.llm.chat(messages, "test-model")

    def test_security_constants_defined(self):
        """Test that security constants are properly defined."""
        assert hasattr(self.llm, "MAX_RESPONSE_SIZE_BYTES")
        assert hasattr(self.llm, "MAX_RESPONSE_SIZE_WARNING")
        assert hasattr(self.llm, "ALLOWED_CONTENT_TYPES")

        assert self.llm.MAX_RESPONSE_SIZE_BYTES == 10 * 1024 * 1024  # 10MB
        assert self.llm.MAX_RESPONSE_SIZE_WARNING == 5 * 1024 * 1024  # 5MB
        assert "application/json" in self.llm.ALLOWED_CONTENT_TYPES

    def test_validation_prevents_memory_exhaustion(self):
        """Test that validation prevents memory exhaustion attacks."""
        mock_response = Mock()
        mock_response.headers = {
            "content-type": "application/json",
            "content-length": str(100 * 1024 * 1024),  # 100MB attack
        }

        result = self.llm._validate_and_parse_response(mock_response, "test")

        # Should reject without trying to read the response
        assert result is None
        mock_response.iter_content.assert_not_called()

    def test_validation_prevents_type_confusion(self):
        """Test that validation prevents type confusion attacks."""
        mock_response = Mock()
        mock_response.headers = {"content-type": "application/javascript"}
        mock_response.iter_content.return_value = [b'alert("xss")']

        result = self.llm._validate_and_parse_response(mock_response, "test")

        # Should reject JavaScript content
        assert result is None
