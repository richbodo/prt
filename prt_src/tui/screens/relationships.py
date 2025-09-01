"""Relationships screen for PRT TUI.

Manage contact relationships with dual selector.
"""

from textual.app import ComposeResult
from textual.widgets import Static

from prt_src.tui.screens import register_screen
from prt_src.tui.screens.base import BaseScreen, EscapeIntent


class RelationshipsScreen(BaseScreen):
    """Relationships management screen."""

    def get_screen_name(self) -> str:
        """Get screen identifier."""
        return "relationships"

    def __init__(self, *args, **kwargs):
        """Initialize relationships screen."""
        super().__init__(*args, **kwargs)
        self._is_editing = False

    def on_escape(self) -> EscapeIntent:
        """CONFIRM if editing, else HOME."""
        if self._is_editing and self.has_unsaved_changes():
            return EscapeIntent.CONFIRM
        return EscapeIntent.HOME

    def get_footer_config(self) -> dict:
        """Configure footer with relationship hints."""
        config = super().get_footer_config()
        if config:
            config["keyHints"] = ["[a]dd", "[e]dit", "[d]elete", "[TAB] Switch", "[ESC] Back"]
        return config

    def compose(self) -> ComposeResult:
        """Compose relationships screen layout."""
        # TODO: Add RelationshipEditor widget
        # TODO: Add RelationshipList widget
        # TODO: Wire ValidationSystem
        yield Static("Relationships Screen - Dual Selector", classes="screen-placeholder")


# Register this screen
register_screen("relationships", RelationshipsScreen)
