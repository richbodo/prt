"""Integration tests for the Textual application.

Tests the full app initialization and first-run flow.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from prt_src.db import Database
from prt_src.tui.app import AppMode, PRTApp


class TestAppIntegration:
    """Integration tests for PRTApp."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        db = Database(db_path)
        db.connect()
        db.initialize()  # Create schema

        yield db

        # Cleanup
        db.session.close()
        db_path.unlink(missing_ok=True)

    def test_app_initializes_with_database(self, temp_db):
        """Test that app properly initializes with a database."""
        with patch("prt_src.tui.app.load_config") as mock_config:
            mock_config.return_value = {"db_path": str(temp_db.path)}

            app = PRTApp()

            assert app.db is not None
            assert app.first_run_handler is not None
            assert app.current_mode == AppMode.NAVIGATION

    def test_first_run_detection_flow(self, temp_db):
        """Test the complete first-run detection flow."""
        with patch("prt_src.tui.app.load_config") as mock_config:
            mock_config.return_value = {"db_path": str(temp_db.path)}

            # First run - no "You" contact exists
            app = PRTApp()
            assert app._is_first_run is True

            # Create "You" contact
            you_contact = app.first_run_handler.create_you_contact("Test User")
            assert you_contact["first_name"] == "Test"
            assert you_contact["last_name"] == "User"

            # Second run - "You" contact exists
            app2 = PRTApp()
            assert app2._is_first_run is False

    def test_mode_switching_updates_ui(self):
        """Test that mode switching updates the UI subtitle."""
        with patch("prt_src.tui.app.load_config") as mock_config:
            mock_config.return_value = {"db_path": ":memory:"}

            app = PRTApp()

            # Initial state
            assert app.current_mode == AppMode.NAVIGATION

            # Toggle to edit mode
            app.action_toggle_mode()
            assert app.current_mode == AppMode.EDIT
            assert app.sub_title == "Mode: EDIT"

            # Toggle back
            app.action_toggle_mode()
            assert app.current_mode == AppMode.NAVIGATION
            assert app.sub_title == "Mode: NAV"

    def test_quit_only_works_in_navigation_mode(self):
        """Test that quit action only works in navigation mode."""
        with patch("prt_src.tui.app.load_config") as mock_config:
            mock_config.return_value = {"db_path": ":memory:"}

            app = PRTApp()

            # Mock the exit method
            app.exit = lambda: setattr(app, "_exited", True)
            app._exited = False

            # In navigation mode, quit should work
            app.current_mode = AppMode.NAVIGATION
            app.action_quit()
            assert app._exited is True

            # Reset
            app._exited = False

            # In edit mode, quit should not work
            app.current_mode = AppMode.EDIT
            app.action_quit()
            assert app._exited is False
