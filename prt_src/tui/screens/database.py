"""Database management screen for PRT TUI.

Game-style backup/restore with slots.
"""

from textual.app import ComposeResult
from textual.widgets import Static

from prt_src.tui.screens import register_screen
from prt_src.tui.screens.base import BaseScreen


class DatabaseScreen(BaseScreen):
    """Database management screen."""

    def get_screen_name(self) -> str:
        """Get screen identifier."""
        return "database"

    def get_footer_config(self) -> dict:
        """Configure footer with database actions."""
        config = super().get_footer_config()
        if config:
            config["keyHints"] = ["[b]ackup", "[r]estore", "[d]elete", "[ESC] Home"]
        return config

    def compose(self) -> ComposeResult:
        """Compose database screen layout."""
        # TODO: Create and add BackupSlots widget
        # TODO: Add database statistics panel
        # TODO: Add connection status
        yield Static("Database Screen - Backup Slots", classes="screen-placeholder")


# Register this screen
register_screen("database", DatabaseScreen)
