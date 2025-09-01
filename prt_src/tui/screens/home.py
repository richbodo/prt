"""Home screen for PRT TUI.

Main navigation screen with menu and stats.
"""

from textual.app import ComposeResult
from textual.widgets import Static

from prt_src.tui.screens import register_screen
from prt_src.tui.screens.base import BaseScreen, EscapeIntent
from prt_src.tui.widgets.navigation_menu import NavigationMenu


class HomeScreen(BaseScreen):
    """Home screen with navigation menu."""

    def get_screen_name(self) -> str:
        """Get screen identifier."""
        return "home"

    def on_escape(self) -> EscapeIntent:
        """ESC at home does nothing."""
        return EscapeIntent.CANCEL

    def compose(self) -> ComposeResult:
        """Compose home screen layout."""
        # TODO: Add NavigationMenu widget
        # TODO: Add quick stats display
        yield Static("Home Screen - Navigation Menu", classes="screen-placeholder")
        yield NavigationMenu()


# Register this screen
register_screen("home", HomeScreen)
