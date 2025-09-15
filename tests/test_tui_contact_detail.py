"""Test Contact Detail View for the Textual TUI.

Lightweight TDD approach for contact detail display and editing.
"""

from prt_src.tui.app import AppMode
from prt_src.tui.widgets.contact_detail import ContactDetailView
from prt_src.tui.widgets.contact_detail import FieldEditor


class TestContactDetailView:
    """Test the ContactDetailView widget."""

    def test_contact_detail_creation(self):
        """Test that ContactDetailView can be created."""
        view = ContactDetailView()
        assert view is not None
        assert hasattr(view, "contact")

    def test_contact_detail_displays_contact(self):
        """Test that ContactDetailView displays contact information."""
        contact = {
            "id": 1,
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "555-0123",
            "notes": "Test notes",
        }

        view = ContactDetailView()
        view.load_contact(contact)

        assert view.contact == contact
        assert view.get_field_value("name") == "John Doe"
        assert view.get_field_value("email") == "john@example.com"

    def test_contact_detail_edit_mode(self):
        """Test that ContactDetailView handles edit mode."""
        view = ContactDetailView()
        view.load_contact({"id": 1, "name": "Test"})

        # Initially in navigation mode
        assert view.mode == AppMode.NAVIGATION
        assert not view.is_editing

        # Enter edit mode
        view.set_mode(AppMode.EDIT)
        assert view.mode == AppMode.EDIT
        assert view.is_editing

    def test_contact_detail_field_editing(self):
        """Test editing individual fields."""
        view = ContactDetailView()
        view.load_contact({"id": 1, "name": "Old Name"})

        # Edit name field
        view.set_mode(AppMode.EDIT)
        view.select_field("name")
        view.update_field("name", "New Name")

        assert view.get_field_value("name") == "New Name"
        assert view.has_unsaved_changes

    def test_contact_detail_save_changes(self):
        """Test saving changes to contact."""
        save_called = False
        saved_contact = None

        def on_save(contact):
            nonlocal save_called, saved_contact
            save_called = True
            saved_contact = contact

        view = ContactDetailView(on_save=on_save)
        view.load_contact({"id": 1, "name": "Old"})

        # Make changes
        view.set_mode(AppMode.EDIT)
        view.update_field("name", "New")

        # Save changes
        view.save_changes()

        assert save_called
        assert saved_contact["name"] == "New"
        assert not view.has_unsaved_changes


class TestFieldEditor:
    """Test the FieldEditor widget."""

    def test_field_editor_creation(self):
        """Test that FieldEditor can be created."""
        editor = FieldEditor("name", "John Doe")
        assert editor is not None
        assert editor.field_name == "name"
        assert editor.value == "John Doe"

    def test_field_editor_read_only_mode(self):
        """Test field editor in read-only mode."""
        editor = FieldEditor("email", "test@example.com")

        assert not editor.is_editable
        assert editor.display_value == "test@example.com"

    def test_field_editor_edit_mode(self):
        """Test field editor in edit mode."""
        editor = FieldEditor("phone", "555-0123")

        # Enable editing
        editor.set_editable(True)
        assert editor.is_editable

        # Update value
        editor.set_value("555-9999")
        assert editor.value == "555-9999"
        assert editor.has_changed

    def test_field_editor_validation(self):
        """Test field validation."""
        editor = FieldEditor("email", "invalid")
        editor.set_validator(lambda v: "@" in v)

        # Invalid value
        assert not editor.is_valid()

        # Valid value
        editor.set_value("valid@example.com")
        assert editor.is_valid()
