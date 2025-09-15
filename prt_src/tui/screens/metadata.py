"""Metadata management screen for PRT TUI.

Manage tags and notes for contacts.
"""

from typing import Dict
from typing import List
from typing import Optional

from textual import events
from textual import on
from textual.app import ComposeResult
from textual.containers import Container
from textual.containers import Vertical
from textual.widgets import Button
from textual.widgets import DataTable
from textual.widgets import Input
from textual.widgets import Label
from textual.widgets import TabbedContent
from textual.widgets import TabPane
from textual.widgets import TextArea

from prt_src.logging_config import get_logger
from prt_src.tui.screens import register_screen
from prt_src.tui.screens.base import BaseScreen
from prt_src.tui.screens.base import EscapeIntent

logger = get_logger(__name__)


class MetadataScreen(BaseScreen):
    """Metadata (tags/notes) management screen."""

    def __init__(self, *args, **kwargs):
        """Initialize metadata screen."""
        super().__init__(*args, **kwargs)

        # Data containers
        self.tags_data: List[Dict] = []
        self.notes_data: List[Dict] = []

        # Widget references
        self.tags_table: Optional[DataTable] = None
        self.notes_table: Optional[DataTable] = None
        self.tabbed_content: Optional[TabbedContent] = None

        # State tracking
        self.selected_tag: Optional[Dict] = None
        self.selected_note: Optional[Dict] = None
        self.current_tab = "tags"  # "tags" or "notes"

        # Form widgets
        self.tag_input: Optional[Input] = None
        self.note_title_input: Optional[Input] = None
        self.note_content_area: Optional[TextArea] = None

    def get_screen_name(self) -> str:
        """Get screen identifier."""
        return "metadata"

    def on_escape(self) -> EscapeIntent:
        """POP as ESC intent."""
        return EscapeIntent.POP

    def get_header_config(self) -> dict:
        """Configure header with title."""
        config = super().get_header_config()
        if config:
            config["title"] = "Metadata Management"
        return config

    def get_footer_config(self) -> dict:
        """Configure footer with context-sensitive hints."""
        config = super().get_footer_config()
        if config:
            if self.current_tab == "tags":
                config["keyHints"] = [
                    "[Tab] Switch",
                    "[a]dd tag",
                    "[e]dit tag",
                    "[d]elete tag",
                    "[ESC] Back",
                ]
            else:
                config["keyHints"] = [
                    "[Tab] Switch",
                    "[a]dd note",
                    "[e]dit note",
                    "[d]elete note",
                    "[ESC] Back",
                ]
        return config

    def compose(self) -> ComposeResult:
        """Compose metadata screen layout."""
        with TabbedContent(initial="tags_tab", id="metadata-tabs") as self.tabbed_content:
            # Tags tab
            with TabPane("Tags", id="tags_tab"):
                with Vertical(classes="tab-content"):
                    yield Label("Manage tags used in contacts", classes="tab-description")

                    # Tags table
                    self.tags_table = DataTable(
                        id="tags-table",
                        cursor_type="row",
                        zebra_stripes=True,
                        show_cursor=True,
                        classes="metadata-table",
                    )
                    self.tags_table.add_columns(
                        ("id", "ID"),  # Hidden column for tag ID
                        ("name", "Tag Name"),
                        ("usage_count", "Usage Count"),
                    )
                    # Hide the ID column
                    self.tags_table.show_column("id", False)
                    yield self.tags_table

                    # Tags form container (initially hidden)
                    with Container(id="tags-form", classes="form-container hidden"):
                        yield Label("Tag Name:", classes="form-label")
                        self.tag_input = Input(
                            placeholder="Enter tag name...", id="tag-input", classes="form-input"
                        )
                        yield self.tag_input

                        with Container(classes="form-buttons"):
                            yield Button("Save", id="save-tag", variant="primary")
                            yield Button("Cancel", id="cancel-tag", variant="default")

            # Notes tab
            with TabPane("Notes", id="notes_tab"):
                with Vertical(classes="tab-content"):
                    yield Label("Manage notes for contacts", classes="tab-description")

                    # Notes table
                    self.notes_table = DataTable(
                        id="notes-table",
                        cursor_type="row",
                        zebra_stripes=True,
                        show_cursor=True,
                        classes="metadata-table",
                    )
                    self.notes_table.add_columns(
                        ("id", "ID"),  # Hidden column for note ID
                        ("title", "Title"),
                        ("content_preview", "Content Preview"),
                        ("created_at", "Created"),
                    )
                    # Hide the ID column
                    self.notes_table.show_column("id", False)
                    yield self.notes_table

                    # Notes form container (initially hidden)
                    with Container(id="notes-form", classes="form-container hidden"):
                        yield Label("Note Title:", classes="form-label")
                        self.note_title_input = Input(
                            placeholder="Enter note title...",
                            id="note-title-input",
                            classes="form-input",
                        )
                        yield self.note_title_input

                        yield Label("Note Content:", classes="form-label")
                        self.note_content_area = TextArea(
                            placeholder="Enter note content...",
                            id="note-content-area",
                            classes="form-textarea",
                        )
                        yield self.note_content_area

                        with Container(classes="form-buttons"):
                            yield Button("Save", id="save-note", variant="primary")
                            yield Button("Cancel", id="cancel-note", variant="default")

    async def on_mount(self) -> None:
        """Load metadata when screen is mounted."""
        await super().on_mount()
        await self._load_all_data()

    async def on_show(self) -> None:
        """Refresh metadata when screen becomes visible."""
        await super().on_show()
        await self._load_all_data()

    async def _load_all_data(self) -> None:
        """Load both tags and notes data."""
        await self._load_tags()
        await self._load_notes()

    async def _load_tags(self) -> None:
        """Load tags data from the data service."""
        if not self.data_service:
            logger.warning("Data service not available")
            return

        try:
            self.tags_data = await self.data_service.get_tags()
            if self.tags_table:
                await self._populate_tags_table()
        except Exception as e:
            logger.error(f"Failed to load tags: {e}")
            if self.notification_service:
                await self.notification_service.show_error("Failed to load tags")

    async def _load_notes(self) -> None:
        """Load notes data from the data service."""
        if not self.data_service:
            logger.warning("Data service not available")
            return

        try:
            self.notes_data = await self.data_service.get_notes()
            if self.notes_table:
                await self._populate_notes_table()
        except Exception as e:
            logger.error(f"Failed to load notes: {e}")
            if self.notification_service:
                await self.notification_service.show_error("Failed to load notes")

    async def _populate_tags_table(self) -> None:
        """Populate the tags table with data."""
        if not self.tags_table:
            return

        # Clear existing rows
        self.tags_table.clear()

        # Add tags data
        for tag in self.tags_data:
            self.tags_table.add_row(
                str(tag.get("id", "")), tag.get("name", ""), str(tag.get("contact_count", 0))
            )

    async def _populate_notes_table(self) -> None:
        """Populate the notes table with data."""
        if not self.notes_table:
            return

        # Clear existing rows
        self.notes_table.clear()

        # Add notes data
        for note in self.notes_data:
            content = note.get("content", "")
            preview = content[:50] + "..." if len(content) > 50 else content
            created = note.get("created_at", "")

            self.notes_table.add_row(
                str(note.get("id", "")), note.get("title", ""), preview, created
            )

    # Event handlers

    async def on_key(self, event: events.Key) -> None:
        """Handle key presses."""
        key = event.key

        if key == "tab":
            # Switch between tabs
            await self._handle_tab_switch()
        elif key == "a":
            # Add new item
            await self._handle_add()
        elif key == "e":
            # Edit selected item
            await self._handle_edit()
        elif key == "d":
            # Delete selected item
            await self._handle_delete()
        else:
            # Let parent handle other keys
            await super().on_key(event)

    @on(TabbedContent.TabActivated)
    async def on_tabbed_content_tab_activated(self, message: TabbedContent.TabActivated) -> None:
        """Handle tab activation."""
        if message.tab.id == "tags_tab":
            self.current_tab = "tags"
        elif message.tab.id == "notes_tab":
            self.current_tab = "notes"

        # Update footer hints
        self.app.call_after_refresh(self.refresh_footer)

    def refresh_footer(self) -> None:
        """Refresh footer to update key hints."""
        # Trigger a refresh of the footer

    @on(DataTable.RowSelected)
    async def on_data_table_row_selected(self, message: DataTable.RowSelected) -> None:
        """Handle row selection in data tables."""
        if message.data_table == self.tags_table:
            await self._handle_tag_selection(message.row_key)
        elif message.data_table == self.notes_table:
            await self._handle_note_selection(message.row_key)

    async def _handle_tab_switch(self) -> None:
        """Switch between tabs."""
        if not self.tabbed_content:
            return

        if self.current_tab == "tags":
            self.tabbed_content.active = "notes_tab"
        else:
            self.tabbed_content.active = "tags_tab"

    async def _handle_add(self) -> None:
        """Handle add new item."""
        if self.current_tab == "tags":
            await self._show_tag_form()
        else:
            await self._show_note_form()

    async def _handle_edit(self) -> None:
        """Handle edit selected item."""
        if self.current_tab == "tags":
            if self.selected_tag:
                await self._show_tag_form(edit_mode=True)
            else:
                if self.notification_service:
                    await self.notification_service.show_warning("Please select a tag to edit")
        else:
            if self.selected_note:
                await self._show_note_form(edit_mode=True)
            else:
                if self.notification_service:
                    await self.notification_service.show_warning("Please select a note to edit")

    async def _handle_delete(self) -> None:
        """Handle delete selected item."""
        if self.current_tab == "tags":
            if self.selected_tag:
                await self._delete_tag()
            else:
                if self.notification_service:
                    await self.notification_service.show_warning("Please select a tag to delete")
        else:
            if self.selected_note:
                await self._delete_note()
            else:
                if self.notification_service:
                    await self.notification_service.show_warning("Please select a note to delete")

    async def _handle_tag_selection(self, row_key) -> None:
        """Handle tag row selection."""
        try:
            # Get the selected tag data
            row_data = self.tags_table.get_row(row_key)
            tag_id = int(row_data[0])  # ID is in the first column

            # Find the corresponding tag in our data
            for tag in self.tags_data:
                if tag.get("id") == tag_id:
                    self.selected_tag = tag
                    break

        except (ValueError, IndexError, TypeError) as e:
            logger.error(f"Error handling tag selection: {e}")
            self.selected_tag = None

    async def _handle_note_selection(self, row_key) -> None:
        """Handle note row selection."""
        try:
            # Get the selected note data
            row_data = self.notes_table.get_row(row_key)
            note_id = int(row_data[0])  # ID is in the first column

            # Find the corresponding note in our data
            for note in self.notes_data:
                if note.get("id") == note_id:
                    self.selected_note = note
                    break

        except (ValueError, IndexError, TypeError) as e:
            logger.error(f"Error handling note selection: {e}")
            self.selected_note = None

    # Form handling methods

    async def _show_tag_form(self, edit_mode: bool = False) -> None:
        """Show the tag form."""
        form_container = self.query_one("#tags-form")
        if form_container:
            form_container.remove_class("hidden")

            if edit_mode and self.selected_tag:
                if self.tag_input:
                    self.tag_input.value = self.selected_tag.get("name", "")
            else:
                if self.tag_input:
                    self.tag_input.value = ""

            # Focus the input
            if self.tag_input:
                self.tag_input.focus()

    async def _show_note_form(self, edit_mode: bool = False) -> None:
        """Show the note form."""
        form_container = self.query_one("#notes-form")
        if form_container:
            form_container.remove_class("hidden")

            if edit_mode and self.selected_note:
                if self.note_title_input:
                    self.note_title_input.value = self.selected_note.get("title", "")
                if self.note_content_area:
                    self.note_content_area.text = self.selected_note.get("content", "")
            else:
                if self.note_title_input:
                    self.note_title_input.value = ""
                if self.note_content_area:
                    self.note_content_area.text = ""

            # Focus the title input
            if self.note_title_input:
                self.note_title_input.focus()

    def _hide_forms(self) -> None:
        """Hide all forms."""
        try:
            tag_form = self.query_one("#tags-form")
            tag_form.add_class("hidden")
        except Exception:
            pass

        try:
            note_form = self.query_one("#notes-form")
            note_form.add_class("hidden")
        except Exception:
            pass

    # Button event handlers

    @on(Button.Pressed, "#save-tag")
    async def on_save_tag_pressed(self, message: Button.Pressed) -> None:
        """Handle save tag button press."""
        await self._save_tag()

    @on(Button.Pressed, "#cancel-tag")
    async def on_cancel_tag_pressed(self, message: Button.Pressed) -> None:
        """Handle cancel tag button press."""
        self._hide_forms()

    @on(Button.Pressed, "#save-note")
    async def on_save_note_pressed(self, message: Button.Pressed) -> None:
        """Handle save note button press."""
        await self._save_note()

    @on(Button.Pressed, "#cancel-note")
    async def on_cancel_note_pressed(self, message: Button.Pressed) -> None:
        """Handle cancel note button press."""
        self._hide_forms()

    # CRUD operations

    async def _save_tag(self) -> None:
        """Save tag (create or update)."""
        if not self.tag_input or not self.data_service:
            return

        tag_name = self.tag_input.value.strip()
        if not tag_name:
            if self.notification_service:
                await self.notification_service.show_warning("Please enter a tag name")
            return

        try:
            if self.selected_tag:
                # Update existing tag
                old_name = self.selected_tag.get("name", "")
                if old_name != tag_name:
                    success = await self.data_service.update_tag(old_name, tag_name)
                    if success:
                        if self.notification_service:
                            await self.notification_service.show_success(
                                f"Updated tag '{old_name}' to '{tag_name}'"
                            )
                        await self._load_tags()
                    else:
                        if self.notification_service:
                            await self.notification_service.show_error("Failed to update tag")
                else:
                    if self.notification_service:
                        await self.notification_service.show_info("No changes to save")
            else:
                # Create new tag
                result = await self.data_service.create_tag(tag_name)
                if result:
                    if self.notification_service:
                        await self.notification_service.show_success(f"Created tag '{tag_name}'")
                    await self._load_tags()
                else:
                    if self.notification_service:
                        await self.notification_service.show_error("Failed to create tag")

            self._hide_forms()
            self.selected_tag = None

        except Exception as e:
            logger.error(f"Error saving tag: {e}")
            if self.notification_service:
                await self.notification_service.show_error("Failed to save tag")

    async def _save_note(self) -> None:
        """Save note (create or update)."""
        if not self.note_title_input or not self.note_content_area or not self.data_service:
            return

        title = self.note_title_input.value.strip()
        content = self.note_content_area.text.strip()

        if not title:
            if self.notification_service:
                await self.notification_service.show_warning("Please enter a note title")
            return

        if not content:
            if self.notification_service:
                await self.notification_service.show_warning("Please enter note content")
            return

        try:
            if self.selected_note:
                # Update existing note
                note_id = self.selected_note.get("id")
                if note_id:
                    success = await self.data_service.update_note(note_id, title, content)
                    if success:
                        if self.notification_service:
                            await self.notification_service.show_success(f"Updated note '{title}'")
                        await self._load_notes()
                    else:
                        if self.notification_service:
                            await self.notification_service.show_error("Failed to update note")
            else:
                # Create new note
                result = await self.data_service.create_note(title, content)
                if result:
                    if self.notification_service:
                        await self.notification_service.show_success(f"Created note '{title}'")
                    await self._load_notes()
                else:
                    if self.notification_service:
                        await self.notification_service.show_error("Failed to create note")

            self._hide_forms()
            self.selected_note = None

        except Exception as e:
            logger.error(f"Error saving note: {e}")
            if self.notification_service:
                await self.notification_service.show_error("Failed to save note")

    async def _delete_tag(self) -> None:
        """Delete the selected tag."""
        if not self.selected_tag or not self.data_service or not self.notification_service:
            return

        tag_name = self.selected_tag.get("name", "Unknown")
        usage_count = self.selected_tag.get("contact_count", 0)

        # Show warning if tag is in use
        if usage_count > 0:
            confirmed = await self.notification_service.show_delete_dialog(
                f"Tag '{tag_name}' is used by {usage_count} contact(s). This will remove the tag from all contacts."
            )
        else:
            confirmed = await self.notification_service.show_delete_dialog(f"Tag '{tag_name}'")

        if confirmed:
            try:
                success = await self.data_service.delete_tag(tag_name)
                if success:
                    await self.notification_service.show_success(f"Deleted tag '{tag_name}'")
                    await self._load_tags()
                    self.selected_tag = None
                else:
                    await self.notification_service.show_error("Failed to delete tag")
            except Exception as e:
                logger.error(f"Error deleting tag: {e}")
                await self.notification_service.show_error("Failed to delete tag")

    async def _delete_note(self) -> None:
        """Delete the selected note."""
        if not self.selected_note or not self.data_service or not self.notification_service:
            return

        note_title = self.selected_note.get("title", "Unknown")
        confirmed = await self.notification_service.show_delete_dialog(f"Note '{note_title}'")

        if confirmed:
            try:
                note_id = self.selected_note.get("id")
                if note_id:
                    success = await self.data_service.delete_note(note_id)
                    if success:
                        await self.notification_service.show_success(f"Deleted note '{note_title}'")
                        await self._load_notes()
                        self.selected_note = None
                    else:
                        await self.notification_service.show_error("Failed to delete note")
            except Exception as e:
                logger.error(f"Error deleting note: {e}")
                await self.notification_service.show_error("Failed to delete note")


# Register this screen
register_screen("metadata", MetadataScreen)
