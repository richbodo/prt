"""Bottom navigation/status bar widget."""

from textual.app import ComposeResult
from textual.widgets import Static


class BottomNav(Static):
    """Bottom status bar with key hints and status messages.

    Layout: (esc) Toggle Nav/Edit (x) Exit (?) Help │ Status message...
    """

    def __init__(self, **kwargs):
        """Initialize BottomNav.

        Args:
            **kwargs: Additional keyword arguments for Static
        """
        super().__init__(**kwargs)
        self.status_message = ""

    def compose(self) -> ComposeResult:
        """Compose the status bar."""
        self.update(self._format_status_line())
        return super().compose()

    def show_status(self, message: str) -> None:
        """Update status message.

        Args:
            message: Status message to display
        """
        self.status_message = message
        self.update(self._format_status_line())

    def clear_status(self) -> None:
        """Clear status message."""
        self.status_message = ""
        self.update(self._format_status_line())

    def _format_status_line(self) -> str:
        """Format the status bar content.

        Returns:
            Formatted string for status bar
        """
        base = "(esc) Toggle Nav/Edit  (x) Exit  (?) Help"
        if self.status_message:
            return f"{base}  │  {self.status_message}"
        return base
