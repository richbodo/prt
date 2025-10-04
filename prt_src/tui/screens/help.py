"""Help screen for PRT TUI - Issue #114.

Displays comprehensive key binding reference and usage guide.
"""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static

from prt_src.logging_config import get_logger
from prt_src.tui.screens import register_screen
from prt_src.tui.screens.base import BaseScreen
from prt_src.tui.screens.base import EscapeIntent

logger = get_logger(__name__)


class HelpScreen(BaseScreen):
    """Help screen with comprehensive key bindings and usage guide."""

    def get_screen_name(self) -> str:
        """Get screen identifier."""
        return "help"

    def on_escape(self) -> EscapeIntent:
        """ESC goes back to previous screen."""
        return EscapeIntent.POP

    def get_footer_config(self):
        """Get footer configuration for help screen."""
        return {
            "keyHints": ["[ESC] Back"],
            "pager": None,
            "statusRight": None,
        }

    def compose(self) -> ComposeResult:
        """Compose help screen layout."""
        with Vertical(classes="help-container"):
            # Help title
            yield Static("🆘 PRT Help & Key Bindings", classes="help-title")

            # Global navigation section
            yield Static("Global Navigation:", classes="help-section-title")
            yield Static("Alt         - Toggle top nav menu", classes="help-item")
            yield Static("ESC         - Back/Cancel/Mode toggle", classes="help-item")
            yield Static("?           - Show this help screen", classes="help-item")
            yield Static("q           - Quit application", classes="help-item")
            yield Static("x           - Exit with confirmation", classes="help-item")

            # Top nav menu section
            yield Static("Top Nav Menu (when open with Alt):", classes="help-section-title")
            yield Static("B           - Back to previous screen", classes="help-item")
            yield Static("H           - Go to home screen", classes="help-item")
            yield Static("?           - Show this help screen", classes="help-item")

            # Home screen section
            yield Static("Home Screen:", classes="help-section-title")
            yield Static("c           - Contacts", classes="help-item")
            yield Static("s           - Search", classes="help-item")
            yield Static("r           - Relationships", classes="help-item")
            yield Static("y           - Relationship Types", classes="help-item")
            yield Static("i           - Import", classes="help-item")
            yield Static("e           - Export", classes="help-item")
            yield Static("d           - Database", classes="help-item")
            yield Static("m           - Metadata", classes="help-item")
            yield Static("t           - Chat", classes="help-item")

            # Contacts screen section
            yield Static("Contacts Screen:", classes="help-section-title")
            yield Static("a           - Add new contact", classes="help-item")
            yield Static("e           - Edit selected contact", classes="help-item")
            yield Static("d           - Delete selected contact", classes="help-item")
            yield Static("Enter       - View contact details", classes="help-item")
            yield Static("/           - Search contacts", classes="help-item")

            # Search screen section
            yield Static("Search Screen:", classes="help-section-title")
            yield Static("/           - Focus search input", classes="help-item")
            yield Static("Tab         - Cycle through filters", classes="help-item")
            yield Static("Enter       - Select search result", classes="help-item")

            # Chat screen section
            yield Static("Chat Screen:", classes="help-section-title")
            yield Static("Enter       - Send message", classes="help-item")
            yield Static("Shift+Enter - New line in message", classes="help-item")
            yield Static("Up/Down     - Navigate command history", classes="help-item")
            yield Static("Ctrl+L      - Clear chat history", classes="help-item")

            # Mode system section
            yield Static("Mode System:", classes="help-section-title")
            yield Static(
                "Navigation Mode - Default mode for browsing (j/k, single keys)",
                classes="help-item",
            )
            yield Static(
                "Edit Mode       - Text input mode (ESC toggles back)", classes="help-item"
            )

            # Debug features (if available)
            yield Static("Debug Features (Development):", classes="help-section-title")
            yield Static("d           - Toggle debug borders (dev mode)", classes="help-item")
            yield Static("l           - Log layout analysis (dev mode)", classes="help-item")
            yield Static("n           - Test notifications (dev mode)", classes="help-item")
            yield Static("s           - Screenshot capture (dev mode)", classes="help-item")
            yield Static("r           - Test responsive behavior (dev mode)", classes="help-item")


# Register the help screen
register_screen("help", HelpScreen)
