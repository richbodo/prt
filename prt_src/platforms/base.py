"""Base platform abstraction classes."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class PlatformCapabilities:
    """Describes what a platform can do."""

    can_export_files: bool = True
    can_import_files: bool = True
    can_show_images: bool = False
    can_play_sounds: bool = False
    can_access_clipboard: bool = True
    can_open_urls: bool = True
    has_persistent_storage: bool = True
    supports_notifications: bool = False
    supports_background_tasks: bool = False
    max_display_width: int = 120
    max_display_height: int = 40


class Platform(ABC):
    """Abstract base class for platform-specific functionality."""

    def __init__(self):
        """Initialize platform with capabilities."""
        self.capabilities = self.get_capabilities()

    @abstractmethod
    def get_capabilities(self) -> PlatformCapabilities:
        """Get platform capabilities.

        Returns:
            PlatformCapabilities describing what this platform can do
        """
        pass

    @abstractmethod
    def get_input(
        self,
        prompt: str,
        choices: Optional[List[str]] = None,
        default: Optional[str] = None,
        password: bool = False,
    ) -> str:
        """Get input from user.

        Args:
            prompt: Prompt to display
            choices: Optional list of valid choices
            default: Default value if user just hits enter
            password: If True, mask input

        Returns:
            User input string
        """
        pass

    @abstractmethod
    def display_output(
        self, content: Any, style: Optional[str] = None, format: str = "text"
    ) -> None:
        """Display output to user.

        Args:
            content: Content to display (str, dict, list, etc.)
            style: Optional style (e.g., "error", "success", "warning")
            format: Output format ("text", "table", "json")
        """
        pass

    @abstractmethod
    def get_file_path(
        self,
        title: str = "Select File",
        file_types: Optional[List[Tuple[str, str]]] = None,
        save: bool = False,
    ) -> Optional[Path]:
        """Get file path from user.

        Args:
            title: Dialog title
            file_types: List of (description, extension) tuples
            save: If True, get path for saving; if False, for opening

        Returns:
            Selected file path or None if cancelled
        """
        pass

    @abstractmethod
    def get_export_path(self, default_name: str, extension: str = ".json") -> Optional[Path]:
        """Get path for exporting data.

        Args:
            default_name: Default filename
            extension: File extension

        Returns:
            Export path or None if cancelled
        """
        pass

    @abstractmethod
    def show_progress(self, message: str, current: int = 0, total: int = 100) -> None:
        """Show progress indicator.

        Args:
            message: Progress message
            current: Current progress value
            total: Total value for completion
        """
        pass

    @abstractmethod
    def confirm(self, message: str, default: bool = False) -> bool:
        """Get yes/no confirmation from user.

        Args:
            message: Confirmation message
            default: Default response if user just hits enter

        Returns:
            True if confirmed, False otherwise
        """
        pass

    def show_error(self, message: str) -> None:
        """Display error message.

        Args:
            message: Error message to display
        """
        self.display_output(message, style="error")

    def show_success(self, message: str) -> None:
        """Display success message.

        Args:
            message: Success message to display
        """
        self.display_output(message, style="success")

    def show_warning(self, message: str) -> None:
        """Display warning message.

        Args:
            message: Warning message to display
        """
        self.display_output(message, style="warning")

    def show_info(self, message: str) -> None:
        """Display info message.

        Args:
            message: Info message to display
        """
        self.display_output(message, style="info")

    @abstractmethod
    def clear_screen(self) -> None:
        """Clear the display/screen."""
        pass

    def get_clipboard_text(self) -> Optional[str]:
        """Get text from clipboard.

        Returns:
            Clipboard text or None if not supported
        """
        if not self.capabilities.can_access_clipboard:
            return None
        return self._get_clipboard_text_impl()

    def set_clipboard_text(self, text: str) -> bool:
        """Set clipboard text.

        Args:
            text: Text to put on clipboard

        Returns:
            True if successful, False otherwise
        """
        if not self.capabilities.can_access_clipboard:
            return False
        return self._set_clipboard_text_impl(text)

    def _get_clipboard_text_impl(self) -> Optional[str]:
        """Platform-specific clipboard get implementation."""
        return None

    def _set_clipboard_text_impl(self, text: str) -> bool:
        """Platform-specific clipboard set implementation."""
        return False

    def open_url(self, url: str) -> bool:
        """Open URL in default browser.

        Args:
            url: URL to open

        Returns:
            True if successful, False otherwise
        """
        if not self.capabilities.can_open_urls:
            return False
        return self._open_url_impl(url)

    def _open_url_impl(self, url: str) -> bool:
        """Platform-specific URL opening implementation."""
        return False

    def show_notification(self, title: str, message: str, icon: Optional[str] = None) -> bool:
        """Show system notification.

        Args:
            title: Notification title
            message: Notification message
            icon: Optional icon name/path

        Returns:
            True if shown, False if not supported
        """
        if not self.capabilities.supports_notifications:
            return False
        return self._show_notification_impl(title, message, icon)

    def _show_notification_impl(self, title: str, message: str, icon: Optional[str] = None) -> bool:
        """Platform-specific notification implementation."""
        return False

    def get_storage_path(self, filename: str) -> Path:
        """Get path for persistent storage.

        Args:
            filename: Name of file to store

        Returns:
            Full path for storage
        """
        return Path.home() / ".prt" / filename

    def format_table(
        self, headers: List[str], rows: List[List[Any]], max_width: Optional[int] = None
    ) -> str:
        """Format data as table.

        Args:
            headers: Column headers
            rows: Data rows
            max_width: Maximum table width

        Returns:
            Formatted table string
        """
        if max_width is None:
            max_width = self.capabilities.max_display_width

        # Simple text table formatting
        col_widths = []
        for i, header in enumerate(headers):
            max_col = len(str(header))
            for row in rows:
                if i < len(row):
                    max_col = max(max_col, len(str(row[i])))
            col_widths.append(min(max_col, max_width // len(headers)))

        # Build table
        lines = []

        # Header
        header_line = " | ".join(str(h)[:w].ljust(w) for h, w in zip(headers, col_widths))
        lines.append(header_line)
        lines.append("-" * len(header_line))

        # Rows
        for row in rows:
            row_line = " | ".join(
                str(row[i] if i < len(row) else "")[:w].ljust(w) for i, w in enumerate(col_widths)
            )
            lines.append(row_line)

        return "\n".join(lines)

    def paginate(
        self, items: List[Any], page: int = 0, page_size: int = 10
    ) -> Tuple[List[Any], Dict[str, Any]]:
        """Paginate a list of items.

        Args:
            items: List to paginate
            page: Current page (0-indexed)
            page_size: Items per page

        Returns:
            Tuple of (page_items, pagination_info)
        """
        total = len(items)
        start = page * page_size
        end = min(start + page_size, total)

        page_items = items[start:end] if start < total else []

        pagination_info = {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
            "has_next": end < total,
            "has_prev": page > 0,
            "start": start + 1 if page_items else 0,
            "end": end,
        }

        return page_items, pagination_info
