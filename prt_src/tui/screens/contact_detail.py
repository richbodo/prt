"""Contact detail screen for PRT TUI.

Shows full contact information with relationships, tags, and notes.
Provides edit and delete functionality.
"""

from typing import Dict, List, Optional

from textual import events
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, LoadingIndicator, Static

from prt_src.logging_config import get_logger
from prt_src.tui.screens import register_screen
from prt_src.tui.screens.base import BaseScreen, EscapeIntent

logger = get_logger(__name__)


class ContactDetailScreen(BaseScreen):
    """Contact detail screen showing full contact information."""

    def __init__(self, contact_id: int = None, *args, **kwargs):
        """Initialize contact detail screen.

        Args:
            contact_id: ID of the contact to display
        """
        super().__init__(*args, **kwargs)
        self.contact_id = contact_id
        self.contact_data: Optional[Dict] = None
        self.relationships_data: List[Dict] = []
        self.loading_indicator: Optional[LoadingIndicator] = None

        # UI components
        self.contact_name_label: Optional[Static] = None
        self.contact_email_label: Optional[Static] = None
        self.contact_phone_label: Optional[Static] = None
        self.relationships_table: Optional[DataTable] = None
        self.tags_label: Optional[Static] = None
        self.notes_label: Optional[Static] = None
        self.edit_button: Optional[Button] = None
        self.delete_button: Optional[Button] = None
        self.back_button: Optional[Button] = None

    def get_screen_name(self) -> str:
        """Get screen identifier."""
        return "contact_detail"

    def on_escape(self) -> EscapeIntent:
        """ESC goes back to previous screen."""
        return EscapeIntent.POP

    def get_header_config(self) -> dict:
        """Configure header."""
        config = super().get_header_config()
        if config:
            config["title"] = "Contact Details"
        return config

    def get_footer_config(self) -> dict:
        """Configure footer with action hints."""
        config = super().get_footer_config()
        if config:
            config["keyHints"] = ["[e]dit", "[d]elete", "[Enter] Back", "[ESC] Back"]
        return config

    def compose(self) -> ComposeResult:
        """Compose contact detail screen layout."""
        with Vertical(classes="contact-detail"):
            # Loading indicator (initially hidden)
            self.loading_indicator = LoadingIndicator()
            yield self.loading_indicator

            # Action buttons header
            with Horizontal(id="detail-actions"):
                self.edit_button = Button("Edit", variant="primary", classes="action-button")
                self.delete_button = Button("Delete", variant="error", classes="action-button")
                self.back_button = Button("Back", variant="default", classes="action-button")
                yield self.edit_button
                yield self.delete_button
                yield self.back_button

            # Contact information section
            with Vertical(id="contact-info-section"):
                yield Static("Contact Information", classes="section-title")

                with Vertical(classes="field-container"):
                    yield Static("Name:", classes="field-label")
                    self.contact_name_label = Static("", classes="field-value")
                    yield self.contact_name_label

                with Vertical(classes="field-container"):
                    yield Static("Email:", classes="field-label")
                    self.contact_email_label = Static("", classes="field-value")
                    yield self.contact_email_label

                with Vertical(classes="field-container"):
                    yield Static("Phone:", classes="field-label")
                    self.contact_phone_label = Static("", classes="field-value")
                    yield self.contact_phone_label

            # Tags section
            with Vertical(id="tags-section"):
                yield Static("Tags", classes="section-title")
                self.tags_label = Static("", classes="field-value")
                yield self.tags_label

            # Relationships section
            with Vertical(id="relationships-section"):
                yield Static("Relationships", classes="section-title")

                self.relationships_table = DataTable(
                    id="relationships-table",
                    cursor_type="row",
                    zebra_stripes=True,
                    show_cursor=False,
                )
                self.relationships_table.add_columns(
                    ("direction", "Direction"),
                    ("contact", "Contact"),
                    ("type", "Relationship Type"),
                )
                yield self.relationships_table

            # Notes section
            with Vertical(id="notes-section"):
                yield Static("Notes", classes="section-title")
                self.notes_label = Static("", classes="field-value")
                yield self.notes_label

    async def on_mount(self) -> None:
        """Load contact data when screen is mounted."""
        await super().on_mount()
        if self.contact_id is not None:
            await self._load_contact()
        else:
            logger.error("No contact_id provided to contact detail screen")
            if self.notification_service:
                self.notification_service.show_error("No contact ID provided")

    async def on_show(self) -> None:
        """Refresh contact data when screen becomes visible."""
        await super().on_show()
        if self.contact_id is not None:
            await self._load_contact()

    async def _load_contact(self) -> None:
        """Load contact data and relationships."""
        if not self.data_service:
            logger.warning("No data service available")
            return

        try:
            # Show loading indicator
            if self.loading_indicator:
                self.loading_indicator.display = True

            # Load contact data
            self.contact_data = await self.data_service.get_contact(self.contact_id)

            if not self.contact_data:
                logger.error(f"Contact {self.contact_id} not found")
                if self.notification_service:
                    self.notification_service.show_error("Contact not found")
                return

            # Update contact info display
            await self._update_contact_display()

            # Load relationships
            self.relationships_data = await self.data_service.get_relationships(self.contact_id)
            await self._update_relationships_display()

            # Load tags and notes
            await self._update_tags_display()
            await self._update_notes_display()

            logger.info(f"Loaded contact {self.contact_id} details")

        except Exception as e:
            logger.error(f"Failed to load contact {self.contact_id}: {e}")
            if self.notification_service:
                self.notification_service.show_error(f"Failed to load contact: {e}")
        finally:
            # Hide loading indicator
            if self.loading_indicator:
                self.loading_indicator.display = False

    async def _update_contact_display(self) -> None:
        """Update the contact information display."""
        if not self.contact_data:
            return

        # Format contact name (handle both 'name' field and separate first/last)
        name = self.contact_data.get("name", "")
        if not name:
            first_name = self.contact_data.get("first_name", "")
            last_name = self.contact_data.get("last_name", "")
            name = f"{first_name} {last_name}".strip()
            if not name:
                name = "Unknown"

        # Update display labels
        if self.contact_name_label:
            self.contact_name_label.update(name)

        if self.contact_email_label:
            email = self.contact_data.get("email", "") or "(not provided)"
            self.contact_email_label.update(email)

        if self.contact_phone_label:
            phone = self.contact_data.get("phone", "") or "(not provided)"
            self.contact_phone_label.update(phone)

    async def _update_relationships_display(self) -> None:
        """Update the relationships table."""
        if not self.relationships_table:
            return

        self.relationships_table.clear()

        for relationship in self.relationships_data:
            # Determine direction and contact name based on relationship structure
            direction = ""
            contact_name = ""
            rel_type = relationship.get("type", "unknown")

            # Handle both from/to relationship and contact-specific relationships
            if relationship.get("from_contact_id") == self.contact_id:
                direction = "→"  # This contact is the source
                contact_name = relationship.get("to_contact_name", "Unknown")
            elif relationship.get("to_contact_id") == self.contact_id:
                direction = "←"  # This contact is the target
                contact_name = relationship.get("from_contact_name", "Unknown")
            else:
                # Fall back to basic relationship display
                direction = "—"
                contact_name = relationship.get("contact_name", "Unknown")

            self.relationships_table.add_row(direction, contact_name, rel_type)

    async def _update_tags_display(self) -> None:
        """Update the tags display."""
        if not self.tags_label:
            return

        try:
            # Get all tags and filter for this contact
            # TODO: Add when API supports getting contact-specific tags
            # all_tags = await self.data_service.get_tags()

            # TODO: Need API method to get contact-specific tags
            # For now, show placeholder
            tags_text = "Tags functionality coming soon..."
            self.tags_label.update(tags_text)

        except Exception as e:
            logger.error(f"Failed to load tags: {e}")
            self.tags_label.update("Error loading tags")

    async def _update_notes_display(self) -> None:
        """Update the notes display."""
        if not self.notes_label:
            return

        try:
            # Get contact-specific notes
            notes = await self.data_service.get_notes(contact_id=self.contact_id)

            if not notes:
                notes_text = "No notes"
            else:
                # Display first few notes or count
                if len(notes) == 1:
                    notes_text = f"1 note: {notes[0].get('title', 'Untitled')}"
                else:
                    notes_text = f"{len(notes)} notes"

            self.notes_label.update(notes_text)

        except Exception as e:
            logger.error(f"Failed to load notes: {e}")
            self.notes_label.update("Error loading notes")

    async def on_key(self, event: events.Key) -> None:
        """Handle key events for contact detail screen."""
        key = event.key

        if key == "e":
            # Edit contact
            await self._handle_edit_contact()
        elif key == "d":
            # Delete contact
            await self._handle_delete_contact()
        elif key == "enter":
            # Go back
            await self._handle_back()
        else:
            # Let parent handle other keys
            await super().on_key(event)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button == self.edit_button:
            await self._handle_edit_contact()
        elif event.button == self.delete_button:
            await self._handle_delete_contact()
        elif event.button == self.back_button:
            await self._handle_back()

    async def _handle_edit_contact(self) -> None:
        """Handle edit contact action."""
        logger.info(f"Edit contact {self.contact_id} requested")

        if self.nav_service:
            try:
                self.nav_service.push(
                    "contact_form", {"contact_id": self.contact_id, "mode": "edit"}
                )
                if hasattr(self.app, "switch_screen"):
                    await self.app.switch_screen("contact_form")
            except Exception as e:
                logger.error(f"Failed to navigate to edit contact screen: {e}")
                if self.notification_service:
                    self.notification_service.show_error("Failed to open edit contact screen")

    async def _handle_delete_contact(self) -> None:
        """Handle delete contact action."""
        logger.info(f"Delete contact {self.contact_id} requested")

        if not self.contact_data:
            logger.error("No contact data loaded for delete operation")
            return

        # Get contact name for confirmation dialog
        name = self.contact_data.get("name", "this contact")

        if self.notification_service:
            try:
                # Show confirmation dialog
                confirmed = await self.notification_service.show_delete_dialog(name)

                if confirmed and self.data_service:
                    # Delete the contact
                    success = await self.data_service.delete_contact(self.contact_id)

                    if success:
                        self.notification_service.show_success(f"Deleted {name}")
                        # Navigate back to contacts list
                        await self._handle_back()
                    else:
                        self.notification_service.show_error(f"Failed to delete {name}")

            except Exception as e:
                logger.error(f"Failed to delete contact {self.contact_id}: {e}")
                if self.notification_service:
                    self.notification_service.show_error("Failed to delete contact")

    async def _handle_back(self) -> None:
        """Handle back navigation."""
        logger.info("Back to contacts list requested")

        if self.nav_service:
            try:
                self.nav_service.pop()
                if hasattr(self.app, "switch_screen"):
                    await self.app.switch_screen("contacts")
            except Exception as e:
                logger.error(f"Failed to navigate back: {e}")
                if self.notification_service:
                    self.notification_service.show_error("Failed to go back")


# Register this screen
register_screen("contact_detail", ContactDetailScreen)
