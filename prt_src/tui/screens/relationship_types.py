"""Relationship types screen for PRT TUI.

Displays relationship types in a DataTable with management capabilities including
add, edit, delete, and usage count display.
"""

from typing import Dict
from typing import List
from typing import Optional

from textual import events
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.containers import Vertical
from textual.widgets import Button
from textual.widgets import Checkbox
from textual.widgets import DataTable
from textual.widgets import Input
from textual.widgets import LoadingIndicator
from textual.widgets import Static

from prt_src.core.components.validation import ValidationSystem
from prt_src.logging_config import get_logger
from prt_src.tui.screens import register_screen
from prt_src.tui.screens.base import BaseScreen
from prt_src.tui.screens.base import EscapeIntent

logger = get_logger(__name__)


class RelationshipTypesScreen(BaseScreen):
    """Relationship types management screen with DataTable display."""

    def __init__(self, *args, **kwargs):
        """Initialize relationship types screen."""
        super().__init__(*args, **kwargs)
        self.types_table: Optional[DataTable] = None
        self.types_data: List[Dict] = []
        self.usage_counts: Dict[str, int] = {}
        self.loading_indicator: Optional[LoadingIndicator] = None
        self.selected_type_key: Optional[str] = None
        self.validation_system = ValidationSystem()

    def get_screen_name(self) -> str:
        """Get screen identifier."""
        return "relationship_types"

    def on_escape(self) -> EscapeIntent:
        """ESC goes back to previous screen."""
        return EscapeIntent.POP

    def get_header_config(self) -> dict:
        """Configure header."""
        config = super().get_header_config()
        if config:
            config["title"] = "Relationship Types"
        return config

    def get_footer_config(self) -> dict:
        """Configure footer with relationship type hints."""
        config = super().get_footer_config()
        if config:
            config["keyHints"] = ["[a]dd", "[e]dit", "[d]elete", "[Enter] View", "[ESC] Back"]
        return config

    def compose(self) -> ComposeResult:
        """Compose relationship types screen layout."""
        with Vertical(classes="relationship-types-container"):
            # Header with action buttons
            with Horizontal(id="types-actions"):
                yield Button(
                    "Add Type", id="add-type-btn", variant="primary", classes="action-button"
                )

            # Loading indicator (initially hidden)
            self.loading_indicator = LoadingIndicator()
            yield self.loading_indicator

            # Relationship types table
            self.types_table = DataTable(
                id="types-table", cursor_type="row", zebra_stripes=True, show_cursor=True
            )
            self.types_table.add_columns(
                ("type_key", "Type Key"),
                ("description", "Description"),
                ("inverse_type_key", "Inverse Type"),
                ("is_symmetrical", "Symmetrical"),
                ("usage_count", "Usage Count"),
            )
            yield self.types_table

    async def on_mount(self) -> None:
        """Load relationship types data when screen is mounted."""
        await super().on_mount()
        await self._load_relationship_types()

    async def on_show(self) -> None:
        """Refresh relationship types data when screen becomes visible."""
        await super().on_show()
        # Refresh the types list when returning to this screen
        await self._load_relationship_types()

    async def _load_relationship_types(self) -> None:
        """Load relationship types data from the data service."""
        if not self.data_service:
            logger.warning("No data service available")
            return

        try:
            # Show loading indicator
            if self.loading_indicator:
                self.loading_indicator.display = True

            # Load relationship types data
            types_data = await self.data_service.get_relationship_types()
            self.types_data = types_data

            # Load usage counts for each type
            self.usage_counts = {}
            for rel_type in types_data:
                type_key = rel_type.get("type_key", "")
                if type_key:
                    usage_count = await self.data_service.get_relationship_type_usage_count(
                        type_key
                    )
                    self.usage_counts[type_key] = usage_count

            # Clear and populate table
            if self.types_table:
                self.types_table.clear()

                # Sort relationship types by type_key
                sorted_types = sorted(types_data, key=lambda x: x.get("type_key", "").lower())

                for rel_type in sorted_types:
                    type_key = rel_type.get("type_key", "")
                    description = rel_type.get("description", "")
                    inverse_type_key = rel_type.get("inverse_type_key") or "None"
                    is_symmetrical = "Yes" if rel_type.get("is_symmetrical") else "No"
                    usage_count = str(self.usage_counts.get(type_key, 0))

                    # Add row to table
                    self.types_table.add_row(
                        type_key,
                        description,
                        inverse_type_key,
                        is_symmetrical,
                        usage_count,
                        key=type_key,  # Use type_key as row key
                    )

            logger.info(f"Loaded {len(types_data)} relationship types")

        except Exception as e:
            logger.error(f"Failed to load relationship types: {e}")
            if self.notification_service:
                await self.notification_service.show_error(
                    f"Failed to load relationship types: {e}"
                )
        finally:
            # Hide loading indicator
            if self.loading_indicator:
                self.loading_indicator.display = False

    def _get_selected_type_key(self) -> Optional[str]:
        """Get the type key of the currently selected relationship type."""
        if not self.types_table or self.types_table.cursor_row < 0:
            return None

        try:
            # Get the row key which is the type_key
            cursor_coordinate = self.types_table.coordinate_to_cell_key(
                self.types_table.cursor_coordinate
            )
            if cursor_coordinate.row_key:
                return cursor_coordinate.row_key.value
            return None
        except (ValueError, AttributeError, TypeError):
            return None

    async def on_key(self, event: events.Key) -> None:
        """Handle key events for relationship types screen."""
        key = event.key

        # Get selected type key for operations that need it
        selected_type_key = self._get_selected_type_key()

        if key == "a":
            # Add new relationship type
            await self._handle_add_type()
        elif key == "e":
            # Edit selected relationship type
            if selected_type_key:
                await self._handle_edit_type(selected_type_key)
            else:
                if self.notification_service:
                    await self.notification_service.show_warning("No relationship type selected")
        elif key == "d":
            # Delete selected relationship type
            if selected_type_key:
                await self._handle_delete_type(selected_type_key)
            else:
                if self.notification_service:
                    await self.notification_service.show_warning("No relationship type selected")
        elif key == "enter":
            # View type details
            if selected_type_key:
                await self._handle_view_type(selected_type_key)
            else:
                if self.notification_service:
                    await self.notification_service.show_warning("No relationship type selected")
        else:
            # Let parent handle other keys
            await super().on_key(event)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "add-type-btn":
            await self._handle_add_type()

    async def _handle_add_type(self) -> None:
        """Handle add new relationship type action."""
        logger.info("Add relationship type requested")
        await self._show_type_dialog(mode="add")

    async def _handle_edit_type(self, type_key: str) -> None:
        """Handle edit relationship type action."""
        logger.info(f"Edit relationship type {type_key} requested")
        await self._show_type_dialog(mode="edit", type_key=type_key)

    async def _handle_delete_type(self, type_key: str) -> None:
        """Handle delete relationship type action."""
        logger.info(f"Delete relationship type {type_key} requested")

        # Check usage count
        usage_count = self.usage_counts.get(type_key, 0)

        if usage_count > 0:
            if self.notification_service:
                await self.notification_service.show_error(
                    f"Cannot delete relationship type '{type_key}' - it is used in {usage_count} relationships"
                )
            return

        # Find type details for confirmation dialog
        type_desc = type_key
        for rel_type in self.types_data:
            if rel_type.get("type_key") == type_key:
                description = rel_type.get("description", "")
                if description:
                    type_desc = f"{type_key} - {description}"
                break

        if self.notification_service:
            try:
                # Show confirmation dialog
                confirmed = await self.notification_service.show_delete_dialog(
                    f"relationship type '{type_desc}'"
                )

                if confirmed and self.data_service:
                    # Delete the relationship type
                    success = await self.data_service.delete_relationship_type(type_key)

                    if success:
                        await self.notification_service.show_success(
                            f"Deleted relationship type '{type_key}'"
                        )
                        # Reload the types list
                        await self._load_relationship_types()
                    else:
                        await self.notification_service.show_error(
                            f"Failed to delete relationship type '{type_key}'"
                        )

            except Exception as e:
                logger.error(f"Failed to delete relationship type {type_key}: {e}")
                if self.notification_service:
                    await self.notification_service.show_error("Failed to delete relationship type")

    async def _handle_view_type(self, type_key: str) -> None:
        """Handle view relationship type details action."""
        logger.info(f"View relationship type {type_key} requested")

        # Find the type data
        type_data = None
        for rel_type in self.types_data:
            if rel_type.get("type_key") == type_key:
                type_data = rel_type
                break

        if not type_data:
            if self.notification_service:
                await self.notification_service.show_error("Relationship type not found")
            return

        # Show type details in a dialog
        await self._show_type_details_dialog(type_data)

    async def _show_type_dialog(self, mode: str = "add", type_key: str = None) -> None:
        """Show dialog for adding/editing relationship type."""
        if not self.notification_service:
            logger.error("No notification service available for dialog")
            return

        try:
            # For a full implementation, you would create a custom dialog widget
            # For now, we'll use a simplified approach with multiple input dialogs

            if mode == "add":
                title = "Add Relationship Type"
                existing_type = None
            else:
                title = "Edit Relationship Type"
                existing_type = None
                for rel_type in self.types_data:
                    if rel_type.get("type_key") == type_key:
                        existing_type = rel_type
                        break

                if not existing_type:
                    await self.notification_service.show_error("Relationship type not found")
                    return

            # This is a simplified dialog implementation
            # In a full implementation, you would create a proper form dialog
            await self.notification_service.show_info(
                f"{title} dialog functionality needs to be implemented with proper form widgets"
            )

            # TODO: Implement proper dialog with:
            # - Type key input field
            # - Description input field
            # - Inverse type key dropdown
            # - Symmetrical checkbox
            # - Save and Cancel buttons

        except Exception as e:
            logger.error(f"Failed to show type dialog: {e}")
            if self.notification_service:
                await self.notification_service.show_error("Failed to open type dialog")

    async def _show_type_details_dialog(self, type_data: Dict) -> None:
        """Show dialog with relationship type details."""
        if not self.notification_service:
            return

        try:
            type_key = type_data.get("type_key", "Unknown")
            description = type_data.get("description", "No description")
            inverse_type_key = type_data.get("inverse_type_key") or "None"
            is_symmetrical = "Yes" if type_data.get("is_symmetrical") else "No"
            usage_count = self.usage_counts.get(type_key, 0)

            details = f"""Relationship Type Details:

Type Key: {type_key}
Description: {description}
Inverse Type: {inverse_type_key}
Symmetrical: {is_symmetrical}
Usage Count: {usage_count}"""

            # Show details in an info dialog
            # In a full implementation, you might want a custom dialog widget
            await self.notification_service.show_info(details)

        except Exception as e:
            logger.error(f"Failed to show type details: {e}")


