"""Test Settings Screen for the Textual TUI.

Lightweight TDD for settings management functionality.
"""

from prt_src.tui.widgets.settings import SettingItem, SettingsCategory, SettingsScreen


class TestSettingItem:
    """Test the SettingItem widget."""

    def test_setting_item_creation(self):
        """Test that SettingItem can be created."""
        item = SettingItem("theme", "Dark Mode", "dark", ["light", "dark"])
        assert item is not None
        assert item.key == "theme"
        assert item.label == "Dark Mode"
        assert item.value == "dark"

    def test_setting_item_toggle(self):
        """Test boolean setting toggle."""
        item = SettingItem("vim_mode", "Vim Mode", True, bool)

        assert item.value is True
        item.toggle()
        assert item.value is False
        item.toggle()
        assert item.value is True

    def test_setting_item_cycle_options(self):
        """Test cycling through options."""
        item = SettingItem("theme", "Theme", "light", ["light", "dark", "auto"])

        assert item.value == "light"
        item.cycle_next()
        assert item.value == "dark"
        item.cycle_next()
        assert item.value == "auto"
        item.cycle_next()
        assert item.value == "light"

    def test_setting_item_validation(self):
        """Test setting validation."""
        item = SettingItem("port", "Port", 8080, int)
        item.set_validator(lambda v: 1000 <= v <= 9999)

        assert item.is_valid(8080)
        assert not item.is_valid(500)
        assert not item.is_valid(10000)


class TestSettingsCategory:
    """Test the SettingsCategory widget."""

    def test_settings_category_creation(self):
        """Test that SettingsCategory can be created."""
        category = SettingsCategory("General", "General settings")
        assert category is not None
        assert category.category_name == "General"
        assert category.description == "General settings"

    def test_settings_category_add_items(self):
        """Test adding items to category."""
        category = SettingsCategory("Appearance")

        category.add_item(SettingItem("theme", "Theme", "dark"))
        category.add_item(SettingItem("font_size", "Font Size", 14))

        assert len(category.items) == 2
        assert category.items[0].key == "theme"
        assert category.items[1].key == "font_size"

    def test_settings_category_get_item(self):
        """Test getting item by key."""
        category = SettingsCategory("Test")
        item = SettingItem("test_key", "Test", "value")
        category.add_item(item)

        found = category.get_item("test_key")
        assert found == item

        not_found = category.get_item("missing")
        assert not_found is None


class TestSettingsScreen:
    """Test the SettingsScreen widget."""

    def test_settings_screen_creation(self):
        """Test that SettingsScreen can be created."""
        screen = SettingsScreen()
        assert screen is not None
        assert hasattr(screen, "categories")
        assert hasattr(screen, "settings")

    def test_settings_screen_load_settings(self):
        """Test loading settings."""
        settings = {"theme": "dark", "vim_mode": True, "auto_save": False, "font_size": 14}

        screen = SettingsScreen()
        screen.load_settings(settings)

        assert screen.settings == settings
        assert screen.get_setting("theme") == "dark"
        assert screen.get_setting("vim_mode") is True

    def test_settings_screen_update_setting(self):
        """Test updating a setting."""
        screen = SettingsScreen()
        screen.load_settings({"theme": "light"})

        screen.update_setting("theme", "dark")
        assert screen.get_setting("theme") == "dark"
        assert screen.has_unsaved_changes

    def test_settings_screen_save(self):
        """Test saving settings."""
        save_called = False
        saved_settings = None

        def on_save(settings):
            nonlocal save_called, saved_settings
            save_called = True
            saved_settings = settings

        screen = SettingsScreen(on_save=on_save)
        screen.load_settings({"theme": "light"})
        screen.update_setting("theme", "dark")

        screen.save_settings()

        assert save_called
        assert saved_settings["theme"] == "dark"
        assert not screen.has_unsaved_changes

    def test_settings_screen_reset(self):
        """Test resetting to defaults."""
        defaults = {"theme": "light", "vim_mode": False}

        screen = SettingsScreen(defaults=defaults)
        screen.load_settings({"theme": "dark", "vim_mode": True})

        screen.reset_to_defaults()

        assert screen.get_setting("theme") == "light"
        assert screen.get_setting("vim_mode") is False
