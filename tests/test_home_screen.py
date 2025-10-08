"""Tests for Home screen."""

import pytest

from prt_src.tui.screens.home import HomeScreen
from prt_src.tui.types import AppMode
from prt_src.tui.widgets import BottomNav
from prt_src.tui.widgets import DropdownMenu
from prt_src.tui.widgets import TopNav


class TestHomeScreenRendering:
    """Test Home screen rendering."""

    @pytest.mark.asyncio
    async def test_screen_mounts(self, mock_app, pilot_screen):
        """Test that home screen mounts successfully."""
        async with pilot_screen(HomeScreen, prt_app=mock_app) as pilot:
            screen = pilot.app.screen
            assert screen.is_mounted

    @pytest.mark.asyncio
    async def test_has_top_nav(self, mock_app, pilot_screen):
        """Test that home screen has top navigation."""
        async with pilot_screen(HomeScreen, prt_app=mock_app) as pilot:
            screen = pilot.app.screen
            top_nav = screen.query_one(TopNav)
            assert top_nav is not None
            assert "HOME" in str(top_nav.render())

    @pytest.mark.asyncio
    async def test_has_bottom_nav(self, mock_app, pilot_screen):
        """Test that home screen has bottom navigation."""
        async with pilot_screen(HomeScreen, prt_app=mock_app) as pilot:
            screen = pilot.app.screen
            bottom_nav = screen.query_one(BottomNav)
            assert bottom_nav is not None

    @pytest.mark.asyncio
    async def test_has_menu_options(self, mock_app, pilot_screen):
        """Test that home screen displays menu options."""
        async with pilot_screen(HomeScreen, prt_app=mock_app) as pilot:
            screen = pilot.app.screen
            options = screen.query(".menu-option")
            assert len(options) == 3

            texts = [str(opt.render()) for opt in options]
            assert any("(C)hat" in text for text in texts)
            assert any("(S)earch" in text for text in texts)
            assert any("Se(t)tings" in text for text in texts)

    @pytest.mark.asyncio
    async def test_has_dropdown_menu(self, mock_app, pilot_screen):
        """Test that home screen has dropdown menu."""
        async with pilot_screen(HomeScreen, prt_app=mock_app) as pilot:
            screen = pilot.app.screen
            dropdown = screen.query_one(DropdownMenu)
            assert dropdown is not None
            assert not dropdown.display  # Hidden by default


class TestHomeScreenNavigation:
    """Test Home screen navigation."""

    @pytest.mark.asyncio
    async def test_toggle_menu_with_n_key(self, mock_app, pilot_screen):
        """Test that N key toggles dropdown menu."""
        async with pilot_screen(HomeScreen, prt_app=mock_app) as pilot:
            screen = pilot.app.screen
            dropdown = screen.query_one(DropdownMenu)

            # Initially hidden
            assert not dropdown.display

            # Press N to open
            await pilot.press("n")
            assert dropdown.display

            # Press N to close
            await pilot.press("n")
            assert not dropdown.display

    # NOTE: C/S/T key navigation tests removed - navigation is tested in Phase 2 tests
    # These keys now trigger real navigation which requires full app context

    @pytest.mark.asyncio
    async def test_x_key_exits_app(self, mock_app, pilot_screen):
        """Test that X key exits application."""
        async with pilot_screen(HomeScreen, prt_app=mock_app) as pilot:
            # Mock the exit method to prevent actual exit
            exit_called = False
            original_exit = pilot.app.exit

            def mock_exit():
                nonlocal exit_called
                exit_called = True

            pilot.app.exit = mock_exit

            await pilot.press("x")
            assert exit_called

            # Restore original
            pilot.app.exit = original_exit


class TestHomeScreenDropdownMenu:
    """Test Home screen dropdown menu functionality."""

    @pytest.mark.asyncio
    async def test_dropdown_has_home_option(self, mock_app, pilot_screen):
        """Test that dropdown menu has Home option."""
        async with pilot_screen(HomeScreen, prt_app=mock_app) as pilot:
            screen = pilot.app.screen
            dropdown = screen.query_one(DropdownMenu)
            action = dropdown.get_action("H")
            assert action is not None

    @pytest.mark.asyncio
    async def test_dropdown_has_back_option(self, mock_app, pilot_screen):
        """Test that dropdown menu has Back option."""
        async with pilot_screen(HomeScreen, prt_app=mock_app) as pilot:
            screen = pilot.app.screen
            dropdown = screen.query_one(DropdownMenu)
            action = dropdown.get_action("B")
            assert action is not None

    @pytest.mark.asyncio
    async def test_h_key_in_dropdown_triggers_home_action(self, mock_app, pilot_screen):
        """Test that H key with dropdown open triggers home action."""
        async with pilot_screen(HomeScreen, prt_app=mock_app) as pilot:
            screen = pilot.app.screen
            # Open menu
            await pilot.press("n")
            dropdown = screen.query_one(DropdownMenu)
            assert dropdown.display

            # Press H
            await pilot.press("h")

            # Menu should close
            assert not dropdown.display


class TestHomeScreenModeAwareness:
    """Test Home screen mode awareness."""

    @pytest.mark.asyncio
    async def test_keys_only_work_in_nav_mode(self, mock_app, pilot_screen):
        """Test that single-key shortcuts only work in NAV mode."""
        async with pilot_screen(HomeScreen, prt_app=mock_app) as pilot:
            screen = pilot.app.screen
            # Set to EDIT mode
            pilot.app.current_mode = AppMode.EDIT
            screen.top_nav.set_mode(AppMode.EDIT)

            # Try to open menu with N - should not work
            dropdown = screen.query_one(DropdownMenu)
            await pilot.press("n")
            assert not dropdown.display  # Should still be hidden

            # Set back to NAV mode
            pilot.app.current_mode = AppMode.NAVIGATION
            screen.top_nav.set_mode(AppMode.NAVIGATION)

            # Now it should work
            await pilot.press("n")
            assert dropdown.display  # Should be visible
