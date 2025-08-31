"""Integration tests for TUI widgets.

Tests widget interaction and composition.
"""

from unittest.mock import patch

from prt_src.tui.app import AppMode, PRTApp
from prt_src.tui.widgets.base import (
    ConfirmDialog,
    ModeAwareWidget,
    StatusBar,
    ToastNotification,
)


class TestStatusBarIntegration:
    """Test StatusBar integration."""

    def test_status_bar_with_prt_app(self):
        """Test StatusBar integration with PRTApp."""
        with patch("prt_src.tui.app.load_config") as mock_config:
            mock_config.return_value = {"db_path": ":memory:"}

            app = PRTApp()

            # Create a status bar
            status_bar = StatusBar()

            # Test mode synchronization
            status_bar.set_mode(app.current_mode)
            assert status_bar.mode_text == app.current_mode.value

    def test_status_bar_state_management(self):
        """Test StatusBar manages multiple states correctly."""
        status_bar = StatusBar()

        # Set all states
        status_bar.set_mode(AppMode.EDIT)
        status_bar.update_selection_count(5)
        status_bar.update_help_hints("Press ESC to exit")
        status_bar.update_location("Home > Contacts > Edit")

        # Verify all states are maintained
        assert status_bar.mode_text == "EDIT"
        assert status_bar.selection_text == "5 selected"
        assert status_bar.help_text == "Press ESC to exit"
        assert status_bar.location_text == "Home > Contacts > Edit"


class TestToastNotificationIntegration:
    """Test ToastNotification integration."""

    def test_toast_types(self):
        """Test different toast types."""
        # Success toast
        toast_success = ToastNotification("Success!", toast_type="success")
        assert toast_success.message == "Success!"
        assert toast_success.toast_type == "success"
        assert "success" in toast_success.classes

        # Error toast
        toast_error = ToastNotification("Error!", toast_type="error")
        assert toast_error.toast_type == "error"
        assert "error" in toast_error.classes

        # Warning toast
        toast_warning = ToastNotification("Warning!", toast_type="warning")
        assert toast_warning.toast_type == "warning"
        assert "warning" in toast_warning.classes

    def test_toast_dismiss_behavior(self):
        """Test toast dismiss behavior."""
        toast = ToastNotification("Test", duration=2.0)

        # Initially visible
        assert toast.display is not False

        # Manual dismiss
        toast.dismiss()
        assert toast.display is False


class TestConfirmDialogIntegration:
    """Test ConfirmDialog integration."""

    def test_confirm_dialog_callbacks(self):
        """Test dialog callbacks are stored correctly."""
        confirm_called = False
        cancel_called = False

        def on_confirm():
            nonlocal confirm_called
            confirm_called = True

        def on_cancel():
            nonlocal cancel_called
            cancel_called = True

        dialog = ConfirmDialog("Test?", on_confirm=on_confirm, on_cancel=on_cancel)

        # Check callbacks are stored
        assert dialog.on_confirm is on_confirm
        assert dialog.on_cancel is on_cancel

        # Test confirm handling
        if dialog.on_confirm:
            dialog.on_confirm()
        assert confirm_called

        # Test cancel handling
        if dialog.on_cancel:
            dialog.on_cancel()
        assert cancel_called

    def test_dangerous_dialog_configuration(self):
        """Test dangerous dialog configuration."""
        dialog = ConfirmDialog(
            "Delete all data?", confirm_label="DELETE", cancel_label="Keep", dangerous=True
        )

        # Check properties
        assert dialog.message == "Delete all data?"
        assert dialog.dangerous is True
        assert dialog.confirm_button.label == "DELETE"
        assert dialog.cancel_button.label == "Keep"
        assert "dangerous" in dialog.confirm_button.classes


class TestWidgetModeAwareness:
    """Test mode awareness across widgets."""

    def test_mode_aware_widget_inheritance(self):
        """Test widgets properly inherit from ModeAwareWidget."""
        # StatusBar should inherit mode awareness
        status_bar = StatusBar()
        assert isinstance(status_bar, ModeAwareWidget)
        assert hasattr(status_bar, "mode")
        assert hasattr(status_bar, "set_mode")

        # Test mode changes
        status_bar.set_mode(AppMode.EDIT)
        assert status_bar.mode == AppMode.EDIT
        assert "edit" in status_bar.classes

    def test_multiple_widgets_mode_coordination(self):
        """Test multiple widgets can coordinate modes."""
        widgets = [StatusBar(), ModeAwareWidget(), ModeAwareWidget()]

        # Set all to edit mode
        for widget in widgets:
            widget.set_mode(AppMode.EDIT)

        # Verify all are in edit mode
        for widget in widgets:
            assert widget.mode == AppMode.EDIT
            assert "edit" in widget.classes

        # Switch all to navigation
        for widget in widgets:
            widget.set_mode(AppMode.NAVIGATION)

        # Verify all switched
        for widget in widgets:
            assert widget.mode == AppMode.NAVIGATION
            assert "navigation" in widget.classes
