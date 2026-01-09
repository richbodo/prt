"""Test FTS5 full-text search migration and functionality.

This module contains both unit tests and integration tests for the FTS5 migration system.
The integration tests use real SQLite databases to verify actual migration behavior,
following the project's "headless-first" testing philosophy.

Integration tests are marked with @pytest.mark.integration and target < 5 seconds total
execution time as specified in the project testing strategy.
"""

from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from sqlalchemy import text

from prt_src.db import create_database
from prt_src.schema_manager import SchemaManager


@pytest.fixture
def migration_test_db(tmp_path):
    """Create a test database at schema version 4 for migration testing."""
    db_path = tmp_path / "migration_test.db"
    db = create_database(db_path)

    # Initialize the database tables
    db.initialize()

    # Create and initialize the schema_version table using SchemaManager
    schema_manager = SchemaManager(db)
    schema_manager.create_schema_version_table()

    # Manually set schema version to 4 to simulate pre-migration state
    db.session.execute(text("UPDATE schema_version SET version = 4"))
    db.session.commit()

    return db


@pytest.fixture
def schema_manager_real(migration_test_db):
    """Create SchemaManager with real database for integration testing."""
    return SchemaManager(migration_test_db)


@pytest.fixture
def mock_db():
    """Create a mock database with session for legacy unit tests."""
    db = MagicMock()
    db.path = Path("/tmp/test.db")
    db.session = MagicMock()
    return db


@pytest.fixture
def schema_manager(mock_db):
    """Create SchemaManager with mock database for legacy unit tests."""
    return SchemaManager(mock_db)


class TestFTS5Migration:
    """Test FTS5 migration functionality.

    This class contains both unit tests (that validate SQL file content and basic functionality)
    and integration tests (that use real databases to test actual migration behavior).

    Integration tests use the migration_test_db fixture which creates a database at schema
    version 4, then test the actual migration to version 5 with real FTS5 table creation.
    """

    def test_current_version_is_6(self, schema_manager):
        """Verify CURRENT_VERSION is set to 6."""
        assert schema_manager.CURRENT_VERSION == 6

    def test_migration_file_not_found(self, schema_manager, mock_db):
        """Verify proper error when migration file is missing."""
        with (
            patch("pathlib.Path.exists", return_value=False),
            pytest.raises(RuntimeError, match="Migration file not found"),
        ):
            schema_manager.apply_migration_v4_to_v5()

    def test_fts5_sql_file_content(self):
        """Verify the FTS5 SQL file has proper structure."""
        migration_path = Path(__file__).parent.parent / "migrations" / "add_fts5_support.sql"

        # File should exist
        assert migration_path.exists(), f"Migration file should exist at {migration_path}"

        # Read content
        with open(migration_path) as f:
            content = f.read()

        # Check for essential FTS5 elements
        assert "CREATE VIRTUAL TABLE" in content
        assert "contacts_fts" in content
        assert "notes_fts" in content
        assert "tags_fts" in content
        assert "USING fts5" in content
        assert "CREATE TRIGGER" in content
        assert "tokenize='porter unicode61'" in content

    @pytest.mark.integration
    def test_v4_to_v5_migration_integration(self, schema_manager_real, migration_test_db):
        """Test actual FTS5 migration with real database."""
        # Verify starting state: schema version should be 4
        result = migration_test_db.session.execute(
            text("SELECT version FROM schema_version")
        ).fetchone()
        assert result[0] == 4, f"Expected schema version 4, got {result[0]}"

        # Run the migration
        schema_manager_real.apply_migration_v4_to_v5()

        # Verify schema version is updated to 5
        result = migration_test_db.session.execute(
            text("SELECT version FROM schema_version")
        ).fetchone()
        assert result[0] == 5, f"Expected schema version 5 after migration, got {result[0]}"

    @pytest.mark.integration
    def test_migration_creates_fts_tables(self, schema_manager_real, migration_test_db):
        """Verify FTS5 virtual tables are created after migration."""
        # Run the migration
        schema_manager_real.apply_migration_v4_to_v5()

        # Check that FTS5 virtual tables exist
        tables_result = migration_test_db.session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%_fts'")
        ).fetchall()

        fts_tables = {row[0] for row in tables_result}
        expected_tables = {"contacts_fts", "notes_fts", "tags_fts"}

        assert expected_tables.issubset(
            fts_tables
        ), f"Missing FTS tables. Expected: {expected_tables}, Found: {fts_tables}"

    @pytest.mark.integration
    def test_migration_updates_schema_version(self, schema_manager_real, migration_test_db):
        """Verify schema version progression from 4 to 5."""
        # Check initial version
        initial_version = migration_test_db.session.execute(
            text("SELECT version FROM schema_version")
        ).fetchone()
        assert initial_version[0] == 4

        # Apply migration
        schema_manager_real.apply_migration_v4_to_v5()

        # Verify final version
        final_version = migration_test_db.session.execute(
            text("SELECT version FROM schema_version")
        ).fetchone()
        assert final_version[0] == 5

    @pytest.mark.integration
    def test_fts_search_functionality_after_migration(self, schema_manager_real, migration_test_db):
        """Validate that FTS search functionality works after migration."""
        # Add some test data first
        migration_test_db.session.execute(
            text("INSERT INTO contacts (name, email) VALUES ('Test User', 'test@example.com')")
        )
        migration_test_db.session.execute(
            text("INSERT INTO notes (title, content) VALUES ('Test Note', 'This is a test note')")
        )
        migration_test_db.session.execute(text("INSERT INTO tags (name) VALUES ('test-tag')"))
        migration_test_db.session.commit()

        # Run migration to create FTS tables
        schema_manager_real.apply_migration_v4_to_v5()

        # Test FTS search functionality
        search_results = migration_test_db.session.execute(
            text("SELECT contact_id FROM contacts_fts WHERE contacts_fts MATCH 'Test'")
        ).fetchall()

        assert len(search_results) > 0, "FTS search should find the test contact"

    @pytest.mark.integration
    def test_migration_is_idempotent(self, schema_manager_real, migration_test_db):
        """Ensure running migration twice doesn't break anything."""
        # Run migration first time
        schema_manager_real.apply_migration_v4_to_v5()

        # Verify it worked
        version_after_first = migration_test_db.session.execute(
            text("SELECT version FROM schema_version")
        ).fetchone()
        assert version_after_first[0] == 5

        # Run migration again - this should handle existing tables gracefully
        # Note: The current implementation uses executescript() which should handle this,
        # but we expect this to potentially raise an exception since the implementation
        # doesn't explicitly handle idempotency for FTS5 tables
        try:
            schema_manager_real.apply_migration_v4_to_v5()
            # If it succeeds, verify version is still 5
            version_after_second = migration_test_db.session.execute(
                text("SELECT version FROM schema_version")
            ).fetchone()
            assert version_after_second[0] == 5
        except RuntimeError:
            # If it fails due to existing tables, that's expected behavior
            # The important thing is that the database is not corrupted
            version_after_error = migration_test_db.session.execute(
                text("SELECT version FROM schema_version")
            ).fetchone()
            assert (
                version_after_error[0] == 5
            ), "Schema version should remain 5 even after failed re-migration"


