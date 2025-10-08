"""Dropdown menu widget."""

from typing import Callable
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static

from prt_src.logging_config import get_logger

logger = get_logger(__name__)


class DropdownMenu(Container):
    """Simple dropdown menu overlay.

    Displays a vertical list of menu items that can be activated with
    keyboard shortcuts or mouse clicks.
    """

    def __init__(self, items: list[tuple[str, str, Callable]], **kwargs):
        """Initialize DropdownMenu.

        Args:
            items: List of (key, label, action) tuples
                   e.g., [("H", "Home", lambda: navigate("home"))]
            **kwargs: Additional keyword arguments for Container
        """
        super().__init__(**kwargs)
        self.items = items
        self.add_class("dropdown-menu")

    def compose(self) -> ComposeResult:
        """Compose menu items."""
        for key, label, _action in self.items:
            item = Static(f"({key.upper()}) {label}", classes="menu-item")
            yield item

    def show(self) -> None:
        """Show the dropdown menu."""
        self.add_class("visible")
        self.display = True

    def hide(self) -> None:
        """Hide the dropdown menu."""
        self.remove_class("visible")
        self.display = False

    def toggle(self) -> None:
        """Toggle menu visibility."""
        if self.display:
            self.hide()
        else:
            self.show()

    def get_action(self, key: str) -> Optional[Callable]:
        """Get action for a key press.

        Args:
            key: Key pressed (case-insensitive)

        Returns:
            Action callable or None if key not found
        """
        key_upper = key.upper()
        logger.info(f"[DROPDOWN] get_action called with key='{key}' (upper='{key_upper}')")
        logger.info(
            f"[DROPDOWN] Available menu items: {[(key, label) for key, label, _ in self.items]}"
        )

        for item_key, label, action in self.items:
            if item_key.upper() == key_upper:
                logger.info(
                    f"[DROPDOWN] Found match: key='{item_key}', label='{label}', action={action}"
                )
                return action

        logger.warning(f"[DROPDOWN] No action found for key '{key}'")
        return None
