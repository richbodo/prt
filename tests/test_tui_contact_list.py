"""Test Contact List Widget for the Textual TUI.

Lightweight TDD approach - start with basic tests, then expand.
"""

from prt_src.tui.widgets.contact_list import ContactListWidget
from prt_src.tui.widgets.contact_list import ContactRow


class TestContactListWidget:
    """Test the ContactListWidget."""

    def test_contact_list_creation(self):
        """Test that ContactListWidget can be created."""
        widget = ContactListWidget()
        assert widget is not None
        assert hasattr(widget, "contacts")

    def test_contact_list_displays_contacts(self):
        """Test that ContactListWidget displays contact rows."""
        contacts = [
            {"id": 1, "name": "John Doe", "email": "john@example.com"},
            {"id": 2, "name": "Jane Smith", "email": "jane@example.com"},
        ]

        widget = ContactListWidget()
        widget.load_contacts(contacts)

        assert len(widget.contacts) == 2
        assert widget.contacts[0]["name"] == "John Doe"

    def test_contact_list_handles_selection(self):
        """Test that ContactListWidget handles row selection."""
        widget = ContactListWidget()
        widget.load_contacts([{"id": 1, "name": "Test", "email": "test@test.com"}])

        # Select first contact
        widget.select_contact(0)
        assert widget.selected_index == 0
        assert widget.selected_contact["id"] == 1

    def test_contact_list_vim_navigation(self):
        """Test vim-style navigation in contact list."""
        widget = ContactListWidget()
        widget.load_contacts(
            [
                {"id": 1, "name": "Contact 1"},
                {"id": 2, "name": "Contact 2"},
                {"id": 3, "name": "Contact 3"},
            ]
        )

        # Test 'j' moves down
        widget.handle_key("j")
        assert widget.selected_index == 1

        # Test 'k' moves up
        widget.handle_key("k")
        assert widget.selected_index == 0

        # Test 'G' goes to bottom
        widget.handle_key("G")
        assert widget.selected_index == 2

        # Test 'g' goes to top
        widget.handle_key("g")
        assert widget.selected_index == 0


class TestContactRow:
    """Test the ContactRow widget."""

    def test_contact_row_creation(self):
        """Test that ContactRow can be created."""
        contact = {"id": 1, "name": "John Doe", "email": "john@example.com"}
        row = ContactRow(contact)
        assert row is not None
        assert row.contact == contact

    def test_contact_row_displays_info(self):
        """Test that ContactRow displays contact information."""
        contact = {"id": 1, "name": "John Doe", "email": "john@example.com", "phone": "555-0123"}
        row = ContactRow(contact)

        assert row.name_text == "John Doe"
        assert row.email_text == "john@example.com"
        assert row.phone_text == "555-0123"

    def test_contact_row_selection_state(self):
        """Test that ContactRow handles selection state."""
        contact = {"id": 1, "name": "Test"}
        row = ContactRow(contact)

        # Initially not selected
        assert not row.is_selected

        # Select the row
        row.set_selected(True)
        assert row.is_selected
        assert "selected" in row.classes

        # Deselect the row
        row.set_selected(False)
        assert not row.is_selected
        assert "selected" not in row.classes
