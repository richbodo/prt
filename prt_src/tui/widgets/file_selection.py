"""File selection widget for Google Takeout files."""

from pathlib import Path

from textual import events
from textual.app import ComposeResult
from textual.containers import Container
from textual.containers import Vertical
from textual.message import Message
from textual.widgets import Static

from prt_src.logging_config import get_logger

logger = get_logger(__name__)


class FileSelectionWidget(Container, can_focus=True):
    """Widget for selecting a Google Takeout file from multiple options.

    Displays a numbered list of files with metadata (size, location) and handles
    keyboard selection (1-9), browse ('b'), and cancel ('c').
    """

    # Default CSS to ensure widget can receive focus
    DEFAULT_CSS = """
    FileSelectionWidget {
        width: 100%;
        height: auto;
    }
    """

    class FileSelected(Message):
        """Message emitted when a file is selected."""

        def __init__(self, file_path: Path) -> None:
            """Initialize message with selected file path.

            Args:
                file_path: The selected file path
            """
            super().__init__()
            self.file_path = file_path

    class SelectionCancelled(Message):
        """Message emitted when selection is cancelled."""

    def __init__(
        self,
        files: list[Path],
        title: str = "Select Google Takeout File",
        **kwargs,
    ):
        """Initialize file selection widget.

        Args:
            files: List of file paths to choose from
            title: Title to display above file list
            **kwargs: Additional container arguments
        """
        super().__init__(**kwargs)
        self.files = files
        self.title_text = title
        self.add_class("file-selection-widget")

    def compose(self) -> ComposeResult:
        """Compose the file selection layout."""
        with Container(id="file-selection-container"):
            yield Static(self.title_text, id="file-selection-title")

            # Show instructions
            yield Static(
                "Select a file to import:",
                id="file-selection-instructions",
            )

            # Display each file with metadata
            with Vertical(id="file-list"):
                for idx, file_path in enumerate(self.files, 1):
                    # Only show first 9 files (keyboard limitation)
                    if idx > 9:
                        break

                    # Get file metadata
                    file_size_mb = file_path.stat().st_size / 1024 / 1024
                    location = str(file_path.parent)

                    # Create file entry
                    file_info = (
                        f"[{idx}] {file_path.name}\n"
                        f"    Size: {file_size_mb:.1f} MB\n"
                        f"    Location: {location}"
                    )
                    yield Static(file_info, classes="file-entry")

            # Show additional files count if more than 9
            if len(self.files) > 9:
                yield Static(
                    f"\n⚠️  Showing first 9 of {len(self.files)} files",
                    id="files-overflow-notice",
                )

            # Show keyboard hints
            yield Static(
                "\nPress 1-9 to select  |  Press 'c' to cancel",
                id="file-selection-hints",
            )

    async def on_key(self, event: events.Key) -> None:
        """Handle key presses for file selection.

        Args:
            event: Key event
        """
        key = event.key.lower()
        logger.info(f"[FILE_SELECTION] Key pressed: '{key}'")

        # Handle number keys (1-9)
        if key.isdigit():
            file_index = int(key) - 1
            if 0 <= file_index < len(self.files) and file_index < 9:
                selected_file = self.files[file_index]
                logger.info(f"[FILE_SELECTION] File selected: {selected_file.name}")
                self.post_message(self.FileSelected(selected_file))
                event.prevent_default()
                return

        # Handle cancel
        if key == "c" or key == "escape":
            logger.info("[FILE_SELECTION] Selection cancelled")
            self.post_message(self.SelectionCancelled())
            event.prevent_default()
            return

        # Other keys are ignored (no action needed)

    def dismiss(self) -> None:
        """Dismiss the file selection widget."""
        logger.info("[FILE_SELECTION] Dismissing widget")
        self.display = False
        try:
            self.remove()
        except Exception as e:
            logger.warning(f"[FILE_SELECTION] Error removing widget: {e}")
