"""Tests for contact form screen."""

from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from prt_src.tui.screens.base import EscapeIntent
from prt_src.tui.screens.contact_form import ContactFormScreen


class TestContactFormScreen:
    """Test cases for ContactFormScreen."""

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
    def tags_data(self):
        """Sample tags data for testing."""
        return [{"id": 1, "name": "work"}, {"id": 2, "name": "family"}, {"id": 3, "name": "friend"}]

    def test_screen_initialization_add_mode(self, mock_services):
        """Test screen initialization in add mode."""
        screen = ContactFormScreen(mode="add", **mock_services)

        assert screen.get_screen_name() == "contact_form"
        assert screen.mode == "add"
        assert screen.contact_id is None
        assert screen.contact_data is None
        assert screen.selected_tags == set()
        assert screen.validation_system is not None

    def test_screen_initialization_edit_mode(self, mock_services):
        """Test screen initialization in edit mode."""
        screen = ContactFormScreen(mode="edit", contact_id=1, **mock_services)

        assert screen.mode == "edit"
        assert screen.contact_id == 1

    def test_escape_intent_with_changes(self, mock_services):
        """Test escape intent when form has unsaved changes."""
        screen = ContactFormScreen(mode="add", **mock_services)

        # Mock form fields to simulate unsaved changes
        screen.first_name_input = MagicMock()
        screen.first_name_input.value = "John"
        screen.last_name_input = MagicMock()
        screen.last_name_input.value = ""
        screen.email_input = MagicMock()
        screen.email_input.value = ""
        screen.phone_input = MagicMock()
        screen.phone_input.value = ""
        screen.notes_textarea = MagicMock()
        screen.notes_textarea.text = ""

        assert screen.on_escape() == EscapeIntent.CONFIRM

    def test_escape_intent_without_changes(self, mock_services):
        """Test escape intent when form has no unsaved changes."""
        screen = ContactFormScreen(mode="add", **mock_services)

        assert screen.on_escape() == EscapeIntent.POP

    def test_header_config_add_mode(self, mock_services):
        """Test header configuration in add mode."""
        screen = ContactFormScreen(mode="add", **mock_services)
        config = screen.get_header_config()

        assert config["title"] == "Add Contact"

    def test_header_config_edit_mode(self, mock_services):
        """Test header configuration in edit mode."""
        screen = ContactFormScreen(mode="edit", contact_id=1, **mock_services)
        config = screen.get_header_config()

        assert config["title"] == "Edit Contact"

    def test_footer_config(self, mock_services):
        """Test footer configuration."""
        screen = ContactFormScreen(mode="add", **mock_services)
        config = screen.get_footer_config()

        assert "[Ctrl+S] Save" in config["keyHints"]
        assert "[Ctrl+C] Cancel" in config["keyHints"]
        assert "[Tab] Next field" in config["keyHints"]
        assert "[ESC] Back" in config["keyHints"]

    @pytest.mark.asyncio
    async def test_load_form_data_add_mode(self, mock_services, tags_data):
        """Test loading form data in add mode."""
        mock_services["data_service"].get_tags.return_value = tags_data

        screen = ContactFormScreen(mode="add", **mock_services)
        screen.loading_indicator = MagicMock()
        screen._setup_tag_checkboxes = AsyncMock()

        await screen._load_form_data()

        mock_services["data_service"].get_tags.assert_called_once()
        screen._setup_tag_checkboxes.assert_called_once()
        assert screen.available_tags == tags_data

    @pytest.mark.asyncio
    async def test_load_form_data_edit_mode(self, mock_services, contact_data, tags_data):
        """Test loading form data in edit mode."""
        mock_services["data_service"].get_tags.return_value = tags_data
        mock_services["data_service"].get_contact.return_value = contact_data

        screen = ContactFormScreen(mode="edit", contact_id=1, **mock_services)
        screen.loading_indicator = MagicMock()
        screen._setup_tag_checkboxes = AsyncMock()
        screen._populate_form_fields = AsyncMock()

        await screen._load_form_data()

        mock_services["data_service"].get_tags.assert_called_once()
        mock_services["data_service"].get_contact.assert_called_once_with(1)
        screen._setup_tag_checkboxes.assert_called_once()
        screen._populate_form_fields.assert_called_once()
        assert screen.contact_data == contact_data

    @pytest.mark.asyncio
    async def test_load_form_data_contact_not_found(self, mock_services, tags_data):
        """Test loading form data when contact not found in edit mode."""
        mock_services["data_service"].get_tags.return_value = tags_data
        mock_services["data_service"].get_contact.return_value = None

        screen = ContactFormScreen(mode="edit", contact_id=999, **mock_services)
        screen.loading_indicator = MagicMock()
        screen._setup_tag_checkboxes = AsyncMock()

        await screen._load_form_data()

        mock_services["notification_service"].show_error.assert_called_once_with(
            "Contact not found"
        )

    @pytest.mark.asyncio
    async def test_setup_tag_checkboxes(self, mock_services, tags_data):
        """Test setting up tag checkboxes."""
        screen = ContactFormScreen(mode="add", **mock_services)
        screen.available_tags = tags_data
        screen.tags_container = MagicMock()
        screen.tags_container.mount = AsyncMock()
        screen.tags_container.remove_children = AsyncMock()

        await screen._setup_tag_checkboxes()

        screen.tags_container.remove_children.assert_called_once()
        assert len(screen.tag_checkboxes) == 3
        assert "work" in screen.tag_checkboxes
        assert "family" in screen.tag_checkboxes
        assert "friend" in screen.tag_checkboxes
        assert screen.tags_container.mount.call_count == 3

    @pytest.mark.asyncio
    async def test_populate_form_fields(self, mock_services, contact_data):
        """Test populating form fields with contact data."""
        screen = ContactFormScreen(mode="edit", contact_id=1, **mock_services)
        screen.contact_data = contact_data

        # Mock form fields
        screen.first_name_input = MagicMock()
        screen.last_name_input = MagicMock()
        screen.email_input = MagicMock()
        screen.phone_input = MagicMock()

        await screen._populate_form_fields()

        assert screen.first_name_input.value == "John"
        assert screen.last_name_input.value == "Doe"
        assert screen.email_input.value == "john@example.com"
        assert screen.phone_input.value == "+1234567890"

    def test_has_unsaved_changes_add_mode_empty(self, mock_services):
        """Test unsaved changes detection in add mode with empty form."""
        screen = ContactFormScreen(mode="add", **mock_services)

        # Mock empty form fields
        screen.first_name_input = MagicMock()
        screen.first_name_input.value = ""
        screen.last_name_input = MagicMock()
        screen.last_name_input.value = ""
        screen.email_input = MagicMock()
        screen.email_input.value = ""
        screen.phone_input = MagicMock()
        screen.phone_input.value = ""
        screen.notes_textarea = MagicMock()
        screen.notes_textarea.text = ""

        assert not screen.has_unsaved_changes()

    def test_has_unsaved_changes_add_mode_with_data(self, mock_services):
        """Test unsaved changes detection in add mode with form data."""
        screen = ContactFormScreen(mode="add", **mock_services)

        # Mock form fields with data
        screen.first_name_input = MagicMock()
        screen.first_name_input.value = "John"
        screen.last_name_input = MagicMock()
        screen.last_name_input.value = ""
        screen.email_input = MagicMock()
        screen.email_input.value = ""
        screen.phone_input = MagicMock()
        screen.phone_input.value = ""
        screen.notes_textarea = MagicMock()
        screen.notes_textarea.text = ""

        assert screen.has_unsaved_changes()

    def test_has_unsaved_changes_edit_mode_no_changes(self, mock_services, contact_data):
        """Test unsaved changes detection in edit mode with no changes."""
        screen = ContactFormScreen(mode="edit", contact_id=1, **mock_services)
        screen.contact_data = contact_data

        # Mock form fields with original data
        screen.first_name_input = MagicMock()
        screen.first_name_input.value = "John"
        screen.last_name_input = MagicMock()
        screen.last_name_input.value = "Doe"
        screen.email_input = MagicMock()
        screen.email_input.value = "john@example.com"
        screen.phone_input = MagicMock()
        screen.phone_input.value = "+1234567890"

        assert not screen.has_unsaved_changes()

    def test_has_unsaved_changes_edit_mode_with_changes(self, mock_services, contact_data):
        """Test unsaved changes detection in edit mode with changes."""
        screen = ContactFormScreen(mode="edit", contact_id=1, **mock_services)
        screen.contact_data = contact_data

        # Mock form fields with modified data
        screen.first_name_input = MagicMock()
        screen.first_name_input.value = "Jane"  # Changed
        screen.last_name_input = MagicMock()
        screen.last_name_input.value = "Doe"
        screen.email_input = MagicMock()
        screen.email_input.value = "john@example.com"
        screen.phone_input = MagicMock()
        screen.phone_input.value = "+1234567890"

        assert screen.has_unsaved_changes()

    def test_collect_form_data(self, mock_services):
        """Test collecting data from form fields."""
        screen = ContactFormScreen(mode="add", **mock_services)

        # Mock form fields
        screen.first_name_input = MagicMock()
        screen.first_name_input.value = "  John  "  # With spaces
        screen.last_name_input = MagicMock()
        screen.last_name_input.value = "  Doe  "
        screen.email_input = MagicMock()
        screen.email_input.value = "  john@example.com  "
        screen.phone_input = MagicMock()
        screen.phone_input.value = "  +1234567890  "

        data = screen._collect_form_data()

        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"
        assert data["email"] == "john@example.com"
        assert data["phone"] == "+1234567890"
        assert data["name"] == "John Doe"

    def test_collect_form_data_empty_fields(self, mock_services):
        """Test collecting data with empty optional fields."""
        screen = ContactFormScreen(mode="add", **mock_services)

        # Mock form fields
        screen.first_name_input = MagicMock()
        screen.first_name_input.value = "John"
        screen.last_name_input = MagicMock()
        screen.last_name_input.value = "Doe"
        screen.email_input = MagicMock()
        screen.email_input.value = ""  # Empty
        screen.phone_input = MagicMock()
        screen.phone_input.value = ""  # Empty

        data = screen._collect_form_data()

        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"
        assert data["name"] == "John Doe"
        assert "email" not in data
        assert "phone" not in data

    @pytest.mark.asyncio
    async def test_handle_save_add_mode_success(self, mock_services):
        """Test successful save in add mode."""
        created_contact = {"id": 1, "name": "John Doe"}
        mock_services["data_service"].create_contact.return_value = created_contact

        screen = ContactFormScreen(mode="add", **mock_services)
        screen._collect_form_data = MagicMock(
            return_value={"first_name": "John", "last_name": "Doe", "name": "John Doe"}
        )
        screen._apply_tags_to_contact = AsyncMock()
        screen._navigate_back = AsyncMock()
        screen.validation_message = MagicMock()

        with patch.object(screen.validation_system, "validate_entity") as mock_validate:
            mock_validate.return_value.is_valid = True
            mock_validate.return_value.sanitized_data = {
                "first_name": "John",
                "last_name": "Doe",
                "name": "John Doe",
            }

            await screen._handle_save()

            mock_services["data_service"].create_contact.assert_called_once()
            screen._apply_tags_to_contact.assert_called_once_with(1)
            mock_services["notification_service"].show_success.assert_called_once()
            screen._navigate_back.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_save_edit_mode_success(self, mock_services):
        """Test successful save in edit mode."""
        mock_services["data_service"].update_contact.return_value = True

        screen = ContactFormScreen(mode="edit", contact_id=1, **mock_services)
        screen._collect_form_data = MagicMock(
            return_value={"first_name": "John", "last_name": "Doe", "name": "John Doe"}
        )
        screen._apply_tags_to_contact = AsyncMock()
        screen._navigate_back = AsyncMock()
        screen.validation_message = MagicMock()

        with patch.object(screen.validation_system, "validate_entity") as mock_validate:
            mock_validate.return_value.is_valid = True
            mock_validate.return_value.sanitized_data = {
                "first_name": "John",
                "last_name": "Doe",
                "name": "John Doe",
            }

            await screen._handle_save()

            mock_services["data_service"].update_contact.assert_called_once_with(
                1, {"first_name": "John", "last_name": "Doe", "name": "John Doe"}
            )
            screen._apply_tags_to_contact.assert_called_once_with(1)
            mock_services["notification_service"].show_success.assert_called_once()
            screen._navigate_back.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_save_validation_error(self, mock_services):
        """Test save with validation errors."""
        screen = ContactFormScreen(mode="add", **mock_services)
        screen._collect_form_data = MagicMock(return_value={"name": ""})
        screen.validation_message = MagicMock()

        with patch.object(screen.validation_system, "validate_entity") as mock_validate:
            mock_validate.return_value.is_valid = False
            mock_validate.return_value.errors = ["Name is required"]

            await screen._handle_save()

            mock_services["data_service"].create_contact.assert_not_called()
            screen.validation_message.update.assert_called_with(
                "Validation errors:\nName is required"
            )
            mock_services["notification_service"].show_error.assert_called_once_with(
                "Please fix validation errors"
            )

    @pytest.mark.asyncio
    async def test_handle_save_create_failed(self, mock_services):
        """Test save when create contact fails."""
        mock_services["data_service"].create_contact.return_value = None

        screen = ContactFormScreen(mode="add", **mock_services)
        screen._collect_form_data = MagicMock(
            return_value={"first_name": "John", "last_name": "Doe", "name": "John Doe"}
        )
        screen.validation_message = MagicMock()

        with patch.object(screen.validation_system, "validate_entity") as mock_validate:
            mock_validate.return_value.is_valid = True
            mock_validate.return_value.sanitized_data = None

            await screen._handle_save()

            mock_services["notification_service"].show_error.assert_called_once_with(
                "Failed to create contact"
            )

    @pytest.mark.asyncio
    async def test_apply_tags_to_contact(self, mock_services):
        """Test applying tags to contact."""
        screen = ContactFormScreen(mode="add", **mock_services)
        screen.selected_tags = {"work", "family"}

        await screen._apply_tags_to_contact(1)

        assert mock_services["data_service"].add_tag_to_contact.call_count == 2

    @pytest.mark.asyncio
    async def test_handle_cancel_no_changes(self, mock_services):
        """Test cancel with no unsaved changes."""
        screen = ContactFormScreen(mode="add", **mock_services)
        screen._navigate_back = AsyncMock()

        # Mock no unsaved changes
        screen.first_name_input = MagicMock()
        screen.first_name_input.value = ""
        screen.last_name_input = MagicMock()
        screen.last_name_input.value = ""
        screen.email_input = MagicMock()
        screen.email_input.value = ""
        screen.phone_input = MagicMock()
        screen.phone_input.value = ""
        screen.notes_textarea = MagicMock()
        screen.notes_textarea.text = ""

        await screen._handle_cancel()

        # Should not show confirmation dialog
        mock_services["notification_service"].show_confirm_dialog.assert_not_called()
        screen._navigate_back.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_cancel_with_changes_confirmed(self, mock_services):
        """Test cancel with unsaved changes and user confirms."""
        mock_services["notification_service"].show_confirm_dialog.return_value = True

        screen = ContactFormScreen(mode="add", **mock_services)
        screen._navigate_back = AsyncMock()

        # Mock unsaved changes
        screen.first_name_input = MagicMock()
        screen.first_name_input.value = "John"
        screen.last_name_input = MagicMock()
        screen.last_name_input.value = ""
        screen.email_input = MagicMock()
        screen.email_input.value = ""
        screen.phone_input = MagicMock()
        screen.phone_input.value = ""
        screen.notes_textarea = MagicMock()
        screen.notes_textarea.text = ""

        await screen._handle_cancel()

        mock_services["notification_service"].show_confirm_dialog.assert_called_once()
        screen._navigate_back.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_cancel_with_changes_declined(self, mock_services):
        """Test cancel with unsaved changes and user declines."""
        mock_services["notification_service"].show_confirm_dialog.return_value = False

        screen = ContactFormScreen(mode="add", **mock_services)
        screen._navigate_back = AsyncMock()

        # Mock unsaved changes
        screen.first_name_input = MagicMock()
        screen.first_name_input.value = "John"
        screen.last_name_input = MagicMock()
        screen.last_name_input.value = ""
        screen.email_input = MagicMock()
        screen.email_input.value = ""
        screen.phone_input = MagicMock()
        screen.phone_input.value = ""
        screen.notes_textarea = MagicMock()
        screen.notes_textarea.text = ""

        await screen._handle_cancel()

        mock_services["notification_service"].show_confirm_dialog.assert_called_once()
        screen._navigate_back.assert_not_called()

    @pytest.mark.asyncio
    async def test_navigate_back_add_mode(self, mock_services):
        """Test navigation back in add mode."""
        screen = ContactFormScreen(mode="add", **mock_services)
        mock_app = AsyncMock()
        mock_app.switch_screen = AsyncMock()

        # Use patch to mock the app property
        with patch.object(type(screen), "app", mock_app):
            await screen._navigate_back()

        mock_services["nav_service"].pop.assert_called_once()
        mock_app.switch_screen.assert_called_once_with("contacts")

    @pytest.mark.asyncio
    async def test_navigate_back_edit_mode(self, mock_services):
        """Test navigation back in edit mode."""
        screen = ContactFormScreen(mode="edit", contact_id=1, **mock_services)
        mock_app = AsyncMock()
        mock_app.switch_screen = AsyncMock()

        # Use patch to mock the app property
        with patch.object(type(screen), "app", mock_app):
            await screen._navigate_back()

        mock_services["nav_service"].pop.assert_called_once()
        mock_app.switch_screen.assert_called_once_with("contact_detail")

    @pytest.mark.asyncio
    async def test_key_events(self, mock_services):
        """Test key event handling."""
        screen = ContactFormScreen(mode="add", **mock_services)
        screen._handle_save = AsyncMock()
        screen._handle_cancel = AsyncMock()

        # Test save key (Ctrl+S)
        event = MagicMock()
        event.ctrl = True
        event.key = "s"
        await screen.on_key(event)
        screen._handle_save.assert_called_once()

        # Test cancel key (Ctrl+C)
        screen._handle_save.reset_mock()
        event.key = "c"
        await screen.on_key(event)
        screen._handle_cancel.assert_called_once()

    @pytest.mark.asyncio
    async def test_button_events(self, mock_services):
        """Test button press events."""
        screen = ContactFormScreen(mode="add", **mock_services)
        screen.save_button = MagicMock()
        screen.cancel_button = MagicMock()

        screen._handle_save = AsyncMock()
        screen._handle_cancel = AsyncMock()

        # Test save button
        event = MagicMock()
        event.button = screen.save_button
        await screen.on_button_pressed(event)
        screen._handle_save.assert_called_once()

        # Test cancel button
        event.button = screen.cancel_button
        await screen.on_button_pressed(event)
        screen._handle_cancel.assert_called_once()

    @pytest.mark.asyncio
    async def test_input_changed_events(self, mock_services):
        """Test input change event handling."""
        screen = ContactFormScreen(mode="add", **mock_services)
        screen.validation_message = MagicMock()

        event = MagicMock()
        await screen.on_input_changed(event)

        # Should mark as unsaved and clear validation message
        screen.validation_message.update.assert_called_once_with("")

    @pytest.mark.asyncio
    async def test_textarea_changed_events(self, mock_services):
        """Test textarea change event handling."""
        screen = ContactFormScreen(mode="add", **mock_services)

        event = MagicMock()
        await screen.on_text_area_changed(event)

        # Should mark form as having unsaved changes

    @pytest.mark.asyncio
    async def test_checkbox_changed_events(self, mock_services):
        """Test checkbox change event handling."""
        screen = ContactFormScreen(mode="add", **mock_services)

        # Test checking a checkbox
        checkbox = MagicMock()
        checkbox.value = True
        checkbox.label = "work"
        event = MagicMock()
        event.checkbox = checkbox

        await screen.on_checkbox_changed(event)

        assert "work" in screen.selected_tags

        # Test unchecking a checkbox
        checkbox.value = False
        await screen.on_checkbox_changed(event)

        assert "work" not in screen.selected_tags

    @pytest.mark.asyncio
    async def test_on_show_focuses_first_input(self, mock_services):
        """Test that on_show focuses the first input field."""
        screen = ContactFormScreen(mode="add", **mock_services)
        screen.first_name_input = MagicMock()

        await screen.on_show()

        screen.first_name_input.focus.assert_called_once()
