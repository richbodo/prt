"""Database management screen for PRT TUI.

Game-style backup/restore with slots.
"""

from datetime import datetime
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from textual import on
from textual.app import ComposeResult
from textual.containers import Container
from textual.containers import Horizontal
from textual.containers import Vertical
from textual.widgets import Button
from textual.widgets import DataTable
from textual.widgets import Label
from textual.widgets import Rule

from prt_src.logging_config import get_logger
from prt_src.tui.screens import register_screen
from prt_src.tui.screens.base import BaseScreen
from prt_src.tui.screens.base import EscapeIntent

logger = get_logger(__name__)


class DatabaseScreen(BaseScreen):
    """Database management screen."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._stats: Dict[str, Any] = {}
        self._backups: List[Dict[str, Any]] = []
        self._db_size: int = 0
        self._last_backup: Optional[str] = None

    def get_screen_name(self) -> str:
        """Get screen identifier."""
        return "database"

    def get_header_config(self) -> Optional[Dict[str, Any]]:
        """Get header configuration."""
        config = super().get_header_config()
        if config:
            config["title"] = "Database Management"
        return config

    def get_footer_config(self) -> dict:
        """Configure footer with database actions."""
        config = super().get_footer_config()
        if config:
            config["keyHints"] = [
                "[b]ackup",
                "[r]estore",
                "[e]xport",
                "[i]mport",
                "[v]acuum",
                "[ESC] Back",
            ]
        return config

    def on_escape(self) -> EscapeIntent:
        """Set ESC intent to POP as required."""
        return EscapeIntent.POP

    async def on_mount(self) -> None:
        """Load database statistics on mount."""
        await super().on_mount()
        await self._load_database_stats()

    async def on_show(self) -> None:
        """Refresh data when screen is shown."""
        await super().on_show()
        await self._load_database_stats()

    async def _load_database_stats(self) -> None:
        """Load database statistics and backup information."""
        if not self.data_service:
            return

        try:
            # Get database statistics
            self._stats = await self.data_service.get_database_stats()

            # Get database file size
            self._db_size = await self.data_service.get_database_size()

            # Get backup history
            self._backups = await self.data_service.get_backup_history()

            # Get last backup date
            if self._backups:
                self._last_backup = self._backups[0].get("created_at")
            else:
                self._last_backup = None

            # Update the statistics display
            self._update_stats_display()
            self._update_backups_display()

        except Exception as e:
            logger.error(f"Failed to load database stats: {e}")
            if self.notification_service:
                await self.notification_service.show_error(f"Failed to load database stats: {e}")

    def _update_stats_display(self) -> None:
        """Update the statistics display with current data."""
        stats_table = self.query_one("#stats-table", DataTable)
        stats_table.clear()

        # Check if columns need to be added
        if not hasattr(stats_table, "_columns_added") or not stats_table._columns_added:
            stats_table.add_column("Statistic", width=20)
            stats_table.add_column("Value", width=15)
            stats_table._columns_added = True

        # Format database size
        size_mb = self._db_size / (1024 * 1024) if self._db_size > 0 else 0
        size_str = f"{size_mb:.2f} MB" if size_mb > 0 else "Unknown"

        # Format last backup date
        backup_str = "Never"
        if self._last_backup:
            try:
                # Parse ISO format timestamp
                backup_date = datetime.fromisoformat(self._last_backup.replace("Z", "+00:00"))
                backup_str = backup_date.strftime("%Y-%m-%d %H:%M")
            except (ValueError, AttributeError):
                backup_str = str(self._last_backup)[:16]  # Truncate if needed

        stats_table.add_row("Total Contacts", str(self._stats.get("contacts", 0)))
        stats_table.add_row("Total Relationships", str(self._stats.get("relationships", 0)))
        stats_table.add_row("Total Notes", str(self._stats.get("notes", 0)))
        stats_table.add_row("Total Tags", str(self._stats.get("tags", 0)))
        stats_table.add_row("Database Size", size_str)
        stats_table.add_row("Last Backup", backup_str)

    def _update_backups_display(self) -> None:
        """Update the backups display with current data."""
        backups_table = self.query_one("#backups-table", DataTable)
        backups_table.clear()

        # Check if columns need to be added
        if not hasattr(backups_table, "_columns_added") or not backups_table._columns_added:
            backups_table.add_column("ID", width=5)
            backups_table.add_column("Date", width=18)
            backups_table.add_column("Comment", width=30)
            backups_table.add_column("Auto", width=6)
            backups_table._columns_added = True

        # Show recent backups (limit to 10)
        recent_backups = self._backups[:10]
        for backup in recent_backups:
            backup_id = str(backup.get("id", "N/A"))

            # Format date
            created_at = backup.get("created_at", "")
            if created_at:
                try:
                    backup_date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    date_str = backup_date.strftime("%Y-%m-%d %H:%M")
                except (ValueError, AttributeError):
                    date_str = str(created_at)[:16]
            else:
                date_str = "Unknown"

            comment = backup.get("comment", "No comment")[:28]
            if len(backup.get("comment", "")) > 28:
                comment += "..."

            is_auto = "Yes" if backup.get("is_auto", False) else "No"

            backups_table.add_row(backup_id, date_str, comment, is_auto)

    async def on_key(self, event) -> None:
        """Handle key presses for database actions."""
        if event.key == "b":
            await self._handle_backup()
        elif event.key == "r":
            await self._handle_restore()
        elif event.key == "e":
            await self._handle_export()
        elif event.key == "i":
            await self._handle_import()
        elif event.key == "v":
            await self._handle_vacuum()

    async def _handle_backup(self) -> None:
        """Handle creating a database backup."""
        if not self.data_service:
            return

        try:
            if self.notification_service:
                await self.notification_service.show_info("Creating database backup...")

            backup_info = await self.data_service.create_backup()

            if backup_info:
                if self.notification_service:
                    await self.notification_service.show_success(
                        f"Backup created successfully: {backup_info.get('filename', 'Unknown')}"
                    )
                await self._load_database_stats()  # Refresh display
            else:
                if self.notification_service:
                    await self.notification_service.show_error("Failed to create backup")

        except Exception as e:
            logger.error(f"Backup failed: {e}")
            if self.notification_service:
                await self.notification_service.show_error(f"Backup failed: {e}")

    async def _handle_restore(self) -> None:
        """Handle restoring from a backup."""
        if not self.data_service or not self._backups:
            if self.notification_service:
                await self.notification_service.show_warning("No backups available to restore from")
            return

        try:
            # For now, restore from the most recent backup
            # In a more advanced implementation, we could show a selection dialog
            backup_to_restore = self._backups[0]
            backup_id = backup_to_restore.get("id")

            if not backup_id:
                if self.notification_service:
                    await self.notification_service.show_error("Invalid backup ID")
                return

            if self.notification_service:
                await self.notification_service.show_info(f"Restoring from backup {backup_id}...")

            success = await self.data_service.restore_backup(backup_id)

            if success:
                if self.notification_service:
                    await self.notification_service.show_success("Database restored successfully")
                await self._load_database_stats()  # Refresh display
            else:
                if self.notification_service:
                    await self.notification_service.show_error("Failed to restore database")

        except Exception as e:
            logger.error(f"Restore failed: {e}")
            if self.notification_service:
                await self.notification_service.show_error(f"Restore failed: {e}")

    async def _handle_export(self) -> None:
        """Handle exporting data."""
        if not self.data_service:
            return

        try:
            if self.notification_service:
                await self.notification_service.show_info("Exporting database...")

            export_path = await self.data_service.export_data()

            if export_path:
                if self.notification_service:
                    await self.notification_service.show_success(f"Data exported to: {export_path}")
            else:
                if self.notification_service:
                    await self.notification_service.show_error("Failed to export data")

        except Exception as e:
            logger.error(f"Export failed: {e}")
            if self.notification_service:
                await self.notification_service.show_error(f"Export failed: {e}")

    async def _handle_import(self) -> None:
        """Handle importing data."""
        if self.notification_service:
            await self.notification_service.show_info("Import functionality not yet implemented")

    async def _handle_vacuum(self) -> None:
        """Handle database vacuum/optimization."""
        if not self.data_service:
            return

        try:
            if self.notification_service:
                await self.notification_service.show_info("Optimizing database...")

            success = await self.data_service.vacuum_database()

            if success:
                if self.notification_service:
                    await self.notification_service.show_success("Database optimized successfully")
                await self._load_database_stats()  # Refresh display
            else:
                if self.notification_service:
                    await self.notification_service.show_error("Failed to optimize database")

        except Exception as e:
            logger.error(f"Vacuum failed: {e}")
            if self.notification_service:
                await self.notification_service.show_error(f"Vacuum failed: {e}")

    def compose(self) -> ComposeResult:
        """Compose database screen layout."""
        yield Vertical(
            # Database Statistics Section
            Container(
                Label("Database Statistics", classes="section-title"),
                DataTable(id="stats-table", classes="stats-table"),
                classes="stats-section",
            ),
            Rule(),
            # Recent Backups Section
            Container(
                Label("Recent Backups", classes="section-title"),
                DataTable(id="backups-table", classes="backups-table"),
                classes="backups-section",
            ),
            Rule(),
            # Action Buttons
            Container(
                Label("Actions", classes="section-title"),
                Horizontal(
                    Button("Create Backup (b)", id="backup-btn", variant="primary"),
                    Button("Restore (r)", id="restore-btn", variant="default"),
                    Button("Export (e)", id="export-btn", variant="default"),
                    Button("Vacuum (v)", id="vacuum-btn", variant="default"),
                    classes="action-buttons",
                ),
                classes="actions-section",
            ),
            classes="database-container",
        )

    @on(Button.Pressed, "#backup-btn")
    async def backup_pressed(self) -> None:
        """Handle backup button press."""
        await self._handle_backup()

    @on(Button.Pressed, "#restore-btn")
    async def restore_pressed(self) -> None:
        """Handle restore button press."""
        await self._handle_restore()

    @on(Button.Pressed, "#export-btn")
    async def export_pressed(self) -> None:
        """Handle export button press."""
        await self._handle_export()

    @on(Button.Pressed, "#vacuum-btn")
    async def vacuum_pressed(self) -> None:
        """Handle vacuum button press."""
        await self._handle_vacuum()


# Register this screen
register_screen("database", DatabaseScreen)