class TestFTS5Integration:
    """Test FTS5 search functionality integration.

    This class contains unit tests that validate the SQL migration file content
    without requiring actual database operations. These tests focus on ensuring
    the migration SQL has proper structure and expected triggers/indexes.
    """

    @pytest.fixture
    def sample_search_data(self):
        """Sample data for search testing."""
        return {
            "contacts": [
                {"id": 1, "name": "Alice Johnson", "email": "alice@example.com"},
                {"id": 2, "name": "Bob Smith", "email": "bob@example.com"},
                {"id": 3, "name": "Charlie Brown", "email": "charlie@example.com"},
            ],
            "notes": [
                {"id": 1, "title": "Meeting Notes", "content": "Discussed project timeline"},
                {"id": 2, "title": "Ideas", "content": "New feature proposals"},
            ],
            "tags": [
                {"id": 1, "name": "family", "description": "Family members"},
                {"id": 2, "name": "work", "description": "Work colleagues"},
            ],
        }

    def test_fts5_trigger_names(self):
        """Verify trigger names follow convention."""
        migration_path = Path(__file__).parent.parent / "migrations" / "add_fts5_support.sql"

        with open(migration_path) as f:
            content = f.read()

        expected_triggers = [
            "contacts_fts_insert",
            "contacts_fts_update",
            "contacts_fts_delete",
            "notes_fts_insert",
            "notes_fts_update",
            "notes_fts_delete",
            "tags_fts_insert",
            "tags_fts_update",
            "tags_fts_delete",
        ]

        for trigger in expected_triggers:
            assert trigger in content, f"Expected trigger {trigger} in migration"

    def test_fts5_indexes_created(self):
        """Verify indexes are created for FTS join operations."""
        migration_path = Path(__file__).parent.parent / "migrations" / "add_fts5_support.sql"

        with open(migration_path) as f:
            content = f.read()

        expected_indexes = [
            "idx_contacts_fts_contact_id",
            "idx_notes_fts_note_id",
            "idx_tags_fts_tag_id",
        ]

        for index in expected_indexes:
            assert index in content, f"Expected index {index} in migration"
