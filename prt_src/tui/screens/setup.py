"""Setup screen for first-run or forced setup mode."""

from pathlib import Path
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static

from prt_src.api import PRTAPI
from prt_src.logging_config import get_logger
from prt_src.tui.screens.base import BaseScreen
from prt_src.tui.screens.home import HomeScreen
from prt_src.tui.services.fixture import FixtureService
from prt_src.tui.services.google_takeout import GoogleTakeoutService
from prt_src.tui.widgets.file_selection import FileSelectionWidget

logger = get_logger(__name__)


class SetupScreen(BaseScreen):
    """Setup screen for importing contacts or loading fixtures.

    Shown when:
    - Database has no contacts (empty DB)
    - --setup flag is used

    Options:
    - Press '1': Import from Google Takeout
    - Press '2': Load Demo Data (fixtures)
    - Press 'q': Quit application
    """

    CSS = """
    SetupScreen {
        align: center middle;
    }

    #setup-container {
        width: 70;
        height: auto;
        border: thick $primary;
        padding: 2 4;
    }

    #setup-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    #setup-subtitle {
        text-align: center;
        color: $text-muted;
        margin-bottom: 2;
    }

    .setup-option {
        margin: 1 0;
        padding: 1 2;
        background: $surface;
        border: solid $primary;
    }

    .setup-option-key {
        text-style: bold;
        color: $accent;
    }

    #setup-status {
        margin-top: 2;
        text-align: center;
        color: $warning;
    }

    #setup-error {
        margin-top: 1;
        text-align: center;
        color: $error;
    }
    """

    def __init__(self, **kwargs):
        """Initialize Setup screen."""
        super().__init__(**kwargs)
        self.screen_title = "SETUP"
        self._api: Optional[PRTAPI] = None
        self._takeout_service: Optional[GoogleTakeoutService] = None
        self._fixture_service: Optional[FixtureService] = None
        self._status_widget: Optional[Static] = None
        self._error_widget: Optional[Static] = None
        self._wait_for_keypress: bool = False
        self._navigation_pending: str = ""
        self._file_selection_widget: Optional[FileSelectionWidget] = None
        self._pending_files: list = []  # Files waiting for user selection

    def compose(self) -> ComposeResult:
        """Compose the setup screen layout."""
        with Container(id="setup-container"):
            yield Static("Welcome to PRT!", id="setup-title")
            yield Static("Let's set up your contacts.", id="setup-subtitle")

            # Option 1: Import
            with Container(classes="setup-option"):
                yield Static(
                    "[1] Import from Google Takeout\n"
                    "    → Import your real contacts from Google",
                    markup=True,
                )

            # Option 2: Fixtures
            with Container(classes="setup-option"):
                yield Static(
                    "[2] Load Demo Data (Fixtures)\n"
                    "    → Try PRT with 7 sample contacts (safe - uses isolated database)",
                    markup=True,
                )

            # Option q: Quit
            with Container(classes="setup-option"):
                yield Static("[q] Quit", markup=True)

            # Status and error messages
            self._status_widget = Static("", id="setup-status")
            yield self._status_widget

            self._error_widget = Static("", id="setup-error")
            yield self._error_widget

    async def on_mount(self) -> None:
        """Handle screen mount - initialize services."""
        await super().on_mount()
        logger.info("Setup screen mounted")

        # Initialize services
        try:
            self._api = self.data_service.api if self.data_service else PRTAPI()
            self._takeout_service = GoogleTakeoutService(self._api)

            # Get database from data_service if available
            if hasattr(self.data_service, "api") and hasattr(self.data_service.api, "db"):
                db = self.data_service.api.db
                self._fixture_service = FixtureService(db)
            else:
                logger.warning("Could not access database for fixture service")
        except Exception as e:
            logger.error(f"Error initializing setup services: {e}", exc_info=True)
            self._show_error(f"Setup error: {e}")

    def on_key(self, event) -> None:
        """Handle key presses.

        Args:
            event: Key event
        """
        key = event.key.lower()
        logger.info(f"[SETUP] Key pressed: '{key}'")

        # If waiting for keypress after success, any key continues
        if self._wait_for_keypress:
            logger.info("[SETUP] User pressed key to continue after success")
            self._wait_for_keypress = False
            if self._navigation_pending == "home":
                self._navigate_to_home()
            event.prevent_default()
            return

        # Normal menu handling
        if key == "1":
            logger.info("[SETUP] User selected: Import from Google Takeout")
            self.app.call_later(self._handle_import_takeout)
            event.prevent_default()
        elif key == "2":
            logger.info("[SETUP] User selected: Load Demo Data")
            self.app.call_later(self._handle_load_fixtures)
            event.prevent_default()
        elif key == "q":
            logger.info("[SETUP] User selected: Quit")
            self.app.exit()
            event.prevent_default()

    async def _handle_import_takeout(self) -> None:
        """Handle Google Takeout import workflow."""
        files = []  # Initialize to prevent NameError in exception handler
        try:
            self._show_status("🔍 Searching for takeout files...")
            logger.info("[SETUP] Searching for takeout files")

            # Find takeout files
            files = await self._takeout_service.find_takeout_files()

            if not files:
                self._show_error(
                    "No takeout files found.\n\n" + self._takeout_service.get_search_instructions()
                )
                return

            # If multiple files, show selection widget
            if len(files) > 1:
                logger.info(f"[SETUP] Found {len(files)} files, showing selection widget")
                self._show_file_selection(files)
                return  # Wait for user selection

            # Single file - use it directly
            file_path = files[0]
            logger.info(f"[SETUP] Found 1 file: {file_path}")

            # Continue with import
            await self._continue_import_with_file(file_path)

        except Exception as e:
            logger.error(f"[SETUP] Error in import workflow: {e}", exc_info=True)
            # file_path might not be defined if error occurred during file search
            file_path_for_error = files[0] if files else None
            detailed_error = self._build_detailed_error(str(e), file_path_for_error, e)
            self._show_error(detailed_error)

    async def _handle_load_fixtures(self) -> None:
        """Handle fixture loading workflow with isolated database."""
        try:
            self._show_status("📊 Preparing demo data...")
            logger.info("[SETUP] Setting up isolated fixture database")

            # Get fixture summary for preview
            from prt_src.fixture_manager import get_fixture_summary

            summary = get_fixture_summary()
            self._show_status(
                f"Demo data includes:\n"
                f"• {summary['contacts']} contacts\n"
                f"• {summary['tags']} tags\n"
                f"• {summary['notes']} notes\n"
                f"• Profile images included\n\n"
                "✅ Your real data is safe - using isolated database.\n"
                "💾 Setting up demo database..."
            )

            # Create isolated fixture database (does not touch real data)
            from prt_src.fixture_manager import setup_fixture_mode

            fixture_config = await self._run_in_executor(
                setup_fixture_mode, True, True
            )  # regenerate=True, quiet=True

            if fixture_config:
                # Update the app to use the fixture database
                await self._update_app_with_fixture_config(fixture_config)

                # Build success summary
                summary_text = self._build_fixture_success_summary(summary)
                self._show_status(summary_text)

                # Wait for user keypress before navigating
                self._wait_for_keypress = True
                self._navigation_pending = "home"
                logger.info(
                    "[SETUP] Fixture database created successfully, waiting for user keypress"
                )
            else:
                self._show_error("Failed to create fixture database")
                logger.error("[SETUP] Failed to create fixture database")

        except Exception as e:
            logger.error(f"[SETUP] Error setting up fixture database: {e}", exc_info=True)
            detailed_error = self._build_detailed_error(str(e), exception=e)
            self._show_error(detailed_error)

    def _show_file_selection(self, files: list) -> None:
        """Show file selection widget for multiple takeout files.

        Args:
            files: List of file paths to choose from
        """
        logger.info(f"[SETUP] Showing file selection widget with {len(files)} files")

        # Hide status/error messages
        self._show_status("")
        self._show_error("")

        # Create and mount the file selection widget
        self._file_selection_widget = FileSelectionWidget(
            files=files,
            title=f"Found {len(files)} Google Takeout files",
        )
        self._pending_files = files

        # Mount the widget to the screen
        container = self.query_one("#setup-container", Container)
        container.mount(self._file_selection_widget)
        self._file_selection_widget.focus()

        logger.info("[SETUP] File selection widget mounted and focused")

    def on_file_selection_widget_file_selected(
        self, message: FileSelectionWidget.FileSelected
    ) -> None:
        """Handle file selection from the widget.

        Args:
            message: FileSelected message with the chosen file path
        """
        logger.info(f"[SETUP] File selected: {message.file_path.name}")

        # Remove the selection widget
        if self._file_selection_widget:
            self._file_selection_widget.dismiss()
            self._file_selection_widget = None

        # Continue with import using selected file
        self.app.call_later(self._continue_import_with_file, message.file_path)

    def on_file_selection_widget_selection_cancelled(
        self, message: FileSelectionWidget.SelectionCancelled
    ) -> None:
        """Handle cancellation of file selection.

        Args:
            message: SelectionCancelled message
        """
        logger.info("[SETUP] File selection cancelled")

        # Remove the selection widget
        if self._file_selection_widget:
            self._file_selection_widget.dismiss()
            self._file_selection_widget = None

        # Show the main menu again
        self._show_status("")
        self._show_error("")
        self._pending_files = []

    async def _continue_import_with_file(self, file_path: Path) -> None:
        """Continue the import workflow with the selected file.

        Args:
            file_path: Path to the selected takeout file
        """
        try:
            logger.info(f"[SETUP] Continuing import with: {file_path}")

            # Validate
            self._show_status(f"✓ Validating {file_path.name}...")
            is_valid, message = await self._takeout_service.validate_file(file_path)

            if not is_valid:
                self._show_error(f"Invalid file: {message}")
                return

            # Get preview
            self._show_status("📊 Getting preview...")
            preview = await self._takeout_service.get_preview(file_path)

            if not preview.get("valid"):
                self._show_error(f"Error reading file: {preview.get('error')}")
                return

            # Show preview and import
            contact_count = preview.get("contact_count", 0)
            image_count = preview.get("contacts_with_images", 0)
            self._show_status(
                f"✓ Found {contact_count} contacts ({image_count} with images)\n" "💾 Importing..."
            )

            # Import
            success, msg, info = await self._takeout_service.import_contacts(file_path)

            if success:
                # Build detailed success summary
                summary = self._build_import_summary(info)
                self._show_status(summary)

                # Wait for user keypress before navigating
                self._wait_for_keypress = True
                self._navigation_pending = "home"
                logger.info("[SETUP] Import successful, waiting for user keypress")
            else:
                # Show detailed error with debug info
                detailed_error = self._build_detailed_error(msg, file_path)
                self._show_error(detailed_error)
                logger.error(f"[SETUP] Import failed: {msg}")

        except Exception as e:
            logger.error(f"[SETUP] Error continuing import: {e}", exc_info=True)
            detailed_error = self._build_detailed_error(str(e), file_path, e)
            self._show_error(detailed_error)

    def _build_import_summary(self, info: dict) -> str:
        """Build detailed import summary message.

        Args:
            info: Import info dictionary from GoogleTakeoutService

        Returns:
            Formatted summary string
        """
        from pathlib import Path

        lines = [
            "✅ Successfully imported contacts!",
            "",
            "📊 Import Summary:",
            f"  • Total contacts: {info.get('contact_count', 0):,}",
        ]

        # Add image info if available
        if info.get("contacts_with_images"):
            image_count = info["contacts_with_images"]
            total = info.get("contact_count", 1)
            percentage = (image_count / total * 100) if total > 0 else 0
            lines.append(f"  • With profile images: {image_count} ({percentage:.0f}%)")

        # Add deduplication info if available
        if info.get("duplicates_removed", 0) > 0:
            lines.append(f"  • De-duplicated: {info['duplicates_removed']} contacts")

        # Add timing info if available
        if info.get("total_time"):
            lines.append(f"  • Import time: {info['total_time']:.1f}s")

        # Add source file
        if info.get("source_file"):
            lines.append("")
            lines.append(f"📁 Source: {Path(info['source_file']).name}")

        lines.extend(["", "━" * 44, "", "Press any key to continue to home screen"])

        return "\n".join(lines)

    def _build_fixture_summary(self, result: dict) -> str:
        """Build detailed fixture load summary message.

        Args:
            result: Result dictionary from FixtureService

        Returns:
            Formatted summary string
        """
        lines = [
            "✅ Successfully loaded demo data!",
            "",
            "📊 Load Summary:",
            f"  • Total contacts: {result.get('contacts', 0)}",
            f"  • Tags: {result.get('tags', 0)}",
            f"  • Notes: {result.get('notes', 0)}",
            "  • Profile images: Included",
        ]

        # Add timing info if available
        if result.get("total_time"):
            lines.append(f"  • Load time: {result['total_time']:.1f}s")

        lines.extend(["", "━" * 44, "", "Press any key to continue to home screen"])

        return "\n".join(lines)

    def _build_detailed_error(
        self, error: str, file_path: Optional["Path"] = None, exception: Optional[Exception] = None
    ) -> str:
        """Build detailed error message with debug info.

        Args:
            error: Main error message
            file_path: Optional path to file that caused error
            exception: Optional exception object

        Returns:
            Formatted error string with debug info
        """

        lines = [
            "❌ Operation Failed",
            "",
            f"Error: {error}",
        ]

        # Add debug information if file_path provided
        if file_path:
            lines.extend(
                [
                    "",
                    "🔍 Debug Information:",
                    f"  File: {file_path.name}",
                    f"  Location: {file_path.parent}",
                ]
            )

            if file_path.exists():
                file_size_mb = file_path.stat().st_size / 1024 / 1024
                lines.append(f"  Size: {file_size_mb:.1f} MB")
            else:
                lines.append("  Status: File not found")

        # Add troubleshooting tips
        troubleshooting = self._get_troubleshooting_tips(error, exception)
        if troubleshooting:
            lines.extend(
                [
                    "",
                    "📋 Troubleshooting:",
                ]
            )
            for i, tip in enumerate(troubleshooting, 1):
                lines.append(f"  {i}. {tip}")

        # Add log file reference
        lines.extend(
            [
                "",
                "📄 Full error log:",
                "  prt_data/prt.log",
            ]
        )

        # Add navigation options
        lines.extend(["", "Press 2 to load demo data  |  Press q to quit"])

        return "\n".join(lines)

    def _get_troubleshooting_tips(self, error: str, exception: Optional[Exception] = None) -> list:
        """Get context-specific troubleshooting tips.

        Args:
            error: Error message
            exception: Optional exception object

        Returns:
            List of troubleshooting tips
        """
        error_lower = error.lower()

        if "zip" in error_lower or "invalid" in error_lower:
            return [
                "Verify you downloaded 'Contacts' only from Google Takeout",
                "Check the zip file isn't corrupted",
                "Ensure it's from takeout.google.com, not another service",
            ]
        elif "permission" in error_lower or "access" in error_lower:
            return [
                "Check file permissions on the zip file",
                "Try moving the file to ~/Downloads",
                "Ensure PRT has read access to the file",
            ]
        elif "no contacts" in error_lower or "empty" in error_lower:
            return [
                "The zip file might be empty or incorrectly structured",
                "Re-download from Google Takeout",
                "Select 'Contacts' in the export options",
            ]
        elif "database" in error_lower:
            return [
                "Check database file permissions",
                "Ensure enough disk space is available",
                "Try clearing the database and reloading",
            ]
        else:
            return [
                "Check the log file for detailed error information",
                "Try a different takeout file or fixture data",
                "Report this issue on GitHub if it persists",
            ]

    def _navigate_to_home(self) -> None:
        """Navigate to home screen."""
        logger.info("[SETUP] Navigating to home screen")
        self.app.push_screen(HomeScreen())

    def _show_status(self, message: str) -> None:
        """Show status message."""
        if self._status_widget:
            self._status_widget.update(message)
        if self._error_widget:
            self._error_widget.update("")

    def _show_error(self, message: str) -> None:
        """Show error message."""
        if self._error_widget:
            self._error_widget.update(message)
        if self._status_widget:
            self._status_widget.update("")

    async def _run_in_executor(self, func, *args):
        """Run a function in an executor to prevent blocking."""
        import asyncio

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args)

    async def _update_app_with_fixture_config(self, fixture_config: dict) -> None:
        """Update the app to use the fixture database configuration."""
        try:
            logger.info(f"[SETUP] Updating app with fixture config: {fixture_config}")

            # Update the data service if available
            if hasattr(self, "data_service") and self.data_service:
                logger.info("[SETUP] Updating data service with fixture database")
                # Create new API instance with fixture config
                from prt_src.api import PRTAPI

                new_api = PRTAPI(fixture_config)

                # Update the data service
                self.data_service.api = new_api
                logger.info("[SETUP] Data service updated successfully")

            # Update the app's configuration
            if hasattr(self.app, "config"):
                self.app.config = fixture_config
                logger.info("[SETUP] App configuration updated")

        except Exception as e:
            logger.error(f"[SETUP] Error updating app with fixture config: {e}", exc_info=True)
            raise

    def _build_fixture_success_summary(self, summary: dict) -> str:
        """Build fixture loading success summary."""
        lines = [
            "✅ Successfully set up demo database!",
            "",
            "📊 Demo Data Summary:",
            f"  • Total contacts: {summary.get('contacts', 0)}",
            f"  • Tags: {summary.get('tags', 0)}",
            f"  • Notes: {summary.get('notes', 0)}",
            "  • Profile images: Included",
            "",
            "🔒 Data Safety:",
            "  • Your real data is completely safe",
            "  • Demo data uses isolated database",
            "  • Next restart returns to your real data",
            "",
            "━" * 44,
            "",
            "Press any key to continue to home screen",
        ]
        return "\n".join(lines)
