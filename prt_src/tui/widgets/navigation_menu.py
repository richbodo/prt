"""Navigation Menu Widget for the PRT Textual TUI.

Provides a keyboard-driven menu for navigating between application sections.
Supports single-key activation and vim-style navigation.
"""

from dataclasses import dataclass
from typing import Callable, List, Optional

from textual import events
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import Static

from prt_src.tui.widgets.base import ModeAwareWidget


@dataclass
class MenuItem:
    """Represents a single menu item."""

    key: str  # Single-character keyboard shortcut
    label: str  # Display label for the item
    description: str  # Longer description
    action: str  # Action identifier when selected
    icon: Optional[str] = None  # Optional emoji/icon
    disabled: bool = False  # Whether the item is disabled

    @property
    def display_text(self) -> str:
        """Get the formatted display text for the menu item.

        Returns:
            Formatted string with icon (if present) and key shortcut
        """
        if self.icon:
            return f"{self.icon} [{self.key}] {self.label}"
        return f"[{self.key}] {self.label}"


class NavigationMenu(ModeAwareWidget):
    """A navigation menu widget with keyboard shortcuts.

    This widget displays a vertical menu of options, each with a single-key
    shortcut. It supports both direct key activation and vim-style navigation.
    """

    selected_index = reactive(0)
    current_section = reactive("")

    def __init__(
        self,
        items: Optional[List[MenuItem]] = None,
        on_activate: Optional[Callable[[MenuItem], None]] = None,
    ):
        """Initialize the navigation menu.

        Args:
            items: Custom menu items (uses defaults if None)
            on_activate: Callback when a menu item is activated
        """
        super().__init__()
        self.on_activate = on_activate
        self.menu_items = items if items is not None else self._get_default_items()
        self.menu_rows: List[Static] = []
        self.add_class("navigation-menu")

    def _get_default_items(self) -> List[MenuItem]:
        """Get the default menu items for the home screen.

        Returns:
            List of default menu items
        """
        return [
            MenuItem("c", "Contacts", "View and manage contacts", "contacts", icon="👤"),
            MenuItem(
                "r",
                "Relationships",
                "Manage contact relationships",
                "relationships",
                icon="👥",
            ),
            MenuItem(
                "y",
                "Relationship Types",
                "Manage relationship types",
                "relationship_types",
                icon="🔗",
            ),
            MenuItem("s", "Search", "Search contacts and notes", "search", icon="🔍"),
            MenuItem("i", "Import", "Import contacts from Google Takeout", "import", icon="📥"),
            MenuItem("e", "Export", "Export data and create directories", "export", icon="📤"),
            MenuItem("d", "Database", "Backup and restore database", "database", icon="💾"),
            MenuItem(
                "m",
                "Contact Metadata",
                "Manage tags and notes",
                "metadata",
                icon="🏷️",
            ),
            MenuItem("t", "Chat Mode", "Natural language interface", "chat", icon="💬"),
            MenuItem("?", "Help", "Show help and documentation", "help", icon="❓"),
            MenuItem("q", "Quit", "Exit the application", "quit", icon="🚪"),
        ]

    def compose(self) -> ComposeResult:
        """Compose the menu layout.

        Returns:
            The menu structure
        """
        with Vertical(classes="menu-container"):
            for i, item in enumerate(self.menu_items):
                row_class = "menu-item"
                if item.disabled:
                    row_class += " disabled"
                if i == self.selected_index:
                    row_class += " selected"
                if item.action == self.current_section:
                    row_class += " current"

                row = Static(item.display_text, classes=row_class, id=f"menu-item-{i}")
                if item.description:
                    row.tooltip = item.description
                self.menu_rows.append(row)
                yield row

    def select_next(self) -> None:
        """Select the next menu item, wrapping at the end."""
        self.selected_index = (self.selected_index + 1) % len(self.menu_items)
        self._update_selection()

    def select_previous(self) -> None:
        """Select the previous menu item, wrapping at the beginning."""
        self.selected_index = (self.selected_index - 1) % len(self.menu_items)
        self._update_selection()

    def select_by_key(self, key: str) -> Optional[MenuItem]:
        """Select and activate a menu item by its key shortcut.

        Args:
            key: The single-character key

        Returns:
            The activated MenuItem if found and not disabled, None otherwise
        """
        for i, item in enumerate(self.menu_items):
            if item.key == key:
                if item.disabled:
                    return None
                self.selected_index = i
                self._update_selection()
                return self._activate_current()
        return None

    def get_selected(self) -> Optional[MenuItem]:
        """Get the currently selected menu item.

        Returns:
            The currently selected MenuItem
        """
        if 0 <= self.selected_index < len(self.menu_items):
            return self.menu_items[self.selected_index]
        return None

    def highlight_section(self, section: str) -> None:
        """Highlight a specific section as current.

        Args:
            section: The action identifier of the section to highlight
        """
        self.current_section = section
        self._update_selection()

    def _update_selection(self) -> None:
        """Update the visual selection state of menu items."""
        for i, row in enumerate(self.menu_rows):
            row.remove_class("selected")
            if i == self.selected_index:
                row.add_class("selected")

            # Update current section highlighting
            item = self.menu_items[i]
            row.remove_class("current")
            if item.action == self.current_section:
                row.add_class("current")

    def _activate_current(self) -> Optional[MenuItem]:
        """Activate the currently selected menu item.

        Returns:
            The activated MenuItem if not disabled, None otherwise
        """
        item = self.get_selected()
        if item and not item.disabled:
            if self.on_activate:
                self.on_activate(item)
            return item
        return None

    def handle_key(self, key: str) -> bool:
        """Handle keyboard input for menu navigation.

        Args:
            key: The key that was pressed

        Returns:
            True if the key was handled, False otherwise
        """
        # Vim-style navigation
        if key == "j":  # Move down
            self.select_next()
            return True
        elif key == "k":  # Move up
            self.select_previous()
            return True
        elif key == "G":  # Go to last item
            self.selected_index = len(self.menu_items) - 1
            self._update_selection()
            return True
        elif key == "g":  # Go to first item
            self.selected_index = 0
            self._update_selection()
            return True
        elif key == "enter":  # Activate selected item
            self._activate_current()
            return True
        else:
            # Try direct key activation
            result = self.select_by_key(key)
            if result is not None:
                return True

        # If navigation menu didn't handle it, return False so parent can handle
        return False

    def on_mount(self) -> None:
        """Called when the widget is mounted."""
        # Initialize selection state
        self._update_selection()

    async def on_click(self, event: events.Click) -> None:
        """Handle mouse clicks on menu items."""
        # Find which widget was clicked and get its ID
        clicked_widget = event.widget
        if (
            hasattr(clicked_widget, "id")
            and clicked_widget.id
            and clicked_widget.id.startswith("menu-item-")
        ):
            try:
                item_index = int(clicked_widget.id.split("-")[-1])
                if 0 <= item_index < len(self.menu_items):
                    self.selected_index = item_index
                    self._update_selection()
                    self._activate_current()
            except (ValueError, IndexError):
                pass
