"""Help screen - Simple help message placeholder."""

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static

from prt_src.logging_config import get_logger
from prt_src.tui.constants import WidgetIDs
from prt_src.tui.screens.base import BaseScreen
from prt_src.tui.screens.base import EscapeIntent
from prt_src.tui.widgets import BottomNav
from prt_src.tui.widgets import DropdownMenu
from prt_src.tui.widgets import TopNav

logger = get_logger(__name__)


class HelpScreen(BaseScreen):
    """Help screen with placeholder message.

    Per spec:
    - Top Nav
    - Single line: "Help not implemented yet."
    - Bottom Nav
    """

    def __init__(self, **kwargs):
        """Initialize Help screen."""
        super().__init__(**kwargs)
        self.screen_title = "HELP"

    def compose(self) -> ComposeResult:
        """Compose the help screen layout."""
        # Top navigation bar
        self.top_nav = TopNav(self.screen_title, id=WidgetIDs.TOP_NAV)
        yield self.top_nav

        # Main content container
        with Container(id=WidgetIDs.HELP_CONTENT):
            yield Static("Help not implemented yet.", id=WidgetIDs.HELP_MESSAGE)

        # Dropdown menu (hidden by default)
        self.dropdown = DropdownMenu(
            [
                ("H", "Home", self.action_go_home),
                ("B", "Back", self.action_go_back),
            ],
            id=WidgetIDs.DROPDOWN_MENU,
        )
        self.dropdown.display = False
        yield self.dropdown

        # Bottom navigation/status bar
        self.bottom_nav = BottomNav(id=WidgetIDs.BOTTOM_NAV)
        yield self.bottom_nav

    async def on_mount(self) -> None:
        """Handle screen mount."""
        await super().on_mount()
        logger.info("Help screen mounted")

    def on_escape(self) -> EscapeIntent:
        """Handle ESC key on help screen.

        Returns:
            EscapeIntent.POP to go back to previous screen
        """
        return EscapeIntent.POP

    def on_key(self, event) -> None:
        """Handle key presses.

        Args:
            event: Key event
        """

        from prt_src.tui.types import AppMode

        key = event.key.lower()
        logger.info(
            f"[HELP] on_key called: key='{key}', dropdown.display={self.dropdown.display}, mode={self.app.current_mode}"
        )

        # When ESC is pressed with dropdown open, close the dropdown
        if key == "escape" and self.dropdown.display:
            self.call_after_refresh(self._close_dropdown_if_open)

        # In NAV mode, handle keys
        if self.app.current_mode == AppMode.NAVIGATION:
            if key == "n":
                logger.info("[HELP] Handling 'n' key - toggling menu")
                self.action_toggle_menu()
                event.prevent_default()
            elif self.dropdown.display:
                # When menu is open, check for menu actions
                logger.info(f"[HELP] Menu is open, looking for action for key '{key}'")
                action = self.dropdown.get_action(key)
                logger.info(f"[HELP] get_action('{key}') returned: {action}")
                if action:
                    logger.info(f"[HELP] Calling action for key '{key}'")
                    action()
                    logger.info(f"[HELP] Action for key '{key}' completed")
                    event.prevent_default()
                else:
                    logger.warning(f"[HELP] No action found for key '{key}'")

    def _close_dropdown_if_open(self) -> None:
        """Close dropdown menu if open (called after ESC key)."""
        if self.dropdown.display:
            self.dropdown.hide()
            self.top_nav.menu_open = False
            self.top_nav.refresh_display()
            logger.info("[HELP] Closed dropdown menu after ESC key")

    def action_toggle_menu(self) -> None:
        """Toggle dropdown menu visibility."""
        if self.dropdown.display:
            self.dropdown.hide()
            self.top_nav.menu_open = False
        else:
            self.dropdown.show()
            self.top_nav.menu_open = True
        self.top_nav.refresh_display()
        logger.debug(f"Help screen menu toggled: {self.dropdown.display}")

    def action_go_home(self) -> None:
        """Navigate to home screen."""
        logger.info("[HELP] action_go_home STARTED")
        logger.info(
            f"[HELP] Before hide - dropdown.display={self.dropdown.display}, menu_open={self.top_nav.menu_open}"
        )
        self.dropdown.hide()
        self.top_nav.menu_open = False
        self.top_nav.refresh_display()
        logger.info(
            f"[HELP] After hide - dropdown.display={self.dropdown.display}, menu_open={self.top_nav.menu_open}"
        )
        logger.info("[HELP] Calling navigate_to('home')")
        self.app.navigate_to("home")
        logger.info("[HELP] action_go_home COMPLETED")

    def action_go_back(self) -> None:
        """Go back to previous screen."""
        logger.info("[HELP] action_go_back STARTED")
        logger.info(
            f"[HELP] Before hide - dropdown.display={self.dropdown.display}, menu_open={self.top_nav.menu_open}"
        )
        self.dropdown.hide()
        self.top_nav.menu_open = False
        self.top_nav.refresh_display()
        logger.info(
            f"[HELP] After hide - dropdown.display={self.dropdown.display}, menu_open={self.top_nav.menu_open}"
        )
        logger.info("[HELP] Calling pop_screen()")
        self.app.pop_screen()
        logger.info("[HELP] action_go_back COMPLETED")
