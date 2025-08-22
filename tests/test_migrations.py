"""
Tests for database migrations and setup.

This module tests the migration utilities, setup processes,
and encrypted database integration.
"""

import pytest
import tempfile
import shutil
import sqlite3
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the prt package to the path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

# from migrations.run_migrations import MigrationRunner, MigrationTracker  # No longer needed
from utils.setup_database import setup_database, initialize_database
from utils.encrypt_database import (
    encrypt_database,
    decrypt_database,
    backup_database,
    verify_database_integrity
)
from prt_src.config import load_config, save_config, get_encryption_key
from prt_src.db import create_database
from prt_src.encrypted_db import create_encrypted_database, PYSQLCIPHER3_AVAILABLE


def test_migration_tracker(tmp_path):
    """Test migration tracking functionality."""
    pytest.skip("Migration tracker functionality replaced by SchemaManager")
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
    pytest.skip("Migration runner functionality replaced by SchemaManager")
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
    pytest.skip("Migration runner functionality replaced by SchemaManager")
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
    pytest.skip("Migration runner functionality replaced by SchemaManager")
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
    pytest.skip("Migration runner functionality replaced by SchemaManager")
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


class TestSetupDatabase:
    """Test database setup functionality."""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary directory for configuration files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            yield temp_path
    
    def test_setup_database_basic(self, temp_config_dir):
        """Test basic database setup."""
        with patch('prt_src.config.data_dir', return_value=temp_config_dir):
            config = setup_database(quiet=True)
            
            assert 'db_username' in config
            assert 'db_password' in config
            assert 'db_path' in config
            assert config['db_encrypted'] is False
            assert config['db_type'] == 'sqlite'
    
    def test_setup_database_encrypted(self, temp_config_dir):
        """Test encrypted database setup."""
        with patch('prt_src.config.data_dir', return_value=temp_config_dir):
            config = setup_database(quiet=True, encrypted=True)
            
            assert 'db_username' in config
            assert 'db_password' in config
            assert 'db_path' in config
            assert config['db_encrypted'] is True
            assert config['db_type'] == 'sqlite'
    
    def test_setup_database_force(self, temp_config_dir):
        """Test forced database setup."""
        with patch('prt_src.config.data_dir', return_value=temp_config_dir):
            # First setup
            config1 = setup_database(quiet=True)
            
            # Force setup
            config2 = setup_database(force=True, quiet=True)
            
            # Should have different credentials
            assert config1['db_username'] != config2['db_username']
            assert config1['db_password'] != config2['db_password']


class TestInitializeDatabase:
    """Test database initialization."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database path."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        yield db_path
        # Cleanup
        if db_path.exists():
            db_path.unlink()
    
    def test_initialize_unencrypted_database(self, temp_db_path):
        """Test initializing an unencrypted database."""
        config = {
            'db_path': str(temp_db_path),
            'db_encrypted': False
        }
        
        result = initialize_database(config, quiet=True)
        assert result is True
        
        # Verify database was created
        assert temp_db_path.exists()
        
        # Verify it's a valid database
        db = create_database(temp_db_path, encrypted=False)
        assert db.is_valid() is True
    
    def test_initialize_encrypted_database(self, temp_db_path):
        """Test initializing an encrypted database."""
        config = {
            'db_path': str(temp_db_path),
            'db_encrypted': True
        }
        
        result = initialize_database(config, quiet=True)
        assert result is True
        
        # Verify database was created
        assert temp_db_path.exists()
        
        # Verify it's a valid encrypted database
        db = create_encrypted_database(temp_db_path)
        assert db.is_valid() is True
        assert db.test_encryption() is True
    
    def test_initialize_existing_database(self, temp_db_path):
        """Test initializing when database already exists."""
        # Create database first
        config = {
            'db_path': str(temp_db_path),
            'db_encrypted': False
        }
        
        initialize_database(config, quiet=True)
        
        # Try to initialize again
        result = initialize_database(config, quiet=True)
        assert result is True  # Should succeed with existing database


class TestEncryptionMigration:
    """Test encryption migration functionality."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database path."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        yield db_path
        # Cleanup
        if db_path.exists():
            db_path.unlink()
    
    def test_encrypt_database(self, temp_db_path):
        """Test encrypting an unencrypted database."""
        # Create unencrypted database with data
        db = create_database(temp_db_path, encrypted=False)
        db.initialize()
        
        # Add some test data
        from prt_src.models import Contact, Relationship
        contact = Contact(name="Test Contact", email="test@example.com")
        db.session.add(contact)
        db.session.flush()
        
        relationship = Relationship(contact_id=contact.id)
        db.session.add(relationship)
        db.session.commit()
        db.session.close()
        
        # Encrypt the database
        result = encrypt_database(
            db_path=temp_db_path,
            backup=False,
            verify=True,
            quiet=True
        )
        
        assert result is True
        
        # Verify it's now encrypted
        encrypted_db = create_encrypted_database(temp_db_path)
        assert encrypted_db.is_valid() is True
        assert encrypted_db.test_encryption() is True
        
        # Verify data is still there
        assert encrypted_db.count_contacts() == 1
        assert encrypted_db.count_relationships() == 1
    
    def test_decrypt_database(self, temp_db_path):
        """Test decrypting an encrypted database."""
        # Create encrypted database with data
        db = create_encrypted_database(temp_db_path)
        db.initialize()
        
        # Add some test data
        from prt_src.models import Contact, Relationship
        contact = Contact(name="Test Contact", email="test@example.com")
        db.session.add(contact)
        db.session.flush()
        
        relationship = Relationship(contact_id=contact.id)
        db.session.add(relationship)
        db.session.commit()
        db.session.close()
        
        # Decrypt the database
        result = decrypt_database(
            db_path=temp_db_path,
            backup=False,
            quiet=True
        )
        
        assert result is True
        
        # Verify it's now unencrypted
        unencrypted_db = create_database(temp_db_path, encrypted=False)
        assert unencrypted_db.is_valid() is True
        
        # Verify data is still there
        assert unencrypted_db.count_contacts() == 1
        assert unencrypted_db.count_relationships() == 1
    
    def test_backup_database(self, temp_db_path):
        """Test database backup functionality."""
        # Create a database file
        db = create_database(temp_db_path, encrypted=False)
        db.initialize()
        db.session.close()
        
        # Create backup
        backup_path = backup_database(temp_db_path, ".test_backup")
        
        assert backup_path.exists()
        assert backup_path != temp_db_path
        
        # Cleanup
        backup_path.unlink()
    
    def test_verify_database_integrity(self, temp_db_path):
        """Test database integrity verification."""
        # Create a valid database
        db = create_database(temp_db_path, encrypted=False)
        db.initialize()
        
        # Add some data
        from prt_src.models import Contact
        contact = Contact(name="Test Contact", email="test@example.com")
        db.session.add(contact)
        db.session.commit()
        
        # Verify integrity
        result = verify_database_integrity(db)
        assert result is True
        
        db.session.close()


