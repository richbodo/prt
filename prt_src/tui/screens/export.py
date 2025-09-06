"""Export screen for PRT TUI.

Handles exporting data in various formats and creating directory visualizations.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
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
from textual.widgets import Checkbox
from textual.widgets import Input
from textual.widgets import Label
from textual.widgets import ProgressBar
from textual.widgets import RadioButton
from textual.widgets import RadioSet
from textual.widgets import Rule
from textual.widgets import Static

from prt_src.logging_config import get_logger
from prt_src.tui.screens import register_screen
from prt_src.tui.screens.base import BaseScreen
from prt_src.tui.screens.base import EscapeIntent

logger = get_logger(__name__)


class ExportScreen(BaseScreen):
    """Export screen for data and directory generation."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._export_complete: bool = False
        self._export_results: Optional[Dict[str, Any]] = None
        self._is_exporting: bool = False
        self._current_search_results: Optional[List[Dict[str, Any]]] = None
        self._available_tags: List[str] = []

    def get_screen_name(self) -> str:
        """Get screen identifier."""
        return "export"

    def get_header_config(self) -> Optional[Dict[str, Any]]:
        """Get header configuration."""
        config = super().get_header_config()
        if config:
            config["title"] = "Export Data"
        return config

    def get_footer_config(self) -> dict:
        """Configure footer with export actions."""
        config = super().get_footer_config()
        if config:
            if self._is_exporting:
                config["keyHints"] = ["Export in progress..."]
            elif self._export_complete:
                config["keyHints"] = ["[o]pen folder", "[e]xport another", "[ESC] Back"]
            else:
                config["keyHints"] = ["[e]xport", "[ESC] Back"]
        return config

    def on_escape(self) -> EscapeIntent:
        """Handle ESC key - prevent exit during export."""
        if self._is_exporting:
            return EscapeIntent.CUSTOM
        return EscapeIntent.POP

    def handle_custom_escape(self) -> None:
        """Custom ESC handler - show message if export in progress."""
        if self._is_exporting:
            if self.notification_service:
                self.notification_service.info("Export in progress, please wait...")

    def compose(self) -> ComposeResult:
        """Compose export screen layout."""
        with Vertical(classes="export-container"):
            # Title
            yield Static("📤 Export Data", classes="export-title")

            # Format selection section
            with Container(classes="format-section"):
                yield Label("Export Format:", classes="section-label")
                with RadioSet(id="format-selection", classes="format-selection"):
                    yield RadioButton(
                        "JSON - Structured data with full details", value=True, id="format-json"
                    )
                    yield RadioButton("CSV - Spreadsheet-compatible tabular data", id="format-csv")
                    yield RadioButton(
                        "HTML Directory - Interactive contact visualization", id="format-html"
                    )

            yield Rule()

            # Scope selection section
            with Container(classes="scope-section"):
                yield Label("Export Scope:", classes="section-label")
                with RadioSet(id="scope-selection", classes="scope-selection"):
                    yield RadioButton("All contacts", value=True, id="scope-all")
                    yield RadioButton("Current search results (if available)", id="scope-search")
                    yield RadioButton("Contacts filtered by tag", id="scope-tag")

                # Tag selection (initially hidden)
                with Container(id="tag-selection-container", classes="tag-selection-container"):
                    yield Label("Select Tag:", classes="sub-label")
                    yield Input(
                        placeholder="Enter tag name...", id="tag-input", classes="tag-input"
                    )
                    yield Static("", id="tag-status", classes="tag-status")

            yield Rule()

            # Options section
            with Container(classes="options-section"):
                yield Label("Export Options:", classes="section-label")
                with Vertical(classes="options-list"):
                    yield Checkbox("Include profile images", value=True, id="include-images")
                    yield Checkbox(
                        "Generate directory visualization (HTML format only)",
                        value=True,
                        id="generate-directory",
                    )
                    yield Checkbox(
                        "Include relationship data", value=True, id="include-relationships"
                    )
                    yield Checkbox("Include notes and tags", value=True, id="include-metadata")

            yield Rule()

            # Output path section
            with Container(classes="output-section"):
                yield Label("Output Location:", classes="section-label")
                with Horizontal(classes="output-input-container"):
                    yield Input(
                        placeholder="/path/to/export/directory",
                        id="output-path-input",
                        classes="output-path-input",
                    )
                    yield Button("Browse", id="output-browse-button", classes="browse-button")

                with Horizontal(classes="export-actions"):
                    yield Button("Export Data", id="export-button", variant="primary")
                    yield Button("Reset", id="reset-button", variant="error")

            yield Rule()

            # Progress section (initially hidden)
            with Container(id="progress-section", classes="progress-section"):
                yield Label("Export Progress:", classes="section-label")
                yield ProgressBar(id="export-progress", show_percentage=False)
                yield Static("", id="progress-status", classes="progress-status")

            yield Rule()

            # Results section (initially hidden)
            with Container(id="results-section", classes="results-section"):
                yield Label("Export Results:", classes="section-label")
                yield Static("", id="results-summary", classes="results-summary")
                yield Static("", id="results-details", classes="results-details")

                with Horizontal(classes="results-actions"):
                    yield Button("Open Export Folder", id="open-folder-button", variant="primary")
                    yield Button("Export Another", id="export-another-button")
                    yield Button("Home", id="home-button")

    async def on_mount(self) -> None:
        """Initialize screen state."""
        await super().on_mount()
        self._hide_sections()
        await self._load_available_tags()
        self._set_default_output_path()

    def _hide_sections(self) -> None:
        """Hide conditional sections initially."""
        self.query_one("#tag-selection-container").display = False
        self.query_one("#progress-section").display = False
        self.query_one("#results-section").display = False

    def _set_default_output_path(self) -> None:
        """Set default output path."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_path = Path.cwd() / "exports" / f"prt_export_{timestamp}"
        self.query_one("#output-path-input").value = str(default_path)

    async def _load_available_tags(self) -> None:
        """Load available tags for filtering."""
        if not self.data_service:
            return

        try:
            tags = await self.data_service.get_tags()
            self._available_tags = [tag["name"] for tag in tags]
        except Exception as e:
            logger.error(f"Failed to load tags: {e}")
            self._available_tags = []

    @on(RadioSet.Changed, "#scope-selection")
    def on_scope_changed(self, event: RadioSet.Changed) -> None:
        """Handle scope selection changes."""
        if event.pressed.id == "scope-tag":
            self.query_one("#tag-selection-container").display = True
        else:
            self.query_one("#tag-selection-container").display = False

    @on(RadioSet.Changed, "#format-selection")
    def on_format_changed(self, event: RadioSet.Changed) -> None:
        """Handle format selection changes."""
        # Enable/disable directory generation option based on format
        directory_checkbox = self.query_one("#generate-directory", Checkbox)

        if event.pressed.id == "format-html":
            directory_checkbox.disabled = False
        else:
            directory_checkbox.disabled = True
            directory_checkbox.value = False

    @on(Input.Changed, "#tag-input")
    async def on_tag_input_changed(self, event: Input.Changed) -> None:
        """Handle tag input changes."""
        tag_name = event.value.strip()
        status_widget = self.query_one("#tag-status")

        if not tag_name:
            status_widget.update("")
            return

        # Check if tag exists
        if tag_name in self._available_tags:
            status_widget.update("✅ Tag found")
            status_widget.remove_class("error")
            status_widget.add_class("success")
        else:
            status_widget.update("❌ Tag not found")
            status_widget.remove_class("success")
            status_widget.add_class("error")

    @on(Button.Pressed, "#output-browse-button")
    def on_output_browse_pressed(self, event: Button.Pressed) -> None:
        """Handle output browse button press."""
        if self.notification_service:
            self.notification_service.info("Enter the full path to your export directory")

        # Focus the input field
        self.query_one("#output-path-input").focus()

    @on(Button.Pressed, "#export-button")
    async def on_export_pressed(self, event: Button.Pressed) -> None:
        """Handle export button press."""
        await self._perform_export()

    @on(Button.Pressed, "#reset-button")
    def on_reset_pressed(self, event: Button.Pressed) -> None:
        """Handle reset button press."""
        self._reset_form()

    @on(Button.Pressed, "#open-folder-button")
    async def on_open_folder_pressed(self, event: Button.Pressed) -> None:
        """Handle open folder button press."""
        if self._export_results and self._export_results.get("export_path"):
            export_path = Path(self._export_results["export_path"])
            if export_path.exists():
                # Simulate opening the folder
                if self.notification_service:
                    self.notification_service.info(f"Export location: {export_path}")
            else:
                if self.notification_service:
                    self.notification_service.error("Export folder no longer exists")

    @on(Button.Pressed, "#export-another-button")
    def on_export_another_pressed(self, event: Button.Pressed) -> None:
        """Reset for another export."""
        self._reset_export_state()

    @on(Button.Pressed, "#home-button")
    async def on_home_button_pressed(self, event: Button.Pressed) -> None:
        """Navigate to home screen."""
        if self.nav_service:
            self.nav_service.push("home")
            await self.app.switch_screen("home")

    def _reset_form(self) -> None:
        """Reset form to defaults."""
        # Reset format to JSON
        json_radio = self.query_one("#format-json", RadioButton)
        json_radio.value = True

        # Reset scope to all
        all_radio = self.query_one("#scope-all", RadioButton)
        all_radio.value = True

        # Reset checkboxes
        self.query_one("#include-images", Checkbox).value = True
        self.query_one("#generate-directory", Checkbox).value = True
        self.query_one("#include-relationships", Checkbox).value = True
        self.query_one("#include-metadata", Checkbox).value = True

        # Reset output path
        self._set_default_output_path()

        # Hide tag selection
        self.query_one("#tag-selection-container").display = False

    def _reset_export_state(self) -> None:
        """Reset export state and show form."""
        self._export_complete = False
        self._export_results = None
        self._is_exporting = False

        # Hide result sections
        self._hide_sections()

    async def _perform_export(self) -> None:
        """Perform the actual export operation."""
        if not self.data_service:
            if self.notification_service:
                self.notification_service.error("Data service not available")
            return

        self._is_exporting = True

        try:
            # Get export configuration
            export_config = await self._get_export_config()
            if not export_config:
                return

            # Show progress section
            self.query_one("#progress-section").display = True
            progress_bar = self.query_one("#export-progress", ProgressBar)
            status_widget = self.query_one("#progress-status")

            # Step 1: Gather data
            progress_bar.advance(20)
            status_widget.update("📊 Gathering data...")
            await asyncio.sleep(0.1)

            export_data = await self._gather_export_data(export_config)

            # Step 2: Prepare export
            progress_bar.advance(20)
            status_widget.update("📦 Preparing export...")
            await asyncio.sleep(0.1)

            export_path = Path(export_config["output_path"])
            export_path.mkdir(parents=True, exist_ok=True)

            # Step 3: Export based on format
            progress_bar.advance(30)
            status_widget.update("💾 Exporting data...")
            await asyncio.sleep(0.1)

            if export_config["format"] == "json":
                exported_files = await self._export_json(export_data, export_path, export_config)
            elif export_config["format"] == "csv":
                exported_files = await self._export_csv(export_data, export_path, export_config)
            elif export_config["format"] == "html":
                exported_files = await self._export_html(export_data, export_path, export_config)
            else:
                raise ValueError(f"Unsupported export format: {export_config['format']}")

            # Step 4: Generate directory if requested
            progress_bar.advance(20)
            directory_generated = False

            if export_config.get("generate_directory") and export_config["format"] == "html":
                status_widget.update("🎨 Generating directory visualization...")
                await asyncio.sleep(0.1)
                directory_generated = await self._generate_directory_visualization(
                    export_data, export_path
                )

            # Step 5: Complete
            progress_bar.advance(10)
            status_widget.update("✅ Export completed successfully!")

            # Store results
            self._export_results = {
                "success": True,
                "export_path": str(export_path),
                "format": export_config["format"],
                "contact_count": len(export_data["contacts"]),
                "files_created": len(exported_files),
                "directory_generated": directory_generated,
                "exported_files": exported_files,
            }

            # Show results
            self._show_export_results()

        except Exception as e:
            logger.error(f"Export failed: {e}")

            # Show error
            status_widget.update(f"❌ Export failed: {e}")

            self._export_results = {
                "success": False,
                "error": str(e),
                "export_path": export_config.get("output_path", ""),
                "format": export_config.get("format", "unknown"),
                "contact_count": 0,
                "files_created": 0,
                "directory_generated": False,
                "exported_files": [],
            }

            self._show_export_results()

            if self.notification_service:
                self.notification_service.error(f"Export failed: {e}")

        finally:
            self._is_exporting = False
            self._export_complete = True

    async def _get_export_config(self) -> Optional[Dict[str, Any]]:
        """Get export configuration from UI."""
        try:
            # Get format
            format_selection = self.query_one("#format-selection", RadioSet)
            if format_selection.pressed.id == "format-json":
                export_format = "json"
            elif format_selection.pressed.id == "format-csv":
                export_format = "csv"
            elif format_selection.pressed.id == "format-html":
                export_format = "html"
            else:
                export_format = "json"  # Default

            # Get scope
            scope_selection = self.query_one("#scope-selection", RadioSet)
            if scope_selection.pressed.id == "scope-all":
                scope = "all"
                scope_filter = None
            elif scope_selection.pressed.id == "scope-search":
                scope = "search"
                scope_filter = self._current_search_results
            elif scope_selection.pressed.id == "scope-tag":
                scope = "tag"
                tag_name = self.query_one("#tag-input").value.strip()
                if not tag_name:
                    if self.notification_service:
                        self.notification_service.error(
                            "Please enter a tag name for tag-based export"
                        )
                    return None
                scope_filter = tag_name
            else:
                scope = "all"
                scope_filter = None

            # Get options
            include_images = self.query_one("#include-images", Checkbox).value
            generate_directory = self.query_one("#generate-directory", Checkbox).value
            include_relationships = self.query_one("#include-relationships", Checkbox).value
            include_metadata = self.query_one("#include-metadata", Checkbox).value

            # Get output path
            output_path = self.query_one("#output-path-input").value.strip()
            if not output_path:
                if self.notification_service:
                    self.notification_service.error("Please specify an output path")
                return None

            return {
                "format": export_format,
                "scope": scope,
                "scope_filter": scope_filter,
                "include_images": include_images,
                "generate_directory": generate_directory and export_format == "html",
                "include_relationships": include_relationships,
                "include_metadata": include_metadata,
                "output_path": output_path,
            }

        except Exception as e:
            logger.error(f"Error getting export config: {e}")
            if self.notification_service:
                self.notification_service.error(f"Error reading export settings: {e}")
            return None

    async def _gather_export_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Gather data for export based on configuration."""
        export_data = {
            "contacts": [],
            "tags": [],
            "notes": [],
            "relationships": [],
            "export_info": {
                "timestamp": datetime.now().isoformat(),
                "format": config["format"],
                "scope": config["scope"],
                "source": "PRT Export Screen",
            },
        }

        # Get contacts based on scope
        if config["scope"] == "all":
            export_data["contacts"] = await self.data_service.get_contacts(limit=10000)
        elif config["scope"] == "search":
            export_data["contacts"] = config["scope_filter"] or []
        elif config["scope"] == "tag":
            tag_name = config["scope_filter"]
            export_data["contacts"] = self.data_service.api.get_contacts_by_tag(tag_name)

        # Get additional data if requested
        if config["include_metadata"]:
            export_data["tags"] = await self.data_service.get_tags()
            export_data["notes"] = await self.data_service.get_notes()

        if config["include_relationships"]:
            export_data["relationships"] = await self.data_service.get_relationships()

        return export_data

    async def _export_json(
        self, data: Dict[str, Any], export_path: Path, config: Dict[str, Any]
    ) -> List[str]:
        """Export data as JSON format."""
        files_created = []

        # Main export file
        main_file = export_path / "export.json"
        with open(main_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        files_created.append(str(main_file))

        # Copy profile images if requested
        if config["include_images"]:
            images_dir = export_path / "profile_images"
            images_dir.mkdir(exist_ok=True)

            # This would copy images from the database
            # Implementation depends on how images are stored
            # For now, just create the directory

        return files_created

    async def _export_csv(
        self, data: Dict[str, Any], export_path: Path, config: Dict[str, Any]
    ) -> List[str]:
        """Export data as CSV format."""
        files_created = []

        # Contacts CSV
        contacts_file = export_path / "contacts.csv"
        with open(contacts_file, "w", encoding="utf-8", newline="") as f:
            import csv

            if data["contacts"]:
                writer = csv.DictWriter(f, fieldnames=data["contacts"][0].keys())
                writer.writeheader()
                for contact in data["contacts"]:
                    # Remove binary data for CSV export
                    row = {k: v for k, v in contact.items() if not isinstance(v, bytes)}
                    writer.writerow(row)
        files_created.append(str(contacts_file))

        # Tags CSV if included
        if config["include_metadata"] and data["tags"]:
            tags_file = export_path / "tags.csv"
            with open(tags_file, "w", encoding="utf-8", newline="") as f:
                import csv

                writer = csv.DictWriter(f, fieldnames=data["tags"][0].keys())
                writer.writeheader()
                writer.writerows(data["tags"])
            files_created.append(str(tags_file))

        return files_created

    async def _export_html(
        self, data: Dict[str, Any], export_path: Path, config: Dict[str, Any]
    ) -> List[str]:
        """Export data as HTML format."""
        files_created = []

        # Create a simple HTML report
        html_file = export_path / "contacts.html"

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PRT Contact Export</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f0f0f0; padding: 20px; margin-bottom: 20px; }}
        .contact {{ border: 1px solid #ccc; margin: 10px 0; padding: 15px; }}
        .contact-name {{ font-weight: bold; font-size: 1.2em; }}
        .contact-details {{ margin-top: 10px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>PRT Contact Export</h1>
        <p>Generated: {data['export_info']['timestamp']}</p>
        <p>Total Contacts: {len(data['contacts'])}</p>
    </div>
    
    <div class="contacts">
        {''.join([f'''
        <div class="contact">
            <div class="contact-name">{contact.get('name', 'Unknown')}</div>
            <div class="contact-details">
                {f"Email: {contact.get('email', 'N/A')}<br>" if contact.get('email') else ''}
                {f"Phone: {contact.get('phone', 'N/A')}<br>" if contact.get('phone') else ''}
            </div>
        </div>
        ''' for contact in data['contacts']])}
    </div>
</body>
</html>"""

        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        files_created.append(str(html_file))

        return files_created

    async def _generate_directory_visualization(
        self, data: Dict[str, Any], export_path: Path
    ) -> bool:
        """Generate directory visualization using make_directory.py."""
        try:
            # Create a temporary JSON file in the expected format for make_directory.py
            temp_export = {
                "export_info": {
                    "search_type": "contacts",
                    "query": "export",
                    "total_results": len(data["contacts"]),
                },
                "results": data["contacts"],
            }

            temp_json_file = export_path / "temp_search_results.json"
            with open(temp_json_file, "w", encoding="utf-8") as f:
                json.dump(temp_export, f, indent=2, default=str)

            # Import and use the DirectoryGenerator
            from tools.make_directory import DirectoryGenerator

            generator = DirectoryGenerator(
                export_path=export_path, output_path=export_path / "directory", layout="graph"
            )

            # Update the json file path for the generator
            generator.json_file = temp_json_file
            generator.export_data = temp_export
            generator.contact_data = data["contacts"]

            # Generate the directory
            success = (
                generator.create_output_directory()
                and generator.generate_data_js()
                and generator.generate_html()
            )

            # Clean up temp file
            if temp_json_file.exists():
                temp_json_file.unlink()

            return success

        except Exception as e:
            logger.error(f"Error generating directory visualization: {e}")
            return False

    def _show_export_results(self) -> None:
        """Show export results."""
        if not self._export_results:
            return

        # Hide progress, show results
        self.query_one("#progress-section").display = False
        self.query_one("#results-section").display = True

        results = self._export_results
        summary_widget = self.query_one("#results-summary")
        details_widget = self.query_one("#results-details")

        if results["success"]:
            # Success summary
            summary_text = "✅ Export completed successfully!"

            # Detailed results
            details_text = f"""📊 Export Summary:
• Format: {results['format'].upper()}
• Contacts exported: {results['contact_count']}
• Files created: {results['files_created']}
• Directory visualization: {"✅" if results['directory_generated'] else "❌"}
• Location: {results['export_path']}"""

            if self.notification_service:
                self.notification_service.success(
                    f"Successfully exported {results['contact_count']} contacts!"
                )

        else:
            # Error summary
            summary_text = "❌ Export failed"
            details_text = f"Error: {results.get('error', 'Unknown error occurred')}"

        summary_widget.update(summary_text)
        details_widget.update(details_text)


# Register this screen
register_screen("export", ExportScreen)
