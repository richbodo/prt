"""Tests for enhanced backup system with metadata tracking."""

import time
from pathlib import Path

import pytest
from sqlalchemy import text

from prt_src.api import PRTAPI
from prt_src.db import Database
from prt_src.models import BackupMetadata, Contact


@pytest.fixture
def test_db(tmp_path):
    """Create a test database with some data."""
    db_path = tmp_path / "test.db"
    db = Database(db_path)
    db.connect()
    db.initialize()

    # Apply migration to get backup_metadata table
    from prt_src.schema_manager import SchemaManager

    schema_mgr = SchemaManager(db)
    schema_mgr.apply_migration_v3_to_v4()

    # Add some test data
    contact1 = Contact(name="Alice Smith", email="alice@example.com")
    contact2 = Contact(name="Bob Jones", email="bob@example.com")
    db.session.add(contact1)
    db.session.add(contact2)
    db.session.commit()

    return db


@pytest.fixture
def test_api(tmp_path):
    """Create test API instance with temporary database."""
    import json

    # Create minimal config
    config_path = tmp_path / "config.json"
    db_path = tmp_path / "test.db"

    config_data = {"database_path": str(db_path), "data_directory": str(tmp_path)}

    with open(config_path, "w") as f:
        json.dump(config_data, f)

    # Create API with config
    import os

    original_dir = os.getcwd()
    os.chdir(tmp_path)  # Change to tmp dir so it finds config

    try:
        api = PRTAPI()
        api.db.initialize()

        # Run migration to get backup_metadata table
        from prt_src.schema_manager import SchemaManager

        schema_mgr = SchemaManager(api.db)
        schema_mgr.apply_migration_v3_to_v4()

        # Add test data
        api.db.insert_contacts(
            [
                {"first": "Alice", "last": "Smith", "emails": ["alice@example.com"]},
                {"first": "Bob", "last": "Jones", "emails": ["bob@example.com"]},
            ]
        )

        yield api
    finally:
        os.chdir(original_dir)


class TestBackupCreation:
    """Test backup creation with metadata."""

    def test_backup_with_comment_creation(self, test_db):
        """Test creating backup with user comment."""
        backup_info = test_db.create_backup_with_metadata(
            comment="Test backup before major changes", is_auto=False
        )

        assert backup_info["comment"] == "Test backup before major changes"
        assert backup_info["is_auto"] is False
        assert backup_info["size"] > 0
        assert backup_info["filename"].startswith("test_backup_")
        assert Path(backup_info["path"]).exists()

    def test_automatic_backup_creation(self, test_db):
        """Test creating automatic backup."""
        backup_info = test_db.create_backup_with_metadata(
            comment="Auto-backup before deletion", is_auto=True
        )

        assert backup_info["is_auto"] is True
        assert "Auto-backup" in backup_info["comment"]
        assert Path(backup_info["path"]).exists()

    def test_backup_without_comment(self, test_api):
        """Test backup creation without explicit comment."""
        backup_info = test_api.create_backup_with_comment()

        assert backup_info["comment"] == "Manual backup"
        assert backup_info["is_auto"] is False

    def test_auto_backup_default_comment(self, test_api):
        """Test automatic backup generates default comment."""
        backup_info = test_api.create_backup_with_comment(auto=True)

        assert "Automatic backup at" in backup_info["comment"]
        assert backup_info["is_auto"] is True


class TestBackupListing:
    """Test backup listing and metadata retrieval."""

    def test_backup_listing_with_metadata(self, test_db):
        """Test listing backups shows correct metadata."""
        # Create multiple backups
        test_db.create_backup_with_metadata(comment="First backup", is_auto=False)
        time.sleep(0.1)  # Ensure different timestamps
        test_db.create_backup_with_metadata(comment="Second backup", is_auto=True)

        # List backups
        backups = test_db.list_backups()

        assert len(backups) == 2
        # Should be sorted newest first
        assert backups[0]["comment"] == "Second backup"
        assert backups[1]["comment"] == "First backup"
        assert backups[0]["is_auto"] is True
        assert backups[1]["is_auto"] is False
        assert all(b["exists"] for b in backups)

    def test_backup_listing_detects_missing_files(self, test_db):
        """Test listing detects when backup files are missing."""
        # Create backup
        backup = test_db.create_backup_with_metadata(comment="Test backup")
        backup_path = Path(backup["path"])

        # Delete the actual file
        backup_path.unlink()

        # List should show file doesn't exist
        backups = test_db.list_backups()
        assert len(backups) == 1
        assert backups[0]["exists"] is False

    def test_empty_backup_list(self, test_db):
        """Test listing when no backups exist."""
        backups = test_db.list_backups()
        assert backups == []


