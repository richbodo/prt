"""Import screen for PRT TUI.

Handles importing contacts from Google Takeout zip files.
"""

import asyncio
from pathlib import Path
from typing import Any, Dict, Optional

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Input, Label, ProgressBar, Rule, Static

from prt_src.google_takeout import GoogleTakeoutParser, parse_takeout_contacts
from prt_src.logging_config import get_logger
from prt_src.tui.screens import register_screen
from prt_src.tui.screens.base import BaseScreen, EscapeIntent

logger = get_logger(__name__)


class ImportScreen(BaseScreen):
    """Import screen for Google Takeout contacts."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._import_path: Optional[str] = None
        self._preview_info: Optional[Dict[str, Any]] = None
        self._import_complete: bool = False
        self._import_results: Optional[Dict[str, Any]] = None
        self._is_importing: bool = False

    def get_screen_name(self) -> str:
        """Get screen identifier."""
        return "import"

    def get_header_config(self) -> Optional[Dict[str, Any]]:
        """Get header configuration."""
        config = super().get_header_config()
        if config:
            config["title"] = "Import Contacts"
        return config

    def get_footer_config(self) -> dict:
        """Configure footer with import actions."""
        config = super().get_footer_config()
        if config:
            if self._is_importing:
                config["keyHints"] = ["Import in progress..."]
            elif self._import_complete:
                config["keyHints"] = ["[h]ome", "[c]ontacts", "[ESC] Back"]
            else:
                config["keyHints"] = ["[i]mport", "[p]review", "[ESC] Back"]
        return config

    def on_escape(self) -> EscapeIntent:
        """Handle ESC key - prevent exit during import."""
        if self._is_importing:
            return EscapeIntent.CUSTOM
        return EscapeIntent.POP

    def handle_custom_escape(self) -> None:
        """Custom ESC handler - show message if import in progress."""
        if self._is_importing:
            if self.notification_service:
                self.notification_service.info("Import in progress, please wait...")

    def compose(self) -> ComposeResult:
        """Compose import screen layout."""
        with Vertical(classes="import-container"):
            # Title
            yield Static("📥 Import Contacts from Google Takeout", classes="import-title")

            # File selection section
            with Container(classes="file-section"):
                yield Label("Google Takeout ZIP File:", classes="section-label")
                with Horizontal(classes="file-input-container"):
                    yield Input(
                        placeholder="/path/to/takeout-file.zip",
                        id="file-path-input",
                        classes="file-path-input",
                    )
                    yield Button("Browse", id="browse-button", classes="browse-button")

                # File validation status
                yield Static("", id="file-status", classes="file-status")

            yield Rule()

            # Preview section (initially hidden)
            with Container(id="preview-section", classes="preview-section"):
                yield Label("Preview:", classes="section-label")
                yield Static("", id="preview-info", classes="preview-info")

                with Horizontal(classes="preview-actions"):
                    yield Button("Import Contacts", id="import-button", variant="primary")
                    yield Button("Clear", id="clear-button", variant="error")

            yield Rule()

            # Import progress section (initially hidden)
            with Container(id="progress-section", classes="progress-section"):
                yield Label("Import Progress:", classes="section-label")
                yield ProgressBar(id="import-progress", show_percentage=False)
                yield Static("", id="progress-status", classes="progress-status")

            yield Rule()

            # Results section (initially hidden)
            with Container(id="results-section", classes="results-section"):
                yield Label("Import Results:", classes="section-label")
                yield Static("", id="results-summary", classes="results-summary")
                yield Static("", id="results-details", classes="results-details")

                with Horizontal(classes="results-actions"):
                    yield Button("View Contacts", id="view-contacts-button", variant="primary")
                    yield Button("Import Another", id="import-another-button")
                    yield Button("Home", id="home-button")

    async def on_mount(self) -> None:
        """Initialize screen state."""
        await super().on_mount()
        self._hide_sections()

    def _hide_sections(self) -> None:
        """Hide conditional sections initially."""
        self.query_one("#preview-section").display = False
        self.query_one("#progress-section").display = False
        self.query_one("#results-section").display = False

    @on(Input.Changed, "#file-path-input")
    async def on_file_path_changed(self, event: Input.Changed) -> None:
        """Handle file path input changes."""
        file_path = event.value.strip()
        if not file_path:
            self._clear_preview()
            return

        # Validate file path
        try:
            path = Path(file_path)
            if not path.exists():
                self._show_file_status("❌ File does not exist", "error")
                self._clear_preview()
                return

            if not path.is_file():
                self._show_file_status("❌ Path is not a file", "error")
                self._clear_preview()
                return

            if not path.suffix.lower() == ".zip":
                self._show_file_status("⚠️ File should be a ZIP archive", "warning")
            else:
                self._show_file_status("✅ File found", "success")

            self._import_path = str(path)
            await self._validate_takeout_file()

        except Exception as e:
            logger.error(f"Error validating file path: {e}")
            self._show_file_status(f"❌ Error: {e}", "error")
            self._clear_preview()

    def _show_file_status(self, message: str, status_type: str) -> None:
        """Show file validation status."""
        status_widget = self.query_one("#file-status")
        status_widget.update(message)
        status_widget.remove_class("success", "warning", "error")
        status_widget.add_class(status_type)

    async def _validate_takeout_file(self) -> None:
        """Validate and preview Google Takeout file."""
        if not self._import_path:
            return

        try:
            # Show loading status
            self._show_file_status("🔍 Analyzing file...", "info")

            # Parse takeout file for preview
            parser = GoogleTakeoutParser(Path(self._import_path))
            self._preview_info = parser.get_preview_info()

            if not self._preview_info["valid"]:
                self._show_file_status(f"❌ {self._preview_info['error']}", "error")
                self._clear_preview()
                return

            # Show success and enable preview
            self._show_file_status("✅ Valid Google Takeout file", "success")
            self._show_preview()

        except Exception as e:
            logger.error(f"Error validating takeout file: {e}")
            self._show_file_status(f"❌ Error analyzing file: {e}", "error")
            self._clear_preview()

    def _show_preview(self) -> None:
        """Show file preview information."""
        if not self._preview_info:
            return

        preview_widget = self.query_one("#preview-info")

        # Format preview information
        contact_count = self._preview_info.get("contact_count", 0)
        image_count = self._preview_info.get("image_count", 0)
        contacts_with_images = self._preview_info.get("contacts_with_images", 0)

        preview_text = f"""📊 Found {contact_count} contacts and {image_count} profile images
