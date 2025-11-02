"""
Tests for fixture database isolation functionality.

This module tests the critical bug fix that ensures fixture data never
touches the user's real database, preventing data loss during demo mode.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

from prt_src.api import PRTAPI
from prt_src.config import data_dir
from prt_src.config import get_database_mode_from_config
from prt_src.config import is_safe_mode
from prt_src.db import create_database
from prt_src.fixture_manager import cleanup_fixture_database
from prt_src.fixture_manager import get_database_mode
from prt_src.fixture_manager import get_fixture_summary
from prt_src.fixture_manager import is_fixture_mode
from prt_src.fixture_manager import setup_fixture_mode


class TestFixtureIsolation:
    """Test fixture database isolation to prevent data loss."""

    def test_setup_fixture_mode_creates_isolated_database(self):
        """Test that setup_fixture_mode creates a separate database file."""
        # Act
        config = setup_fixture_mode(regenerate=True, quiet=True)

        # Assert
        assert config is not None
        assert "fixture.db" in config["db_path"]
        assert config["database_mode"] == "fixture"

        # Verify the database file was actually created
        fixture_db_path = Path(config["db_path"])
        assert fixture_db_path.exists()
        assert fixture_db_path.name == "fixture.db"

    def test_fixture_database_does_not_touch_real_database(self, test_db_empty):
        """Test that fixture setup never modifies the real database."""
        real_db = test_db_empty
        original_real_db_path = real_db.path

        # Create some data in the "real" database via API
        real_config = {
            "db_path": str(original_real_db_path),
            "db_username": "test",
            "db_password": "test",
        }
        real_api = PRTAPI(real_config)

        # Insert a test contact using DB's insert method
        real_db.insert_contacts([{"first": "Real", "last": "User", "email": "real@example.com"}])

        original_contact_count = real_db.count_contacts()
        assert original_contact_count == 1

        # Act - Set up fixture mode
        fixture_config = setup_fixture_mode(regenerate=True, quiet=True)

        # Assert - Real database is untouched
        real_contacts_after = real_api.search_contacts("")  # Get all contacts
        assert len(real_contacts_after) == original_contact_count
        assert any(c["name"] == "Real User" for c in real_contacts_after)

        # Assert - Fixture database has different data
        fixture_api = PRTAPI(fixture_config)
        fixture_contacts = fixture_api.search_contacts("")  # Get all contacts
        assert len(fixture_contacts) > 1  # Fixture data has multiple contacts
        assert not any(c["name"] == "Real User" for c in fixture_contacts)

    def test_fixture_mode_detection(self):
        """Test that fixture mode is correctly detected."""
        # Create fixture config
        fixture_config = setup_fixture_mode(regenerate=True, quiet=True)

        # Test detection by path
        assert is_fixture_mode(fixture_config)
        assert get_database_mode(fixture_config) == "fixture"

        # Test detection by explicit marker
        explicit_config = {"database_mode": "fixture", "db_path": "/some/path/other.db"}
        assert is_fixture_mode(explicit_config)
        assert get_database_mode(explicit_config) == "fixture"

        # Test non-fixture config
        real_config = {"db_path": str(data_dir() / "prt.db"), "database_mode": "real"}
        assert not is_fixture_mode(real_config)
        assert get_database_mode(real_config) == "real"

    def test_fixture_database_has_sample_data(self):
        """Test that fixture database contains expected sample data."""
        # Act
        config = setup_fixture_mode(regenerate=True, quiet=True)

        # Assert
        fixture_api = PRTAPI(config)
        contacts = fixture_api.search_contacts("")  # Get all contacts
        tags = fixture_api.list_all_tags()
        notes = fixture_api.list_all_notes()

        # Should have the expected fixture data
        assert len(contacts) > 0
        assert len(tags) > 0
        assert len(notes) > 0

        # Should match the fixture summary
        summary = get_fixture_summary()
        assert len(contacts) == summary["contacts"]
        assert len(tags) == summary["tags"]
        assert len(notes) == summary["notes"]

    def test_fixture_database_reuse(self):
        """Test that existing fixture database is reused when regenerate=False."""
        # Create initial fixture database
        config1 = setup_fixture_mode(regenerate=True, quiet=True)
        fixture_path = Path(config1["db_path"])

        # Modify the fixture database to add custom data
        fixture_db = create_database(fixture_path)
        fixture_db.insert_contacts(
            [{"first": "Custom", "last": "Test", "email": "custom@test.com"}]
        )

        # Act - Set up fixture mode again without regenerating
        config2 = setup_fixture_mode(regenerate=False, quiet=True)

        # Assert - Same database is reused with custom data intact
        assert config2["db_path"] == config1["db_path"]
        reused_api = PRTAPI(config2)
        contacts = reused_api.search_contacts("")
        assert any(c["name"] == "Custom Test" for c in contacts)

    def test_fixture_cleanup(self):
        """Test that fixture database can be cleaned up."""
        # Create fixture database
        config = setup_fixture_mode(regenerate=True, quiet=True)
        fixture_path = Path(config["db_path"])
        assert fixture_path.exists()

        # Act
        success = cleanup_fixture_database()

        # Assert
        assert success
        assert not fixture_path.exists()

    def test_get_fixture_summary_without_database(self):
        """Test that fixture summary can be obtained without creating database."""
        # Act
        summary = get_fixture_summary()

        # Assert
        assert "contacts" in summary
        assert "tags" in summary
        assert "notes" in summary
        assert "relationships" in summary
        assert summary["contacts"] > 0
        assert summary["has_images"] is True
        assert isinstance(summary["description"], str)

    def test_config_mode_detection_functions(self):
        """Test configuration mode detection functions."""
        # Test fixture mode
        fixture_config = {"db_path": str(data_dir() / "fixture.db"), "database_mode": "fixture"}
        assert get_database_mode_from_config(fixture_config) == "fixture"

        # Test debug mode
        debug_config = {"db_path": str(data_dir() / "debug.db")}
        assert get_database_mode_from_config(debug_config) == "debug"

        # Test real mode
        real_config = {"db_path": str(data_dir() / "prt.db")}
        assert get_database_mode_from_config(real_config) == "real"

        # Test unknown mode
        unknown_config = {"db_path": "/some/unknown/path.db"}
        assert get_database_mode_from_config(unknown_config) == "unknown"

    @patch("prt_src.config.load_config")
    def test_is_safe_mode_function(self, mock_load_config):
        """Test the is_safe_mode function for detecting safe modes."""
        # Test fixture mode is safe
        mock_load_config.return_value = {
            "db_path": str(data_dir() / "fixture.db"),
            "database_mode": "fixture",
        }
        assert is_safe_mode() is True

        # Test debug mode is safe
        mock_load_config.return_value = {"db_path": str(data_dir() / "debug.db")}
        assert is_safe_mode() is True

        # Test real mode is not safe
        mock_load_config.return_value = {"db_path": str(data_dir() / "prt.db")}
        assert is_safe_mode() is False


class TestDataSafetyRegression:
    """Regression tests to ensure data safety is maintained."""

    def test_api_with_fixture_config_does_not_affect_real_data(self, test_db_empty):
        """Test that using API with fixture config doesn't affect real database."""
        # Setup real database with data
        real_db = test_db_empty
        real_db.insert_contacts([{"first": "Real", "last": "Data", "email": "real@example.com"}])
        original_count = real_db.count_contacts()

        # Create fixture configuration
        fixture_config = setup_fixture_mode(regenerate=True, quiet=True)

        # Act - Use API with fixture config
        fixture_api = PRTAPI(fixture_config)
        fixture_contacts = fixture_api.search_contacts("")  # Get all contacts

        # Assert - Real database is unchanged
        real_config = {"db_path": str(real_db.path), "db_username": "test", "db_password": "test"}
        real_api = PRTAPI(real_config)
        real_contacts_after = real_api.search_contacts("")
        assert len(real_contacts_after) == original_count
        assert any(c["name"] == "Real Data" for c in real_contacts_after)

        # Assert - Fixture API has different data
        assert len(fixture_contacts) != original_count
        assert not any(c["name"] == "Real Data" for c in fixture_contacts)

    def test_multiple_fixture_setups_are_isolated(self):
        """Test that multiple fixture setups create independent databases."""
        # Create first fixture database in temp location
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Patch data_dir to use temp directory
            with patch("prt_src.fixture_manager.data_dir", return_value=temp_path):
                config1 = setup_fixture_mode(regenerate=True, quiet=True)
                db1_path = Path(config1["db_path"])

                # Modify first database
                db1 = create_database(db1_path)
                db1.insert_contacts(
                    [{"first": "Custom1", "last": "Test", "email": "custom1@test.com"}]
                )

            # Create second fixture database in different temp location
            with tempfile.TemporaryDirectory() as temp_dir2:
                temp_path2 = Path(temp_dir2)

                with patch("prt_src.fixture_manager.data_dir", return_value=temp_path2):
                    config2 = setup_fixture_mode(regenerate=True, quiet=True)
                    db2_path = Path(config2["db_path"])

                    # Assert - Different database files
                    assert db1_path != db2_path

                    # Assert - Second database doesn't have first database's custom data
                    api2 = PRTAPI(config2)
                    contacts2 = api2.search_contacts("")
                    assert not any(c["name"] == "Custom1 Test" for c in contacts2)

    def test_fixture_mode_prevents_accidental_data_modification(self):
        """Test that fixture mode configuration prevents accidental real data modification."""
        # This test verifies that the configuration isolation works correctly
        fixture_config = setup_fixture_mode(regenerate=True, quiet=True)

        # Verify configuration clearly identifies fixture mode
        assert fixture_config["database_mode"] == "fixture"
        assert "fixture.db" in fixture_config["db_path"]

        # Verify the database path doesn't point to production database
        assert "prt.db" not in fixture_config["db_path"]
        assert fixture_config["db_path"] != str(data_dir() / "prt.db")

        # Verify mode detection works
        assert is_fixture_mode(fixture_config)
        assert get_database_mode(fixture_config) == "fixture"
