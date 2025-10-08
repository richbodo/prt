"""Home screen - Main entry point for TUI navigation."""

from textual import events
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static

from prt_src.logging_config import get_logger
from prt_src.tui.constants import CSSClasses
from prt_src.tui.constants import WidgetIDs
from prt_src.tui.screens.base import BaseScreen
from prt_src.tui.types import AppMode
from prt_src.tui.widgets import BottomNav
from prt_src.tui.widgets import DropdownMenu
from prt_src.tui.widgets import TopNav

logger = get_logger(__name__)


class HomeScreen(BaseScreen):
    """Home screen with simple navigation options.

    Per spec:
    - Top Nav with dropdown menu
    - Three text options: Chat, Search, Settings
    - Bottom Nav with key hints
    - Dropdown menu (N key toggles)
    """

    def __init__(self, **kwargs):
        """Initialize Home screen."""
        super().__init__(**kwargs)
        self.screen_title = "HOME"

    def compose(self) -> ComposeResult:
        """Compose the home screen layout."""
        # Top navigation bar
        self.top_nav = TopNav(self.screen_title, id=WidgetIDs.TOP_NAV)
        yield self.top_nav

        # Main content container
        with Container(id=WidgetIDs.HOME_CONTENT):
            yield Static("* (C)hat - opens chat screen", classes=CSSClasses.MENU_OPTION)
            yield Static("* (S)earch - opens search screen", classes=CSSClasses.MENU_OPTION)
            yield Static("* Se(t)tings - opens settings screen", classes=CSSClasses.MENU_OPTION)

        # Dropdown menu (hidden by default)
        menu_items = [
            ("H", "Home", self.action_go_home),
            ("B", "Back", self.action_go_back),
        ]
        self.dropdown = DropdownMenu(menu_items, id=WidgetIDs.DROPDOWN_MENU)
        self.dropdown.display = False
        yield self.dropdown

        # Bottom navigation/status bar
        self.bottom_nav = BottomNav(id=WidgetIDs.BOTTOM_NAV)
        yield self.bottom_nav

    async def on_mount(self) -> None:
        """Handle screen mount."""
        await super().on_mount()
        logger.info("Home screen mounted")

    def on_key(self, event: events.Key) -> None:
        """Handle key presses.

        Args:
            event: Key event
        """
        key = event.key.lower()

        # When ESC is pressed with dropdown open, close the dropdown
        if key == "escape" and self.dropdown.display:
            self.call_after_refresh(self._close_dropdown_if_open)

        # In NAV mode, handle single-key shortcuts
        if self.app.current_mode == AppMode.NAVIGATION:
            if key == "n":
                self.action_toggle_menu()
                event.prevent_default()
            elif key == "c":
                self.action_open_chat()
                event.prevent_default()
            elif key == "s":
                self.action_open_search()
                event.prevent_default()
            elif key == "t":
                self.action_open_settings()
                event.prevent_default()
            elif key == "x":
                self.action_exit()
                event.prevent_default()
            # Note: "?" key is handled by global App.action_help() binding
            # Don't handle it here to avoid double-push
            else:
                # Check if key matches dropdown menu action
                if self.dropdown.display:
                    action = self.dropdown.get_action(key)
                    if action:
                        action()
                        event.prevent_default()

    def _close_dropdown_if_open(self) -> None:
        """Close dropdown menu if open (called after ESC key)."""
        if self.dropdown.display:
            self.dropdown.hide()
            self.top_nav.menu_open = False
            self.top_nav.refresh_display()
            logger.info("Closed dropdown menu after ESC key")

    def action_toggle_menu(self) -> None:
        """Toggle dropdown menu visibility."""
        if self.dropdown.display:
            self.dropdown.hide()
            self.top_nav.menu_open = False
        else:
            self.dropdown.show()
            self.top_nav.menu_open = True
        self.top_nav.refresh_display()

    def action_go_home(self) -> None:
        """Navigate to home screen (already here)."""
        self.bottom_nav.show_status("Already on home screen")
        self.action_toggle_menu()  # Close menu

    def action_go_back(self) -> None:
        """Navigate back (no-op on home screen)."""
        self.bottom_nav.show_status("Already on home screen")
        self.action_toggle_menu()  # Close menu

    def action_open_chat(self) -> None:
        """Open chat screen."""
        logger.info("Navigate to chat screen")
        self.app.navigate_to("chat")

    def action_open_search(self) -> None:
        """Open search screen."""
        logger.info("Navigate to search screen")
        self.app.navigate_to("search")

    def action_open_settings(self) -> None:
        """Open settings screen."""
        logger.info("Navigate to settings screen")
        self.app.navigate_to("settings")

    def action_show_help(self) -> None:
        """Show help screen."""
        logger.info("Navigate to help screen")
        self.app.navigate_to("help")

    def action_exit(self) -> None:
        """Exit application."""
        logger.info("Exit requested from home screen")
        self.app.exit()
