"""Tests for Phase 2 screens - Chat, Search, Settings (UI shells only)."""

import pytest

from prt_src.tui.constants import WidgetIDs
from prt_src.tui.screens.chat import ChatScreen
from prt_src.tui.screens.search import SearchScreen
from prt_src.tui.screens.settings import SettingsScreen

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


class TestChatScreen:
    """Test suite for Chat screen rendering and basic navigation."""

    @pytest.mark.asyncio
    async def test_screen_mounts(self, mock_app, pilot_screen):
        """Test that chat screen mounts without errors."""
        async with pilot_screen(ChatScreen, prt_app=mock_app) as pilot:
            assert pilot.app is not None
            assert isinstance(pilot.app.screen, ChatScreen)

    @pytest.mark.asyncio
    async def test_has_top_nav(self, mock_app, pilot_screen):
        """Test that chat screen has top navigation."""
        async with pilot_screen(ChatScreen, prt_app=mock_app) as pilot:
            top_nav = pilot.app.screen.query_one(f"#{WidgetIDs.TOP_NAV}")
            assert top_nav is not None

    @pytest.mark.asyncio
    async def test_has_bottom_nav(self, mock_app, pilot_screen):
        """Test that chat screen has bottom navigation."""
        async with pilot_screen(ChatScreen, prt_app=mock_app) as pilot:
            bottom_nav = pilot.app.screen.query_one(f"#{WidgetIDs.BOTTOM_NAV}")
            assert bottom_nav is not None

    @pytest.mark.asyncio
    async def test_has_chat_status(self, mock_app, pilot_screen):
        """Test that chat screen has status line."""
        async with pilot_screen(ChatScreen, prt_app=mock_app) as pilot:
            chat_status = pilot.app.screen.query_one(f"#{WidgetIDs.CHAT_STATUS}")
            assert chat_status is not None
            # Query the Static widget inside the container
            chat_status_text = pilot.app.screen.query_one("#chat-status-text")
            assert chat_status_text is not None
            assert "LLM" in str(chat_status_text.render())

    @pytest.mark.asyncio
    async def test_has_chat_input(self, mock_app, pilot_screen):
        """Test that chat screen has input box."""
        async with pilot_screen(ChatScreen, prt_app=mock_app) as pilot:
            chat_input = pilot.app.screen.query_one(f"#{WidgetIDs.CHAT_INPUT}")
            assert chat_input is not None

    @pytest.mark.asyncio
    async def test_has_chat_response(self, mock_app, pilot_screen):
        """Test that chat screen has response display."""
        async with pilot_screen(ChatScreen, prt_app=mock_app) as pilot:
            chat_response = pilot.app.screen.query_one(f"#{WidgetIDs.CHAT_RESPONSE}")
            assert chat_response is not None


class TestSearchScreen:
    """Test suite for Search screen rendering and basic navigation."""

    @pytest.mark.asyncio
    async def test_screen_mounts(self, mock_app, pilot_screen):
        """Test that search screen mounts without errors."""
        async with pilot_screen(SearchScreen, prt_app=mock_app) as pilot:
            assert pilot.app is not None
            assert isinstance(pilot.app.screen, SearchScreen)

    @pytest.mark.asyncio
    async def test_has_top_nav(self, mock_app, pilot_screen):
        """Test that search screen has top navigation."""
        async with pilot_screen(SearchScreen, prt_app=mock_app) as pilot:
            top_nav = pilot.app.screen.query_one(f"#{WidgetIDs.TOP_NAV}")
            assert top_nav is not None

    @pytest.mark.asyncio
    async def test_has_bottom_nav(self, mock_app, pilot_screen):
        """Test that search screen has bottom navigation."""
        async with pilot_screen(SearchScreen, prt_app=mock_app) as pilot:
            bottom_nav = pilot.app.screen.query_one(f"#{WidgetIDs.BOTTOM_NAV}")
            assert bottom_nav is not None

    @pytest.mark.asyncio
    async def test_has_search_input(self, mock_app, pilot_screen):
        """Test that search screen has search input box."""
        async with pilot_screen(SearchScreen, prt_app=mock_app) as pilot:
            search_input = pilot.app.screen.query_one(f"#{WidgetIDs.SEARCH_INPUT}")
            assert search_input is not None

    @pytest.mark.asyncio
    async def test_has_search_buttons(self, mock_app, pilot_screen):
        """Test that search screen has search type buttons."""
        async with pilot_screen(SearchScreen, prt_app=mock_app) as pilot:
            search_buttons = pilot.app.screen.query_one(f"#{WidgetIDs.SEARCH_BUTTONS}")
            assert search_buttons is not None
            # Should have 5 buttons
            buttons = search_buttons.query("Button")
            assert len(buttons) == 5

    @pytest.mark.asyncio
    async def test_has_search_results(self, mock_app, pilot_screen):
        """Test that search screen has results display."""
        async with pilot_screen(SearchScreen, prt_app=mock_app) as pilot:
            search_results = pilot.app.screen.query_one(f"#{WidgetIDs.SEARCH_RESULTS}")
            assert search_results is not None


class TestSettingsScreen:
    """Test suite for Settings screen rendering and basic navigation."""

    @pytest.mark.asyncio
    async def test_screen_mounts(self, mock_app, pilot_screen):
        """Test that settings screen mounts without errors."""
        async with pilot_screen(SettingsScreen, prt_app=mock_app) as pilot:
            assert pilot.app is not None
            assert isinstance(pilot.app.screen, SettingsScreen)

    @pytest.mark.asyncio
    async def test_has_top_nav(self, mock_app, pilot_screen):
        """Test that settings screen has top navigation."""
        async with pilot_screen(SettingsScreen, prt_app=mock_app) as pilot:
            top_nav = pilot.app.screen.query_one(f"#{WidgetIDs.TOP_NAV}")
            assert top_nav is not None

    @pytest.mark.asyncio
    async def test_has_bottom_nav(self, mock_app, pilot_screen):
        """Test that settings screen has bottom navigation."""
        async with pilot_screen(SettingsScreen, prt_app=mock_app) as pilot:
            bottom_nav = pilot.app.screen.query_one(f"#{WidgetIDs.BOTTOM_NAV}")
            assert bottom_nav is not None

    @pytest.mark.asyncio
    async def test_displays_database_status(self, mock_app, pilot_screen):
        """Test that settings screen displays database status."""
        async with pilot_screen(SettingsScreen, prt_app=mock_app) as pilot:
            db_status = pilot.app.screen.query_one(f"#{WidgetIDs.SETTINGS_DB_STATUS}")
            assert db_status is not None
            # Should show connection status and counts
            status_text = str(db_status.render())
            assert "Connected" in status_text or "connected" in status_text.lower()
            assert "Contacts" in status_text

    @pytest.mark.asyncio
    async def test_displays_placeholder_text(self, mock_app, pilot_screen):
        """Test that settings screen has placeholder for future features."""
        async with pilot_screen(SettingsScreen, prt_app=mock_app) as pilot:
            placeholder = pilot.app.screen.query_one(f"#{WidgetIDs.SETTINGS_PLACEHOLDER}")
            assert placeholder is not None
            status_text = str(placeholder.render())
            assert "Future" in status_text or "future" in status_text.lower()
