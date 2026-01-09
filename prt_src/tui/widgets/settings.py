"""Settings Screen for the PRT Textual TUI.

Provides a comprehensive settings interface with categories,
validation, and persistence.
"""

from collections.abc import Callable
from typing import Any

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import Button
from textual.widgets import Input
from textual.widgets import Label
from textual.widgets import Select
from textual.widgets import Static
from textual.widgets import Switch

from prt_src.tui.widgets.base import ModeAwareWidget


class SettingItem(Static):
    """Individual setting item with label and control."""

    def __init__(
        self,
        key: str,
        label: str,
        value: Any,
        options: list | type = None,
        description: str = "",
    ):
        """Initialize a setting item.

        Args:
            key: Setting key/identifier
            label: Display label
            value: Current value
            options: List of options or type (bool, int, str)
            description: Help text for the setting
        """
        super().__init__()
        self.key = key
        self.label = label
        self.value = value
        self.original_value = value
        self.options = options
        self.description = description
        self.validator: Callable | None = None
        self.add_class("setting-item")

    def compose(self) -> ComposeResult:
        """Compose the setting item layout."""
        with Horizontal(classes="setting-row"):
            # Label and description
            with Vertical(classes="setting-info"):
                yield Label(self.label, classes="setting-label")
                if self.description:
                    yield Label(self.description, classes="setting-description")

            # Control based on type
            if self.options is bool or isinstance(self.value, bool):
                yield Switch(self.value, id=f"switch-{self.key}", classes="setting-control")
            elif isinstance(self.options, list):
                yield Select(
                    [(opt, str(opt)) for opt in self.options],
                    value=self.value,
                    id=f"select-{self.key}",
                    classes="setting-control",
                )
            else:
                yield Input(str(self.value), id=f"input-{self.key}", classes="setting-control")

    def toggle(self) -> None:
        """Toggle boolean value."""
        if isinstance(self.value, bool):
            self.value = not self.value
            self._update_control()

    def cycle_next(self) -> None:
        """Cycle to next option in list."""
        if isinstance(self.options, list) and self.value in self.options:
            current_idx = self.options.index(self.value)
            next_idx = (current_idx + 1) % len(self.options)
            self.value = self.options[next_idx]
            self._update_control()

    def set_validator(self, validator: Callable) -> None:
        """Set validation function.

        Args:
            validator: Function that takes value and returns bool
        """
        self.validator = validator

    def is_valid(self, value: Any = None) -> bool:
        """Check if value is valid.

        Args:
            value: Value to check (uses current if not provided)

        Returns:
            True if valid
        """
        if value is None:
            value = self.value

        if self.validator:
            return self.validator(value)
        return True

    def _update_control(self) -> None:
        """Update the control to reflect current value."""
        try:
            if isinstance(self.value, bool):
                self.query_one(f"#switch-{self.key}", Switch).value = self.value
            elif isinstance(self.options, list):
                self.query_one(f"#select-{self.key}", Select).value = self.value
            else:
                self.query_one(f"#input-{self.key}", Input).value = str(self.value)
        except Exception:
            pass


class SettingsCategory(Static):
    """Category grouping for related settings."""

    def __init__(self, category_name: str, description: str = ""):
        """Initialize a settings category.

        Args:
            category_name: Category name
            description: Category description
        """
        super().__init__()
        self.category_name = category_name
        self.description = description
        self.items: list[SettingItem] = []
        self.add_class("settings-category")

    def compose(self) -> ComposeResult:
        """Compose the category layout."""
        with Vertical(classes="category-container"):
            # Category header
            yield Label(self.category_name, classes="category-title")
            if self.description:
                yield Label(self.description, classes="category-description")

            # Settings items container
            yield Vertical(id=f"items-{self.category_name.lower()}", classes="category-items")

    def add_item(self, item: SettingItem) -> None:
        """Add a setting item to this category.

        Args:
            item: SettingItem to add
        """
        self.items.append(item)
        try:
            container = self.query_one(f"#items-{self.category_name.lower()}", Vertical)
            container.mount(item)
        except Exception:
            pass

    def get_item(self, key: str) -> SettingItem | None:
        """Get item by key.

        Args:
            key: Setting key

        Returns:
            SettingItem or None
        """
        for item in self.items:
            if item.key == key:
                return item
        return None


