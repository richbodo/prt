"""PRT Textual Application - Main entry point for TUI.

This module implements the main Textual application with mode management,
first-run detection, and global keybindings.
"""

from pathlib import Path
from typing import Optional

from textual import events
from textual.app import App
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container

from prt_src.config import load_config
from prt_src.db import Database
from prt_src.logging_config import get_logger
from prt_src.tui.screens import EscapeIntent
from prt_src.tui.screens import HelpScreen
from prt_src.tui.screens import HomeScreen
from prt_src.tui.services.navigation import NavigationService
from prt_src.tui.types import AppMode

logger = get_logger(__name__)


class FirstRunHandler:
    """Handles first-run detection and 'You' contact creation."""

    def __init__(self, db: Database):
        """Initialize the first-run handler.

        Args:
            db: Database instance for checking/creating contacts
        """
        self.db = db
        self._you_contact_id: Optional[int] = None

    def is_first_run(self) -> bool:
        """Check if this is the first run (no 'You' contact exists).

        Returns:
            True if no 'You' contact exists, False otherwise
        """
        try:
            you_contact = self.db.get_you_contact()
            if you_contact:
                self._you_contact_id = you_contact.get("id")
                return False
            return True
        except Exception as e:
            logger.error(f"Error checking for 'You' contact: {e}")
            return True

    def create_you_contact(self, name: Optional[str] = None) -> dict:
        """Create the 'You' contact.

        Args:
            name: Optional full name for the contact. If None, uses "You" as first name.

        Returns:
            The created contact dictionary
        """
        first_name = "You"
        last_name = ""

        if name and name.strip():
            parts = name.strip().split(maxsplit=1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ""

        contact_data = {
            "first_name": first_name,
            "last_name": last_name,
            "is_you": True,  # Special flag for the 'You' contact
        }

        try:
            contact = self.db.create_contact(contact_data)
            self._you_contact_id = contact.get("id")
            logger.info(f"Created 'You' contact with ID: {self._you_contact_id}")
            return contact
        except Exception as e:
            logger.error(f"Error creating 'You' contact: {e}")
            # Raise exception so caller can handle appropriately
            raise RuntimeError(f"Failed to create 'You' contact: {e}") from e

    @property
    def you_contact_id(self) -> Optional[int]:
        """Get the ID of the 'You' contact."""
        return self._you_contact_id


class PRTApp(App):
    """Main PRT Textual application."""

    # CSS file path (relative to app.py)
    CSS_PATH = "styles.tcss"

    # Keybindings
    BINDINGS = [
        Binding("escape", "toggle_mode", "Toggle Mode", priority=True),
        Binding("n", "toggle_top_nav", "Toggle Nav Menu", priority=True),
        Binding("q", "quit", "Quit", show=False),  # Only in NAV mode
        Binding("x", "exit_with_confirmation", "(x)exit", priority=True),  # Universal exit
        Binding("?", "help", "Help"),
    ]

    def __init__(self):
        """Initialize the PRT application."""
        super().__init__()
        self.title = "Personal Relationship Tracker"
        self.sub_title = "Modern TUI for Contact Management"
        self.dark = True  # Use dark theme by default

        # Initialize mode (use private attribute to avoid property conflict)
        self._app_mode = AppMode.NAVIGATION

        # Track current container for proper cleanup
        self.current_container_id: Optional[str] = None

        # Load config and initialize database
        try:
            config = load_config()
            db_path = Path(config["db_path"])
            self.db = TUIDatabase(db_path)
            self.db.connect()
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            # Create a minimal in-memory database for testing
            self.db = TUIDatabase(Path(":memory:"))
            self.db.connect()

        # Ensure database tables are created
        try:
            self.db.initialize()
            logger.info("Database tables initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database tables: {e}")

        # Initialize first-run handler
        self.first_run_handler = FirstRunHandler(self.db)

        # Check first run status
        self._is_first_run = self.first_run_handler.is_first_run()

        # Initialize navigation service
        self.nav_service = NavigationService()

        # Initialize data service
        from prt_src.api import PRTAPI
        from prt_src.tui.services.data import DataService
        from prt_src.tui.services.notification import NotificationService

        prt_api = PRTAPI()  # PRTAPI creates its own database connection
        self.data_service = DataService(prt_api)
        self.notification_service = NotificationService(self)

        # Current screen reference
        self.current_screen = None

        # Initialize database with default data
        self._initialize_database_data()

        # Services to inject into screens
        self.services = {
            "nav_service": self.nav_service,
            "data_service": self.data_service,
            "notification_service": self.notification_service,
            "selection_service": None,  # Will wire Phase 2 service
            "validation_service": None,  # Will wire Phase 2 service
        }

        # Initialize nav menu state (Issue #114)
        self.nav_menu_open = False
        self.nav_dropdown = None

        # Set initial header title (Issue #114)
        self.title = "(N)av menu closed"
        self.sub_title = "Personal Relationship Tracker"

    @property
    def current_mode(self) -> AppMode:
        """Get the current application mode."""
        return self._app_mode

    @current_mode.setter
    def current_mode(self, mode: AppMode) -> None:
        """Set the current application mode."""
        self._app_mode = mode

    def compose(self) -> ComposeResult:
        """Compose the application layout.

        For Issue #120 refactoring: Minimal compose, let screens handle their own layout.
        Textual's Screen system manages screen switching automatically.
        """
        # Return empty - screens compose themselves
        return
        yield  # Make this a generator (unreachable but needed for type)

    def on_mount(self) -> None:
        """Handle application mount event."""
        # Phase 1: Always go to home screen (no wizard yet)
        logger.info("Mounting app - pushing home screen")
        self.push_screen(HomeScreen(app=self, **self.services))

    def action_toggle_mode(self) -> None:
        """Toggle between navigation and edit modes."""
        if self.current_mode == AppMode.NAVIGATION:
            self.current_mode = AppMode.EDIT
        else:
            self.current_mode = AppMode.NAVIGATION

        # Update UI to reflect mode change
        self.sub_title = f"Mode: {self.current_mode.value}"
        logger.debug(f"Switched to {self.current_mode.value} mode")

        # Update TopNav on current screen if it exists
        try:
            from prt_src.tui.widgets import TopNav

            top_nav = self.screen.query_one(TopNav)
            top_nav.set_mode(self.current_mode)
        except Exception as e:
            logger.debug(f"Could not update TopNav: {e}")

    def action_quit(self) -> None:
        """Quit the application (only in navigation mode)."""
        if self.current_mode == AppMode.NAVIGATION:
            self.exit()

    async def action_toggle_top_nav(self) -> None:
        """Toggle the top nav dropdown menu."""
        # Delegate to current screen if it has the action
        try:
            if hasattr(self.screen, "action_toggle_menu"):
                self.screen.action_toggle_menu()
                logger.info("Toggled screen dropdown menu")
        except Exception as e:
            logger.debug(f"Could not toggle menu: {e}")

    async def _handle_nav_menu_key(self, key: str) -> bool:
        """Handle navigation menu key selection (Issue #114).

        Args:
            key: The pressed key

        Returns:
            True if key was handled, False otherwise
        """
        # Only handle keys when menu is open
        if not self.nav_menu_open:
            return False

        if key == "b":
            # Back to previous screen
            previous_screen = self.nav_service.pop()
            if previous_screen:
                self.navigate_to(previous_screen)
            else:
                self.navigate_to("home")
            # Close menu
            await self.action_toggle_top_nav()
            return True
        elif key == "h":
            # Home screen
            self.navigate_to("home")
            # Close menu
            await self.action_toggle_top_nav()
            return True
        elif key == "question_mark":
            # Help screen
            self.navigate_to("help")
            # Close menu
            await self.action_toggle_top_nav()
            return True

        return False

    async def _show_nav_dropdown(self) -> None:
        """Show the nav dropdown menu (Issue #114)."""
        if self.nav_dropdown:
            self.nav_dropdown.remove_class("hidden")
            self.nav_dropdown.add_class("visible")
            logger.info("Nav dropdown shown")

    async def _hide_nav_dropdown(self) -> None:
        """Hide the nav dropdown menu (Issue #114)."""
        if self.nav_dropdown:
            self.nav_dropdown.remove_class("visible")
            self.nav_dropdown.add_class("hidden")
            logger.info("Nav dropdown hidden")

    def action_help(self) -> None:
        """Show help screen."""
        # Navigate to help screen (Issue #114)
        self.call_after_refresh(lambda: self.navigate_to("help"))
        logger.info("Navigating to help screen")

    def action_exit_with_confirmation(self) -> None:
        """Exit with confirmation dialog (universal X key binding - works in any mode)."""
        logger.info(
            f"X key pressed - current mode: {self.current_mode.value} - exit confirmation requested"
        )
        # Schedule async confirmation dialog (works regardless of mode)
        self.call_after_refresh(self._handle_exit_confirmation)

    async def _handle_exit_confirmation(self) -> None:
        """Handle the async part of exit confirmation."""
        confirmed = await self.show_exit_confirmation()
        if confirmed:
            self.exit()

    def toggle_mode(self) -> None:
        """Public method to toggle mode (for testing)."""
        self.action_toggle_mode()

    async def on_key(self, event: events.Key) -> None:
        """Handle global key events.

        Args:
            event: Key event
        """
        logger.info(f"APP LEVEL - Key pressed: '{event.key}', mode: {self.current_mode.value}")

        # Handle exit confirmation if waiting for response
        if hasattr(self, "_waiting_for_exit_confirmation") and self._waiting_for_exit_confirmation:
            if event.key in ["y", "Y"]:
                logger.info("Y pressed - confirming exit")
                await self._handle_exit_confirmed()
                event.prevent_default()
                event.stop()
                return
            elif event.key in ["n", "N", "escape"]:
                logger.info("N/ESC pressed - cancelling exit")
                await self._handle_exit_cancelled()
                event.prevent_default()
                event.stop()
                return

        # Let BINDINGS and screens handle all other keys
        # Don't intercept - let event bubble to BINDINGS and screen handlers

    async def handle_escape(self) -> None:
        """Handle ESC key with per-screen intent."""
        if not self.current_screen:
            return

        # Get screen's ESC intent
        intent = self.current_screen.on_escape()

        if intent == EscapeIntent.CONFIRM:
            # Show discard confirmation dialog
            if await self.show_discard_dialog():
                self.nav_service.pop()
                self.navigate_to(self.nav_service.get_current_screen())
        elif intent == EscapeIntent.POP:
            # Pop navigation stack
            previous = self.nav_service.pop()
            if previous:
                self.navigate_to(previous)
        elif intent == EscapeIntent.HOME:
            # Go to home screen
            self.nav_service.go_home()
            self.navigate_to("home")
        elif intent == EscapeIntent.CUSTOM:
            # Let screen handle it
            self.current_screen.handle_custom_escape()
        # CANCEL means do nothing

    async def show_discard_dialog(self) -> bool:
        """Show discard confirmation dialog.

        Returns:
            True if user confirms discard
        """
        # TODO: Implement actual dialog widget
        # For now, just log and return True
        logger.info("Would show discard dialog")
        return True

    async def show_exit_confirmation(self) -> bool:
        """Show exit confirmation dialog with Y/N prompt, defaulting to N.

        Returns:
            True if user confirms exit (Y), False if cancelled (N or ESC)
        """
        logger.info("Showing simple exit confirmation")

        # Create a simple confirmation overlay
        from textual.containers import Center
        from textual.containers import Vertical
        from textual.widgets import Label

        # Create result tracker
        self._exit_result = {"confirmed": False, "responded": False}

        # Create simple confirmation widget
        confirmation_widget = Container(
            Center(
                Vertical(
                    Label("Exit PRT?", classes="confirm-title"),
                    Label("Y = Yes, (N) = No (default)", classes="confirm-message"),
                    Label("ESC = Cancel", classes="confirm-hint"),
                    classes="confirm-content",
                ),
                classes="confirm-center",
            ),
            id="exit-confirmation",
            classes="exit-confirmation-overlay",
        )

        # Mount the confirmation overlay with error handling
        try:
            await self.mount(confirmation_widget)
            # Set up a simple key handler for this confirmation
            self._waiting_for_exit_confirmation = True
            logger.info("Exit confirmation mounted - waiting for Y/N response")
        except Exception as e:
            logger.error(f"Failed to mount exit confirmation dialog: {e}")
            # Fallback: just exit without confirmation if dialog fails
            logger.warning("Dialog failed - falling back to immediate exit")
            return True

        return False  # For now, return False to avoid infinite loops

    async def _handle_exit_confirmed(self) -> None:
        """Handle confirmed exit."""
        logger.info("Exit confirmed - closing application")
        self._waiting_for_exit_confirmation = False

        # Remove confirmation dialog
        try:
            confirmation = self.query_one("#exit-confirmation")
            await confirmation.remove()
        except Exception:
            pass

        # Exit the application
        self.exit()

    async def _handle_exit_cancelled(self) -> None:
        """Handle cancelled exit."""
        logger.info("Exit cancelled - returning to application")
        self._waiting_for_exit_confirmation = False

        # Remove confirmation dialog
        try:
            confirmation = self.query_one("#exit-confirmation")
            await confirmation.remove()
        except Exception:
            pass

    def navigate_to(self, screen_name: str, params: Optional[dict] = None) -> None:
        """Navigate to a screen using Textual's push_screen.

        Args:
            screen_name: Name of screen to navigate to
            params: Optional parameters for the screen
        """
        params = params or {}

        # Update services with app reference (lazy injection to avoid circular deps)
        if self.services.get("notification_service"):
            self.services["notification_service"].set_app(self)

        # Create new screen instance (Phase 1: only home and help)
        screen_map = {
            "home": HomeScreen,
            "help": HelpScreen,
        }

        screen_class = screen_map.get(screen_name)
        if not screen_class:
            logger.error(f"Unknown screen: {screen_name}")
            return

        new_screen = screen_class(app=self, **self.services, **params)
        self.push_screen(new_screen)
        logger.info(f"Navigated to screen: {screen_name}")

    def _initialize_database_data(self) -> None:
        """Initialize database with default data (relationship types and 'You' contact).

        This method is called during app initialization to ensure:
        1. Default relationship types are seeded
        2. 'You' contact is created if missing (on first run)
        """
        try:
            # Use call_later to run async initialization after app is mounted
            self.call_later(self._async_initialize_database_data)
        except Exception as e:
            logger.error(f"Failed to schedule database data initialization: {e}")

    async def _async_initialize_database_data(self) -> None:
        """Async method to initialize database data."""
        try:
            # Seed default relationship types
            logger.info("Seeding default relationship types...")
            await self.data_service.seed_default_relationship_types()

            # Auto-create "You" contact if missing (first run)
            if self._is_first_run:
                logger.info("First run detected - creating 'You' contact")
                try:
                    self.first_run_handler.create_you_contact()
                    logger.info("'You' contact created successfully")
                except Exception as e:
                    logger.error(f"Failed to create 'You' contact: {e}")

        except Exception as e:
            logger.error(f"Failed to initialize database data: {e}")


# TUI Database Extensions
class TUIDatabase(Database):
    """Extended Database class with TUI-specific methods."""

    def get_you_contact(self):
        """Get the 'You' contact if it exists.

        Returns:
            Contact dict or None if not found
        """
        # Check for contact with is_you flag or first_name="You"
        from sqlalchemy import or_

        from prt_src.models import Contact

        try:
            you_contact = (
                self.session.query(Contact)
                .filter(or_(Contact.is_you.is_(True), Contact.first_name == "You"))
                .first()
            )

            if you_contact:
                return {
                    "id": you_contact.id,
                    "first_name": you_contact.first_name,
                    "last_name": you_contact.last_name or "",
                    "is_you": getattr(you_contact, "is_you", False),
                }
            return None
        except Exception as e:
            logger.error(f"Error getting 'You' contact: {e}")
            return None

    def create_contact(self, contact_data: dict) -> dict:
        """Create a new contact.

        Args:
            contact_data: Dictionary with contact fields

        Returns:
            Created contact as a dictionary
        """
        from prt_src.models import Contact

        try:
            first_name = contact_data.get("first_name", "")
            last_name = contact_data.get("last_name", "")
            full_name = f"{first_name} {last_name}".strip() or "(No name)"

            contact = Contact(
                name=full_name,
                first_name=first_name,
                last_name=last_name,
                email=contact_data.get("email"),
                phone=contact_data.get("phone"),
                is_you=contact_data.get("is_you", False),
            )
            self.session.add(contact)
            self.session.commit()

            return {
                "id": contact.id,
                "first_name": contact.first_name,
                "last_name": contact.last_name or "",
                "email": contact.email,
                "phone": contact.phone,
                "is_you": contact.is_you,
            }
        except Exception as e:
            logger.error(f"Error creating contact: {e}")
            self.session.rollback()
            raise


# Development runner
def main():
    """Run the PRT TUI application."""
    app = PRTApp()
    app.run()


if __name__ == "__main__":
    main()
