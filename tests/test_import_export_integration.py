"""Integration tests for import and export screens."""

from unittest.mock import MagicMock

import pytest

from prt_src.tui.screens import SCREEN_REGISTRY
from prt_src.tui.screens import create_screen


class TestImportExportIntegration:
    """Integration tests for import and export functionality."""

    def test_import_screen_registration(self):
        """Test that the import screen is properly registered."""
        assert "import" in SCREEN_REGISTRY, "Import screen should be registered"

    def test_export_screen_registration(self):
        """Test that the export screen is properly registered."""
        assert "export" in SCREEN_REGISTRY, "Export screen should be registered"

    def test_can_create_import_screen(self):
        """Test that we can create an import screen instance."""
        # Mock services
        mock_services = {
            "nav_service": MagicMock(),
            "data_service": MagicMock(),
            "notification_service": MagicMock(),
            "selection_service": MagicMock(),
            "validation_service": MagicMock(),
        }

        screen = create_screen("import", **mock_services)

        assert screen is not None, "Should be able to create import screen"
        assert screen.get_screen_name() == "import"

    def test_can_create_export_screen(self):
        """Test that we can create an export screen instance."""
        # Mock services
        mock_services = {
            "nav_service": MagicMock(),
            "data_service": MagicMock(),
            "notification_service": MagicMock(),
            "selection_service": MagicMock(),
            "validation_service": MagicMock(),
        }

        screen = create_screen("export", **mock_services)

        assert screen is not None, "Should be able to create export screen"
        assert screen.get_screen_name() == "export"

    def test_navigation_menu_includes_import_export(self):
        """Test that navigation menu includes import and export options."""
        from prt_src.tui.widgets.navigation_menu import NavigationMenu

        menu = NavigationMenu()
        menu_actions = [item.action for item in menu.menu_items]

        assert "import" in menu_actions, "Navigation menu should include import option"
        assert "export" in menu_actions, "Navigation menu should include export option"

        # Check key bindings
        menu_keys = [item.key for item in menu.menu_items]
        assert "i" in menu_keys, "Import should be bound to 'i' key"
        assert "e" in menu_keys, "Export should be bound to 'e' key"

    def test_home_screen_handles_import_export_navigation(self):
        """Test that home screen can handle navigation to import/export screens."""
        from prt_src.tui.screens.home import HomeScreen
        from prt_src.tui.widgets.navigation_menu import MenuItem

        # Mock services
        mock_nav_service = MagicMock()
        mock_app = MagicMock()

        home_screen = HomeScreen(
            nav_service=mock_nav_service, data_service=MagicMock(), notification_service=MagicMock()
        )
        # Mock the app attribute for the async switch
        home_screen._app = mock_app

        # Test import navigation
        import_item = MenuItem("i", "Import", "Import contacts", "import")
        home_screen._handle_menu_activation(import_item)

        # Test export navigation
        export_item = MenuItem("e", "Export", "Export data", "export")
        home_screen._handle_menu_activation(export_item)

        # Verify navigation service was called
        assert mock_nav_service.push.call_count == 2
        mock_nav_service.push.assert_any_call("import")
        mock_nav_service.push.assert_any_call("export")


if __name__ == "__main__":
    pytest.main([__file__])
