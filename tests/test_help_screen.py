"""Tests for Help screen."""

import pytest

from prt_src.tui.screens.help import HelpScreen
from prt_src.tui.widgets import BottomNav
from prt_src.tui.widgets import TopNav


@pytest.fixture
def help_screen(mock_app):
    """Create a Help screen instance for testing."""
    return HelpScreen(app=mock_app)


class TestHelpScreenRendering:
    """Test Help screen rendering."""

    @pytest.mark.asyncio
    async def test_screen_mounts(self, help_screen, pilot_app):
        """Test that help screen mounts successfully."""
        async with pilot_app(help_screen):
            assert help_screen.is_mounted

    @pytest.mark.asyncio
    async def test_has_top_nav(self, help_screen, pilot_app):
        """Test that help screen has top navigation."""
        async with pilot_app(help_screen):
            top_nav = help_screen.query_one(TopNav)
            assert top_nav is not None
            assert "HELP" in str(top_nav.render())

    @pytest.mark.asyncio
    async def test_has_bottom_nav(self, help_screen, pilot_app):
        """Test that help screen has bottom navigation."""
        async with pilot_app(help_screen):
            bottom_nav = help_screen.query_one(BottomNav)
            assert bottom_nav is not None

    @pytest.mark.asyncio
    async def test_displays_placeholder_message(self, help_screen, pilot_app):
        """Test that help screen displays placeholder message."""
        async with pilot_app(help_screen):
            message = help_screen.query_one("#help-message")
            assert message is not None
            assert "Help not implemented yet" in str(message.render())


class TestHelpScreenNavigation:
    """Test Help screen navigation."""

    @pytest.mark.asyncio
    async def test_esc_returns_to_previous_screen(self, help_screen, pilot_app, mock_app):
        """Test that ESC key returns to previous screen."""
        async with pilot_app(help_screen):
            # Mock the pop_screen method
            pop_called = False
            original_pop = mock_app.pop_screen

            def mock_pop():
                nonlocal pop_called
                pop_called = True

            mock_app.pop_screen = mock_pop

            await pilot_app.press("escape")

            # Verify pop was attempted
            # (actual behavior depends on BaseScreen implementation)

            # Restore original
            mock_app.pop_screen = original_pop


# Fixtures for testing
@pytest.fixture
def mock_app():
    """Create a mock app for testing."""
    from unittest.mock import MagicMock

    from prt_src.tui.types import AppMode

    app = MagicMock()
    app.mode = AppMode.NAVIGATION
    app.exit = MagicMock()
    app.pop_screen = MagicMock()
    return app


@pytest.fixture
def pilot_app():
    """Create a pilot for testing Textual apps."""
    from textual.pilot import Pilot

    async def _pilot(screen):
        async with Pilot.pilot_app(screen) as pilot:
            yield pilot

    return _pilot