class TypeFormDialog(Static):
    """Dialog for adding/editing relationship types.

    This is a placeholder for a proper dialog implementation.
    In a full implementation, this would be a modal dialog with form fields.
    """

    def __init__(
        self,
        mode: str = "add",
        type_data: Optional[Dict] = None,
        on_save=None,
        on_cancel=None,
        *args,
        **kwargs,
    ):
        """Initialize type form dialog.

        Args:
            mode: Either "add" or "edit"
            type_data: Existing type data for edit mode
            on_save: Callback for save action
            on_cancel: Callback for cancel action
        """
        super().__init__(*args, **kwargs)
        self.mode = mode
        self.type_data = type_data or {}
        self.on_save = on_save
        self.on_cancel = on_cancel
        self.validation_system = ValidationSystem()

        # Form fields
        self.type_key_input: Optional[Input] = None
        self.description_input: Optional[Input] = None
        self.inverse_key_input: Optional[Input] = None
        self.is_symmetrical_checkbox: Optional[Checkbox] = None
        self.save_button: Optional[Button] = None
        self.cancel_button: Optional[Button] = None

    def compose(self) -> ComposeResult:
        """Compose type form dialog layout."""
        title = "Add Relationship Type" if self.mode == "add" else "Edit Relationship Type"

        with Vertical(classes="type-form-dialog"):
            yield Static(title, classes="dialog-title")

            # Form fields
            with Vertical(classes="form-fields"):
                yield Static("Type Key:", classes="field-label")
                self.type_key_input = Input(
                    value=self.type_data.get("type_key", ""),
                    placeholder="e.g., friend, parent, mentor",
                    classes="field-input",
                )
                yield self.type_key_input

                yield Static("Description:", classes="field-label")
                self.description_input = Input(
                    value=self.type_data.get("description", ""),
                    placeholder="e.g., Is a friend of, Is the parent of",
                    classes="field-input",
                )
                yield self.description_input

                yield Static("Inverse Type Key (optional):", classes="field-label")
                self.inverse_key_input = Input(
                    value=self.type_data.get("inverse_type_key", "") or "",
                    placeholder="e.g., friend, child, mentee",
                    classes="field-input",
                )
                yield self.inverse_key_input

                self.is_symmetrical_checkbox = Checkbox(
                    "Is Symmetrical",
                    value=bool(self.type_data.get("is_symmetrical", False)),
                    classes="field-checkbox",
                )
                yield self.is_symmetrical_checkbox

            # Action buttons
            with Horizontal(classes="dialog-actions"):
                self.save_button = Button("Save", variant="primary")
                self.cancel_button = Button("Cancel", variant="default")
                yield self.save_button
                yield self.cancel_button

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button == self.save_button:
            await self._handle_save()
        elif event.button == self.cancel_button:
            await self._handle_cancel()

    async def _handle_save(self) -> None:
        """Handle save action."""
        if not self.on_save:
            return

        # Collect form data
        form_data = {
            "type_key": self.type_key_input.value.strip() if self.type_key_input else "",
            "description": self.description_input.value.strip() if self.description_input else "",
            "inverse_type_key": (
                self.inverse_key_input.value.strip() if self.inverse_key_input else None
            ),
            "is_symmetrical": (
                self.is_symmetrical_checkbox.value if self.is_symmetrical_checkbox else False
            ),
        }

        # Basic validation
        if not form_data["type_key"]:
            # Show validation error
            return

        # Call save callback
        await self.on_save(form_data)

    async def _handle_cancel(self) -> None:
        """Handle cancel action."""
        if self.on_cancel:
            await self.on_cancel()


# Register this screen
register_screen("relationship_types", RelationshipTypesScreen)
