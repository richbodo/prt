"""Base screen infrastructure for PRT TUI screens.

Provides thin base class with lifecycle hooks, slot configuration,
and ESC intent handling. Uses composition over inheritance with
injected services.

Refactored for Issue #120 to use Textual's Screen class directly.
"""

import contextlib
from enum import Enum
from typing import Any
from typing import Dict
from typing import Optional

from textual.app import ComposeResult
from textual.screen import Screen
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


class BaseScreen(Screen):
    """Base class for all TUI screens.

    Thin base with lifecycle hooks and slot configuration.
    All functionality via injected services.
    """

    def __init__(
        self,
        prt_app=None,
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
            prt_app: Reference to the main PRT app
            nav_service: Navigation service for screen transitions
            data_service: Data service wrapping PRTAPI
            notification_service: Service for toasts/dialogs
            selection_service: Phase 2 selection system
            validation_service: Phase 2 validation system
        """
        # Don't pass prt_app to Screen - it doesn't accept it
        super().__init__(*args, **kwargs)

        # Store app reference (Screen has its own 'app' property for Textual App)
        self.prt_app = prt_app
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
            with contextlib.suppress(Exception):
                breadcrumb = self.nav_service.get_breadcrumb()

        return {
            "title": self.__class__.__name__,
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

    def has_unsaved_changes(self) -> bool:
        """Check if screen has unsaved changes.

        Returns:
            True if there are unsaved changes
        """
        return self._has_unsaved_changes

    def mark_unsaved(self) -> None:
        """Mark the screen as having unsaved changes."""
        self._has_unsaved_changes = True
        logger.debug(f"{self.__class__.__name__} marked as having unsaved changes")

    def clear_unsaved(self) -> None:
        """Clear the unsaved changes flag."""
        self._has_unsaved_changes = False
        logger.debug(f"{self.__class__.__name__} unsaved changes cleared")

    def can_leave(self) -> bool:
        """Check if screen can be left.

        Returns:
            True if navigation away is allowed
        """
        # Return True if no unsaved changes, False otherwise
        return not self.has_unsaved_changes()

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
        logger.debug(f"{self.__class__.__name__} screen mounted")

    async def on_show(self) -> None:
        """Called when screen becomes visible.

        Refresh data if needed.
        """
        logger.debug(f"{self.__class__.__name__} screen shown")

    async def on_hide(self) -> None:
        """Called when screen is hidden but not destroyed.

        Save state if needed.
        """
        logger.debug(f"{self.__class__.__name__} screen hidden")

    async def on_unmount(self) -> None:
        """Called when screen is destroyed.

        Clean up resources.
        """
        logger.debug(f"{self.__class__.__name__} screen unmounted")

    def has_editable_widgets(self) -> bool:
        """Check if screen has any editable widgets (TextArea or Input).

        Uses automatic detection to support dynamic screens that may show/hide
        edit boxes based on state.

        Returns:
            True if screen has at least one TextArea or Input widget
        """
        try:
            from textual.widgets import Input
            from textual.widgets import TextArea

            editable = list(self.query(TextArea)) + list(self.query(Input))
            has_widgets = len(editable) > 0
            logger.debug(
                f"{self.__class__.__name__} has_editable_widgets: {has_widgets} ({len(editable)} widgets found)"
            )
            return has_widgets
        except Exception as e:
            logger.debug(f"Error checking for editable widgets: {e}")
            return False

    def on_mode_changed(self, mode) -> None:
        """Called when app mode changes between NAV and EDIT.

        Override in subclasses to handle mode changes (e.g., focus inputs when entering EDIT).

        Args:
            mode: The new AppMode
        """
        logger.debug(f"{self.__class__.__name__} mode changed to {mode.value}")

    def compose(self) -> ComposeResult:
        """Default compose for screens.

        Override to add screen content.
        """
        yield Static(f"{self.__class__.__name__} Screen", classes="screen-placeholder")
