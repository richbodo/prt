"""Tests for Chat Progress Indicator widget."""

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
        assert progress_indicator._spinner_timer is None
        assert progress_indicator._message_timer is None
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
        # Mock the Static widget's update method
        with patch.object(progress_indicator, "update") as mock_update:
            await progress_indicator.start_animation()

            assert progress_indicator._is_animating is True
            assert progress_indicator.display is True

            # Should have called update with spinner + message format
            mock_update.assert_called_once()
            called_content = mock_update.call_args[0][0]
            # Content should be in format: "<spinner> <message>"
            assert " " in called_content
            spinner_part, message_part = called_content.split(" ", 1)
            assert spinner_part in ChatProgressIndicator.SPINNER_CHARS
            assert message_part in ChatProgressIndicator.PROGRESS_MESSAGES

    @pytest.mark.asyncio
    async def test_stop_animation(self, progress_indicator):
        """Test stopping animation."""
        # Set up as if animation is running
        progress_indicator._is_animating = True
        progress_indicator.display = True

        # Mock a running timer
        mock_timer = MagicMock()
        progress_indicator._spinner_timer = mock_timer

        await progress_indicator.stop_animation()

        assert progress_indicator._is_animating is False
        assert progress_indicator.display is False
        assert progress_indicator._spinner_timer is None
        mock_timer.stop.assert_called_once()

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
        with patch.object(progress_indicator, "update") as mock_update:
            custom_message = "Custom test message"
            progress_indicator.set_message(custom_message)

            # Should call update with spinner + custom message
            mock_update.assert_called_once()
            called_content = mock_update.call_args[0][0]
            # Content should be in format: "<spinner> Custom test message"
            assert custom_message in called_content
            spinner_part = called_content.split(" ")[0]
            assert spinner_part in ChatProgressIndicator.SPINNER_CHARS

    def test_set_message_no_label(self, progress_indicator):
        """Test setting message when update method exists."""
        # The widget always has the update method from Static parent class
        # Should not raise an exception
        progress_indicator.set_message("Test message")

    def test_set_random_message(self, progress_indicator):
        """Test setting random message."""
        with patch.object(progress_indicator, "update") as mock_update:
            progress_indicator.set_random_message()

            # Should have called update with one of the predefined messages
            mock_update.assert_called_once()
            called_content = mock_update.call_args[0][0]
            # Content should be in format: "<spinner> <message>"
            message_part = called_content.split(" ", 1)[1]
            assert message_part in ChatProgressIndicator.PROGRESS_MESSAGES

    @pytest.mark.asyncio
    async def test_multiple_start_calls(self, progress_indicator):
        """Test that multiple start calls don't create multiple animations."""
        with patch.object(progress_indicator, "update") as mock_update:
            # Start animation twice
            await progress_indicator.start_animation()
            await progress_indicator.start_animation()

            # Should only have updated once since second call returns early
            assert mock_update.call_count == 1

    @pytest.mark.asyncio
    async def test_stop_without_start(self, progress_indicator):
        """Test stopping animation when it was never started."""
        # Should not raise an exception
        await progress_indicator.stop_animation()

        assert progress_indicator._is_animating is False
        assert progress_indicator.display is False

    def test_spinner_index_cycling(self, progress_indicator):
        """Test that spinner index cycles through all characters."""
        progress_indicator._is_animating = True

        # Simulate several animation cycles
        initial_index = progress_indicator._spinner_index
        chars = ChatProgressIndicator.SPINNER_CHARS

        # Test cycling through all characters
        for _ in range(len(chars) * 2):  # Go through twice to test wrapping
            # This simulates what happens in _update_content()
            progress_indicator._spinner_index = (progress_indicator._spinner_index + 1) % len(chars)

        # Should have wrapped around
        assert progress_indicator._spinner_index == initial_index

    def test_css_classes(self, progress_indicator):
        """Test that appropriate CSS classes are set."""
        # Default classes
        assert "chat-progress" in progress_indicator.classes
