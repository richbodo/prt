"""Top navigation bar widget."""

from textual.app import ComposeResult
from textual.widgets import Static

from prt_src.tui.types import AppMode


class TopNav(Static):
    """Top navigation bar with menu button, screen name, and mode indicator.

    Layout: (N)av menu closed | SCREEN_NAME | Mode: Nav
    """

    def __init__(self, screen_name: str, **kwargs):
        """Initialize TopNav.

        Args:
            screen_name: Name of current screen (e.g., "HOME", "CHAT")
            **kwargs: Additional keyword arguments for Static
        """
        super().__init__(**kwargs)
        self.screen_name = screen_name.upper()
        self.menu_open = False
        self._current_mode = AppMode.NAVIGATION

    def compose(self) -> ComposeResult:
        """Compose the navigation bar."""
        self.update(self._format_nav_line())
        return super().compose()

    def toggle_menu(self) -> None:
        """Toggle menu open/closed state."""
        self.menu_open = not self.menu_open
        self.update(self._format_nav_line())

    def set_mode(self, mode: AppMode) -> None:
        """Update mode indicator.

        Args:
            mode: Current application mode
        """
        self._current_mode = mode
        self.update(self._format_nav_line())

    def set_screen_name(self, name: str) -> None:
        """Update screen name.

        Args:
            name: New screen name
        """
        self.screen_name = name.upper()
        self.update(self._format_nav_line())

    def refresh_display(self) -> None:
        """Refresh the navigation bar display.

        Public method to update the display with current state.
        Use this instead of calling _format_nav_line() directly.
        """
        self.update(self._format_nav_line())

    def _format_nav_line(self) -> str:
        """Format the navigation bar content.

        Returns:
            Formatted string for navigation bar
        """
        menu_state = "open" if self.menu_open else "closed"
        mode_text = "Edit" if self._current_mode == AppMode.EDIT else "Nav"
        return f"(N)av menu {menu_state}  │  {self.screen_name}  │  Mode: {mode_text}"
