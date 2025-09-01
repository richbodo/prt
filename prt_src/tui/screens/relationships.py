"""Relationships screen for PRT TUI.

Displays relationships in a DataTable with management capabilities.
"""

from datetime import datetime
from typing import Optional

from textual import events
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import DataTable, LoadingIndicator

from prt_src.logging_config import get_logger
from prt_src.tui.screens import register_screen
from prt_src.tui.screens.base import BaseScreen, EscapeIntent

logger = get_logger(__name__)


class RelationshipsScreen(BaseScreen):
    """Relationships management screen with DataTable display."""

    def __init__(self, *args, **kwargs):
        """Initialize relationships screen."""
        super().__init__(*args, **kwargs)
        self.relationships_table: Optional[DataTable] = None
        self.relationships_data = []
        self.loading_indicator: Optional[LoadingIndicator] = None
        self.selected_relationship_id: Optional[int] = None

    def get_screen_name(self) -> str:
        """Get screen identifier."""
        return "relationships"

    def on_escape(self) -> EscapeIntent:
        """ESC goes back to previous screen."""
        return EscapeIntent.POP

    def get_header_config(self) -> dict:
        """Configure header."""
        config = super().get_header_config()
        if config:
            config["title"] = "Relationships"
        return config

    def get_footer_config(self) -> dict:
        """Configure footer with relationship hints."""
        config = super().get_footer_config()
        if config:
            config["keyHints"] = ["[a]dd", "[e]dit", "[d]elete", "[Enter] View", "[ESC] Back"]
        return config

    def compose(self) -> ComposeResult:
        """Compose relationships screen layout."""
        with Vertical(classes="relationships-container"):
            # Loading indicator (initially hidden)
            self.loading_indicator = LoadingIndicator()
            yield self.loading_indicator

            # Relationships table
            self.relationships_table = DataTable(
                id="relationships-table", cursor_type="row", zebra_stripes=True, show_cursor=True
            )
            self.relationships_table.add_columns(
                ("id", "ID"),  # Hidden column for relationship ID
                ("person1", "Person 1"),
                ("relationship_type", "Relationship Type"),
                ("person2", "Person 2"),
                ("start_date", "Start Date"),
                ("status", "Status"),
            )
            # Hide the ID column
            self.relationships_table.show_column("id", False)
            yield self.relationships_table

    async def on_mount(self) -> None:
        """Load relationships data when screen is mounted."""
        await super().on_mount()
        await self._load_relationships()

    async def on_show(self) -> None:
        """Refresh relationships data when screen becomes visible."""
        await super().on_show()
        # Refresh the relationships list when returning to this screen
        await self._load_relationships()

    async def _load_relationships(self) -> None:
        """Load relationships data from the data service."""
        if not self.data_service:
            logger.warning("No data service available")
            return

        try:
            # Show loading indicator
            if self.loading_indicator:
                self.loading_indicator.display = True

            # Load relationships data (all relationships, not contact-specific)
            relationships = await self.data_service.get_relationships()
            self.relationships_data = relationships

            # Clear and populate table
            if self.relationships_table:
                self.relationships_table.clear()

                # Group relationships by type for better organization
                grouped_relationships = {}
                for relationship in relationships:
                    type_key = relationship.get("type_key", "unknown")
                    if type_key not in grouped_relationships:
                        grouped_relationships[type_key] = []
                    grouped_relationships[type_key].append(relationship)

                # Add relationships grouped by type
                for type_key in sorted(grouped_relationships.keys()):
                    relationships_of_type = grouped_relationships[type_key]

                    # Sort relationships within each type by person1 name
                    relationships_of_type.sort(key=lambda x: x.get("person1", "").lower())

                    for relationship in relationships_of_type:
                        # Format start date
                        start_date = "N/A"
                        if relationship.get("start_date"):
                            try:
                                if isinstance(relationship["start_date"], str):
                                    date_obj = datetime.fromisoformat(relationship["start_date"])
                                    start_date = date_obj.strftime("%Y-%m-%d")
                                elif hasattr(relationship["start_date"], "strftime"):
                                    # Handle datetime.date or datetime.datetime objects
                                    start_date = relationship["start_date"].strftime("%Y-%m-%d")
                                else:
                                    start_date = str(relationship["start_date"])
                            except (ValueError, AttributeError, TypeError):
                                start_date = (
                                    str(relationship["start_date"])
                                    if relationship["start_date"]
                                    else "N/A"
                                )

                        # Add row to table
                        self.relationships_table.add_row(
                            str(relationship.get("relationship_id", "")),  # Hidden ID column
                            relationship.get("person1", "Unknown"),
                            relationship.get("relationship_type", "Unknown"),
                            relationship.get("person2", "Unknown"),
                            start_date,
                            relationship.get("status", "Active"),
                            key=str(
                                relationship.get("relationship_id", "")
                            ),  # Use relationship ID as row key
                        )

            logger.info(f"Loaded {len(relationships)} relationships")

        except Exception as e:
            logger.error(f"Failed to load relationships: {e}")
            if self.notification_service:
                self.notification_service.show_error(f"Failed to load relationships: {e}")
        finally:
            # Hide loading indicator
            if self.loading_indicator:
                self.loading_indicator.display = False

    def _get_selected_relationship_id(self) -> Optional[int]:
        """Get the ID of the currently selected relationship."""
        if not self.relationships_table or self.relationships_table.cursor_row < 0:
            return None

        try:
            # Get the row key which is the relationship ID
            cursor_coordinate = self.relationships_table.coordinate_to_cell_key(
                self.relationships_table.cursor_coordinate
            )
            if cursor_coordinate.row_key:
                return int(cursor_coordinate.row_key.value)
            return None
        except (ValueError, AttributeError, TypeError):
            return None

    async def on_key(self, event: events.Key) -> None:
        """Handle key events for relationships screen."""
        key = event.key

        # Get selected relationship ID for operations that need it
        selected_id = self._get_selected_relationship_id()

        if key == "a":
            # Add new relationship
            await self._handle_add_relationship()
        elif key == "e":
            # Edit selected relationship
            if selected_id:
                await self._handle_edit_relationship(selected_id)
            else:
                if self.notification_service:
                    self.notification_service.show_warning("No relationship selected")
        elif key == "d":
            # Delete selected relationship
            if selected_id:
                await self._handle_delete_relationship(selected_id)
            else:
                if self.notification_service:
                    self.notification_service.show_warning("No relationship selected")
        elif key == "enter":
            # View relationship details
            if selected_id:
                await self._handle_view_relationship(selected_id)
            else:
                if self.notification_service:
                    self.notification_service.show_warning("No relationship selected")
        else:
            # Let parent handle other keys
            await super().on_key(event)

    async def _handle_add_relationship(self) -> None:
        """Handle add new relationship action."""
        logger.info("Add relationship requested")

        if self.notification_service:
            self.notification_service.show_info("Add relationship functionality coming soon")

    async def _handle_edit_relationship(self, relationship_id: int) -> None:
        """Handle edit relationship action."""
        logger.info(f"Edit relationship {relationship_id} requested")

        if self.notification_service:
            self.notification_service.show_info("Edit relationship functionality coming soon")

    async def _handle_delete_relationship(self, relationship_id: int) -> None:
        """Handle delete relationship action."""
        logger.info(f"Delete relationship {relationship_id} requested")

        # Find relationship details for confirmation dialog
        relationship_desc = "this relationship"
        for relationship in self.relationships_data:
            if relationship.get("relationship_id") == relationship_id:
                person1 = relationship.get("person1", "Unknown")
                person2 = relationship.get("person2", "Unknown")
                rel_type = relationship.get("relationship_type", "Unknown")
                relationship_desc = f"{person1} → {rel_type} → {person2}"
                break

        if self.notification_service:
            try:
                # Show confirmation dialog
                confirmed = await self.notification_service.show_delete_dialog(relationship_desc)

                if confirmed and self.data_service:
                    # Delete the relationship
                    success = await self.data_service.delete_relationship(relationship_id)

                    if success:
                        self.notification_service.show_success(f"Deleted {relationship_desc}")
                        # Reload the relationships list
                        await self._load_relationships()
                    else:
                        self.notification_service.show_error(
                            f"Failed to delete {relationship_desc}"
                        )

            except Exception as e:
                logger.error(f"Failed to delete relationship {relationship_id}: {e}")
                if self.notification_service:
                    self.notification_service.show_error("Failed to delete relationship")

    async def _handle_view_relationship(self, relationship_id: int) -> None:
        """Handle view relationship details action."""
        logger.info(f"View relationship {relationship_id} requested")

        if self.notification_service:
            self.notification_service.show_info(
                "View relationship details functionality coming soon"
            )


# Register this screen
register_screen("relationships", RelationshipsScreen)
