"""Chat mode screen for PRT TUI.

Natural language interface with command detection.
"""

from textual.app import ComposeResult
from textual.widgets import Static

from prt_src.tui.screens import register_screen
from prt_src.tui.screens.base import BaseScreen, EscapeIntent


class ChatScreen(BaseScreen):
    """Chat interface screen."""

    def get_screen_name(self) -> str:
        """Get screen identifier."""
        return "chat"

    def __init__(self, *args, **kwargs):
        """Initialize chat screen."""
        super().__init__(*args, **kwargs)
        self._has_input = False
        # Hide chrome for full-screen chat
        self.hide_chrome()

    def on_escape(self) -> EscapeIntent:
        """CUSTOM - clear input first, then HOME."""
        return EscapeIntent.CUSTOM

    def handle_custom_escape(self) -> None:
        """Handle custom ESC behavior."""
        if self._has_input:
            # Clear input field
            self._clear_input()
            self._has_input = False
        else:
            # Go home if no input
            if self.nav_service:
                self.nav_service.go_home()

    def _clear_input(self) -> None:
        """Clear the chat input field."""
        # TODO: Implement when chat input widget is added
        pass

    def compose(self) -> ComposeResult:
        """Compose chat screen layout."""
        # TODO: Add chat history display
        # TODO: Add input field with command detection
        # TODO: Add results preview pane
        yield Static("Chat Screen - Natural Language Interface", classes="screen-placeholder")


# Register this screen
register_screen("chat", ChatScreen)
