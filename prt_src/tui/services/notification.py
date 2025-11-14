"""Notification service for PRT TUI.

Provides toast notifications and dialog management.
"""

import contextlib
from enum import Enum
from typing import Optional

from textual.app import App
from textual.timer import Timer

from prt_src.logging_config import get_logger
from prt_src.tui.widgets.base import ConfirmDialog
from prt_src.tui.widgets.base import ToastNotification

logger = get_logger(__name__)


class NotificationType(Enum):
    """Notification types."""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class NotificationService:
    """Service for managing notifications and dialogs."""

    def __init__(self, app: Optional[App] = None):
        """Initialize notification service.

        Args:
            app: Textual app instance
        """
        self.app = app
        self._toast_timer: Optional[Timer] = None

    def set_app(self, app: App) -> None:
        """Set the app instance.

        Args:
            app: Textual app instance
        """
        self.app = app

    async def show_toast(
        self,
        message: str,
        type: NotificationType = NotificationType.INFO,
        duration: float = 3.0,
    ) -> None:
        """Show a toast notification.

        Args:
            message: Notification message
            type: Type of notification
            duration: How long to show (seconds)
        """
        if not self.app:
            logger.warning("No app instance - cannot show toast")
            return

        try:
            # Create toast widget
            toast = ToastNotification(message, type.value)

            # Mount it
            await self.app.mount(toast)

            # Schedule removal
            if self._toast_timer:
                self._toast_timer.stop()

            self._toast_timer = self.app.set_timer(duration, lambda: self._remove_toast(toast))

            logger.debug(f"Showing {type.value} toast: {message}")
        except Exception as e:
            logger.error(f"Failed to show toast: {e}")

    def _remove_toast(self, toast: ToastNotification) -> None:
        """Remove a toast notification.

        Args:
            toast: Toast widget to remove
        """
        with contextlib.suppress(Exception):
            toast.remove()  # Toast may already be removed

    def show_info(self, message: str) -> None:
        """Show info toast.

        Args:
            message: Info message
        """
        if self.app:
            self.app.call_later(self.show_toast, message, NotificationType.INFO)
        else:
            logger.warning(f"No app instance - cannot show info toast: {message}")

    def show_success(self, message: str) -> None:
        """Show success toast.

        Args:
            message: Success message
        """
        if self.app:
            self.app.call_later(self.show_toast, message, NotificationType.SUCCESS)
        else:
            logger.warning(f"No app instance - cannot show success toast: {message}")

    def show_warning(self, message: str) -> None:
        """Show warning toast.

        Args:
            message: Warning message
        """
        if self.app:
            self.app.call_later(self.show_toast, message, NotificationType.WARNING)
        else:
            logger.warning(f"No app instance - cannot show warning toast: {message}")

    def show_error(self, message: str) -> None:
        """Show error toast.

        Args:
            message: Error message
        """
        if self.app:
            self.app.call_later(self.show_toast, message, NotificationType.ERROR)
        else:
            logger.error(f"No app instance - cannot show error toast: {message}")

    async def show_confirm_dialog(
        self,
        title: str,
        message: str,
        confirm_text: str = "Confirm",
        cancel_text: str = "Cancel",
        dangerous: bool = False,
    ) -> bool:
        """Show a confirmation dialog.

        Args:
            title: Dialog title
            message: Confirmation message
            confirm_text: Text for confirm button
            cancel_text: Text for cancel button
            dangerous: Whether this is a dangerous operation

        Returns:
            True if user confirmed
        """
        if not self.app:
            logger.warning("No app instance - cannot show dialog")
            return False

        try:
            # Create dialog
            dialog = ConfirmDialog(
                title=title,
                message=message,
                confirm_text=confirm_text,
                cancel_text=cancel_text,
                dangerous=dangerous,
            )

            # Mount and wait for result
            await self.app.mount(dialog)
            result = await dialog.wait_for_result()

            # Remove dialog
            dialog.remove()

            return result
        except Exception as e:
            logger.error(f"Failed to show confirm dialog: {e}")
            return False

    async def show_discard_dialog(self) -> bool:
        """Show discard changes dialog.

        Returns:
            True if user wants to discard changes
        """
        return await self.show_confirm_dialog(
            title="Unsaved Changes",
            message="You have unsaved changes. Discard them?",
            confirm_text="Discard",
            cancel_text="Keep Editing",
            dangerous=True,
        )

    async def show_delete_dialog(self, item_name: str) -> bool:
        """Show delete confirmation dialog.

        Args:
            item_name: Name of item being deleted

        Returns:
            True if user confirms deletion
        """
        return await self.show_confirm_dialog(
            title="Confirm Delete",
            message=f"Are you sure you want to delete {item_name}?",
            confirm_text="Delete",
            cancel_text="Cancel",
            dangerous=True,
        )
