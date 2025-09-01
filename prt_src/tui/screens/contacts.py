"""Contacts screen for PRT TUI.

Displays paginated contact list with search and multi-select.
"""

from textual.app import ComposeResult
from textual.widgets import Static

from prt_src.tui.screens import register_screen
from prt_src.tui.screens.base import BaseScreen


class ContactsScreen(BaseScreen):
    """Contacts management screen."""

    def get_screen_name(self) -> str:
        """Get screen identifier."""
        return "contacts"

    def get_header_config(self) -> dict:
        """Configure header with search box."""
        config = super().get_header_config()
        if config:
            config["searchBox"] = True
        return config

    def get_footer_config(self) -> dict:
        """Configure footer with action hints."""
        config = super().get_footer_config()
        if config:
            config["keyHints"] = ["[a]dd", "[e]dit", "[d]elete", "[s]earch", "[ESC] Home"]
        return config

    def compose(self) -> ComposeResult:
        """Compose contacts screen layout."""
        # TODO: Add ContactListWidget
        # TODO: Add ContactDetailView
        # TODO: Wire PaginationSystem
        yield Static("Contacts Screen - List & Detail", classes="screen-placeholder")


# Register this screen
register_screen("contacts", ContactsScreen)
