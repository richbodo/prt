"""PRT Textual Application - Main entry point for TUI.

This module implements the main Textual application with mode management,
first-run detection, and global keybindings.
"""

from enum import Enum
from pathlib import Path
from typing import Optional

from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Footer, Header, Static

from prt_src.config import load_config
from prt_src.db import Database
from prt_src.logging_config import get_logger
from prt_src.tui.screens import EscapeIntent, create_screen
from prt_src.tui.services.navigation import NavigationService

logger = get_logger(__name__)


class AppMode(Enum):
    """Application mode enumeration."""

    NAVIGATION = "NAV"
    EDIT = "EDIT"


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
        Binding("q", "quit", "Quit", show=False),  # Only in NAV mode
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

        # Load config and initialize database
        try:
            config = load_config()
            db_path = Path(config["db_path"])
            self.db = Database(db_path)
            self.db.connect()
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            # Create a minimal in-memory database for testing
            self.db = Database(Path(":memory:"))
            self.db.connect()

        # Initialize first-run handler
        self.first_run_handler = FirstRunHandler(self.db)

        # Check first run status
        self._is_first_run = self.first_run_handler.is_first_run()

        # Initialize navigation service
        self.nav_service = NavigationService()

        # Current screen reference
        self.current_screen = None

        # Services to inject into screens (will be expanded in 4A.4)
        self.services = {
            "nav_service": self.nav_service,
            "data_service": None,  # Will be added in 4A.4
            "notification_service": None,  # Will be added in 4A.4
            "selection_service": None,  # Will wire Phase 2 service
            "validation_service": None,  # Will wire Phase 2 service
        }

    @property
    def current_mode(self) -> AppMode:
        """Get the current application mode."""
        return self._app_mode

    @current_mode.setter
    def current_mode(self, mode: AppMode) -> None:
        """Set the current application mode."""
        self._app_mode = mode

    def compose(self) -> ComposeResult:
        """Compose the application layout."""
        yield Header()
        yield Container(Static("Welcome to PRT!", id="welcome"), id="main-container")
        yield Footer()

    def on_mount(self) -> None:
        """Handle application mount event."""
        if self._is_first_run:
            # Will show first-run setup in future
            logger.info("First run detected - will show setup")
        else:
            logger.info("Existing installation detected")

    def action_toggle_mode(self) -> None:
        """Toggle between navigation and edit modes."""
        if self.current_mode == AppMode.NAVIGATION:
            self.current_mode = AppMode.EDIT
        else:
            self.current_mode = AppMode.NAVIGATION

        # Update UI to reflect mode change
        self.sub_title = f"Mode: {self.current_mode.value}"
        logger.debug(f"Switched to {self.current_mode.value} mode")

    def action_quit(self) -> None:
        """Quit the application (only in navigation mode)."""
        if self.current_mode == AppMode.NAVIGATION:
            self.exit()

    def action_help(self) -> None:
        """Show help screen."""
        # Will implement help screen later
        logger.info("Help requested")

    def toggle_mode(self) -> None:
        """Public method to toggle mode (for testing)."""
        self.action_toggle_mode()

    async def on_key(self, event: events.Key) -> None:
        """Handle global key events.

        Args:
            event: Key event
        """
        if event.key == "escape":
            await self.handle_escape()

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
                await self.switch_screen(self.nav_service.get_current_screen())
        elif intent == EscapeIntent.POP:
            # Pop navigation stack
            previous = self.nav_service.pop()
            if previous:
                await self.switch_screen(previous)
        elif intent == EscapeIntent.HOME:
            # Go to home screen
            self.nav_service.go_home()
            await self.switch_screen("home")
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

    async def switch_screen(self, screen_name: str, params: Optional[dict] = None) -> None:
        """Switch to a different screen.

        Args:
            screen_name: Name of screen to switch to
            params: Optional parameters for the screen
        """
        params = params or {}

        # Create new screen instance
        new_screen = create_screen(screen_name, **self.services, **params)

        if not new_screen:
            logger.error(f"Failed to create screen: {screen_name}")
            return

        # Hide current screen
        if self.current_screen:
            await self.current_screen.on_hide()
            self.query_one("#main-container").remove()

        # Mount new screen
        self.current_screen = new_screen
        await self.mount(Container(new_screen, id="main-container"))

        # Show new screen
        await new_screen.on_show()

        logger.info(f"Switched to screen: {screen_name}")


# Placeholder for Database extensions
# We'll need to add get_you_contact method to Database class
def extend_database():
    """Extend Database class with TUI-specific methods."""

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

    # Monkey-patch for now, will properly integrate later
    if not hasattr(Database, "get_you_contact"):
        Database.get_you_contact = get_you_contact
    if not hasattr(Database, "create_contact"):
        Database.create_contact = create_contact


# Apply database extensions on import
extend_database()
