"""Test Textual application structure and first-run logic.

Lightweight TDD approach - start with basic tests, then expand.
"""

from unittest.mock import Mock, patch

import pytest

# These imports will fail initially - that's expected in TDD
from prt_src.tui.app import AppMode, FirstRunHandler, PRTApp


class TestPRTApp:
    """Test the main PRT Textual application."""

    def test_app_creation(self):
        """Test that the app can be created."""
        app = PRTApp()
        assert app is not None
        assert app.title == "Personal Relationship Tracker"
        assert app.current_mode == AppMode.NAVIGATION

    def test_app_has_required_keybindings(self):
        """Test that app has the required global keybindings."""
        app = PRTApp()

        # Check bindings are defined
        binding_keys = [b.key for b in app.BINDINGS]

        # Check for ESC binding (mode toggle)
        assert "escape" in binding_keys

        # Check for quit binding
        assert "q" in binding_keys

        # Check for help binding (? is represented as ?)
        assert "?" in binding_keys

    def test_mode_switching(self):
        """Test that ESC toggles between navigation and edit modes."""
        app = PRTApp()

        # Start in navigation mode
        assert app.current_mode == AppMode.NAVIGATION

        # Toggle to edit mode
        app.toggle_mode()
        assert app.current_mode == AppMode.EDIT

        # Toggle back to navigation
        app.toggle_mode()
        assert app.current_mode == AppMode.NAVIGATION


class TestFirstRunHandler:
    """Test first-run detection and 'You' contact creation."""

    @patch("prt_src.tui.app.Database")
    def test_detects_first_run_when_no_you_contact(self, mock_db_class):
        """Test that first run is detected when 'You' contact doesn't exist."""
        mock_db = Mock()
        mock_db_class.return_value = mock_db
        mock_db.get_you_contact.return_value = None

        handler = FirstRunHandler(mock_db)
        assert handler.is_first_run() is True

    @patch("prt_src.tui.app.Database")
    def test_detects_not_first_run_when_you_exists(self, mock_db_class):
        """Test that first run is false when 'You' contact exists."""
        mock_db = Mock()
        mock_db_class.return_value = mock_db
        mock_db.get_you_contact.return_value = {"id": 1, "first_name": "You"}

        handler = FirstRunHandler(mock_db)
        assert handler.is_first_run() is False

    @patch("prt_src.tui.app.Database")
    def test_create_you_contact_with_name(self, mock_db_class):
        """Test creating 'You' contact with provided name."""
        mock_db = Mock()
        mock_db_class.return_value = mock_db
        mock_db.create_contact.return_value = {"id": 1, "first_name": "John", "last_name": "Doe"}

        handler = FirstRunHandler(mock_db)
        contact = handler.create_you_contact("John Doe")

        assert contact["first_name"] == "John"
        assert contact["last_name"] == "Doe"
        mock_db.create_contact.assert_called_once()

    @patch("prt_src.tui.app.Database")
    def test_create_you_contact_without_name(self, mock_db_class):
        """Test creating 'You' contact when name is skipped."""
        mock_db = Mock()
        mock_db_class.return_value = mock_db
        mock_db.create_contact.return_value = {"id": 1, "first_name": "You", "last_name": ""}

        handler = FirstRunHandler(mock_db)
        contact = handler.create_you_contact(None)

        assert contact["first_name"] == "You"
        assert contact["last_name"] == ""
        mock_db.create_contact.assert_called_once()

    @patch("prt_src.tui.app.Database")
    def test_create_you_contact_handles_db_error(self, mock_db_class):
        """Test that database errors are properly raised."""
        mock_db = Mock()
        mock_db_class.return_value = mock_db
        mock_db.create_contact.side_effect = Exception("Database error")

        handler = FirstRunHandler(mock_db)

        with pytest.raises(RuntimeError, match="Failed to create 'You' contact"):
            handler.create_you_contact("Test User")


class TestAppStyles:
    """Test CSS styling and theme configuration."""

    def test_app_has_css_file(self):
        """Test that the app loads CSS from styles.tcss."""
        app = PRTApp()
        assert app.CSS_PATH == "styles.tcss"

    def test_dark_theme_by_default(self):
        """Test that app uses dark theme by default."""
        app = PRTApp()
        assert app.dark is True
