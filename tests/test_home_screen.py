"""Tests for Home screen."""

import pytest

from prt_src.tui.screens.home import HomeScreen
from prt_src.tui.types import AppMode
from prt_src.tui.widgets import BottomNav
from prt_src.tui.widgets import DropdownMenu
from prt_src.tui.widgets import TopNav


@pytest.fixture
def home_screen(mock_app):
    """Create a Home screen instance for testing."""
    return HomeScreen(app=mock_app)


class TestHomeScreenRendering:
    """Test Home screen rendering."""

    @pytest.mark.asyncio
    async def test_screen_mounts(self, home_screen, pilot_app):
        """Test that home screen mounts successfully."""
        async with pilot_app(home_screen):
            assert home_screen.is_mounted

    @pytest.mark.asyncio
    async def test_has_top_nav(self, home_screen, pilot_app):
        """Test that home screen has top navigation."""
        async with pilot_app(home_screen):
            top_nav = home_screen.query_one(TopNav)
            assert top_nav is not None
            assert "HOME" in str(top_nav.render())

    @pytest.mark.asyncio
    async def test_has_bottom_nav(self, home_screen, pilot_app):
        """Test that home screen has bottom navigation."""
        async with pilot_app(home_screen):
            bottom_nav = home_screen.query_one(BottomNav)
            assert bottom_nav is not None

    @pytest.mark.asyncio
    async def test_has_menu_options(self, home_screen, pilot_app):
        """Test that home screen displays menu options."""
        async with pilot_app(home_screen):
            options = home_screen.query(".menu-option")
            assert len(options) == 3

            texts = [str(opt.render()) for opt in options]
            assert any("Chat" in text for text in texts)
            assert any("Search" in text for text in texts)
            assert any("Settings" in text for text in texts)

    @pytest.mark.asyncio
    async def test_has_dropdown_menu(self, home_screen, pilot_app):
        """Test that home screen has dropdown menu."""
        async with pilot_app(home_screen):
            dropdown = home_screen.query_one(DropdownMenu)
            assert dropdown is not None
            assert not dropdown.display  # Hidden by default


class TestHomeScreenNavigation:
    """Test Home screen navigation."""

    @pytest.mark.asyncio
    async def test_toggle_menu_with_n_key(self, home_screen, pilot_app):
        """Test that N key toggles dropdown menu."""
        async with pilot_app(home_screen):
            dropdown = home_screen.query_one(DropdownMenu)

            # Initially hidden
            assert not dropdown.display

            # Press N to open
            await pilot_app.press("n")
            assert dropdown.display

            # Press N to close
            await pilot_app.press("n")
            assert not dropdown.display

    @pytest.mark.asyncio
    async def test_c_key_attempts_chat_navigation(self, home_screen, pilot_app, caplog):
        """Test that C key attempts to navigate to chat."""
        async with pilot_app(home_screen):
            await pilot_app.press("c")
            # Check that action was triggered (via log or status message)
            bottom_nav = home_screen.query_one(BottomNav)
            # Status should indicate chat not implemented
            assert "Chat" in str(bottom_nav.render()) or "not yet implemented" in str(
                bottom_nav.render()
            )

    @pytest.mark.asyncio
    async def test_s_key_attempts_search_navigation(self, home_screen, pilot_app):
        """Test that S key attempts to navigate to search."""
        async with pilot_app(home_screen):
            await pilot_app.press("s")
            bottom_nav = home_screen.query_one(BottomNav)
            # Status should indicate search not implemented
            assert "Search" in str(bottom_nav.render()) or "not yet implemented" in str(
                bottom_nav.render()
            )

    @pytest.mark.asyncio
    async def test_t_key_attempts_settings_navigation(self, home_screen, pilot_app):
        """Test that T key attempts to navigate to settings."""
        async with pilot_app(home_screen):
            await pilot_app.press("t")
            bottom_nav = home_screen.query_one(BottomNav)
            # Status should indicate settings not implemented
            assert "Settings" in str(bottom_nav.render()) or "not yet implemented" in str(
                bottom_nav.render()
            )

    @pytest.mark.asyncio
    async def test_x_key_exits_app(self, home_screen, pilot_app, mock_app):
        """Test that X key exits application."""
        async with pilot_app(home_screen):
            # Mock the exit method to prevent actual exit
            exit_called = False
            original_exit = mock_app.exit

            def mock_exit():
                nonlocal exit_called
                exit_called = True

            mock_app.exit = mock_exit

            await pilot_app.press("x")
            assert exit_called

            # Restore original
            mock_app.exit = original_exit


class TestHomeScreenDropdownMenu:
    """Test Home screen dropdown menu functionality."""

    @pytest.mark.asyncio
    async def test_dropdown_has_home_option(self, home_screen, pilot_app):
        """Test that dropdown menu has Home option."""
        async with pilot_app(home_screen):
            dropdown = home_screen.query_one(DropdownMenu)
            action = dropdown.get_action("H")
            assert action is not None

    @pytest.mark.asyncio
    async def test_dropdown_has_back_option(self, home_screen, pilot_app):
        """Test that dropdown menu has Back option."""
        async with pilot_app(home_screen):
            dropdown = home_screen.query_one(DropdownMenu)
            action = dropdown.get_action("B")
            assert action is not None

    @pytest.mark.asyncio
    async def test_h_key_in_dropdown_triggers_home_action(self, home_screen, pilot_app):
        """Test that H key with dropdown open triggers home action."""
        async with pilot_app(home_screen):
            # Open menu
            await pilot_app.press("n")
            dropdown = home_screen.query_one(DropdownMenu)
            assert dropdown.display

            # Press H
            await pilot_app.press("h")

            # Menu should close
            assert not dropdown.display


class TestHomeScreenModeAwareness:
    """Test Home screen mode awareness."""

    @pytest.mark.asyncio
    async def test_keys_only_work_in_nav_mode(self, home_screen, pilot_app, mock_app):
        """Test that single-key shortcuts only work in NAV mode."""
        async with pilot_app(home_screen):
            # Set to EDIT mode
            mock_app.mode = AppMode.EDIT
            home_screen.top_nav.set_mode(AppMode.EDIT)

            # Try to open menu with N - should not work
            dropdown = home_screen.query_one(DropdownMenu)
            await pilot_app.press("n")
            assert not dropdown.display  # Should still be hidden

            # Set back to NAV mode
            mock_app.mode = AppMode.NAVIGATION
            home_screen.top_nav.set_mode(AppMode.NAVIGATION)

            # Now it should work
            await pilot_app.press("n")
            assert dropdown.display  # Should be visible


# Fixtures for testing
@pytest.fixture
def mock_app():
    """Create a mock app for testing."""
    from unittest.mock import MagicMock

    app = MagicMock()
    app.mode = AppMode.NAVIGATION
    app.exit = MagicMock()
    app.push_screen = MagicMock()
    return app


@pytest.fixture
def pilot_app():
    """Create a pilot for testing Textual apps."""
    from textual.pilot import Pilot

    async def _pilot(screen):
        async with Pilot.pilot_app(screen) as pilot:
            yield pilot

    return _pilot
