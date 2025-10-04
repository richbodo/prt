"""Tests for Issue #114: N-triggered top nav menu."""

import pytest

from prt_src.tui.app import PRTApp


class TestTopNavMenu:
    """Test suite for the N-triggered top nav menu."""

    def test_app_initializes_with_nav_menu_closed(self):
        """Test app starts with nav menu in closed state."""
        app = PRTApp()
        assert not app.nav_menu_open
        assert "(N)av menu closed" in app.title

    @pytest.mark.asyncio
    async def test_toggle_nav_menu_changes_state(self):
        """Test toggle method changes open/closed state."""
        app = PRTApp()

        # Initially closed
        assert not app.nav_menu_open

        # Toggle should open
        await app.action_toggle_top_nav()
        assert app.nav_menu_open
        assert "(N)av menu open" in app.title

        # Toggle again should close
        await app.action_toggle_top_nav()
        assert not app.nav_menu_open
        assert "(N)av menu closed" in app.title

    @pytest.mark.asyncio
    async def test_nav_menu_key_handling_when_closed(self):
        """Test nav menu keys don't work when menu is closed."""
        app = PRTApp()

        # Menu should be closed
        assert not app.nav_menu_open

        # Keys should not be handled when closed
        result = await app._handle_nav_menu_key("b")
        assert not result

        result = await app._handle_nav_menu_key("h")
        assert not result

        result = await app._handle_nav_menu_key("question_mark")
        assert not result

    @pytest.mark.asyncio
    async def test_nav_menu_key_handling_when_open(self):
        """Test nav menu keys work when menu is open."""
        app = PRTApp()

        # Open the menu
        await app.action_toggle_top_nav()
        assert app.nav_menu_open

        # Keys should be handled when open
        result = await app._handle_nav_menu_key("h")
        assert result
        # Menu should close after selection
        assert not app.nav_menu_open


class TestHelpScreen:
    """Test suite for the new Help screen."""

    def test_help_screen_imports(self):
        """Test help screen can be imported without errors."""
        from prt_src.tui.screens.help import HelpScreen

        help_screen = HelpScreen()
        assert help_screen.get_screen_name() == "help"

    def test_help_screen_escape_intent(self):
        """Test help screen ESC behavior."""
        from prt_src.tui.screens.base import EscapeIntent
        from prt_src.tui.screens.help import HelpScreen

        help_screen = HelpScreen()
        assert help_screen.on_escape() == EscapeIntent.POP