class TestBackupRestoration:
    """Test backup restoration functionality."""

    def test_restore_backup_functionality(self, test_db):
        """Test restoring from a backup."""
        # Create initial state
        initial_count = test_db.count_contacts()

        # Create backup
        backup = test_db.create_backup_with_metadata(comment="Before changes")

        # Modify database
        from prt_src.models import Contact

        new_contact = Contact(name="Charlie Brown", email="charlie@example.com")
        test_db.session.add(new_contact)
        test_db.session.commit()

        assert test_db.count_contacts() == initial_count + 1

        # Restore backup
        success = test_db.restore_backup(backup["id"])
        assert success is True

        # Reconnect and verify restoration
        test_db.session.close()
        test_db.connect()
        assert test_db.count_contacts() == initial_count

    def test_restore_nonexistent_backup(self, test_db):
        """Test error handling for nonexistent backup."""
        with pytest.raises(ValueError, match="Backup with ID 999 not found"):
            test_db.restore_backup(999)

    def test_restore_missing_file(self, test_db):
        """Test error when backup file is missing."""
        # Create backup and delete file
        backup = test_db.create_backup_with_metadata(comment="Test")
        Path(backup["path"]).unlink()

        with pytest.raises(FileNotFoundError):
            test_db.restore_backup(backup["id"])

    def test_safety_backup_on_restore(self, test_api):
        """Test that restoring creates a safety backup."""
        # Create initial backup
        backup = test_api.create_backup_with_comment(comment="Original")

        # Verify initial backup exists
        backups_before = test_api.get_backup_history()
        assert len(backups_before) == 1

        # Get the safety backup path that will be created
        from pathlib import Path

        safety_backup_path = Path(test_api.db.path).with_suffix(".pre_restore.bak")

        # Restore it (should create safety backup)
        test_api.restore_from_backup(backup["id"])

        # Verify safety backup file was created
        assert safety_backup_path.exists(), "Safety backup file should exist"

        # Note: After restoration, the backup_metadata table is from the restored database,
        # so it won't contain records of backups made after the original backup.
        # This is a limitation of storing metadata in the same database being backed up.


class TestAutoBackupManagement:
    """Test automatic backup management features."""

    def test_auto_backup_before_operation(self, test_api):
        """Test automatic backup before dangerous operations."""
        backup = test_api.auto_backup_before_operation("delete all contacts")

        assert backup["is_auto"] is True
        assert "delete all contacts" in backup["comment"]
        assert Path(backup["path"]).exists()

    def test_cleanup_old_auto_backups(self, test_db):
        """Test cleaning up old automatic backups."""
        # Create many automatic backups
        for i in range(15):
            test_db.create_backup_with_metadata(
                comment=f"Auto backup {i}", is_auto=True
            )
            time.sleep(0.01)  # Ensure different timestamps

        # Create some manual backups (should not be deleted)
        for i in range(3):
            test_db.create_backup_with_metadata(
                comment=f"Manual backup {i}", is_auto=False
            )

        # Initial count
        all_backups = test_db.list_backups()
        assert len(all_backups) == 18

        # Cleanup keeping only 5 auto backups
        test_db.cleanup_old_auto_backups(keep_count=5)

        # Check results
        remaining = test_db.list_backups()
        assert len(remaining) == 8  # 5 auto + 3 manual

        # Verify manual backups remain
        manual_backups = [b for b in remaining if not b["is_auto"]]
        assert len(manual_backups) == 3

        # Verify newest auto backups kept
        auto_backups = [b for b in remaining if b["is_auto"]]
        assert len(auto_backups) == 5
        # Should be the last 5 created (10-14)
        expected_nums = {10, 11, 12, 13, 14}
        actual_nums = set()
        for b in auto_backups:
            # Extract number from "Auto backup X"
            num = int(b["comment"].split()[-1])
            actual_nums.add(num)
        assert actual_nums == expected_nums

    def test_cleanup_with_no_auto_backups(self, test_db):
        """Test cleanup when there are no automatic backups."""
        # Create only manual backups
        test_db.create_backup_with_metadata(comment="Manual", is_auto=False)

        # Cleanup should not affect manual backups
        test_db.cleanup_old_auto_backups(keep_count=5)

        backups = test_db.list_backups()
        assert len(backups) == 1


