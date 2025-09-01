"""Contact Detail View for the PRT Textual TUI.

Displays and allows editing of contact information with
field-level editing and validation support.
"""

from typing import Callable, Dict, Optional

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Button, Input, Label, Static, TextArea

from prt_src.tui.types import AppMode
from prt_src.tui.widgets.base import ModeAwareWidget


class FieldEditor(Static):
    """An editable field in the contact detail view."""

    def __init__(self, field_name: str, value: str = "", label: str = None):
        """Initialize the field editor.

        Args:
            field_name: Name of the field
            value: Initial value
            label: Display label (defaults to field_name)
        """
        super().__init__()
        self.field_name = field_name
        self.value = value
        self.original_value = value
        self.label = label or field_name.replace("_", " ").title()
        self.is_editable = False
        self.has_changed = False
        self.validator: Optional[Callable] = None
        self.add_class("field-editor")

    @property
    def display_value(self) -> str:
        """Get the display value for the field."""
        return self.value if self.value else "(empty)"

    def compose(self) -> ComposeResult:
        """Compose the field editor layout."""
        with Vertical(classes="field-container"):
            yield Label(self.label, classes="field-label")
            if self.is_editable:
                if self.field_name == "notes":
                    yield TextArea(self.value, id=f"input-{self.field_name}", classes="field-input")
                else:
                    yield Input(self.value, id=f"input-{self.field_name}", classes="field-input")
            else:
                yield Static(self.display_value, classes="field-value")

    def set_editable(self, editable: bool) -> None:
        """Set whether the field is editable.

        Args:
            editable: Whether the field should be editable
        """
        self.is_editable = editable
        self.refresh()

    def set_value(self, value: str) -> None:
        """Set the field value.

        Args:
            value: New value for the field
        """
        self.value = value
        self.has_changed = value != self.original_value
        if self.is_editable:
            try:
                if self.field_name == "notes":
                    self.query_one(f"#input-{self.field_name}", TextArea).load_text(value)
                else:
                    self.query_one(f"#input-{self.field_name}", Input).value = value
            except Exception:
                pass

    def set_validator(self, validator: Callable) -> None:
        """Set a validation function for the field.

        Args:
            validator: Function that takes a value and returns True if valid
        """
        self.validator = validator

    def is_valid(self) -> bool:
        """Check if the current value is valid.

        Returns:
            True if valid or no validator set
        """
        if not self.validator:
            return True
        return self.validator(self.value)

    def reset(self) -> None:
        """Reset the field to its original value."""
        self.set_value(self.original_value)
        self.has_changed = False


class ContactDetailView(ModeAwareWidget):
    """Detailed view and editor for a single contact."""

    is_editing = reactive(False)

    def __init__(self, on_save: Optional[Callable] = None):
        """Initialize the contact detail view.

        Args:
            on_save: Callback when contact is saved
        """
        super().__init__()
        self.contact: Optional[Dict] = None
        self.field_editors: Dict[str, FieldEditor] = {}
        self.has_unsaved_changes = False
        self.on_save = on_save
        self.selected_field: Optional[str] = None
        self.add_class("contact-detail")

    def compose(self) -> ComposeResult:
        """Compose the contact detail layout."""
        with Vertical(id="detail-container"):
            # Header with title and actions
            with Horizontal(id="detail-header"):
                yield Label("Contact Details", classes="detail-title")
                with Horizontal(id="detail-actions"):
                    yield Button("Edit", id="edit-btn", classes="action-button")
                    yield Button("Save", id="save-btn", classes="action-button", disabled=True)
                    yield Button("Cancel", id="cancel-btn", classes="action-button", disabled=True)

            # Fields container
            yield Vertical(id="fields-container")

    def load_contact(self, contact: Dict) -> None:
        """Load a contact for display/editing.

        Args:
            contact: Contact dictionary to display
        """
        self.contact = contact.copy()
        self.field_editors.clear()
        self.has_unsaved_changes = False

        # Create field editors for standard fields
        fields = [
            ("name", "Name"),
            ("email", "Email"),
            ("phone", "Phone"),
            ("address", "Address"),
            ("notes", "Notes"),
        ]

        for field_name, label in fields:
            value = contact.get(field_name, "")
            editor = FieldEditor(field_name, str(value) if value else "", label)
            self.field_editors[field_name] = editor

            # Set email validator
            if field_name == "email":
                editor.set_validator(lambda v, fn=field_name: not v or "@" in v)

        # Try to mount in UI if widget is mounted
        try:
            container = self.query_one("#fields-container", Vertical)
            container.remove_children()

            for editor in self.field_editors.values():
                container.mount(editor)

        except Exception:
            # Widget not mounted yet, that's ok
            pass

    def get_field_value(self, field_name: str) -> str:
        """Get the current value of a field.

        Args:
            field_name: Name of the field

        Returns:
            Current value of the field
        """
        if field_name in self.field_editors:
            return self.field_editors[field_name].value
        return ""

    def update_field(self, field_name: str, value: str) -> None:
        """Update a field value.

        Args:
            field_name: Name of the field to update
            value: New value
        """
        if field_name in self.field_editors:
            self.field_editors[field_name].set_value(value)
            self.has_unsaved_changes = True
            self._update_buttons()

    def select_field(self, field_name: str) -> None:
        """Select a field for editing.

        Args:
            field_name: Name of the field to select
        """
        self.selected_field = field_name
        if field_name in self.field_editors:
            try:
                self.field_editors[field_name].focus()
            except Exception:
                # Not in app context
                pass

    def set_mode(self, mode: AppMode) -> None:
        """Set the mode and update editing state.

        Args:
            mode: The new application mode
        """
        super().set_mode(mode)
        self.is_editing = mode == AppMode.EDIT

        # Update all field editors
        for editor in self.field_editors.values():
            editor.set_editable(self.is_editing)

        self._update_buttons()

    def save_changes(self) -> None:
        """Save changes to the contact."""
        if not self.has_unsaved_changes:
            return

        # Validate all fields
        for editor in self.field_editors.values():
            if not editor.is_valid():
                return

        # Update contact with new values
        for field_name, editor in self.field_editors.items():
            if editor.has_changed:
                self.contact[field_name] = editor.value
                editor.original_value = editor.value
                editor.has_changed = False

        self.has_unsaved_changes = False
        self.set_mode(AppMode.NAVIGATION)

        # Call save callback
        if self.on_save:
            self.on_save(self.contact)

    def cancel_editing(self) -> None:
        """Cancel editing and revert changes."""
        for editor in self.field_editors.values():
            editor.reset()

        self.has_unsaved_changes = False
        self.set_mode(AppMode.NAVIGATION)

    def _update_buttons(self) -> None:
        """Update button states based on editing mode."""
        try:
            edit_btn = self.query_one("#edit-btn", Button)
            save_btn = self.query_one("#save-btn", Button)
            cancel_btn = self.query_one("#cancel-btn", Button)

            edit_btn.disabled = self.is_editing
            save_btn.disabled = not self.is_editing or not self.has_unsaved_changes
            cancel_btn.disabled = not self.is_editing
        except Exception:
            pass