class TestErrorHandling:
    """Test error handling in migrations."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database path."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        yield db_path
        # Cleanup
        if db_path.exists():
            db_path.unlink()
    
    def test_encrypt_nonexistent_database(self):
        """Test encrypting a database that doesn't exist."""
        result = encrypt_database(
            db_path=Path("/nonexistent/path/database.db"),
            backup=False,
            quiet=True
        )
        
        assert result is False
    
    def test_encrypt_already_encrypted_database(self, temp_db_path):
        """Test encrypting an already encrypted database.""" 
        from unittest.mock import patch
        
        # Create encrypted database
        db = create_encrypted_database(temp_db_path)
        db.initialize()
        db.session.close()
        
        # Mock the config to indicate database is encrypted
        mock_config = {
            'db_path': str(temp_db_path),
            'db_encrypted': True
        }
        
        with patch('utils.encrypt_database.load_config', return_value=mock_config):
            # Try to encrypt again
            result = encrypt_database(
                db_path=temp_db_path,
                backup=False,
                force=False,
                quiet=True
            )
        
        # Should fail without force flag
        assert result is False
    
    def test_decrypt_with_wrong_key(self, temp_db_path):
        """Test decrypting with wrong encryption key."""
        if not PYSQLCIPHER3_AVAILABLE:
            pytest.skip("pysqlcipher3 not available")

        # Create encrypted database with actual data
        db = create_encrypted_database(temp_db_path, "correct_key_32_bytes_long_key!")
        db.initialize()
        
        # Add some test data
        from prt_src.models import Contact, Relationship
        contact = Contact(name="Test Contact", email="test@example.com")
        db.session.add(contact)
        db.session.flush()
        
        relationship = Relationship(contact_id=contact.id)
        db.session.add(relationship)
        db.session.commit()
        db.session.close()
        
        # Try to decrypt with wrong key
        result = decrypt_database(
            db_path=temp_db_path,
            encryption_key="wrong_key_32_bytes_long_key!",
            backup=False,
            quiet=True
        )

        assert result is False


class TestConfigurationIntegration:
    """Test configuration integration with migrations."""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary directory for configuration files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            yield temp_path
    
    def test_config_persistence_after_encryption(self, temp_config_dir):
        """Test that configuration is updated after encryption."""
        with patch('prt_src.config.data_dir', return_value=temp_config_dir):
            # Setup unencrypted database
            config = setup_database(quiet=True, encrypted=False)
            db_path = Path(config['db_path'])
            
            # Initialize database
            initialize_database(config, quiet=True)
            
            # Encrypt database
            result = encrypt_database(
                db_path=db_path,
                backup=False,
                quiet=True
            )
            
            assert result is True
            
            # Verify config was updated
            updated_config = load_config()
            assert updated_config['db_encrypted'] is True
    
    def test_config_persistence_after_decryption(self, temp_config_dir):
        """Test that configuration is updated after decryption."""
        with patch('prt_src.config.data_dir', return_value=temp_config_dir):
            # Setup encrypted database
            config = setup_database(quiet=True, encrypted=True)
            db_path = Path(config['db_path'])
            
            # Initialize database
            initialize_database(config, quiet=True)
            
            # Decrypt database
            result = decrypt_database(
                db_path=db_path,
                backup=False,
                quiet=True
            )
            
            assert result is True
            
            # Verify config was updated
            updated_config = load_config()
            assert updated_config['db_encrypted'] is False
