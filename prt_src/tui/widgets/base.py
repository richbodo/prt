"""Base widgets for the PRT Textual TUI.

This module provides foundational widgets that handle mode management,
status display, notifications, and confirmations.
"""

import contextlib
from collections.abc import Callable

from textual import events
from textual import on
from textual.app import ComposeResult
from textual.containers import Container
from textual.containers import Horizontal
from textual.containers import Vertical
from textual.reactive import reactive
from textual.timer import Timer
from textual.widgets import Button
from textual.widgets import Label
from textual.widgets import Static

from prt_src.logging_config import get_logger
from prt_src.tui.types import AppMode

logger = get_logger(__name__)


class ModeAwareWidget(Static):
    """Base widget that responds to application mode changes.

    This widget provides mode-aware styling and behavior, automatically
    updating its appearance based on the current application mode.
    """

    # Reactive mode property
    mode = reactive(AppMode.NAVIGATION)

    def __init__(self, *args, **kwargs):
        """Initialize the mode-aware widget."""
        super().__init__(*args, **kwargs)
        self.on_mode_toggle: Callable | None = None
        self._update_mode_classes()

    def set_mode(self, mode: AppMode) -> None:
        """Set the current mode and update appearance.

        Args:
            mode: The new application mode
        """
        self.mode = mode
        self._update_mode_classes()

    def _update_mode_classes(self) -> None:
        """Update CSS classes based on current mode."""
        # Remove all mode classes
        self.remove_class("navigation", "edit")

        # Add current mode class
        if self.mode == AppMode.NAVIGATION:
            self.add_class("navigation")
        elif self.mode == AppMode.EDIT:
            self.add_class("edit")

    def handle_key(self, key: str) -> bool:
        """Handle key press events.

        Args:
            key: The key that was pressed

        Returns:
            True if the key was handled, False otherwise
        """
        if key == "escape" and self.on_mode_toggle:
            self.on_mode_toggle()
            return True
        return False

    @property
    def classes(self) -> set[str]:
        """Get the current CSS classes."""
        # Use Textual's built-in classes property
        return super().classes


class StatusBar(ModeAwareWidget):
    """Status bar widget showing mode, selection count, and help hints.

    This widget displays:
    - Current application mode (NAV/EDIT)
    - Number of selected items
    - Context-sensitive help hints
    - Current location/breadcrumb
    """

    def __init__(self):
        """Initialize the status bar."""
        super().__init__()
        self.mode_text = "NAV"
        self.selection_text = ""
        self.help_text = ""
        self.location_text = "Home"
        self.add_class("status-bar")

    def compose(self) -> ComposeResult:
        """Compose the status bar layout."""
        with Horizontal(id="status-container"):
            # Left side: mode and selection
            with Horizontal(id="status-left"):
                yield Label(self.mode_text, id="mode-indicator", classes="mode-indicator")
                yield Label(self.selection_text, id="selection-count", classes="selection-count")

            # Center: location
            yield Label(self.location_text, id="location", classes="location")

            # Right side: help hints
            yield Label(self.help_text, id="help-hints", classes="help-hints")

    def set_mode(self, mode: AppMode) -> None:
        """Set the mode and update display.

        Args:
            mode: The new application mode
        """
        super().set_mode(mode)
        self.mode_text = mode.value

        # Try to update UI if mounted
        try:
            mode_label = self.query_one("#mode-indicator", Label)
            mode_label.update(self.mode_text)

            # Update mode indicator styling
            mode_label.remove_class("navigation", "edit")
            mode_label.add_class("navigation" if mode == AppMode.NAVIGATION else "edit")
        except Exception:
            # Widget not mounted yet, that's ok
            pass

    def update_selection_count(self, count: int) -> None:
        """Update the selection count display.

        Args:
            count: Number of selected items
        """
        if count == 0:
            self.selection_text = ""
        elif count == 1:
            self.selection_text = "1 selected"
        else:
            self.selection_text = f"{count} selected"

        # Try to update UI if mounted
        with contextlib.suppress(Exception):
            self.query_one("#selection-count", Label).update(self.selection_text)

    def update_help_hints(self, hints: str) -> None:
        """Update the help hints display.

        Args:
            hints: Help text to display
        """
        self.help_text = hints

        # Try to update UI if mounted
        with contextlib.suppress(Exception):
            self.query_one("#help-hints", Label).update(self.help_text)

    def update_location(self, location: str) -> None:
        """Update the location/breadcrumb display.

        Args:
            location: Current location text
        """
        self.location_text = location

        # Try to update UI if mounted
        with contextlib.suppress(Exception):
            self.query_one("#location", Label).update(self.location_text)


