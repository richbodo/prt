"""Metadata management screen for PRT TUI.

Manage tags and notes for contacts.
"""

from textual.app import ComposeResult
from textual.widgets import Static

from prt_src.tui.screens import register_screen
from prt_src.tui.screens.base import BaseScreen, EscapeIntent


class MetadataScreen(BaseScreen):
    """Metadata (tags/notes) management screen."""

    def get_screen_name(self) -> str:
        """Get screen identifier."""
        return "metadata"

    def on_escape(self) -> EscapeIntent:
        """CONFIRM if unsaved, else HOME."""
        if self.has_unsaved_changes():
            return EscapeIntent.CONFIRM
        return EscapeIntent.HOME

    def get_header_config(self) -> dict:
        """Configure header with breadcrumb."""
        config = super().get_header_config()
        if config:
            config["title"] = "Contact Metadata"
        return config

    def get_footer_config(self) -> dict:
        """Configure footer with metadata actions."""
        config = super().get_footer_config()
        if config:
            config["keyHints"] = ["[t]ag", "[n]ote", "[b]ulk", "[ESC] Back"]
        return config

    def compose(self) -> ComposeResult:
        """Compose metadata screen layout."""
        # TODO: Add ContactListWidget for selection
        # TODO: Add tag management panel
        # TODO: Add note editor
        # TODO: Wire ValidationSystem and SelectionSystem
        yield Static("Metadata Screen - Tags & Notes", classes="screen-placeholder")


# Register this screen
register_screen("metadata", MetadataScreen)
