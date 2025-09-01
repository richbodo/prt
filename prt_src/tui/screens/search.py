"""Search screen for PRT TUI.

Full-text search with filters and export.
"""

from textual.app import ComposeResult
from textual.widgets import Static

from prt_src.tui.screens import register_screen
from prt_src.tui.screens.base import BaseScreen, EscapeIntent


class SearchScreen(BaseScreen):
    """Search screen with results and filters."""

    def get_screen_name(self) -> str:
        """Get screen identifier."""
        return "search"

    def __init__(self, *args, **kwargs):
        """Initialize search screen."""
        super().__init__(*args, **kwargs)
        self._has_results = False

    def on_escape(self) -> EscapeIntent:
        """POP if showing results, else HOME."""
        if self._has_results:
            return EscapeIntent.POP
        return EscapeIntent.HOME

    def get_footer_config(self) -> dict:
        """Configure footer with export hints."""
        config = super().get_footer_config()
        if config:
            config["keyHints"] = ["[e]xport", "[f]ilter", "[ESC] Back"]
        return config

    def compose(self) -> ComposeResult:
        """Compose search screen layout."""
        # TODO: Add SearchableList widget
        # TODO: Add FilterPanel widget
        # TODO: Wire UnifiedSearchAPI
        yield Static("Search Screen - Full-text Search", classes="screen-placeholder")


# Register this screen
register_screen("search", SearchScreen)
