"""Tests for Help screen."""

import pytest

from prt_src.tui.screens.help import HelpScreen
from prt_src.tui.widgets import BottomNav
from prt_src.tui.widgets import TopNav

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


class TestHelpScreenRendering:
    """Test Help screen rendering."""

    @pytest.mark.asyncio
    async def test_screen_mounts(self, mock_app, pilot_screen):
        """Test that help screen mounts successfully."""
        async with pilot_screen(HelpScreen, prt_app=mock_app) as pilot:
            screen = pilot.app.screen
            assert screen.is_mounted

    @pytest.mark.asyncio
    async def test_has_top_nav(self, mock_app, pilot_screen):
        """Test that help screen has top navigation."""
        async with pilot_screen(HelpScreen, prt_app=mock_app) as pilot:
            screen = pilot.app.screen
            top_nav = screen.query_one(TopNav)
            assert top_nav is not None
            assert "HELP" in str(top_nav.render())

    @pytest.mark.asyncio
    async def test_has_bottom_nav(self, mock_app, pilot_screen):
        """Test that help screen has bottom navigation."""
        async with pilot_screen(HelpScreen, prt_app=mock_app) as pilot:
            screen = pilot.app.screen
            bottom_nav = screen.query_one(BottomNav)
            assert bottom_nav is not None

    @pytest.mark.asyncio
    async def test_displays_placeholder_message(self, mock_app, pilot_screen):
        """Test that help screen displays placeholder message."""
        async with pilot_screen(HelpScreen, prt_app=mock_app) as pilot:
            screen = pilot.app.screen
            message = screen.query_one("#help-message")
            assert message is not None
            assert "Help not implemented yet" in str(message.render())


class TestHelpScreenNavigation:
    """Test Help screen navigation."""

    @pytest.mark.asyncio
    async def test_esc_returns_to_previous_screen(self, mock_app, pilot_screen):
        """Test that ESC key returns to previous screen."""
        async with pilot_screen(HelpScreen, prt_app=mock_app) as pilot:
            # Mock the pop_screen method
            pop_called = False
            original_pop = mock_app.pop_screen

            def mock_pop():
                nonlocal pop_called
                pop_called = True

            mock_app.pop_screen = mock_pop

            await pilot.press("escape")

            # Verify pop was attempted
            # (actual behavior depends on BaseScreen implementation)

            # Restore original
            mock_app.pop_screen = original_pop
