"""Relationship form screen for PRT TUI.

Provides add/edit functionality for relationships with validation,
contact selection, relationship type selection, and date fields.
"""

from datetime import datetime
from typing import Dict
from typing import List
from typing import Optional

from textual import events
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.containers import Vertical
from textual.widgets import Button
from textual.widgets import Input
from textual.widgets import LoadingIndicator
from textual.widgets import Select
from textual.widgets import Static

from prt_src.core.components.autocomplete import AutocompleteEngine
from prt_src.core.components.validation import ValidationSystem
from prt_src.logging_config import get_logger
from prt_src.tui.screens import register_screen
from prt_src.tui.screens.base import BaseScreen
from prt_src.tui.screens.base import EscapeIntent

logger = get_logger(__name__)


class RelationshipFormScreen(BaseScreen):
    """Relationship form screen for adding/editing relationships."""

    def __init__(self, mode: str = "add", relationship_id: int = None, *args, **kwargs):
        """Initialize relationship form screen.

        Args:
            mode: Either "add" or "edit"
            relationship_id: ID of relationship to edit (required for edit mode)
        """
        super().__init__(*args, **kwargs)
        self.mode = mode
        self.relationship_id = relationship_id
        self.relationship_data: Optional[Dict] = None
        self.available_contacts: List[Dict] = []
        self.available_relationship_types: List[Dict] = []
        self.validation_system = ValidationSystem()
        self.autocomplete_engine = AutocompleteEngine()

        # Form fields
        self.from_contact_select: Optional[Select] = None
        self.to_contact_select: Optional[Select] = None
        self.relationship_type_select: Optional[Select] = None
        self.start_date_input: Optional[Input] = None
        self.end_date_input: Optional[Input] = None

        # Form controls
        self.loading_indicator: Optional[LoadingIndicator] = None
        self.save_button: Optional[Button] = None
        self.cancel_button: Optional[Button] = None
        self.validation_message: Optional[Static] = None

    def get_screen_name(self) -> str:
        """Get screen identifier."""
        return "relationship_form"

    def on_escape(self) -> EscapeIntent:
        """ESC confirms unsaved changes or goes back."""
        if self.has_unsaved_changes():
            return EscapeIntent.CONFIRM
        return EscapeIntent.POP

    def get_header_config(self) -> dict:
        """Configure header."""
        config = super().get_header_config()
        if config:
            title = "Add Relationship" if self.mode == "add" else "Edit Relationship"
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
        """Compose relationship form screen layout."""
        with Vertical(classes="relationship-form"):
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

            # Contact selection section
            with Vertical(id="contact-selection-section"):
                yield Static("Contact Selection", classes="section-title")

                with Vertical(classes="field-container"):
                    yield Static("From Contact:", classes="field-label")
                    self.from_contact_select = Select(
                        options=[("Select from contact...", "")],
                        classes="field-input",
                        allow_blank=False,
                    )
                    yield self.from_contact_select

                with Vertical(classes="field-container"):
                    yield Static("To Contact:", classes="field-label")
                    self.to_contact_select = Select(
                        options=[("Select to contact...", "")],
                        classes="field-input",
                        allow_blank=False,
                    )
                    yield self.to_contact_select

            # Relationship type section
            with Vertical(id="relationship-type-section"):
                yield Static("Relationship Type", classes="section-title")

                with Vertical(classes="field-container"):
                    yield Static("Relationship Type:", classes="field-label")
                    self.relationship_type_select = Select(
                        options=[("Select relationship type...", "")],
                        classes="field-input",
                        allow_blank=False,
                    )
                    yield self.relationship_type_select

            # Date fields section
            with Vertical(id="dates-section"):
                yield Static("Dates (Optional)", classes="section-title")

                with Horizontal(classes="date-fields-container"):
                    with Vertical(classes="field-container"):
                        yield Static("Start Date (YYYY-MM-DD):", classes="field-label")
                        self.start_date_input = Input(
                            placeholder="Enter start date", classes="field-input date-input"
                        )
                        yield self.start_date_input

                    with Vertical(classes="field-container"):
                        yield Static("End Date (YYYY-MM-DD):", classes="field-label")
                        self.end_date_input = Input(
                            placeholder="Enter end date", classes="field-input date-input"
                        )
                        yield self.end_date_input

    async def on_mount(self) -> None:
        """Load data when screen is mounted."""
        await super().on_mount()
        await self._load_form_data()

    async def on_show(self) -> None:
        """Refresh data when screen becomes visible."""
        await super().on_show()
        # Focus the first select field
        if self.from_contact_select:
            self.from_contact_select.focus()

    async def _load_form_data(self) -> None:
        """Load form data including contacts, relationship types, and existing relationship data."""
        if not self.data_service:
            logger.warning("No data service available")
            return

        try:
            # Show loading indicator
            if self.loading_indicator:
                self.loading_indicator.display = True

            # Load available contacts
            self.available_contacts = await self.data_service.get_contacts(
                limit=1000
            )  # Get all contacts
            await self._setup_contact_selectors()

            # Load available relationship types
            self.available_relationship_types = await self.data_service.get_relationship_types()
            await self._setup_relationship_type_selector()

            # Load relationship data if editing
            if self.mode == "edit" and self.relationship_id:
                self.relationship_data = await self.data_service.get_relationship_details(
                    self.relationship_id
                )

                if self.relationship_data:
                    await self._populate_form_fields()
                else:
                    logger.error(f"Relationship {self.relationship_id} not found for editing")
                    if self.notification_service:
                        await self.notification_service.show_error("Relationship not found")

            logger.info(f"Loaded form data for {self.mode} mode")

        except Exception as e:
            logger.error(f"Failed to load form data: {e}")
            if self.notification_service:
                await self.notification_service.show_error(f"Failed to load form: {e}")
        finally:
            # Hide loading indicator
            if self.loading_indicator:
                self.loading_indicator.display = False

    async def _setup_contact_selectors(self) -> None:
        """Setup contact selector dropdowns."""
        if not self.from_contact_select or not self.to_contact_select:
            return

        # Create contact options
        contact_options = [("Select contact...", "")]
        for contact in self.available_contacts:
            contact_id = contact.get("id", "")
            contact_name = contact.get("name", "Unknown")
            contact_email = contact.get("email", "")

            # Format display name with email if available
            display_name = contact_name
            if contact_email:
                display_name = f"{contact_name} ({contact_email})"

            contact_options.append((display_name, str(contact_id)))

        # Update both selectors
        self.from_contact_select.set_options(contact_options)
        self.to_contact_select.set_options(contact_options)

        # Set up autocomplete for contact selection
        self.autocomplete_engine.set_items(self.available_contacts)

    async def _setup_relationship_type_selector(self) -> None:
        """Setup relationship type selector dropdown."""
        if not self.relationship_type_select:
            return

        # Create relationship type options
        type_options = [("Select relationship type...", "")]
        for rel_type in self.available_relationship_types:
            type_key = rel_type.get("type_key", "")
            description = rel_type.get("description", "")

            # Format display name
            display_name = f"{type_key}"
            if description:
                display_name = f"{type_key} - {description}"

            type_options.append((display_name, type_key))

        # Update selector
        self.relationship_type_select.set_options(type_options)

    async def _populate_form_fields(self) -> None:
        """Populate form fields with existing relationship data."""
        if not self.relationship_data:
            return

        # Populate contact selections
        from_contact_id = str(self.relationship_data.get("person1_id", ""))
        to_contact_id = str(self.relationship_data.get("person2_id", ""))

        if from_contact_id and self.from_contact_select:
            self.from_contact_select.value = from_contact_id

        if to_contact_id and self.to_contact_select:
            self.to_contact_select.value = to_contact_id

        # Populate relationship type
        type_key = self.relationship_data.get("type_key", "")
        if type_key and self.relationship_type_select:
            self.relationship_type_select.value = type_key

        # Populate date fields
        if self.start_date_input:
            start_date = self.relationship_data.get("start_date")
            if start_date:
                # Convert date to string format
                if isinstance(start_date, str):
                    self.start_date_input.value = start_date
                elif hasattr(start_date, "strftime"):
                    self.start_date_input.value = start_date.strftime("%Y-%m-%d")

        if self.end_date_input:
            end_date = self.relationship_data.get("end_date")
            if end_date:
                # Convert date to string format
                if isinstance(end_date, str):
                    self.end_date_input.value = end_date
                elif hasattr(end_date, "strftime"):
                    self.end_date_input.value = end_date.strftime("%Y-%m-%d")

        # Clear unsaved changes flag since we just loaded data
        self.clear_unsaved()

    def has_unsaved_changes(self) -> bool:
        """Check if form has unsaved changes."""
        # If we're in add mode and any field has content, consider it unsaved
        if self.mode == "add":
            return (
                (self.from_contact_select and self.from_contact_select.value)
                or (self.to_contact_select and self.to_contact_select.value)
                or (self.relationship_type_select and self.relationship_type_select.value)
                or (self.start_date_input and self.start_date_input.value.strip())
                or (self.end_date_input and self.end_date_input.value.strip())
            )

        # If we're in edit mode, check if values differ from original
        if self.mode == "edit" and self.relationship_data:
            # This is simplified - in a full implementation you'd compare all fields
            return (
                (
                    self.from_contact_select
                    and self.from_contact_select.value
                    != str(self.relationship_data.get("person1_id", ""))
                )
                or (
                    self.to_contact_select
                    and self.to_contact_select.value
                    != str(self.relationship_data.get("person2_id", ""))
                )
                or (
                    self.relationship_type_select
                    and self.relationship_type_select.value
                    != self.relationship_data.get("type_key", "")
                )
            )

        return super().has_unsaved_changes()

    async def on_input_changed(self, event: Input.Changed) -> None:
        """Mark form as having unsaved changes when input changes."""
        self.mark_unsaved()
        # Clear validation message when user starts typing
        if self.validation_message:
            self.validation_message.update("")

    async def on_select_changed(self, event: Select.Changed) -> None:
        """Mark form as having unsaved changes when select changes."""
        self.mark_unsaved()
        # Clear validation message when user makes selections
        if self.validation_message:
            self.validation_message.update("")

    async def on_key(self, event: events.Key) -> None:
        """Handle key events for relationship form screen."""
        key = event.key

        if event.ctrl and key == "s":
            # Save relationship
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
        """Handle save relationship action."""
        logger.info(f"Save relationship requested in {self.mode} mode")

        # Collect form data
        form_data = self._collect_form_data()

        # Validate form data
        validation_errors = self._validate_form_data(form_data)

        if validation_errors:
            # Show validation errors
            error_message = "Validation errors:\n" + "\n".join(validation_errors)
            if self.validation_message:
                self.validation_message.update(error_message)
            if self.notification_service:
                await self.notification_service.show_error("Please fix validation errors")
            return

        # Clear validation message
        if self.validation_message:
            self.validation_message.update("")

        try:
            if self.mode == "add":
                # Create new relationship
                success = await self.data_service.create_relationship_with_details(
                    from_contact_id=form_data["from_contact_id"],
                    to_contact_id=form_data["to_contact_id"],
                    type_key=form_data["type_key"],
                    start_date=form_data.get("start_date"),
                    end_date=form_data.get("end_date"),
                )

                if success:
                    # Handle bidirectional relationships
                    await self._create_inverse_relationship(form_data)

                    self.clear_unsaved()
                    if self.notification_service:
                        # Get contact names for display
                        from_contact_name = self._get_contact_name(form_data["from_contact_id"])
                        to_contact_name = self._get_contact_name(form_data["to_contact_id"])
                        rel_type = form_data["type_key"]
                        await self.notification_service.show_success(
                            f"Created relationship: {from_contact_name} → {rel_type} → {to_contact_name}"
                        )

                    # Navigate back to relationships list
                    await self._navigate_back()
                else:
                    if self.notification_service:
                        await self.notification_service.show_error("Failed to create relationship")

            elif self.mode == "edit":
                # Update existing relationship
                success = await self.data_service.update_relationship(
                    relationship_id=self.relationship_id,
                    type_key=form_data["type_key"],
                    start_date=form_data.get("start_date"),
                    end_date=form_data.get("end_date"),
                )

                if success:
                    self.clear_unsaved()
                    if self.notification_service:
                        await self.notification_service.show_success("Updated relationship")

                    # Navigate back to relationships list
                    await self._navigate_back()
                else:
                    if self.notification_service:
                        await self.notification_service.show_error("Failed to update relationship")

        except Exception as e:
            logger.error(f"Failed to save relationship: {e}")
            if self.notification_service:
                await self.notification_service.show_error(f"Failed to save relationship: {e}")

    def _collect_form_data(self) -> Dict:
        """Collect data from form fields."""
        data = {}

        # Contact IDs
        if self.from_contact_select and self.from_contact_select.value:
            try:
                data["from_contact_id"] = int(self.from_contact_select.value)
            except ValueError:
                pass

        if self.to_contact_select and self.to_contact_select.value:
            try:
                data["to_contact_id"] = int(self.to_contact_select.value)
            except ValueError:
                pass

        # Relationship type
        if self.relationship_type_select and self.relationship_type_select.value:
            data["type_key"] = self.relationship_type_select.value

        # Date fields (optional)
        if self.start_date_input and self.start_date_input.value.strip():
            data["start_date"] = self.start_date_input.value.strip()

        if self.end_date_input and self.end_date_input.value.strip():
            data["end_date"] = self.end_date_input.value.strip()

        return data

    def _validate_form_data(self, data: Dict) -> List[str]:
        """Validate form data and return list of errors."""
        errors = []

        # Required fields
        if not data.get("from_contact_id"):
            errors.append("From contact is required")

        if not data.get("to_contact_id"):
            errors.append("To contact is required")

        if not data.get("type_key"):
            errors.append("Relationship type is required")

        # Validate contacts are different
        if (
            data.get("from_contact_id")
            and data.get("to_contact_id")
            and data["from_contact_id"] == data["to_contact_id"]
        ):
            errors.append("From and To contacts must be different")

        # Validate date formats
        for date_field in ["start_date", "end_date"]:
            if data.get(date_field):
                try:
                    datetime.fromisoformat(data[date_field])
                except ValueError:
                    errors.append(
                        f"{date_field.replace('_', ' ').title()} must be in YYYY-MM-DD format"
                    )

        # Validate date order
        if data.get("start_date") and data.get("end_date"):
            try:
                start_date = datetime.fromisoformat(data["start_date"])
                end_date = datetime.fromisoformat(data["end_date"])
                if start_date > end_date:
                    errors.append("Start date must be before end date")
            except ValueError:
                pass  # Date format errors already reported above

        return errors

    async def _create_inverse_relationship(self, form_data: Dict) -> None:
        """Create inverse relationship if the relationship type is not symmetrical."""
        try:
            # Find the relationship type details
            type_key = form_data["type_key"]
            rel_type = None
            for rt in self.available_relationship_types:
                if rt.get("type_key") == type_key:
                    rel_type = rt
                    break

            if not rel_type:
                logger.warning(f"Relationship type '{type_key}' not found")
                return

            # Check if relationship is symmetrical
            is_symmetrical = rel_type.get("is_symmetrical", False)

            if is_symmetrical:
                # For symmetrical relationships, create the inverse with the same type
                await self.data_service.create_relationship_with_details(
                    from_contact_id=form_data["to_contact_id"],
                    to_contact_id=form_data["from_contact_id"],
                    type_key=type_key,
                    start_date=form_data.get("start_date"),
                    end_date=form_data.get("end_date"),
                )
            else:
                # For non-symmetrical relationships, create inverse with inverse type if available
                inverse_type_key = rel_type.get("inverse_type_key")
                if inverse_type_key:
                    await self.data_service.create_relationship_with_details(
                        from_contact_id=form_data["to_contact_id"],
                        to_contact_id=form_data["from_contact_id"],
                        type_key=inverse_type_key,
                        start_date=form_data.get("start_date"),
                        end_date=form_data.get("end_date"),
                    )

        except Exception as e:
            logger.error(f"Failed to create inverse relationship: {e}")

    def _get_contact_name(self, contact_id: int) -> str:
        """Get contact name by ID."""
        for contact in self.available_contacts:
            if contact.get("id") == contact_id:
                return contact.get("name", "Unknown")
        return "Unknown"

    async def _handle_cancel(self) -> None:
        """Handle cancel action."""
        logger.info("Cancel relationship form requested")

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
        """Navigate back to the relationships screen."""
        if self.nav_service:
            try:
                # Go back to relationships screen
                self.nav_service.pop()  # Remove current form screen
                if hasattr(self.app, "switch_screen"):
                    await self.app.switch_screen("relationships")
            except Exception as e:
                logger.error(f"Failed to navigate back: {e}")
                if self.notification_service:
                    await self.notification_service.show_error("Failed to navigate back")


# Register this screen
register_screen("relationship_form", RelationshipFormScreen)
