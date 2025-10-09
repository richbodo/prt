"""Greenfield Pilot test demonstrating headless TUI testing.

This test showcases the power of Textual's Pilot API for testing TUIs
without opening a terminal. It demonstrates:

1. Mode toggling and smart mode detection
2. Navigation between screens
3. Input focus verification
4. State assertions

Run with: ./prt_env/bin/python -m pytest tests/test_pilot_demo.py -v
"""

import pytest
from textual.widgets import TextArea

from prt_src.tui.app import PRTApp
from prt_src.tui.types import AppMode


class TestModeSwitching:
    """Test the smart mode toggle system."""

    async def test_mode_toggle_blocked_on_home_screen(self):
        """ESC should NOT switch to EDIT mode on Home (no editable widgets)."""
        app = PRTApp()
        async with app.run_test() as pilot:
            # Arrange: Start on Home screen in NAV mode
            assert pilot.app.current_mode == AppMode.NAVIGATION
            assert pilot.app.screen.screen_title == "HOME"

            # Act: Try to switch to EDIT mode
            await pilot.press("escape")
            await pilot.pause()

            # Assert: Should stay in NAV mode (no editable widgets)
            assert pilot.app.current_mode == AppMode.NAVIGATION
            # Note: Status message "No editable fields" shown, but mode didn't change

    async def test_mode_toggle_succeeds_on_chat_screen(self):
        """ESC should switch to EDIT mode on Chat screen (has TextArea)."""
        app = PRTApp()
        async with app.run_test() as pilot:
            # Arrange: Navigate to Chat screen
            await pilot.press("c")
            await pilot.pause()

            assert pilot.app.screen.screen_title == "CHAT"
            assert pilot.app.current_mode == AppMode.NAVIGATION

            # Act: Switch to EDIT mode
            await pilot.press("escape")
            await pilot.pause()

            # Assert: Mode should change to EDIT
            assert pilot.app.current_mode == AppMode.EDIT

            # Assert: Input should have focus
            chat_input = pilot.app.screen.query_one("#chat-input", TextArea)
            assert chat_input.has_focus

    async def test_mode_toggle_round_trip(self):
        """ESC should toggle NAV <-> EDIT on screens with inputs."""
        app = PRTApp()
        async with app.run_test() as pilot:
            # Navigate to Search screen
            await pilot.press("s")
            await pilot.pause()

            # Start in NAV
            assert pilot.app.current_mode == AppMode.NAVIGATION

            # Toggle to EDIT
            await pilot.press("escape")
            await pilot.pause()
            assert pilot.app.current_mode == AppMode.EDIT

            # Toggle back to NAV
            await pilot.press("escape")
            await pilot.pause()
            assert pilot.app.current_mode == AppMode.NAVIGATION


class TestNavigation:
    """Test navigation between screens."""

    async def test_navigate_to_chat_from_home(self):
        """Pressing 'c' on Home should navigate to Chat screen."""
        app = PRTApp()
        async with app.run_test() as pilot:
            # Arrange: Start on Home screen
            assert pilot.app.screen.screen_title == "HOME"

            # Act: Press 'c' to go to Chat
            await pilot.press("c")
            await pilot.pause()

            # Assert: Now on Chat screen
            assert pilot.app.screen.screen_title == "CHAT"

            # Assert: Chat input exists
            chat_input = pilot.app.screen.query_one("#chat-input", TextArea)
            assert chat_input is not None

    async def test_navigate_to_search_from_home(self):
        """Pressing 's' on Home should navigate to Search screen."""
        app = PRTApp()
        async with app.run_test() as pilot:
            # Act: Press 's' to go to Search
            await pilot.press("s")
            await pilot.pause()

            # Assert: Now on Search screen
            assert pilot.app.screen.screen_title == "SEARCH"

            # Assert: Search input exists
            search_input = pilot.app.screen.query_one("#search-input", TextArea)
            assert search_input is not None

    async def test_navigate_back_with_dropdown_menu(self):
        """Using dropdown 'Back' should navigate to previous screen."""
        app = PRTApp()
        async with app.run_test() as pilot:
            # Navigate to Chat
            await pilot.press("c")
            await pilot.pause()
            assert pilot.app.screen.screen_title == "CHAT"

            # Open dropdown menu
            await pilot.press("n")
            await pilot.pause()

            # Select 'Back'
            await pilot.press("b")
            await pilot.pause()

            # Should be back on Home screen
            assert pilot.app.screen.screen_title == "HOME"


class TestInputFocus:
    """Test focus behavior on screens with inputs."""

    async def test_chat_input_gets_focus_on_edit_mode(self):
        """Entering EDIT mode on Chat should focus the input."""
        app = PRTApp()
        async with app.run_test() as pilot:
            # Navigate to Chat
            await pilot.press("c")
            await pilot.pause()

            # Enter EDIT mode
            await pilot.press("escape")
            await pilot.pause()

            # Chat input should have focus
            chat_input = pilot.app.screen.query_one("#chat-input", TextArea)
            assert chat_input.has_focus

    async def test_search_input_gets_focus_on_edit_mode(self):
        """Entering EDIT mode on Search should focus the input."""
        app = PRTApp()
        async with app.run_test() as pilot:
            # Navigate to Search
            await pilot.press("s")
            await pilot.pause()

            # Enter EDIT mode
            await pilot.press("escape")
            await pilot.pause()

            # Search input should have focus
            search_input = pilot.app.screen.query_one("#search-input", TextArea)
            assert search_input.has_focus


class TestPlaceholderText:
    """Test placeholder text behavior in TextArea widgets."""

    async def test_chat_placeholder_disappears_on_typing(self):
        """Typing in chat input should make placeholder disappear."""
        app = PRTApp()
        async with app.run_test() as pilot:
            # Navigate to Chat and enter EDIT mode
            await pilot.press("c")
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()

            # Get the chat input
            chat_input = pilot.app.screen.query_one("#chat-input", TextArea)

            # Initially empty (placeholder is visual, not in .text)
            assert chat_input.text == ""

            # Type something
            await pilot.press("h", "e", "l", "l", "o")
            await pilot.pause()

            # Text should be there, not placeholder
            assert chat_input.text == "hello"

    async def test_search_placeholder_disappears_on_typing(self):
        """Typing in search input should make placeholder disappear."""
        app = PRTApp()
        async with app.run_test() as pilot:
            # Navigate to Search and enter EDIT mode
            await pilot.press("s")
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()

            # Get the search input
            search_input = pilot.app.screen.query_one("#search-input", TextArea)

            # Initially empty
            assert search_input.text == ""

            # Type something
            await pilot.press("t", "e", "s", "t")
            await pilot.pause()

            # Text should be there
            assert search_input.text == "test"


# This allows running the test file directly for debugging
if __name__ == "__main__":
    # Run with: python tests/test_pilot_demo.py
    pytest.main([__file__, "-v"])
