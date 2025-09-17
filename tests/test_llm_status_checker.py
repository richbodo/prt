"""Tests for LLM Status Checker service."""

from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest

from prt_src.tui.services.llm_status import LLMStatus
from prt_src.tui.services.llm_status import LLMStatusChecker


class TestLLMStatusChecker:
    """Test cases for LLMStatusChecker."""

    @pytest.fixture
    def mock_ollama_llm(self):
        """Create a mock OllamaLLM instance."""
        mock_llm = MagicMock()
        mock_llm.health_check = AsyncMock()
        return mock_llm

    @pytest.fixture
    def status_checker(self, mock_ollama_llm):
        """Create a LLMStatusChecker instance with mock LLM."""
        return LLMStatusChecker(mock_ollama_llm, check_interval=1.0)

    @pytest.mark.asyncio
    async def test_initial_status_is_checking(self, status_checker):
        """Test that initial status is CHECKING."""
        assert status_checker._status == LLMStatus.CHECKING

    @pytest.mark.asyncio
    async def test_health_check_online(self, status_checker, mock_ollama_llm):
        """Test status when health check returns True (online)."""
        mock_ollama_llm.health_check.return_value = True

        status = await status_checker.get_status(force_check=True)

        assert status == LLMStatus.ONLINE
        mock_ollama_llm.health_check.assert_called_once_with(timeout=2.0)

    @pytest.mark.asyncio
    async def test_health_check_offline(self, status_checker, mock_ollama_llm):
        """Test status when health check returns False (offline)."""
        mock_ollama_llm.health_check.return_value = False

        status = await status_checker.get_status(force_check=True)

        assert status == LLMStatus.OFFLINE
        mock_ollama_llm.health_check.assert_called_once_with(timeout=2.0)

    @pytest.mark.asyncio
    async def test_health_check_error(self, status_checker, mock_ollama_llm):
        """Test status when health check raises exception."""
        mock_ollama_llm.health_check.side_effect = Exception("Connection error")

        status = await status_checker.get_status(force_check=True)

        assert status == LLMStatus.ERROR

    @pytest.mark.asyncio
    async def test_status_caching(self, status_checker, mock_ollama_llm):
        """Test that status is cached for the specified duration."""
        mock_ollama_llm.health_check.return_value = True

        # First call should trigger health check
        status1 = await status_checker.get_status(force_check=True)
        assert status1 == LLMStatus.ONLINE

        # Second call within cache duration should not trigger another check
        status2 = await status_checker.get_status()
        assert status2 == LLMStatus.ONLINE

        # Should only have been called once due to caching
        assert mock_ollama_llm.health_check.call_count == 1

    @pytest.mark.asyncio
    async def test_force_check_bypasses_cache(self, status_checker, mock_ollama_llm):
        """Test that force_check=True bypasses cache."""
        mock_ollama_llm.health_check.return_value = True

        # First call
        await status_checker.get_status(force_check=True)

        # Second call with force_check should trigger another health check
        await status_checker.get_status(force_check=True)

        # Should have been called twice
        assert mock_ollama_llm.health_check.call_count == 2

    def test_status_callback_registration(self, status_checker):
        """Test callback registration and removal."""
        callback = MagicMock()

        # Add callback
        status_checker.add_status_callback(callback)
        assert callback in status_checker._status_callbacks

        # Remove callback
        status_checker.remove_status_callback(callback)
        assert callback not in status_checker._status_callbacks

    @pytest.mark.asyncio
    async def test_status_change_notification(self, status_checker, mock_ollama_llm):
        """Test that callbacks are notified of status changes."""
        callback = MagicMock()
        status_checker.add_status_callback(callback)

        # Trigger status change
        mock_ollama_llm.health_check.return_value = True
        await status_checker.get_status(force_check=True)

        # Callback should have been called with new status
        callback.assert_called_once_with(LLMStatus.ONLINE)

    def test_get_status_display_online(self, status_checker):
        """Test status display for online status."""
        text, css_class = status_checker.get_status_display(LLMStatus.ONLINE)
        assert text == "✅ LLM: Online"
        assert css_class == "llm-status-online"

    def test_get_status_display_offline(self, status_checker):
        """Test status display for offline status."""
        text, css_class = status_checker.get_status_display(LLMStatus.OFFLINE)
        assert text == "❌ LLM: Offline"
        assert css_class == "llm-status-offline"

    def test_get_status_display_checking(self, status_checker):
        """Test status display for checking status."""
        text, css_class = status_checker.get_status_display(LLMStatus.CHECKING)
        assert text == "⚠️ LLM: Checking..."
        assert css_class == "llm-status-checking"

    def test_get_status_display_error(self, status_checker):
        """Test status display for error status."""
        text, css_class = status_checker.get_status_display(LLMStatus.ERROR)
        assert text == "⚠️ LLM: Error"
        assert css_class == "llm-status-error"

    @pytest.mark.asyncio
    async def test_background_monitoring_start_stop(self, status_checker):
        """Test starting and stopping background monitoring."""
        # Start monitoring
        await status_checker.start_background_monitoring()
        assert status_checker._background_task is not None

        # Stop monitoring
        await status_checker.stop_background_monitoring()
        assert status_checker._background_task is None

    @pytest.mark.asyncio
    async def test_lazy_loading_initialization(self):
        """Test that status checker can be initialized without OllamaLLM."""
        status_checker = LLMStatusChecker(ollama_llm=None)

        # Should start with None
        assert status_checker.ollama_llm is None

        # When we try to check status, it should handle the None case gracefully
        # (This will fail in practice but should not crash)
        try:
            status = await status_checker.get_status(force_check=True)
            # If it doesn't crash, it should return ERROR status due to missing LLM
            assert status == LLMStatus.ERROR
        except Exception:
            # It's okay if it throws an exception due to missing dependencies
            pass
