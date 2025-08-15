import pytest
from pathlib import Path
import sqlite3
from migrations.run_migrations import MigrationRunner, MigrationTracker


def test_migration_tracker(tmp_path):
    """Test migration tracking functionality."""
    db_path = tmp_path / "test.db"
    
    # Create a test database
    conn = sqlite3.connect(db_path)
    conn.close()
    
    tracker = MigrationTracker(db_path)
    
    # Test initial state
    applied = tracker.get_applied_migrations()
    assert applied == []
    
    # Test marking migrations as applied
    tracker.mark_migration_applied("test_migration_001")
    applied = tracker.get_applied_migrations()
    assert "test_migration_001" in applied
    
    # Test checking if migration is applied
    assert tracker.is_migration_applied("test_migration_001") == True
    assert tracker.is_migration_applied("test_migration_002") == False


def test_migration_runner_initialization(tmp_path):
    """Test migration runner initialization."""
    db_path = tmp_path / "test.db"
    
    # Create a test database
    conn = sqlite3.connect(db_path)
    conn.close()
    
    runner = MigrationRunner(db_path)
    
    # Test that migration history table was created
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='migration_history'")
    assert cursor.fetchone() is not None
    conn.close()


def test_migration_runner_list_migrations(tmp_path):
    """Test that migration runner can list available migrations."""
    db_path = tmp_path / "test.db"
    
    # Create a test database
    conn = sqlite3.connect(db_path)
    conn.close()
    
    runner = MigrationRunner(db_path)
    
    # Test getting available migrations
    migrations = runner.get_available_migrations()
    # Should find our migration files
    assert len(migrations) > 0
    
    # Check that they're sorted by number
    migration_names = [m.stem for m in migrations]
    assert "001_fix_contacts_schema" in migration_names
    assert "002_fix_relationships_schema" in migration_names


def test_migration_runner_status(tmp_path):
    """Test migration status reporting."""
    db_path = tmp_path / "test.db"
    
    # Create a test database
    conn = sqlite3.connect(db_path)
    conn.close()
    
    runner = MigrationRunner(db_path)
    
    # Test status reporting (should not crash)
    runner.show_status()
    
    # Test listing migrations (should not crash)
    runner.list_migrations()


def test_migration_runner_with_no_migrations(tmp_path):
    """Test migration runner behavior when no migrations are available."""
    db_path = tmp_path / "test.db"
    
    # Create a test database
    conn = sqlite3.connect(db_path)
    conn.close()
    
    # Create a temporary migration directory with no migration files
    temp_migrations_dir = tmp_path / "temp_migrations"
    temp_migrations_dir.mkdir()
    
    # Temporarily modify the runner to use empty directory
    runner = MigrationRunner(db_path)
    original_migrations_dir = runner.migrations_dir
    runner.migrations_dir = temp_migrations_dir
    
    # Test that it handles empty migration directory gracefully
    migrations = runner.get_available_migrations()
    assert len(migrations) == 0
    
    # Test that status reporting works with no migrations
    runner.show_status()
