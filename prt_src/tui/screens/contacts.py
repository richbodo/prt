"""Contacts screen for PRT TUI.

Displays contacts list with DataTable widget and key bindings for management.
"""

from typing import Optional

from textual import events
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import DataTable
from textual.widgets import LoadingIndicator

from prt_src.logging_config import get_logger
from prt_src.tui.screens import register_screen
from prt_src.tui.screens.base import BaseScreen
from prt_src.tui.screens.base import EscapeIntent

logger = get_logger(__name__)


class ContactsScreen(BaseScreen):
    """Contacts management screen with DataTable display."""

    def __init__(self, *args, **kwargs):
        """Initialize contacts screen."""
        super().__init__(*args, **kwargs)
        self.contacts_table: Optional[DataTable] = None
        self.contacts_data = []
        self.loading_indicator: Optional[LoadingIndicator] = None
        self.selected_contact_id: Optional[int] = None

    def get_screen_name(self) -> str:
        """Get screen identifier."""
        return "contacts"

    def on_escape(self) -> EscapeIntent:
        """ESC goes back to previous screen."""
        return EscapeIntent.POP

    def get_header_config(self) -> dict:
        """Configure header with search box."""
        config = super().get_header_config()
        if config:
            config["searchBox"] = True
            config["title"] = "Contacts"
        return config

    def get_footer_config(self) -> dict:
        """Configure footer with action hints."""
        config = super().get_footer_config()
        if config:
            config["keyHints"] = [
                "[a]dd",
                "[e]dit",
                "[d]elete",
                "[Enter] View",
                "[/] Search",
                "[ESC] Back",
            ]
        return config

    def compose(self) -> ComposeResult:
        """Compose contacts screen layout."""
        with Vertical(classes="contacts-container"):
            # Loading indicator (initially hidden)
            self.loading_indicator = LoadingIndicator()
            yield self.loading_indicator

            # Contacts table
            self.contacts_table = DataTable(
                id="contacts-table", cursor_type="row", zebra_stripes=True, show_cursor=True
            )
            self.contacts_table.add_columns(
                ("id", "ID"),  # Hidden column for contact ID
                ("name", "Name"),
                ("email", "Email"),
                ("phone", "Phone"),
                ("last_interaction", "Last Interaction"),
            )
            # Hide the ID column
            self.contacts_table.show_column("id", False)
            yield self.contacts_table

    async def on_mount(self) -> None:
        """Load contacts data when screen is mounted."""
        await super().on_mount()
        await self._load_contacts()

    async def on_show(self) -> None:
        """Refresh contacts data when screen becomes visible."""
        await super().on_show()
        # Refresh the contacts list when returning to this screen
        await self._load_contacts()

    async def _load_contacts(self) -> None:
        """Load contacts data from the data service."""
        if not self.data_service:
            logger.warning("No data service available")
            return

        try:
            # Show loading indicator
            if self.loading_indicator:
                self.loading_indicator.display = True

            # Load contacts data
            contacts = await self.data_service.get_contacts(limit=1000, offset=0)
            self.contacts_data = contacts

            # Clear and populate table
            if self.contacts_table:
                self.contacts_table.clear()
                for contact in contacts:
                    # Format last interaction date
                    last_interaction = "Never"
                    # TODO: Get actual last interaction from relationship_info

                    # Format contact name (handle both 'name' field and separate first/last)
                    if contact.get("name"):
                        name = contact.get("name")
                    else:
                        first_name = contact.get("first_name", "")
                        last_name = contact.get("last_name", "")
                        name = f"{first_name} {last_name}".strip()
                        if not name:
                            name = "Unknown"

                    # Format email and phone
                    email = contact.get("email") or ""
                    phone = contact.get("phone") or ""

                    # Add row to table
                    self.contacts_table.add_row(
                        str(contact.get("id", "")),  # Hidden ID column
                        name,
                        email,
                        phone,
                        last_interaction,
                        key=str(contact.get("id", "")),  # Use contact ID as row key
                    )

            logger.info(f"Loaded {len(contacts)} contacts")

        except Exception as e:
            logger.error(f"Failed to load contacts: {e}")
            if self.notification_service:
                await self.notification_service.show_error(f"Failed to load contacts: {e}")
        finally:
            # Hide loading indicator
            if self.loading_indicator:
                self.loading_indicator.display = False

    def _get_selected_contact_id(self) -> Optional[int]:
        """Get the ID of the currently selected contact."""
        if not self.contacts_table or self.contacts_table.cursor_row < 0:
            return None

        try:
            # Get the row key which is the contact ID (stored as the row key when we add the row)
            cursor_coordinate = self.contacts_table.coordinate_to_cell_key(
                self.contacts_table.cursor_coordinate
            )
            if cursor_coordinate.row_key:
                return int(cursor_coordinate.row_key.value)
            return None
        except (ValueError, AttributeError, TypeError):
            return None

    async def on_key(self, event: events.Key) -> None:
        """Handle key events for contacts screen."""
        key = event.key

        # Get selected contact ID for operations that need it
        selected_id = self._get_selected_contact_id()

        if key == "a":
            # Add new contact
            await self._handle_add_contact()
        elif key == "e":
            # Edit selected contact
            if selected_id:
                await self._handle_edit_contact(selected_id)
            else:
                if self.notification_service:
                    await self.notification_service.show_warning("No contact selected")
        elif key == "d":
            # Delete selected contact
            if selected_id:
                await self._handle_delete_contact(selected_id)
            else:
                if self.notification_service:
                    await self.notification_service.show_warning("No contact selected")
        elif key == "enter":
            # View contact details
            if selected_id:
                await self._handle_view_contact(selected_id)
            else:
                if self.notification_service:
                    await self.notification_service.show_warning("No contact selected")
        elif key == "forward_slash":
            # Focus search box
            await self._handle_search_focus()
        else:
            # Let parent handle other keys
            await super().on_key(event)

    async def _handle_add_contact(self) -> None:
        """Handle add new contact action."""
        logger.info("Add contact requested")

        if self.nav_service:
            try:
                self.nav_service.push("contact_form", {"mode": "add"})
                if hasattr(self.app, "switch_screen"):
                    await self.app.switch_screen("contact_form")
            except Exception as e:
                logger.error(f"Failed to navigate to contact_form screen: {e}")
                if self.notification_service:
                    await self.notification_service.show_error("Failed to open add contact screen")

    async def _handle_edit_contact(self, contact_id: int) -> None:
        """Handle edit contact action."""
        logger.info(f"Edit contact {contact_id} requested")

        if self.nav_service:
            try:
                self.nav_service.push("contact_form", {"contact_id": contact_id, "mode": "edit"})
                if hasattr(self.app, "switch_screen"):
                    await self.app.switch_screen("contact_form")
            except Exception as e:
                logger.error(f"Failed to navigate to contact_form screen: {e}")
                if self.notification_service:
                    await self.notification_service.show_error("Failed to open edit contact screen")

    async def _handle_delete_contact(self, contact_id: int) -> None:
        """Handle delete contact action."""
        logger.info(f"Delete contact {contact_id} requested")

        # Find contact name for confirmation dialog
        contact_name = "this contact"
        for contact in self.contacts_data:
            if contact.get("id") == contact_id:
                contact_name = contact.get("name", "Unknown")
                break

        if self.notification_service:
            try:
                # Show confirmation dialog
                confirmed = await self.notification_service.show_delete_dialog(contact_name)

                if confirmed and self.data_service:
                    # Delete the contact
                    success = await self.data_service.delete_contact(contact_id)

                    if success:
                        await self.notification_service.show_success(f"Deleted {contact_name}")
                        # Reload the contacts list
                        await self._load_contacts()
                    else:
                        await self.notification_service.show_error(
                            f"Failed to delete {contact_name}"
                        )

            except Exception as e:
                logger.error(f"Failed to delete contact {contact_id}: {e}")
                if self.notification_service:
                    await self.notification_service.show_error("Failed to delete contact")

    async def _handle_view_contact(self, contact_id: int) -> None:
        """Handle view contact details action."""
        logger.info(f"View contact {contact_id} requested")

        if self.nav_service:
            try:
                self.nav_service.push("contact_detail", {"contact_id": contact_id})
                if hasattr(self.app, "switch_screen"):
                    await self.app.switch_screen("contact_detail")
            except Exception as e:
                logger.error(f"Failed to navigate to contact_detail screen: {e}")
                if self.notification_service:
                    await self.notification_service.show_error(
                        "Failed to open contact details screen"
                    )

    async def _handle_search_focus(self) -> None:
        """Handle focus search box action."""
        logger.info("Search focus requested")
        # TODO: Implement search box focus when header search is implemented
        if self.notification_service:
            await self.notification_service.show_info("Search functionality coming soon")


# Register this screen
register_screen("contacts", ContactsScreen)
