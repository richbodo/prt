"""Contact List Widget for the PRT Textual TUI.

Provides a scrollable list of contacts with vim-style navigation
and selection support.
"""

import contextlib
from typing import Dict
from typing import List
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.containers import VerticalScroll
from textual.reactive import reactive
from textual.widgets import Static

from prt_src.tui.widgets.base import ModeAwareWidget


class ContactRow(Static):
    """A single row in the contact list."""

    def __init__(self, contact: Dict):
        """Initialize the contact row.

        Args:
            contact: Dictionary containing contact information
        """
        super().__init__()
        self.contact = contact
        self.is_selected = False

        # Extract display values
        self.name_text = contact.get("name", "")
        self.email_text = contact.get("email", "")
        self.phone_text = contact.get("phone", "")

        self.add_class("contact-row")

    def compose(self) -> ComposeResult:
        """Compose the contact row layout."""
        with Vertical(classes="contact-row-content"):
            yield Static(self.name_text, classes="contact-name")
            if self.email_text or self.phone_text:
                info = f"{self.email_text}"
                if self.phone_text:
                    info += f" • {self.phone_text}"
                yield Static(info, classes="contact-info")

    def set_selected(self, selected: bool) -> None:
        """Set the selection state of the row.

        Args:
            selected: Whether the row should be selected
        """
        self.is_selected = selected
        if selected:
            self.add_class("selected")
        else:
            self.remove_class("selected")


class ContactListWidget(ModeAwareWidget):
    """A scrollable list of contacts with selection support."""

    selected_index = reactive(0)

    def __init__(self):
        """Initialize the contact list widget."""
        super().__init__()
        self.contacts: List[Dict] = []
        self.contact_rows: List[ContactRow] = []
        self.selected_contact: Optional[Dict] = None
        self.add_class("contact-list")

    def compose(self) -> ComposeResult:
        """Compose the contact list layout."""
        with VerticalScroll(id="contact-scroll"):
            yield Vertical(id="contact-container")

    def load_contacts(self, contacts: List[Dict]) -> None:
        """Load contacts into the list.

        Args:
            contacts: List of contact dictionaries
        """
        self.contacts = contacts
        self.contact_rows = []

        # Clear existing rows
        try:
            container = self.query_one("#contact-container", Vertical)
            container.remove_children()

            # Add new rows
            for _i, contact in enumerate(contacts):
                row = ContactRow(contact)
                self.contact_rows.append(row)
                container.mount(row)

            # Select first contact if available
            if contacts:
                self.select_contact(0)
        except Exception:
            # Widget not mounted yet
            pass

    def select_contact(self, index: int) -> None:
        """Select a contact by index.

        Args:
            index: Index of the contact to select
        """
        if 0 <= index < len(self.contacts):
            # Deselect previous
            if 0 <= self.selected_index < len(self.contact_rows):
                self.contact_rows[self.selected_index].set_selected(False)

            # Select new
            self.selected_index = index
            self.selected_contact = self.contacts[index]

            if index < len(self.contact_rows):
                self.contact_rows[index].set_selected(True)

                # Scroll to selected row
                with contextlib.suppress(Exception):
                    self.contact_rows[index].scroll_visible()

    def handle_key(self, key: str) -> bool:
        """Handle key press events for navigation.

        Args:
            key: The key that was pressed

        Returns:
            True if the key was handled
        """
        if not self.contacts:
            return False

        handled = False

        if key == "j":  # Move down
            if self.selected_index < len(self.contacts) - 1:
                self.select_contact(self.selected_index + 1)
                handled = True

        elif key == "k":  # Move up
            if self.selected_index > 0:
                self.select_contact(self.selected_index - 1)
                handled = True

        elif key == "G":  # Go to bottom
            self.select_contact(len(self.contacts) - 1)
            handled = True

        elif key == "g":  # Go to top
            self.select_contact(0)
            handled = True

        return handled or super().handle_key(key)
