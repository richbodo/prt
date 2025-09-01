"""Base screen infrastructure for PRT TUI screens.

Provides thin base class with lifecycle hooks, slot configuration,
and ESC intent handling. Uses composition over inheritance with
injected services.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static

from prt_src.logging_config import get_logger

logger = get_logger(__name__)


class EscapeIntent(Enum):
    """Intent for ESC key handling."""

    CONFIRM = "confirm"  # Show discard dialog if unsaved changes
    POP = "pop"  # Pop navigation stack
    HOME = "home"  # Go to home screen
    CANCEL = "cancel"  # Do nothing (e.g., already at home)
    CUSTOM = "custom"  # Screen handles ESC itself


class BaseScreen(Container, ABC):
    """Base class for all TUI screens.

    Thin base with lifecycle hooks and slot configuration.
    All functionality via injected services.
    """

    def __init__(
        self,
        nav_service=None,
        data_service=None,
        notification_service=None,
        selection_service=None,
        validation_service=None,
        *args,
        **kwargs,
    ):
        """Initialize base screen with injected services.

        Args:
            nav_service: Navigation service for screen transitions
            data_service: Data service wrapping PRTAPI
            notification_service: Service for toasts/dialogs
            selection_service: Phase 2 selection system
            validation_service: Phase 2 validation system
        """
        super().__init__(*args, **kwargs)

        # Store injected services
        self.nav_service = nav_service
        self.data_service = data_service
        self.notification_service = notification_service
        self.selection_service = selection_service
        self.validation_service = validation_service

        # Track unsaved changes
        self._has_unsaved_changes = False

        # Track if header/footer should be shown
        self._show_header = True
        self._show_footer = True

        # Screen-specific CSS class
        self.add_class(f"screen-{self.get_screen_name()}")

    @abstractmethod
    def get_screen_name(self) -> str:
        """Get the screen's unique name.

        Returns:
            Screen identifier (e.g., "home", "contacts")
        """
        pass

    def get_header_config(self) -> Optional[Dict[str, Any]]:
        """Get header slot configuration.

        Returns:
            Dict with header config or None to hide header
            {
                "title": str,
                "breadcrumb": List[str],
                "searchBox": bool,
                "compact": bool
            }
        """
        if not self._show_header:
            return None

        # Safe navigation service access with null check
        breadcrumb = []
        if self.nav_service:
            try:
                breadcrumb = self.nav_service.get_breadcrumb()
            except Exception:
                pass  # Navigation service may not be initialized

        return {
            "title": self.get_screen_name().title(),
            "breadcrumb": breadcrumb,
            "searchBox": False,
            "compact": False,
        }

    def get_footer_config(self) -> Optional[Dict[str, Any]]:
        """Get footer slot configuration.

        Returns:
            Dict with footer config or None to hide footer
            {
                "keyHints": List[str],
                "pager": str,
                "statusRight": str
            }
        """
        if not self._show_footer:
            return None

        return {
            "keyHints": ["[ESC] Back", "[?] Help"],
            "pager": None,
            "statusRight": None,
        }

    def on_escape(self) -> EscapeIntent:
        """Declare intent for ESC key handling.

        Returns:
            EscapeIntent enum value
        """
        # Default behavior: confirm if unsaved, else go home
        if self.has_unsaved_changes():
            return EscapeIntent.CONFIRM
        return EscapeIntent.HOME

    def handle_custom_escape(self) -> None:
        """Handle custom ESC behavior.

        Called when on_escape() returns CUSTOM.
        Override in screens that need special ESC handling.
        """
        pass

    def has_unsaved_changes(self) -> bool:
        """Check if screen has unsaved changes.

        Returns:
            True if there are unsaved changes
        """
        return self._has_unsaved_changes

    def mark_unsaved(self) -> None:
        """Mark the screen as having unsaved changes."""
        self._has_unsaved_changes = True
        logger.debug(f"{self.get_screen_name()} marked as having unsaved changes")

    def clear_unsaved(self) -> None:
        """Clear the unsaved changes flag."""
        self._has_unsaved_changes = False
        logger.debug(f"{self.get_screen_name()} unsaved changes cleared")

    def can_leave(self) -> bool:
        """Check if screen can be left.

        Returns:
            True if navigation away is allowed
        """
        # Can always leave if no unsaved changes
        if not self.has_unsaved_changes():
            return True

        # If we have unsaved changes, the app will show confirm dialog
        # This is just for programmatic checks
        return False

    def hide_header(self) -> None:
        """Hide the header for this screen."""
        self._show_header = False

    def show_header(self) -> None:
        """Show the header for this screen."""
        self._show_header = True

    def hide_footer(self) -> None:
        """Hide the footer for this screen."""
        self._show_footer = False

    def show_footer(self) -> None:
        """Show the footer for this screen."""
        self._show_footer = True

    def hide_chrome(self) -> None:
        """Hide both header and footer (full screen mode)."""
        self.hide_header()
        self.hide_footer()

    def show_chrome(self) -> None:
        """Show both header and footer."""
        self.show_header()
        self.show_footer()

    # Lifecycle hooks

    async def on_mount(self) -> None:
        """Called when screen is mounted.

        Load data and initialize state here.
        """
        logger.debug(f"{self.get_screen_name()} screen mounted")

    async def on_show(self) -> None:
        """Called when screen becomes visible.

        Refresh data if needed.
        """
        logger.debug(f"{self.get_screen_name()} screen shown")

    async def on_hide(self) -> None:
        """Called when screen is hidden but not destroyed.

        Save state if needed.
        """
        logger.debug(f"{self.get_screen_name()} screen hidden")

    async def on_unmount(self) -> None:
        """Called when screen is destroyed.

        Clean up resources.
        """
        logger.debug(f"{self.get_screen_name()} screen unmounted")

    def compose(self) -> ComposeResult:
        """Default compose for screens.

        Override to add screen content.
        """
        yield Static(f"{self.get_screen_name().title()} Screen", classes="screen-placeholder")
