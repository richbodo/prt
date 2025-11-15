"""Settings screen - Configuration and database status display."""

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static

from prt_src.logging_config import get_logger
from prt_src.tui.constants import WidgetIDs
from prt_src.tui.screens.base import BaseScreen
from prt_src.tui.widgets import BottomNav
from prt_src.tui.widgets import DropdownMenu
from prt_src.tui.widgets import TopNav

logger = get_logger(__name__)


def get_database_stats_real() -> dict:
    """Get real database statistics using debug info orchestration.

    Returns:
        Dict with database statistics
    """
    try:
        from prt_src.debug_info import collect_database_info

        db_info = collect_database_info()

        if db_info["status"] == "healthy":
            stats = db_info["statistics"]
            return {
                "status": "connected",
                "contacts": stats.get("contacts", 0),
                "tags": stats.get("tags", 0),
                "relationships": stats.get("relationships", 0),
                "notes": stats.get("notes", 0),
            }
        else:
            return {
                "status": "error",
                "contacts": 0,
                "tags": 0,
                "relationships": 0,
                "notes": 0,
                "error": db_info.get("error", "Connection failed"),
            }
    except Exception as e:
        return {
            "status": "error",
            "contacts": 0,
            "tags": 0,
            "relationships": 0,
            "notes": 0,
            "error": str(e),
        }


class SettingsScreen(BaseScreen):
    """Settings screen with database status and configuration.

    Per spec:
    - Top Nav
    - Database Status Line (connection status + counts)
    - Placeholder for future import/export options
    - Bottom Nav
    """

    def __init__(self, **kwargs):
        """Initialize Settings screen."""
        super().__init__(**kwargs)
        self.screen_title = "SETTINGS"

    def compose(self) -> ComposeResult:
        """Compose the settings screen layout."""
        # Top navigation bar
        self.top_nav = TopNav(self.screen_title, id=WidgetIDs.TOP_NAV)
        yield self.top_nav

        # Database status section
        stats = get_database_stats_real()
        status_icon = "🟢" if stats["status"] == "connected" else "🔴"

        if stats["status"] == "connected":
            status_text = (
                f"{status_icon} Connected │ Contacts: {stats['contacts']} │ Tags: {stats['tags']}\n"
                f"Relationships: {stats['relationships']} │ Notes: {stats['notes']}"
            )
        else:
            error_msg = stats.get("error", "Unknown error")
            status_text = f"{status_icon} Error: {error_msg}"

        with Container(id=WidgetIDs.SETTINGS_CONTENT):
            yield Static(status_text, id=WidgetIDs.SETTINGS_DB_STATUS)
            yield Static(
                "\n(Future: Import/Export options)",
                id=WidgetIDs.SETTINGS_PLACEHOLDER,
            )

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
        logger.info("Settings screen mounted")

    def on_key(self, event) -> None:
        """Handle key presses.

        Args:
            event: Key event
        """
        from prt_src.tui.types import AppMode

        key = event.key.lower()

        # When ESC is pressed with dropdown open, close the dropdown
        if key == "escape" and self.dropdown.display:
            self.call_after_refresh(self._close_dropdown_if_open)

        # In NAV mode, handle keys
        if self.app.current_mode == AppMode.NAVIGATION:
            if key == "n":
                self.action_toggle_menu()
                event.prevent_default()
            elif self.dropdown.display:
                # When menu is open, check for menu actions
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
            logger.debug("Closed dropdown menu after ESC key")

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
        """Navigate to home screen."""
        self.dropdown.hide()
        self.top_nav.menu_open = False
        self.top_nav.refresh_display()
        logger.info("Navigating to home from settings screen")
        self.app.navigate_to("home")

    def action_go_back(self) -> None:
        """Go back to previous screen."""
        self.dropdown.hide()
        self.top_nav.menu_open = False
        self.top_nav.refresh_display()
        logger.info("Going back from settings screen")
        self.app.pop_screen()