class SettingsScreen(ModeAwareWidget):
    """Main settings screen with categories and controls."""

    has_unsaved_changes = reactive(False)

    def __init__(self, on_save: Callable | None = None, defaults: dict | None = None):
        """Initialize the settings screen.

        Args:
            on_save: Callback when settings are saved
            defaults: Default settings values
        """
        super().__init__()
        self.settings: dict[str, Any] = {}
        self.categories: list[SettingsCategory] = []
        self.on_save = on_save
        self.defaults = defaults or {}
        self.add_class("settings-screen")

        # Initialize default categories
        self._init_categories()

    def compose(self) -> ComposeResult:
        """Compose the settings screen layout."""
        with Vertical(classes="settings-container"):
            # Header
            with Horizontal(classes="settings-header"):
                yield Label("Settings", classes="settings-title")
                with Horizontal(classes="settings-actions"):
                    yield Button("Save", id="save-settings", classes="action-button")
                    yield Button("Reset", id="reset-settings", classes="action-button")
                    yield Button("Cancel", id="cancel-settings", classes="action-button")

            # Categories container
            yield Vertical(id="categories-container", classes="categories-container")

    def _init_categories(self) -> None:
        """Initialize default setting categories."""
        # General category
        general = SettingsCategory("General", "Basic application settings")
        general.add_item(
            SettingItem(
                "theme",
                "Theme",
                "dark",
                ["light", "dark", "auto"],
                "Choose your preferred color theme",
            )
        )
        general.add_item(
            SettingItem("vim_mode", "Vim Mode", False, bool, "Enable vim-style keyboard navigation")
        )
        general.add_item(
            SettingItem("auto_save", "Auto Save", True, bool, "Automatically save changes")
        )
        self.categories.append(general)

        # Display category
        display = SettingsCategory("Display", "Visual preferences")
        display.add_item(
            SettingItem("font_size", "Font Size", 14, [12, 14, 16, 18, 20], "Interface font size")
        )
        display.add_item(
            SettingItem(
                "show_hints", "Show Hints", True, bool, "Display keyboard hints in status bar"
            )
        )
        self.categories.append(display)

        # Database category
        database = SettingsCategory("Database", "Database configuration")
        database.add_item(
            SettingItem(
                "db_path",
                "Database Path",
                "~/.prt/contacts.db",
                str,
                "Path to the contacts database",
            )
        )
        database.add_item(
            SettingItem(
                "backup_enabled", "Auto Backup", True, bool, "Enable automatic database backups"
            )
        )
        self.categories.append(database)

    def load_settings(self, settings: dict[str, Any]) -> None:
        """Load settings values.

        Args:
            settings: Dictionary of settings
        """
        self.settings = settings.copy()
        self.has_unsaved_changes = False

        # Update all items with loaded values
        for category in self.categories:
            for item in category.items:
                if item.key in settings:
                    item.value = settings[item.key]
                    item.original_value = settings[item.key]

    def get_setting(self, key: str) -> Any:
        """Get a setting value.

        Args:
            key: Setting key

        Returns:
            Setting value or None
        """
        return self.settings.get(key)

    def update_setting(self, key: str, value: Any) -> None:
        """Update a setting value.

        Args:
            key: Setting key
            value: New value
        """
        if key in self.settings and self.settings[key] != value:
            self.settings[key] = value
            self.has_unsaved_changes = True

            # Update the item
            for category in self.categories:
                item = category.get_item(key)
                if item:
                    item.value = value
                    break

    def save_settings(self) -> None:
        """Save current settings."""
        if self.on_save:
            self.on_save(self.settings)

        self.has_unsaved_changes = False

        # Update original values
        for category in self.categories:
            for item in category.items:
                item.original_value = item.value

    def reset_to_defaults(self) -> None:
        """Reset all settings to defaults."""
        self.settings = self.defaults.copy()
        self.has_unsaved_changes = True

        # Update all items
        for category in self.categories:
            for item in category.items:
                if item.key in self.defaults:
                    item.value = self.defaults[item.key]

    def cancel_changes(self) -> None:
        """Cancel unsaved changes."""
        # Revert all items to original values
        for category in self.categories:
            for item in category.items:
                item.value = item.original_value
                self.settings[item.key] = item.original_value

        self.has_unsaved_changes = False
