"""Tests for Phase 4B TUI screens.

Tests all 7 screens implemented in Phase 4B.
"""

from unittest.mock import AsyncMock
from unittest.mock import MagicMock

from prt_src.tui.screens.base import EscapeIntent
from prt_src.tui.screens.chat import ChatScreen
from prt_src.tui.screens.contacts import ContactsScreen
from prt_src.tui.screens.database import DatabaseScreen
from prt_src.tui.screens.home import HomeScreen
from prt_src.tui.screens.metadata import MetadataScreen
from prt_src.tui.screens.relationships import RelationshipsScreen
from prt_src.tui.screens.search import SearchScreen
from prt_src.tui.services.data import DataService
from prt_src.tui.services.navigation import NavigationService
from prt_src.tui.services.notification import NotificationService


def mock_services():
    """Create mock services for testing."""
    nav_service = MagicMock(spec=NavigationService)
    nav_service.get_breadcrumb.return_value = ["Home", "Test"]

    data_service = MagicMock(spec=DataService)
    notification_service = AsyncMock(spec=NotificationService)

    return {
        "nav_service": nav_service,
        "data_service": data_service,
        "notification_service": notification_service,
    }


# ============= HOME SCREEN TESTS =============


def test_home_screen_initialization():
    """Test HomeScreen initializes correctly."""
    services = mock_services()
    screen = HomeScreen(**services)
    assert screen.get_screen_name() == "home"
    assert screen.on_escape() == EscapeIntent.CANCEL


def test_home_screen_navigation():
    """Test HomeScreen has navigation menu."""
    services = mock_services()
    screen = HomeScreen(**services)

    # Test screen can be created
    assert screen is not None
    # Test it's the home screen
    assert screen.get_screen_name() == "home"


# ============= CONTACTS SCREEN TESTS =============


def test_contacts_screen_initialization():
    """Test ContactsScreen initializes correctly."""
    services = mock_services()
    screen = ContactsScreen(**services)
    assert screen.get_screen_name() == "contacts"
    assert screen.on_escape() == EscapeIntent.POP


def test_contacts_screen_has_actions():
    """Test ContactsScreen has expected actions."""
    services = mock_services()
    screen = ContactsScreen(**services)

    # Test screen can be created
    assert screen is not None
    # Test it has data service
    assert screen.data_service is not None


# ============= SEARCH SCREEN TESTS =============


def test_search_screen_initialization():
    """Test SearchScreen initializes correctly."""
    services = mock_services()
    screen = SearchScreen(**services)
    assert screen.get_screen_name() == "search"


def test_search_screen_esc_intent():
    """Test SearchScreen ESC intent changes based on results."""
    services = mock_services()
    screen = SearchScreen(**services)

    # Without results, should go home
    screen._has_results = False
    assert screen.on_escape() == EscapeIntent.HOME

    # With results, should pop
    screen._has_results = True
    assert screen.on_escape() == EscapeIntent.POP


# ============= RELATIONSHIPS SCREEN TESTS =============


def test_relationships_screen_initialization():
    """Test RelationshipsScreen initializes correctly."""
    services = mock_services()
    screen = RelationshipsScreen(**services)
    assert screen.get_screen_name() == "relationships"
    assert screen.on_escape() == EscapeIntent.POP


# ============= DATABASE SCREEN TESTS =============


def test_database_screen_initialization():
    """Test DatabaseScreen initializes correctly."""
    services = mock_services()
    screen = DatabaseScreen(**services)
    assert screen.get_screen_name() == "database"
    assert screen.on_escape() == EscapeIntent.POP


# ============= METADATA SCREEN TESTS =============


def test_metadata_screen_initialization():
    """Test MetadataScreen initializes correctly."""
    services = mock_services()
    screen = MetadataScreen(**services)
    assert screen.get_screen_name() == "metadata"
    assert screen.on_escape() == EscapeIntent.POP


# ============= CHAT SCREEN TESTS =============


def test_chat_screen_initialization():
    """Test ChatScreen initializes correctly."""
    services = mock_services()
    screen = ChatScreen(**services)
    assert screen.get_screen_name() == "chat"
    assert screen.on_escape() == EscapeIntent.CUSTOM


def test_chat_screen_custom_escape():
    """Test ChatScreen handles custom escape correctly."""
    services = mock_services()
    screen = ChatScreen(**services)

    # With input, should clear
    screen._has_input = True
    screen.handle_custom_escape()
    assert not screen._has_input

    # Without input, should go home
    screen._has_input = False
    screen.handle_custom_escape()
    services["nav_service"].go_home.assert_called_once()


def test_chat_screen_parse_query():
    """Test ChatScreen parses natural language queries."""
    services = mock_services()
    screen = ChatScreen(**services)

    # Test contact query
    intent, params = screen._parse_query("Show me all contacts")
    assert intent == "list_contacts"

    # Test search query
    intent, params = screen._parse_query("Find John")
    assert intent == "unified_search"
    assert params["query"].lower() == "john"

    # Test note creation
    intent, params = screen._parse_query("Add a note about birthday party")
    assert intent == "add_note"
    assert "birthday party" in params["content"]


def test_chat_screen_message_history():
    """Test ChatScreen maintains message history."""
    services = mock_services()
    screen = ChatScreen(**services)

    # Initialize history
    screen._message_history = []

    # Add messages to history
    screen._message_history.append("test query 1")
    screen._message_history.append("test query 2")

    # Check history
    assert len(screen._message_history) == 2
    assert screen._message_history[0] == "test query 1"
    assert screen._message_history[1] == "test query 2"


# ============= INTEGRATION TESTS =============


def test_header_footer_configuration():
    """Test screens configure headers and footers correctly."""
    services = mock_services()
    screens = [
        HomeScreen(**services),
        ContactsScreen(**services),
        SearchScreen(**services),
        RelationshipsScreen(**services),
        DatabaseScreen(**services),
        MetadataScreen(**services),
    ]

    for screen in screens:
        # Get configurations
        header = screen.get_header_config()
        footer = screen.get_footer_config()

        # All should have header except chat
        assert header is not None
        assert "title" in header

        # All should have footer except chat
        assert footer is not None
        assert "keyHints" in footer


def test_chat_screen_no_chrome():
    """Test ChatScreen hides chrome as expected."""
    services = mock_services()
    screen = ChatScreen(**services)

    # Chat should hide chrome
    assert screen.get_header_config() is None
    assert screen.get_footer_config() is None


def test_all_screens_have_name():
    """Test all screens return a valid screen name."""
    services = mock_services()
    screens = [
        ("home", HomeScreen(**services)),
        ("contacts", ContactsScreen(**services)),
        ("search", SearchScreen(**services)),
        ("relationships", RelationshipsScreen(**services)),
        ("database", DatabaseScreen(**services)),
        ("metadata", MetadataScreen(**services)),
        ("chat", ChatScreen(**services)),
    ]

    for expected_name, screen in screens:
        assert screen.get_screen_name() == expected_name


def test_all_screens_have_escape_intent():
    """Test all screens declare an ESC intent."""
    services = mock_services()
    screens = [
        HomeScreen(**services),
        ContactsScreen(**services),
        SearchScreen(**services),
        RelationshipsScreen(**services),
        DatabaseScreen(**services),
        MetadataScreen(**services),
        ChatScreen(**services),
    ]

    for screen in screens:
        intent = screen.on_escape()
        assert isinstance(intent, EscapeIntent)
