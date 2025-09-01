"""Contact form screen for PRT TUI.

Provides add/edit functionality for contacts with validation.
Includes fields for basic contact info, tag selection, and notes.
"""

from typing import Dict, List, Optional, Set

from textual import events
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Checkbox, Input, LoadingIndicator, Static, TextArea

from prt_src.core.components.validation import ValidationSystem
from prt_src.logging_config import get_logger
from prt_src.tui.screens import register_screen
from prt_src.tui.screens.base import BaseScreen, EscapeIntent

logger = get_logger(__name__)


class ContactFormScreen(BaseScreen):
    """Contact form screen for adding/editing contacts."""

    def __init__(self, mode: str = "add", contact_id: int = None, *args, **kwargs):
        """Initialize contact form screen.

        Args:
            mode: Either "add" or "edit"
            contact_id: ID of contact to edit (required for edit mode)
        """
        super().__init__(*args, **kwargs)
        self.mode = mode
        self.contact_id = contact_id
        self.contact_data: Optional[Dict] = None
        self.available_tags: List[Dict] = []
        self.selected_tags: Set[str] = set()
        self.validation_system = ValidationSystem()

        # Form fields
        self.first_name_input: Optional[Input] = None
        self.last_name_input: Optional[Input] = None
        self.email_input: Optional[Input] = None
        self.phone_input: Optional[Input] = None
        self.notes_textarea: Optional[TextArea] = None

        # Form controls
        self.loading_indicator: Optional[LoadingIndicator] = None
        self.save_button: Optional[Button] = None
        self.cancel_button: Optional[Button] = None
        self.validation_message: Optional[Static] = None

        # Tag checkboxes (will be populated dynamically)
        self.tag_checkboxes: Dict[str, Checkbox] = {}
        self.tags_container: Optional[Vertical] = None

    def get_screen_name(self) -> str:
        """Get screen identifier."""
        return "contact_form"

    def on_escape(self) -> EscapeIntent:
        """ESC confirms unsaved changes or goes back."""
        if self.has_unsaved_changes():
            return EscapeIntent.CONFIRM
        return EscapeIntent.POP

    def get_header_config(self) -> dict:
        """Configure header."""
        config = super().get_header_config()
        if config:
            title = "Add Contact" if self.mode == "add" else "Edit Contact"
            config["title"] = title
        return config

    def get_footer_config(self) -> dict:
        """Configure footer with action hints."""
        config = super().get_footer_config()
        if config:
            config["keyHints"] = [
                "[Ctrl+S] Save",
                "[Ctrl+C] Cancel",
                "[Tab] Next field",
                "[ESC] Back",
            ]
        return config

    def compose(self) -> ComposeResult:
        """Compose contact form screen layout."""
        with Vertical(classes="contact-form"):
            # Loading indicator (initially hidden)
            self.loading_indicator = LoadingIndicator()
            yield self.loading_indicator

            # Form header with action buttons
            with Horizontal(id="form-actions"):
                self.save_button = Button("Save", variant="primary", classes="action-button")
                self.cancel_button = Button("Cancel", variant="default", classes="action-button")
                yield self.save_button
                yield self.cancel_button

            # Validation message area
            self.validation_message = Static("", id="validation-message", classes="error-message")
            yield self.validation_message

            # Contact information fields
            with Vertical(id="contact-fields-section"):
                yield Static("Contact Information", classes="section-title")

                with Vertical(classes="field-container"):
                    yield Static("First Name:", classes="field-label")
                    self.first_name_input = Input(
                        placeholder="Enter first name", classes="field-input"
                    )
                    yield self.first_name_input

                with Vertical(classes="field-container"):
                    yield Static("Last Name:", classes="field-label")
                    self.last_name_input = Input(
                        placeholder="Enter last name", classes="field-input"
                    )
                    yield self.last_name_input

                with Vertical(classes="field-container"):
                    yield Static("Email:", classes="field-label")
                    self.email_input = Input(
                        placeholder="Enter email address", classes="field-input"
                    )
                    yield self.email_input

                with Vertical(classes="field-container"):
                    yield Static("Phone:", classes="field-label")
                    self.phone_input = Input(
                        placeholder="Enter phone number", classes="field-input"
                    )
                    yield self.phone_input

            # Tags section
            with Vertical(id="tags-section"):
                yield Static("Tags", classes="section-title")
                self.tags_container = Vertical(id="tags-container")
                yield self.tags_container

            # Notes section
            with Vertical(id="notes-section"):
                yield Static("Notes", classes="section-title")
                self.notes_textarea = TextArea(
                    text="", show_line_numbers=False, classes="field-input"
                )
                yield self.notes_textarea

    async def on_mount(self) -> None:
        """Load data when screen is mounted."""
        await super().on_mount()
        await self._load_form_data()

    async def on_show(self) -> None:
        """Refresh data when screen becomes visible."""
        await super().on_show()
        # Focus the first input field
        if self.first_name_input:
            self.first_name_input.focus()

    async def _load_form_data(self) -> None:
        """Load form data including contact data (if editing) and available tags."""
        if not self.data_service:
            logger.warning("No data service available")
            return

        try:
            # Show loading indicator
            if self.loading_indicator:
                self.loading_indicator.display = True

            # Load available tags
            self.available_tags = await self.data_service.get_tags()
            await self._setup_tag_checkboxes()

            # Load contact data if editing
            if self.mode == "edit" and self.contact_id:
                self.contact_data = await self.data_service.get_contact(self.contact_id)

                if self.contact_data:
                    await self._populate_form_fields()
                else:
                    logger.error(f"Contact {self.contact_id} not found for editing")
                    if self.notification_service:
                        self.notification_service.show_error("Contact not found")

            logger.info(f"Loaded form data for {self.mode} mode")

        except Exception as e:
            logger.error(f"Failed to load form data: {e}")
            if self.notification_service:
                self.notification_service.show_error(f"Failed to load form: {e}")
        finally:
            # Hide loading indicator
            if self.loading_indicator:
                self.loading_indicator.display = False

    async def _setup_tag_checkboxes(self) -> None:
        """Create checkboxes for available tags."""
        if not self.tags_container:
            return

        # Clear existing checkboxes
        self.tag_checkboxes.clear()
        await self.tags_container.remove_children()

        # Create checkbox for each available tag
        for tag in self.available_tags:
            tag_name = tag.get("name", "")
            if tag_name:
                checkbox = Checkbox(tag_name, classes="tag-checkbox")
                self.tag_checkboxes[tag_name] = checkbox
                await self.tags_container.mount(checkbox)

    async def _populate_form_fields(self) -> None:
        """Populate form fields with existing contact data."""
        if not self.contact_data:
            return

        # Populate basic fields
        if self.first_name_input:
            first_name = self.contact_data.get("first_name", "")
            self.first_name_input.value = first_name

        if self.last_name_input:
            last_name = self.contact_data.get("last_name", "")
            self.last_name_input.value = last_name

        if self.email_input:
            email = self.contact_data.get("email", "") or ""
            self.email_input.value = email

        if self.phone_input:
            phone = self.contact_data.get("phone", "") or ""
            self.phone_input.value = phone

        # TODO: Load and populate tags for this contact
        # For now, we'll leave tag selection empty

        # TODO: Load and populate notes for this contact
        # For now, we'll leave notes empty

        # Clear unsaved changes flag since we just loaded data
        self.clear_unsaved()

    def has_unsaved_changes(self) -> bool:
        """Check if form has unsaved changes."""
        # If we're in add mode and any field has content, consider it unsaved
        if self.mode == "add":
            return (
                (self.first_name_input and self.first_name_input.value.strip())
                or (self.last_name_input and self.last_name_input.value.strip())
                or (self.email_input and self.email_input.value.strip())
                or (self.phone_input and self.phone_input.value.strip())
                or (self.notes_textarea and self.notes_textarea.text.strip())
                or bool(self.selected_tags)
            )

        # If we're in edit mode, check if values differ from original
        if self.mode == "edit" and self.contact_data:
            return (
                (
                    self.first_name_input
                    and self.first_name_input.value.strip()
                    != (self.contact_data.get("first_name") or "").strip()
                )
                or (
                    self.last_name_input
                    and self.last_name_input.value.strip()
                    != (self.contact_data.get("last_name") or "").strip()
                )
                or (
                    self.email_input
                    and self.email_input.value.strip()
                    != (self.contact_data.get("email") or "").strip()
                )
                or (
                    self.phone_input
                    and self.phone_input.value.strip()
                    != (self.contact_data.get("phone") or "").strip()
                )
                # TODO: Add tag and note comparison
            )

        return super().has_unsaved_changes()

    async def on_input_changed(self, event: Input.Changed) -> None:
        """Mark form as having unsaved changes when input changes."""
        self.mark_unsaved()
        # Clear validation message when user starts typing
        if self.validation_message:
            self.validation_message.update("")

    async def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """Mark form as having unsaved changes when textarea changes."""
        self.mark_unsaved()

    async def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle tag checkbox changes."""
        checkbox = event.checkbox
        tag_name = checkbox.label

        if checkbox.value:
            self.selected_tags.add(tag_name)
        else:
            self.selected_tags.discard(tag_name)

        self.mark_unsaved()

    async def on_key(self, event: events.Key) -> None:
        """Handle key events for contact form screen."""
        key = event.key

        if event.ctrl and key == "s":
            # Save contact
            await self._handle_save()
        elif event.ctrl and key == "c":
            # Cancel
            await self._handle_cancel()
        else:
            # Let parent handle other keys
            await super().on_key(event)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button == self.save_button:
            await self._handle_save()
        elif event.button == self.cancel_button:
            await self._handle_cancel()

    async def _handle_save(self) -> None:
        """Handle save contact action."""
        logger.info(f"Save contact requested in {self.mode} mode")

        # Collect form data
        form_data = self._collect_form_data()

        # Validate form data
        validation_result = self.validation_system.validate_entity(
            "contact", form_data, sanitize=True
        )

        if not validation_result.is_valid:
            # Show validation errors
            error_message = "Validation errors:\n" + "\n".join(validation_result.errors)
            if self.validation_message:
                self.validation_message.update(error_message)
            if self.notification_service:
                self.notification_service.show_error("Please fix validation errors")
            return

        # Clear validation message
        if self.validation_message:
            self.validation_message.update("")

        # Use sanitized data if available
        save_data = validation_result.sanitized_data or form_data

        try:
            if self.mode == "add":
                # Create new contact
                created_contact = await self.data_service.create_contact(save_data)
                if created_contact:
                    contact_id = created_contact.get("id")

                    # Apply tags to the new contact
                    await self._apply_tags_to_contact(contact_id)

                    # TODO: Save notes for the contact

                    self.clear_unsaved()
                    if self.notification_service:
                        name = f"{save_data.get('first_name', '')} {save_data.get('last_name', '')}".strip()
                        self.notification_service.show_success(f"Created contact: {name}")

                    # Navigate back to contacts list
                    await self._navigate_back()
                else:
                    if self.notification_service:
                        self.notification_service.show_error("Failed to create contact")

            elif self.mode == "edit":
                # Update existing contact
                success = await self.data_service.update_contact(self.contact_id, save_data)
                if success:
                    # Apply tags to the contact
                    await self._apply_tags_to_contact(self.contact_id)

                    # TODO: Update notes for the contact

                    self.clear_unsaved()
                    if self.notification_service:
                        name = f"{save_data.get('first_name', '')} {save_data.get('last_name', '')}".strip()
                        self.notification_service.show_success(f"Updated contact: {name}")

                    # Navigate back to contact detail or contacts list
                    await self._navigate_back()
                else:
                    if self.notification_service:
                        self.notification_service.show_error("Failed to update contact")

        except Exception as e:
            logger.error(f"Failed to save contact: {e}")
            if self.notification_service:
                self.notification_service.show_error(f"Failed to save contact: {e}")

    def _collect_form_data(self) -> Dict:
        """Collect data from form fields."""
        data = {}

        if self.first_name_input:
            data["first_name"] = self.first_name_input.value.strip()

        if self.last_name_input:
            data["last_name"] = self.last_name_input.value.strip()

        if self.email_input:
            email = self.email_input.value.strip()
            if email:
                data["email"] = email

        if self.phone_input:
            phone = self.phone_input.value.strip()
            if phone:
                data["phone"] = phone

        # Ensure we have a name field (required by validation)
        first_name = data.get("first_name", "")
        last_name = data.get("last_name", "")
        if first_name or last_name:
            data["name"] = f"{first_name} {last_name}".strip()

        return data

    async def _apply_tags_to_contact(self, contact_id: int) -> None:
        """Apply selected tags to the contact."""
        if not contact_id or not self.data_service:
            return

        try:
            # TODO: This is a simplified implementation
            # In a full implementation, we would:
            # 1. Get current contact tags
            # 2. Remove tags that are no longer selected
            # 3. Add new tags that are selected

            for tag_name in self.selected_tags:
                await self.data_service.add_tag_to_contact(contact_id, tag_name)

        except Exception as e:
            logger.error(f"Failed to apply tags to contact {contact_id}: {e}")

    async def _handle_cancel(self) -> None:
        """Handle cancel action."""
        logger.info("Cancel contact form requested")

        if self.has_unsaved_changes():
            # Show confirmation dialog for unsaved changes
            if self.notification_service:
                try:
                    confirmed = await self.notification_service.show_confirm_dialog(
                        "Discard Changes?",
                        "You have unsaved changes. Are you sure you want to discard them?",
                    )
                    if not confirmed:
                        return  # User chose to stay and continue editing
                except Exception as e:
                    logger.error(f"Failed to show confirmation dialog: {e}")

        # Navigate back
        await self._navigate_back()

    async def _navigate_back(self) -> None:
        """Navigate back to the appropriate screen."""
        if self.nav_service:
            try:
                if self.mode == "edit":
                    # Go back to contact detail screen
                    self.nav_service.pop()  # Remove current form screen
                    if hasattr(self.app, "switch_screen"):
                        await self.app.switch_screen("contact_detail")
                else:
                    # Go back to contacts list
                    self.nav_service.pop()
                    if hasattr(self.app, "switch_screen"):
                        await self.app.switch_screen("contacts")
            except Exception as e:
                logger.error(f"Failed to navigate back: {e}")
                if self.notification_service:
                    self.notification_service.show_error("Failed to navigate back")


# Register this screen
register_screen("contact_form", ContactFormScreen)
