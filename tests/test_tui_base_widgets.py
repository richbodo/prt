"""Test base widgets for the Textual TUI.

Lightweight TDD approach - start with basic tests, then expand.
"""

from textual.widgets import Static

# These imports will fail initially - that's expected in TDD
from prt_src.tui.app import AppMode
from prt_src.tui.widgets.base import (
    ConfirmDialog,
    ModeAwareWidget,
    StatusBar,
    ToastNotification,
)


class TestModeAwareWidget:
    """Test the base ModeAwareWidget class."""

    def test_mode_aware_widget_creation(self):
        """Test that ModeAwareWidget can be created."""
        widget = ModeAwareWidget()
        assert widget is not None
        assert hasattr(widget, "mode")

    def test_mode_aware_widget_inherits_from_static(self):
        """Test that ModeAwareWidget inherits from Static."""
        widget = ModeAwareWidget()
        assert isinstance(widget, Static)

    def test_mode_switching_changes_appearance(self):
        """Test that mode switching changes widget appearance."""
        widget = ModeAwareWidget()

        # Set to navigation mode
        widget.set_mode(AppMode.NAVIGATION)
        assert widget.mode == AppMode.NAVIGATION
        assert "navigation" in widget.classes

        # Switch to edit mode
        widget.set_mode(AppMode.EDIT)
        assert widget.mode == AppMode.EDIT
        assert "edit" in widget.classes

    def test_handles_escape_key(self):
        """Test that widget handles ESC key for mode switching."""
        widget = ModeAwareWidget()

        # Mock the mode toggle callback
        toggle_called = False

        def toggle_callback():
            nonlocal toggle_called
            toggle_called = True

        widget.on_mode_toggle = toggle_callback

        # Simulate ESC key press
        widget.handle_key("escape")
        assert toggle_called


class TestStatusBar:
    """Test the StatusBar widget."""

    def test_status_bar_creation(self):
        """Test that StatusBar can be created."""
        status_bar = StatusBar()
        assert status_bar is not None
        assert isinstance(status_bar, ModeAwareWidget)

    def test_status_bar_shows_mode(self):
        """Test that StatusBar displays current mode."""
        status_bar = StatusBar()

        # Set to navigation mode
        status_bar.set_mode(AppMode.NAVIGATION)
        assert "NAV" in status_bar.mode_text

        # Set to edit mode
        status_bar.set_mode(AppMode.EDIT)
        assert "EDIT" in status_bar.mode_text

    def test_status_bar_shows_selection_count(self):
        """Test that StatusBar displays selection count."""
        status_bar = StatusBar()

        # No selection
        status_bar.update_selection_count(0)
        assert status_bar.selection_text == ""

        # Single selection
        status_bar.update_selection_count(1)
        assert "1 selected" in status_bar.selection_text

        # Multiple selections
        status_bar.update_selection_count(5)
        assert "5 selected" in status_bar.selection_text

    def test_status_bar_shows_help_hints(self):
        """Test that StatusBar displays context-sensitive help."""
        status_bar = StatusBar()

        # Navigation mode hints
        status_bar.set_mode(AppMode.NAVIGATION)
        status_bar.update_help_hints("j/k: navigate | Enter: select")
        assert "j/k: navigate" in status_bar.help_text

        # Edit mode hints
        status_bar.set_mode(AppMode.EDIT)
        status_bar.update_help_hints("Type to edit | ESC: exit")
        assert "Type to edit" in status_bar.help_text

    def test_status_bar_shows_location(self):
        """Test that StatusBar displays current location."""
        status_bar = StatusBar()

        status_bar.update_location("Home > Contacts")
        assert "Home > Contacts" in status_bar.location_text


class TestToastNotification:
    """Test the ToastNotification widget."""

    def test_toast_creation(self):
        """Test that ToastNotification can be created."""
        toast = ToastNotification("Test message")
        assert toast is not None
        assert toast.message == "Test message"

    def test_toast_types(self):
        """Test different toast notification types."""
        # Success toast
        toast = ToastNotification("Success!", toast_type="success")
        assert toast.toast_type == "success"
        assert "success" in toast.classes

        # Error toast
        toast = ToastNotification("Error!", toast_type="error")
        assert toast.toast_type == "error"
        assert "error" in toast.classes

        # Info toast (default)
        toast = ToastNotification("Info")
        assert toast.toast_type == "info"
        assert "info" in toast.classes

    def test_toast_auto_dismiss(self):
        """Test that toast auto-dismisses after timeout."""
        toast = ToastNotification("Test", duration=2.0)
        assert toast.duration == 2.0
        assert hasattr(toast, "set_timer")

    def test_toast_manual_dismiss(self):
        """Test that toast can be manually dismissed."""
        toast = ToastNotification("Test")
        assert hasattr(toast, "dismiss")

        # Should remove itself when dismissed
        toast.dismiss()
        assert toast.display is False


class TestConfirmDialog:
    """Test the ConfirmDialog widget."""

    def test_confirm_dialog_creation(self):
        """Test that ConfirmDialog can be created."""
        dialog = ConfirmDialog("Are you sure?")
        assert dialog is not None
        assert dialog.message == "Are you sure?"

    def test_confirm_dialog_buttons(self):
        """Test that ConfirmDialog has confirm and cancel buttons."""
        dialog = ConfirmDialog("Delete item?")

        assert hasattr(dialog, "confirm_button")
        assert hasattr(dialog, "cancel_button")
        assert dialog.confirm_button.label == "Confirm"
        assert dialog.cancel_button.label == "Cancel"

    def test_confirm_dialog_custom_labels(self):
        """Test that ConfirmDialog accepts custom button labels."""
        dialog = ConfirmDialog("Delete item?", confirm_label="Delete", cancel_label="Keep")

        assert dialog.confirm_button.label == "Delete"
        assert dialog.cancel_button.label == "Keep"

    def test_confirm_dialog_callbacks(self):
        """Test that ConfirmDialog handles callbacks correctly."""
        confirm_called = False
        cancel_called = False

        def on_confirm():
            nonlocal confirm_called
            confirm_called = True

        def on_cancel():
            nonlocal cancel_called
            cancel_called = True

        dialog = ConfirmDialog("Test?", on_confirm=on_confirm, on_cancel=on_cancel)

        # Simulate confirm button press
        dialog.handle_confirm()
        assert confirm_called
        assert not cancel_called

        # Reset and simulate cancel
        confirm_called = False
        dialog.handle_cancel()
        assert not confirm_called
        assert cancel_called

    def test_confirm_dialog_dangerous_action_styling(self):
        """Test that dangerous actions get special styling."""
        dialog = ConfirmDialog("Delete all data?", dangerous=True)

        assert dialog.dangerous
        assert "dangerous" in dialog.confirm_button.classes
