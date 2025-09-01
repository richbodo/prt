"""Tests for contact detail screen."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from prt_src.tui.screens.base import EscapeIntent
from prt_src.tui.screens.contact_detail import ContactDetailScreen


class TestContactDetailScreen:
    """Test cases for ContactDetailScreen."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services for testing."""
        nav_service = MagicMock()
        data_service = AsyncMock()
        notification_service = AsyncMock()
        selection_service = MagicMock()
        validation_service = MagicMock()

        return {
            "nav_service": nav_service,
            "data_service": data_service,
            "notification_service": notification_service,
            "selection_service": selection_service,
            "validation_service": validation_service,
        }

    @pytest.fixture
    def contact_data(self):
        """Sample contact data for testing."""
        return {
            "id": 1,
            "name": "John Doe",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "+1234567890",
        }

    @pytest.fixture
    def relationships_data(self):
        """Sample relationships data for testing."""
        return [
            {
                "from_contact_id": 1,
                "to_contact_id": 2,
                "to_contact_name": "Jane Smith",
                "type": "friend",
            },
            {
                "from_contact_id": 3,
                "to_contact_id": 1,
                "from_contact_name": "Bob Wilson",
                "type": "colleague",
            },
        ]

    def test_screen_initialization(self, mock_services):
        """Test screen initialization."""
        screen = ContactDetailScreen(contact_id=1, **mock_services)

        assert screen.get_screen_name() == "contact_detail"
        assert screen.contact_id == 1
        assert screen.contact_data is None
        assert screen.relationships_data == []
        assert screen.on_escape() == EscapeIntent.POP

    def test_screen_initialization_without_contact_id(self, mock_services):
        """Test screen initialization without contact ID."""
        screen = ContactDetailScreen(**mock_services)

        assert screen.contact_id is None

    def test_header_config(self, mock_services):
        """Test header configuration."""
        screen = ContactDetailScreen(contact_id=1, **mock_services)
        config = screen.get_header_config()

        assert config["title"] == "Contact Details"

    def test_footer_config(self, mock_services):
        """Test footer configuration."""
        screen = ContactDetailScreen(contact_id=1, **mock_services)
        config = screen.get_footer_config()

        assert "[e]dit" in config["keyHints"]
        assert "[d]elete" in config["keyHints"]
        assert "[ESC] Back" in config["keyHints"]

    @pytest.mark.asyncio
    async def test_load_contact_success(self, mock_services, contact_data, relationships_data):
        """Test successful contact loading."""
        mock_services["data_service"].get_contact.return_value = contact_data
        mock_services["data_service"].get_relationships.return_value = relationships_data

        screen = ContactDetailScreen(contact_id=1, **mock_services)

        # Mock the UI components
        screen.loading_indicator = MagicMock()
        screen.contact_name_label = MagicMock()
        screen.contact_email_label = MagicMock()
        screen.contact_phone_label = MagicMock()
        screen.relationships_table = MagicMock()
        screen.tags_label = MagicMock()
        screen.notes_label = MagicMock()

        await screen._load_contact()

        # Verify data service calls
        mock_services["data_service"].get_contact.assert_called_once_with(1)
        mock_services["data_service"].get_relationships.assert_called_once_with(1)

        # Verify UI updates
        screen.contact_name_label.update.assert_called_once_with("John Doe")
        screen.contact_email_label.update.assert_called_once_with("john@example.com")
        screen.contact_phone_label.update.assert_called_once_with("+1234567890")

    @pytest.mark.asyncio
    async def test_load_contact_not_found(self, mock_services):
        """Test loading non-existent contact."""
        mock_services["data_service"].get_contact.return_value = None

        screen = ContactDetailScreen(contact_id=999, **mock_services)
        screen.loading_indicator = MagicMock()

        await screen._load_contact()

        mock_services["notification_service"].show_error.assert_called_once_with(
            "Contact not found"
        )

    @pytest.mark.asyncio
    async def test_load_contact_no_data_service(self, mock_services):
        """Test loading contact without data service."""
        mock_services["data_service"] = None

        screen = ContactDetailScreen(contact_id=1, **mock_services)
        screen.loading_indicator = MagicMock()

        await screen._load_contact()

        # Should handle gracefully without crashing

    @pytest.mark.asyncio
    async def test_update_contact_display_with_separate_names(self, mock_services):
        """Test updating contact display with separate first/last names."""
        contact_data = {
            "id": 1,
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "+1234567890",
        }

        screen = ContactDetailScreen(contact_id=1, **mock_services)
        screen.contact_data = contact_data
        screen.contact_name_label = MagicMock()
        screen.contact_email_label = MagicMock()
        screen.contact_phone_label = MagicMock()

        await screen._update_contact_display()

        screen.contact_name_label.update.assert_called_once_with("John Doe")

    @pytest.mark.asyncio
    async def test_update_contact_display_empty_fields(self, mock_services):
        """Test updating contact display with empty fields."""
        contact_data = {
            "id": 1,
            "name": "John Doe",
            # email and phone are missing
        }

        screen = ContactDetailScreen(contact_id=1, **mock_services)
        screen.contact_data = contact_data
        screen.contact_name_label = MagicMock()
        screen.contact_email_label = MagicMock()
        screen.contact_phone_label = MagicMock()

        await screen._update_contact_display()

        screen.contact_email_label.update.assert_called_once_with("(not provided)")
        screen.contact_phone_label.update.assert_called_once_with("(not provided)")

    @pytest.mark.asyncio
    async def test_update_relationships_display(self, mock_services, relationships_data):
        """Test updating relationships display."""
        screen = ContactDetailScreen(contact_id=1, **mock_services)
        screen.relationships_data = relationships_data
        screen.relationships_table = MagicMock()

        await screen._update_relationships_display()

        # Verify table is cleared and populated
        screen.relationships_table.clear.assert_called_once()
        assert screen.relationships_table.add_row.call_count == 2

        # Verify relationship directions
        calls = screen.relationships_table.add_row.call_args_list
        assert calls[0][0] == ("→", "Jane Smith", "friend")
        assert calls[1][0] == ("←", "Bob Wilson", "colleague")

    @pytest.mark.asyncio
    async def test_handle_edit_contact(self, mock_services):
        """Test edit contact navigation."""
        screen = ContactDetailScreen(contact_id=1, **mock_services)
        mock_app = AsyncMock()
        mock_app.switch_screen = AsyncMock()

        # Use patch to mock the app property
        with patch.object(type(screen), "app", mock_app):
            await screen._handle_edit_contact()

        mock_services["nav_service"].push.assert_called_once_with(
            "contact_form", {"contact_id": 1, "mode": "edit"}
        )
        mock_app.switch_screen.assert_called_once_with("contact_form")

    @pytest.mark.asyncio
    async def test_handle_delete_contact_confirmed(self, mock_services, contact_data):
        """Test delete contact with confirmation."""
        mock_services["notification_service"].show_delete_dialog.return_value = True
        mock_services["data_service"].delete_contact.return_value = True

        screen = ContactDetailScreen(contact_id=1, **mock_services)
        screen.contact_data = contact_data
        screen._handle_back = AsyncMock()

        await screen._handle_delete_contact()

        mock_services["notification_service"].show_delete_dialog.assert_called_once_with("John Doe")
        mock_services["data_service"].delete_contact.assert_called_once_with(1)
        mock_services["notification_service"].show_success.assert_called_once_with(
            "Deleted John Doe"
        )
        screen._handle_back.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_delete_contact_cancelled(self, mock_services, contact_data):
        """Test delete contact cancelled by user."""
        mock_services["notification_service"].show_delete_dialog.return_value = False

        screen = ContactDetailScreen(contact_id=1, **mock_services)
        screen.contact_data = contact_data

        await screen._handle_delete_contact()

        # Delete should not be called
        mock_services["data_service"].delete_contact.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_delete_contact_failed(self, mock_services, contact_data):
        """Test delete contact failure."""
        mock_services["notification_service"].show_delete_dialog.return_value = True
        mock_services["data_service"].delete_contact.return_value = False

        screen = ContactDetailScreen(contact_id=1, **mock_services)
        screen.contact_data = contact_data

        await screen._handle_delete_contact()

        mock_services["notification_service"].show_error.assert_called_once_with(
            "Failed to delete John Doe"
        )

    @pytest.mark.asyncio
    async def test_handle_back_navigation(self, mock_services):
        """Test back navigation."""
        screen = ContactDetailScreen(contact_id=1, **mock_services)
        mock_app = AsyncMock()
        mock_app.switch_screen = AsyncMock()

        # Use patch to mock the app property
        with patch.object(type(screen), "app", mock_app):
            await screen._handle_back()

        mock_services["nav_service"].pop.assert_called_once()
        mock_app.switch_screen.assert_called_once_with("contacts")

    @pytest.mark.asyncio
    async def test_key_events(self, mock_services):
        """Test key event handling."""
        screen = ContactDetailScreen(contact_id=1, **mock_services)
        screen._handle_edit_contact = AsyncMock()
        screen._handle_delete_contact = AsyncMock()
        screen._handle_back = AsyncMock()

        # Test edit key
        event = MagicMock()
        event.key = "e"
        await screen.on_key(event)
        screen._handle_edit_contact.assert_called_once()

        # Test delete key
        screen._handle_edit_contact.reset_mock()
        event.key = "d"
        await screen.on_key(event)
        screen._handle_delete_contact.assert_called_once()

        # Test enter key
        event.key = "enter"
        await screen.on_key(event)
        screen._handle_back.assert_called_once()

    @pytest.mark.asyncio
    async def test_button_events(self, mock_services):
        """Test button press events."""
        screen = ContactDetailScreen(contact_id=1, **mock_services)
        screen.edit_button = MagicMock()
        screen.delete_button = MagicMock()
        screen.back_button = MagicMock()

        screen._handle_edit_contact = AsyncMock()
        screen._handle_delete_contact = AsyncMock()
        screen._handle_back = AsyncMock()

        # Test edit button
        event = MagicMock()
        event.button = screen.edit_button
        await screen.on_button_pressed(event)
        screen._handle_edit_contact.assert_called_once()

        # Test delete button
        event.button = screen.delete_button
        await screen.on_button_pressed(event)
        screen._handle_delete_contact.assert_called_once()

        # Test back button
        event.button = screen.back_button
        await screen.on_button_pressed(event)
        screen._handle_back.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_mount_with_contact_id(self, mock_services):
        """Test mount with valid contact ID."""
        screen = ContactDetailScreen(contact_id=1, **mock_services)
        screen._load_contact = AsyncMock()

        await screen.on_mount()

        screen._load_contact.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_mount_without_contact_id(self, mock_services):
        """Test mount without contact ID."""
        screen = ContactDetailScreen(**mock_services)

        await screen.on_mount()

        mock_services["notification_service"].show_error.assert_called_once_with(
            "No contact ID provided"
        )

    @pytest.mark.asyncio
    async def test_on_show_refreshes_data(self, mock_services):
        """Test that on_show refreshes contact data."""
        screen = ContactDetailScreen(contact_id=1, **mock_services)
        screen._load_contact = AsyncMock()

        await screen.on_show()

        screen._load_contact.assert_called_once()