👤 {contacts_with_images} contacts have profile images

Sample contacts:"""

        sample_contacts = self._preview_info.get("sample_contacts", [])
        for contact in sample_contacts[:5]:  # Show first 5
            name = contact.get("name", "Unknown")
            has_image = "📷" if contact.get("has_image") else "👤"
            preview_text += f"\n  {has_image} {name}"

        if len(sample_contacts) > 5:
            preview_text += f"\n  ... and {len(sample_contacts) - 5} more"

        preview_widget.update(preview_text)
        self.query_one("#preview-section").display = True

    def _clear_preview(self) -> None:
        """Clear preview section."""
        self.query_one("#preview-section").display = False
        self._preview_info = None

    @on(Button.Pressed, "#browse-button")
    def on_browse_pressed(self, event: Button.Pressed) -> None:
        """Handle browse button press - simulate file dialog."""
        if self.notification_service:
            self.notification_service.info("Enter the full path to your Google Takeout ZIP file")

        # Focus the input field
        input_widget = self.query_one("#file-path-input")
        input_widget.focus()

    @on(Button.Pressed, "#import-button")
    async def on_import_pressed(self, event: Button.Pressed) -> None:
        """Handle import button press."""
        if not self._import_path or not self._preview_info:
            if self.notification_service:
                self.notification_service.error("Please select a valid Google Takeout file first")
            return

        await self._perform_import()

    @on(Button.Pressed, "#clear-button")
    def on_clear_pressed(self, event: Button.Pressed) -> None:
        """Handle clear button press."""
        self._clear_import_state()

    @on(Button.Pressed, "#view-contacts-button")
    async def on_view_contacts_pressed(self, event: Button.Pressed) -> None:
        """Navigate to contacts screen."""
        if self.nav_service:
            self.nav_service.push("contacts")
            await self.app.switch_screen("contacts")

    @on(Button.Pressed, "#import-another-button")
    def on_import_another_pressed(self, event: Button.Pressed) -> None:
        """Reset for another import."""
        self._clear_import_state()

    @on(Button.Pressed, "#home-button")
    async def on_home_button_pressed(self, event: Button.Pressed) -> None:
        """Navigate to home screen."""
        if self.nav_service:
            self.nav_service.push("home")
            await self.app.switch_screen("home")

    def _clear_import_state(self) -> None:
        """Clear all import state and reset UI."""
        self._import_path = None
        self._preview_info = None
        self._import_complete = False
        self._import_results = None
        self._is_importing = False

        # Clear input
        self.query_one("#file-path-input").value = ""

        # Hide sections
        self._hide_sections()

        # Clear status
        self.query_one("#file-status").update("")

    async def _perform_import(self) -> None:
        """Perform the actual import operation."""
        if not self._import_path or not self.data_service:
            return

        self._is_importing = True

        try:
            # Show progress section
            self.query_one("#progress-section").display = True
            self.query_one("#preview-section").display = False

            progress_bar = self.query_one("#import-progress", ProgressBar)
            status_widget = self.query_one("#progress-status")

            # Update progress: Step 1 - Parsing
            progress_bar.advance(20)
            status_widget.update("📖 Parsing Google Takeout file...")
            await asyncio.sleep(0.1)  # Allow UI to update

            # Parse contacts from takeout file
            contacts, import_info = parse_takeout_contacts(Path(self._import_path))

            if import_info.get("error"):
                raise Exception(import_info["error"])

            # Update progress: Step 2 - Processing
            progress_bar.advance(30)
            status_widget.update("⚙️ Processing contact data...")
            await asyncio.sleep(0.1)

            # Convert contacts to format expected by data service
            processed_contacts = []
            for contact in contacts:
                processed_contact = {
                    "first_name": contact.get("first", ""),
                    "last_name": contact.get("last", ""),
                    "email": contact.get("emails", [None])[0] if contact.get("emails") else None,
                    "phone": contact.get("phones", [None])[0] if contact.get("phones") else None,
                    "profile_image": contact.get("profile_image"),
                    "profile_image_filename": contact.get("profile_image_filename"),
                    "profile_image_mime_type": contact.get("profile_image_mime_type"),
                }
                processed_contacts.append(processed_contact)

            # Update progress: Step 3 - Importing
            progress_bar.advance(30)
            status_widget.update("💾 Importing contacts to database...")
            await asyncio.sleep(0.1)

            # Import contacts via data service API
            success = self.data_service.api.insert_contacts(processed_contacts)

            if not success:
                raise Exception("Failed to import contacts to database")

            # Update progress: Complete
            progress_bar.advance(20)
            status_widget.update("✅ Import completed successfully!")

            # Store results
            self._import_results = {
                "success": True,
                "contacts_imported": len(processed_contacts),
                "contacts_with_images": len([c for c in contacts if c.get("profile_image")]),
                "duplicates_removed": import_info.get("duplicates_removed", 0),
                "total_processed": import_info.get("raw_contact_count", len(processed_contacts)),
                "errors": 0,
            }

            # Show results
            self._show_import_results()

        except Exception as e:
            logger.error(f"Import failed: {e}")

            # Show error
            status_widget.update(f"❌ Import failed: {e}")

            self._import_results = {
                "success": False,
                "error": str(e),
                "contacts_imported": 0,
                "contacts_with_images": 0,
                "duplicates_removed": 0,
                "total_processed": 0,
                "errors": 1,
            }

            self._show_import_results()

            if self.notification_service:
                self.notification_service.error(f"Import failed: {e}")

        finally:
            self._is_importing = False
            self._import_complete = True

    def _show_import_results(self) -> None:
        """Show import results."""
        if not self._import_results:
            return

        # Hide progress, show results
        self.query_one("#progress-section").display = False
        self.query_one("#results-section").display = True

        results = self._import_results
        summary_widget = self.query_one("#results-summary")
        details_widget = self.query_one("#results-details")

        if results["success"]:
            # Success summary
            summary_text = "✅ Import completed successfully!"

            # Detailed results
            details_text = f"""📊 Import Summary:
• {results['contacts_imported']} contacts imported
• {results['contacts_with_images']} contacts with profile images
• {results['duplicates_removed']} duplicates removed
• {results['total_processed']} total contacts processed"""

            if self.notification_service:
                self.notification_service.success(
                    f"Successfully imported {results['contacts_imported']} contacts!"
                )

        else:
            # Error summary
            summary_text = "❌ Import failed"
            details_text = f"Error: {results.get('error', 'Unknown error occurred')}"

        summary_widget.update(summary_text)
        details_widget.update(details_text)


# Register this screen
register_screen("import", ImportScreen)
