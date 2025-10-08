"""Home screen - Main entry point for TUI navigation."""

from textual import events
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static

from prt_src.logging_config import get_logger
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
        self.top_nav = TopNav(self.screen_title, id="top-nav")
        yield self.top_nav

        # Main content container
        with Container(id="home-content"):
            yield Static("* Chat - opens chat screen", classes="menu-option")
            yield Static("* Search - opens search screen", classes="menu-option")
            yield Static("* Settings - opens settings screen", classes="menu-option")

        # Dropdown menu (hidden by default)
        menu_items = [
            ("H", "Home", self.action_go_home),
            ("B", "Back", self.action_go_back),
        ]
        self.dropdown = DropdownMenu(menu_items, id="dropdown-menu")
        self.dropdown.display = False
        yield self.dropdown

        # Bottom navigation/status bar
        self.bottom_nav = BottomNav(id="bottom-nav")
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
            elif key == "question_mark":
                self.action_show_help()
                event.prevent_default()
            else:
                # Check if key matches dropdown menu action
                if self.dropdown.display:
                    action = self.dropdown.get_action(key)
                    if action:
                        action()
                        event.prevent_default()

    def action_toggle_menu(self) -> None:
        """Toggle dropdown menu visibility."""
        if self.dropdown.display:
            self.dropdown.hide()
            self.top_nav.menu_open = False
        else:
            self.dropdown.show()
            self.top_nav.menu_open = True
        self.top_nav.update(self.top_nav._format_nav_line())

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
        self.bottom_nav.show_status("Chat screen not yet implemented")
        logger.info("Navigate to chat screen (TODO)")
        # TODO: self.app.push_screen("chat")

    def action_open_search(self) -> None:
        """Open search screen."""
        self.bottom_nav.show_status("Search screen not yet implemented")
        logger.info("Navigate to search screen (TODO)")
        # TODO: self.app.push_screen("search")

    def action_open_settings(self) -> None:
        """Open settings screen."""
        self.bottom_nav.show_status("Settings screen not yet implemented")
        logger.info("Navigate to settings screen (TODO)")
        # TODO: self.app.push_screen("settings")

    def action_show_help(self) -> None:
        """Show help screen."""
        logger.info("Navigate to help screen")
        # TODO: Implement help screen navigation
        self.bottom_nav.show_status("Help screen navigation pending")

    def action_exit(self) -> None:
        """Exit application."""
        logger.info("Exit requested from home screen")
        self.app.exit()
