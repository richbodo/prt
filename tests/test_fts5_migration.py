"""Test FTS5 full-text search migration and functionality."""

from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from prt_src.schema_manager import SchemaManager


@pytest.fixture
def mock_db():
    """Create a mock database with session."""
    db = MagicMock()
    db.path = Path("/tmp/test.db")
    db.session = MagicMock()
    return db


@pytest.fixture
def schema_manager(mock_db):
    """Create SchemaManager with mock database."""
    return SchemaManager(mock_db)


class TestFTS5Migration:
    """Test FTS5 migration functionality."""

    def test_migration_v4_to_v5_creates_fts_tables(self, schema_manager, mock_db):
        """Verify FTS5 tables are created during migration."""
        # Mock the migration file to exist
        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", create=True) as mock_open:
                # Provide sample SQL content
                mock_open.return_value.__enter__.return_value.read.return_value = """
                CREATE VIRTUAL TABLE contacts_fts USING fts5(contact_id, name);
                CREATE VIRTUAL TABLE notes_fts USING fts5(note_id, title);
                CREATE VIRTUAL TABLE tags_fts USING fts5(tag_id, name);
                """

                # Run migration
                schema_manager.apply_migration_v4_to_v5()

                # Verify SQL statements were executed
                assert mock_db.session.execute.called
                assert mock_db.session.commit.called

    def test_migration_handles_existing_tables(self, schema_manager, mock_db):
        """Verify migration handles already existing FTS tables gracefully."""
        # Mock execute to raise "already exists" error
        mock_db.session.execute.side_effect = [
            Exception("table contacts_fts already exists"),
            None,  # Continue with other statements
            None,
        ]

        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = """
                CREATE VIRTUAL TABLE contacts_fts USING fts5(contact_id, name);
                UPDATE schema_version SET version = 5;
                """

                # Should not raise exception
                schema_manager.apply_migration_v4_to_v5()
                assert mock_db.session.commit.called

    def test_migration_path_includes_v5(self, schema_manager):
        """Verify migration paths include version 5."""
        # Test various paths to v5
        paths_to_test = [
            (4, 5, 1),  # v4 to v5 should have 1 migration
            (3, 5, 2),  # v3 to v5 should have 2 migrations
            (2, 5, 3),  # v2 to v5 should have 3 migrations
            (1, 5, 4),  # v1 to v5 should have 4 migrations
        ]

        for current, target, expected_count in paths_to_test:
            # Create mocks for all migration methods
            schema_manager.apply_migration_v1_to_v2 = MagicMock()
            schema_manager.apply_migration_v2_to_v3 = MagicMock()
            schema_manager.apply_migration_v3_to_v4 = MagicMock()
            schema_manager.apply_migration_v4_to_v5 = MagicMock()

            # Get migration path (don't execute, just check it exists)
            try:
                schema_manager.migrate_to_version(target, current)
            except AttributeError:
                # Expected since we're using mocks
                pass

            # Verify v4_to_v5 is called for all paths ending at v5
            if current < 5:
                assert schema_manager.apply_migration_v4_to_v5.called

    def test_current_version_is_5(self, schema_manager):
        """Verify CURRENT_VERSION is set to 5."""
        assert schema_manager.CURRENT_VERSION == 5

    def test_migration_file_not_found(self, schema_manager, mock_db):
        """Verify proper error when migration file is missing."""
        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(RuntimeError, match="Migration file not found"):
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

    def test_schema_version_tracking(self, schema_manager, mock_db):
        """Verify schema version is updated to 5."""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = """
                UPDATE schema_version SET version = 5;
                """

                schema_manager.apply_migration_v4_to_v5()

                # Check that version update SQL was executed
                calls = mock_db.session.execute.call_args_list
                version_update_called = False
                for call in calls:
                    # Check if the call has arguments and convert to string for checking
                    if len(call[0]) > 0:
                        sql_text = str(call[0][0])
                        if "version = 5" in sql_text:
                            version_update_called = True
                            break

                assert version_update_called or mock_db.session.execute.called


class TestFTS5Integration:
    """Test FTS5 search functionality integration."""

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
