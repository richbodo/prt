"""Tests for Chat Progress Indicator widget."""

import asyncio
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from prt_src.tui.widgets.progress_indicator import ChatProgressIndicator


class TestChatProgressIndicator:
    """Test cases for ChatProgressIndicator widget."""

    @pytest.fixture
    def progress_indicator(self):
        """Create a ChatProgressIndicator instance."""
        return ChatProgressIndicator()

    def test_initialization(self, progress_indicator):
        """Test widget initialization."""
        assert progress_indicator._animation_task is None
        assert progress_indicator._spinner_index == 0
        assert progress_indicator._message_index == 0
        assert progress_indicator._is_animating is False

        # Check that progress messages and spinner chars are defined
        assert len(ChatProgressIndicator.PROGRESS_MESSAGES) > 0
        assert len(ChatProgressIndicator.SPINNER_CHARS) > 0

    def test_progress_messages_content(self):
        """Test that progress messages are fun and appropriate."""
        messages = ChatProgressIndicator.PROGRESS_MESSAGES

        # Should have a good variety of messages
        assert len(messages) >= 10

        # Check that messages contain emojis and are engaging
        emoji_count = sum(1 for msg in messages if any(ord(char) > 127 for char in msg))
        assert emoji_count > len(messages) // 2  # Most messages should have emojis

        # Check for expected content themes
        themes = ["thinking", "processing", "searching", "consulting", "formulating"]
        found_themes = 0
        for theme in themes:
            if any(theme.lower() in msg.lower() for msg in messages):
                found_themes += 1
        assert found_themes >= 3  # Should cover multiple themes

    def test_spinner_chars(self):
        """Test spinner character rotation."""
        chars = ChatProgressIndicator.SPINNER_CHARS
        assert len(chars) == 4
        assert chars == ["/", "-", "\\", "|"]

    @pytest.mark.asyncio
    async def test_start_animation(self, progress_indicator):
        """Test starting animation."""
        # Mock the compose method components
        progress_indicator.message_label = MagicMock()
        progress_indicator.spinner_label = MagicMock()

        with patch.object(progress_indicator, "_animate", new_callable=AsyncMock) as mock_animate:
            await progress_indicator.start_animation()

            assert progress_indicator._is_animating is True
            assert progress_indicator.display is True
            assert mock_animate.called

            # Should set a random message
            progress_indicator.message_label.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_animation(self, progress_indicator):
        """Test stopping animation."""
        # Set up as if animation is running
        progress_indicator._is_animating = True
        progress_indicator.display = True

        # Create a real task that we can cancel
        async def dummy_task():
            await asyncio.sleep(1)

        progress_indicator._animation_task = asyncio.create_task(dummy_task())

        await progress_indicator.stop_animation()

        assert progress_indicator._is_animating is False
        assert progress_indicator.display is False
        assert progress_indicator._animation_task is None

    def test_animation_state_management(self, progress_indicator):
        """Test animation state management."""
        # Test initial state
        assert progress_indicator._is_animating is False

        # Test state changes
        progress_indicator._is_animating = True
        assert progress_indicator._is_animating is True

        progress_indicator._is_animating = False
        assert progress_indicator._is_animating is False

    def test_set_message(self, progress_indicator):
        """Test setting custom message."""
        progress_indicator.message_label = MagicMock()
        custom_message = "Custom test message"

        progress_indicator.set_message(custom_message)

        progress_indicator.message_label.update.assert_called_once_with(custom_message)

    def test_set_message_no_label(self, progress_indicator):
        """Test setting message when label doesn't exist."""
        progress_indicator.message_label = None

        # Should not raise an exception
        progress_indicator.set_message("Test message")

    def test_set_random_message(self, progress_indicator):
        """Test setting random message."""
        progress_indicator.message_label = MagicMock()

        progress_indicator.set_random_message()

        # Should have called update with one of the predefined messages
        progress_indicator.message_label.update.assert_called_once()
        called_message = progress_indicator.message_label.update.call_args[0][0]
        assert called_message in ChatProgressIndicator.PROGRESS_MESSAGES

    @pytest.mark.asyncio
    async def test_multiple_start_calls(self, progress_indicator):
        """Test that multiple start calls don't create multiple tasks."""
        progress_indicator.message_label = MagicMock()
        progress_indicator.spinner_label = MagicMock()

        with patch.object(progress_indicator, "_animate", new_callable=AsyncMock) as mock_animate:
            # Start animation twice
            await progress_indicator.start_animation()
            await progress_indicator.start_animation()

            # Should only have created one task
            assert mock_animate.call_count == 1

    @pytest.mark.asyncio
    async def test_stop_without_start(self, progress_indicator):
        """Test stopping animation when it was never started."""
        # Should not raise an exception
        await progress_indicator.stop_animation()

        assert progress_indicator._is_animating is False
        assert progress_indicator.display is False

    def test_spinner_index_cycling(self, progress_indicator):
        """Test that spinner index cycles through all characters."""
        progress_indicator.spinner_label = MagicMock()
        progress_indicator._is_animating = True

        # Simulate several animation cycles
        initial_index = progress_indicator._spinner_index
        chars = ChatProgressIndicator.SPINNER_CHARS

        # Test cycling through all characters
        for _ in range(len(chars) * 2):  # Go through twice to test wrapping
            # This simulates what happens in _animate()
            progress_indicator._spinner_index = (progress_indicator._spinner_index + 1) % len(chars)

        # Should have wrapped around
        assert progress_indicator._spinner_index == initial_index

    def test_css_classes(self, progress_indicator):
        """Test that appropriate CSS classes are set."""
        # Default classes
        assert "chat-progress" in progress_indicator.classes