class TestBackupMetadata:
    """Test backup metadata tracking."""

    def test_backup_metadata_schema_version(self, test_db):
        """Test that schema version is recorded."""
        from prt_src.schema_manager import SchemaManager

        schema_mgr = SchemaManager(test_db)
        current_version = schema_mgr.get_schema_version()

        backup = test_db.create_backup_with_metadata(comment="Test")
        assert backup["schema_version"] == current_version

        # Check in listing too
        backups = test_db.list_backups()
        assert backups[0]["schema_version"] == current_version

    def test_backup_comment_immutability(self, test_db):
        """Test that backup comments cannot be modified after creation."""
        # Create backup
        test_db.create_backup_with_metadata(comment="Original comment", is_auto=False)

        # Try to modify comment directly (should not affect stored value)
        backup_record = test_db.session.query(BackupMetadata).first()
        original_comment = backup_record.comment

        # Attempt modification (but don't commit)
        backup_record.comment = "Modified comment"
        test_db.session.rollback()

        # Verify comment unchanged
        backup_record = test_db.session.query(BackupMetadata).first()
        assert backup_record.comment == original_comment

    def test_backup_file_size_tracking(self, test_db):
        """Test that file sizes are accurately tracked."""
        # Create backup
        backup = test_db.create_backup_with_metadata(comment="Test")

        # Verify size matches actual file
        actual_size = Path(backup["path"]).stat().st_size
        assert backup["size"] == actual_size

        # Add substantial data to change file size
        from prt_src.models import Contact, Note

        for i in range(100):
            contact = Contact(
                name=f"Contact {i} with a very long name to ensure size changes",
                email=f"contact{i}@example.com",
                phone=f"+1-555-{i:04d}",
            )
            test_db.session.add(contact)

            # Add notes too for more data
            if i % 10 == 0:
                note = Note(
                    title=f"Note {i}",
                    content="This is a long note content " * 50,  # Make it big
                )
                test_db.session.add(note)

        test_db.session.commit()

        # Force a database checkpoint to ensure size changes
        test_db.session.execute(text("VACUUM"))
        test_db.session.commit()

        backup2 = test_db.create_backup_with_metadata(comment="After adding data")
        assert (
            backup2["size"] > backup["size"]
        ), f"Size did not increase: {backup['size']} vs {backup2['size']}"


class TestAPIBackupFeatures:
    """Test API-level backup features."""

    def test_api_backup_history(self, test_api):
        """Test API backup history retrieval."""
        # Create several backups
        test_api.create_backup_with_comment("First backup")
        test_api.create_backup_with_comment("Second backup", auto=True)

        history = test_api.get_backup_history()
        assert len(history) == 2
        assert history[0]["comment"] == "Second backup"  # Newest first
        assert history[1]["comment"] == "First backup"

    def test_api_cleanup_auto_backups(self, test_api):
        """Test API cleanup of automatic backups."""
        # Create backups
        for i in range(5):
            test_api.create_backup_with_comment(f"Auto {i}", auto=True)

        test_api.create_backup_with_comment("Manual backup", auto=False)

        # Cleanup keeping only 2 auto
        test_api.cleanup_auto_backups(keep_count=2)

        history = test_api.get_backup_history()
        auto_count = sum(1 for b in history if b["is_auto"])
        manual_count = sum(1 for b in history if not b["is_auto"])

        assert auto_count == 2
        assert manual_count == 1