class ToastNotification(Static):
    """Toast notification widget for temporary messages.

    Shows brief notifications that auto-dismiss after a timeout.
    Supports different types (success, error, info, warning).
    """

    def __init__(self, message: str, toast_type: str = "info", duration: float = 3.0):
        """Initialize the toast notification.

        Args:
            message: The message to display
            toast_type: Type of notification (success, error, info, warning)
            duration: How long to show the toast in seconds
        """
        super().__init__(message)
        self.message = message
        self.toast_type = toast_type
        self.duration = duration
        self._timer: Timer | None = None

        # Add appropriate class for styling
        self.add_class("toast", toast_type)

    def on_mount(self) -> None:
        """Set up auto-dismiss timer when mounted."""
        if self.duration > 0:
            self._timer = self.set_timer(self.duration, self.dismiss)

    def dismiss(self) -> None:
        """Dismiss the toast notification."""
        if self._timer:
            self._timer.stop()
        self.display = False

        # Only remove if mounted in an app
        with contextlib.suppress(Exception):
            self.remove()

    def set_timer(self, duration: float, callback: Callable) -> Timer:
        """Set a timer for auto-dismiss.

        Args:
            duration: Duration in seconds
            callback: Function to call when timer expires

        Returns:
            The created timer
        """
        return self.app.set_timer(duration, callback)


class ConfirmDialog(Container):
    """Confirmation dialog for dangerous or important actions.

    Provides a modal dialog with customizable message and button labels.
    Supports marking actions as dangerous for special styling.
    """

    def __init__(
        self,
        message: str,
        confirm_label: str = "Confirm",
        cancel_label: str = "Cancel",
        dangerous: bool = False,
        on_confirm: Callable | None = None,
        on_cancel: Callable | None = None,
    ):
        """Initialize the confirmation dialog.

        Args:
            message: The confirmation message to display
            confirm_label: Label for the confirm button
            cancel_label: Label for the cancel button
            dangerous: Whether this is a dangerous action (adds special styling)
            on_confirm: Callback when confirmed
            on_cancel: Callback when cancelled
        """
        super().__init__()
        self.message = message
        self.dangerous = dangerous
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel

        # Create buttons
        self.confirm_button = Button(confirm_label, id="confirm-btn")
        self.cancel_button = Button(cancel_label, id="cancel-btn")

        if dangerous:
            self.confirm_button.add_class("dangerous")

        self.add_class("confirm-dialog")

    def compose(self) -> ComposeResult:
        """Compose the dialog layout."""
        with Vertical(id="dialog-content"):
            yield Label(self.message, id="dialog-message")
            with Horizontal(id="dialog-buttons"):
                yield self.cancel_button
                yield self.confirm_button

    @on(Button.Pressed, "#confirm-btn")
    def handle_confirm(self) -> None:
        """Handle confirm button press."""
        if self.on_confirm:
            self.on_confirm()
        self.dismiss()

    @on(Button.Pressed, "#cancel-btn")
    def handle_cancel(self) -> None:
        """Handle cancel button press."""
        if self.on_cancel:
            self.on_cancel()
        self.dismiss()

    async def on_key(self, event: events.Key) -> None:
        """Handle Y/N key presses for quick confirmation."""
        if event.key in ["y", "Y"]:
            logger.info("Y key pressed - confirming")
            self.handle_confirm()
        elif event.key in ["n", "N"]:
            logger.info("N key pressed - cancelling")
            self.handle_cancel()
        elif event.key == "escape":
            logger.info("ESC key pressed - cancelling")
            self.handle_cancel()
        else:
            # Let other keys be handled normally
            await super().on_key(event)

    def dismiss(self) -> None:
        """Dismiss the dialog."""
        self.display = False

        # Only remove if mounted in an app
        with contextlib.suppress(Exception):
            self.remove()

    @property
    def label(self) -> str:
        """Get button label for compatibility."""
        return self.confirm_button.label
