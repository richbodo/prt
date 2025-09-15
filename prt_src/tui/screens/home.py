"""Home screen for PRT TUI.

Main navigation screen with menu and stats.
"""

from textual import events
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static

from prt_src.logging_config import get_logger
from prt_src.tui.screens import register_screen
from prt_src.tui.screens.base import BaseScreen
from prt_src.tui.screens.base import EscapeIntent
from prt_src.tui.widgets.navigation_menu import MenuItem
from prt_src.tui.widgets.navigation_menu import NavigationMenu

logger = get_logger(__name__)


class HomeScreen(BaseScreen):
    """Home screen with navigation menu."""

    def __init__(self, *args, **kwargs):
        """Initialize home screen."""
        super().__init__(*args, **kwargs)
        self.navigation_menu = None

    def get_screen_name(self) -> str:
        """Get screen identifier."""
        return "home"

    def on_escape(self) -> EscapeIntent:
        """ESC at home does nothing."""
        return EscapeIntent.CANCEL

    def get_footer_config(self):
        """Get footer configuration for home screen."""
        return {
            "keyHints": [
                "[c] Contacts",
                "[s] Search",
                "[r] Relationships",
                "[y] Rel. Types",
                "[i] Import",
                "[e] Export",
                "[d] Database",
                "[m] Metadata",
                "[t] Chat",
                "[?] Help",
                "[q] Quit",
                "[x] Exit (universal)",
            ],
            "pager": None,
            "statusRight": None,
        }

    def compose(self) -> ComposeResult:
        """Compose home screen layout."""
        with Vertical(classes="home-container"):
            # Welcome message with app title
            yield Static("🏠 Personal Relationship Tracker (PRT)", classes="home-title")
            yield Static(
                "Navigate using the menu below or press the corresponding key",
                classes="home-subtitle",
            )

            # Navigation menu with callback
            self.navigation_menu = NavigationMenu(on_activate=self._handle_menu_activation)
            yield self.navigation_menu

    def _handle_menu_activation(self, menu_item: MenuItem) -> None:
        """Handle navigation menu item activation.

        Args:
            menu_item: The selected menu item
        """
        logger.info(f"Menu item activated: {menu_item.action}")

        try:
            if menu_item.action == "quit":
                # Handle quit action - this would be handled by the app
                logger.info("Quit requested")
                if hasattr(self.app, "exit"):
                    self.app.exit()
                return
            elif menu_item.action == "help":
                # Navigate to help screen
                self._navigate_to_screen("help")
            elif menu_item.action == "contacts":
                # Navigate to contacts screen
                self._navigate_to_screen("contacts")
            elif menu_item.action == "search":
                # Navigate to search screen
                self._navigate_to_screen("search")
            elif menu_item.action == "relationships":
                # Navigate to relationships screen
                self._navigate_to_screen("relationships")
            elif menu_item.action == "relationship_types":
                # Navigate to relationship types screen
                self._navigate_to_screen("relationship_types")
            elif menu_item.action == "import":
                # Navigate to import screen
                self._navigate_to_screen("import")
            elif menu_item.action == "export":
                # Navigate to export screen
                self._navigate_to_screen("export")
            elif menu_item.action == "database":
                # Navigate to database screen
                self._navigate_to_screen("database")
            elif menu_item.action == "metadata":
                # Navigate to metadata screen
                self._navigate_to_screen("metadata")
            elif menu_item.action == "chat":
                # Navigate to chat screen
                self._navigate_to_screen("chat")
            else:
                logger.warning(f"Unknown menu action: {menu_item.action}")

        except Exception as e:
            logger.error(f"Error handling menu activation: {e}")

    def _navigate_to_screen(self, screen_name: str) -> None:
        """Navigate to a screen using the navigation service.

        Args:
            screen_name: Name of the screen to navigate to
        """
        if not self.nav_service:
            logger.warning("Navigation service not available")
            return

        try:
            # Push the screen to navigation stack
            self.nav_service.push(screen_name)

            # Schedule async screen switch using set_timer
            if hasattr(self.app, "switch_screen"):
                self.set_timer(0.01, lambda: self._perform_switch(screen_name))
            else:
                logger.warning("App does not have switch_screen method")

        except Exception as e:
            logger.error(f"Error navigating to {screen_name}: {e}")

    async def _perform_switch(self, screen_name: str) -> None:
        """Perform the actual screen switch asynchronously.

        Args:
            screen_name: Name of the screen to switch to
        """
        try:
            await self.app.switch_screen(screen_name)
        except Exception as e:
            logger.error(f"Error performing screen switch to {screen_name}: {e}")

    async def on_key(self, event: events.Key) -> None:
        """Handle key events for navigation menu.

        Args:
            event: Key event
        """
        logger.info(f"HOME SCREEN - Key pressed: '{event.key}'")

        if self.navigation_menu:
            # Delegate key handling to navigation menu
            handled = self.navigation_menu.handle_key(event.key)
            logger.info(f"Navigation menu handled '{event.key}': {handled}")
            if handled:
                return

        # If navigation menu didn't handle it, let the app handle it
        logger.info(f"HOME SCREEN - Key '{event.key}' not handled by nav menu, checking app level")

        # Check if this is an app-level key binding
        if event.key in ["x", "q", "question_mark"]:
            logger.info(f"HOME SCREEN - Delegating '{event.key}' to app level")
            # Don't call super().on_key() - let the app's key binding system handle it
            return

        # For other keys, fall back to parent handling
        logger.info(f"HOME SCREEN - Falling back to parent for key: '{event.key}'")
        await super().on_key(event)


# Register this screen
register_screen("home", HomeScreen)
