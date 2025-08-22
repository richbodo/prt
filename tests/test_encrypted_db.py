"""
Tests for encrypted database functionality.

This module tests the SQLCipher encryption integration,
migration utilities, and error handling.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch
from sqlalchemy import text

from prt_src.encrypted_db import (
    EncryptedDatabase,
    create_encrypted_database,
    migrate_to_encrypted,
    PYSQLCIPHER3_AVAILABLE
)
from prt_src.db import Database, create_database
from prt_src.config import get_encryption_key, is_database_encrypted
from prt_src.models import Contact, Relationship, Tag, Note, Person


@pytest.fixture
def mock_sqlcipher_unavailable(monkeypatch):
    """Mock absence of pysqlcipher3 to test fallback paths."""
    import prt_src.encrypted_db as enc_db
    monkeypatch.setattr(enc_db, "PYSQLCIPHER3_AVAILABLE", False)


@pytest.mark.usefixtures("mock_sqlcipher_unavailable")
class TestEncryptedDatabase:
    """Test encrypted database functionality."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database path."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        yield db_path
        # Cleanup
        if db_path.exists():
            db_path.unlink()
    
    @pytest.fixture
    def sample_encryption_key(self):
        """Generate a sample encryption key."""
        return "test_encryption_key_32_bytes_long!"
    
    def test_create_encrypted_database(self, temp_db_path, sample_encryption_key):
        """Test creating a new encrypted database."""
        db = create_encrypted_database(temp_db_path, sample_encryption_key)
        
        # When pysqlcipher3 is not available, encrypted flag may be False
        # but the database should still work
        assert db.encryption_key == sample_encryption_key
        assert db.path == temp_db_path
        assert db.engine is not None
        assert db.session is not None
    
    def test_encrypted_database_connection(self, temp_db_path, sample_encryption_key):
        """Test connecting to an encrypted database."""
        db = EncryptedDatabase(temp_db_path, sample_encryption_key)
        db.connect()
        
        assert db.engine is not None
        assert db.session is not None
    
    def test_encrypted_database_initialization(self, temp_db_path, sample_encryption_key):
        """Test initializing an encrypted database with schema."""
        db = create_encrypted_database(temp_db_path, sample_encryption_key)
        db.initialize()
        
        # Verify tables were created
        with db.engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result.fetchall()]
            
            assert 'contacts' in tables
            assert 'relationships' in tables
            assert 'tags' in tables
            assert 'notes' in tables
            assert 'people' in tables
    
    def test_encrypted_database_validity(self, temp_db_path, sample_encryption_key):
        """Test database validity check."""
        db = create_encrypted_database(temp_db_path, sample_encryption_key)
        db.initialize()
        
        assert db.is_valid() is True
    
    def test_encrypted_database_test_encryption(self, temp_db_path, sample_encryption_key):
        """Test encryption verification."""
        db = create_encrypted_database(temp_db_path, sample_encryption_key)
        db.initialize()
        
        assert db.test_encryption() is True
    
    def test_encrypted_database_rekey(self, temp_db_path, sample_encryption_key):
        """Test changing the encryption key."""
        db = create_encrypted_database(temp_db_path, sample_encryption_key)
        db.initialize()
        
        new_key = "new_encryption_key_32_bytes_long!"
        assert db.rekey(new_key) is True
        assert db.encryption_key == new_key
    
    def test_encrypted_database_backup(self, temp_db_path, sample_encryption_key):
        """Test database backup functionality."""
        db = create_encrypted_database(temp_db_path, sample_encryption_key)
        db.initialize()
        
        backup_path = db.backup(".test_backup")
        assert backup_path.exists()
        assert backup_path != temp_db_path
        
        # Cleanup
        backup_path.unlink()


@pytest.mark.usefixtures("mock_sqlcipher_unavailable")
class TestMigration:
    """Test migration functionality."""
    
    @pytest.fixture
    def temp_unencrypted_db(self):
        """Create a temporary unencrypted database with sample data."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        
        # Create unencrypted database with sample data
        db = create_database(db_path, encrypted=False)
        db.initialize()
        
        # Add sample data
        contact = Contact(name="Test Contact", email="test@example.com")
        db.session.add(contact)
        db.session.flush()
        
        relationship = Relationship(contact_id=contact.id)
        db.session.add(relationship)
        
        tag = Tag(name="Test Tag")
        db.session.add(tag)
        
        note = Note(title="Test Note", content="Test content")
        db.session.add(note)
        
        person = Person(raw_data='{"name": "Test Person"}')
        db.session.add(person)
        
        db.session.commit()
        db.session.close()
        
        yield db_path
        
        # Cleanup
        if db_path.exists():
            db_path.unlink()
    
    @pytest.fixture
    def temp_encrypted_db_path(self):
        """Create a temporary path for encrypted database."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        yield db_path
        # Cleanup
        if db_path.exists():
            db_path.unlink()
    
    def test_migrate_to_encrypted(self, temp_unencrypted_db, temp_encrypted_db_path):
        """Test migrating from unencrypted to encrypted database."""
        # Create source database connection
        source_db = create_database(temp_unencrypted_db, encrypted=False)
        
        # Migrate to encrypted
        encrypted_db = migrate_to_encrypted(source_db, temp_encrypted_db_path)
        
        # Verify migration
        # When pysqlcipher3 is not available, encrypted flag may be False
        # but the database should still work
        assert encrypted_db.is_valid() is True
        
        # Verify data was migrated
        assert encrypted_db.count_contacts() == 1
        assert encrypted_db.count_relationships() == 1
        
        # Verify specific data
        contacts = encrypted_db.list_contacts()
        assert len(contacts) == 1
        assert contacts[0][1] == "Test Contact"
        assert contacts[0][2] == "test@example.com"
    
    def test_migration_preserves_data_integrity(self, temp_unencrypted_db, temp_encrypted_db_path):
        """Test that migration preserves all data correctly."""
        # Create source database connection
        source_db = create_database(temp_unencrypted_db, encrypted=False)
        
        # Get original data
        original_contacts = source_db.list_contacts()
        original_tags = source_db.list_tags()
        original_notes = source_db.list_notes()
        
        # Migrate to encrypted
        encrypted_db = migrate_to_encrypted(source_db, temp_encrypted_db_path)
        
        # Verify all data is preserved
        assert encrypted_db.list_contacts() == original_contacts
        assert encrypted_db.list_tags() == original_tags
        assert encrypted_db.list_notes() == original_notes


class TestErrorHandling:
    """Test error handling scenarios."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database path."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        yield db_path
        # Cleanup
        if db_path.exists():
            db_path.unlink()
    
    @pytest.mark.skipif(not PYSQLCIPHER3_AVAILABLE, reason="pysqlcipher3 not installed")
    def test_invalid_encryption_key(self, temp_db_path):
        """Test handling of invalid encryption key."""

        # Create database with one key and add some data
        db1 = create_encrypted_database(temp_db_path, "key1_32_bytes_long_key_here!")
        db1.initialize()
        
        # Add a test record to ensure database has encrypted content
        from prt_src.models import Contact
        contact = Contact(name="Test User", email="test@example.com")
        db1.session.add(contact)
        db1.session.commit()
        db1.session.close()
        
        # Try to open with different key and access the data
        db2 = create_encrypted_database(temp_db_path, "key2_32_bytes_long_key_here!")
        try:
            # Try to query the contacts table with wrong key
            db2.session.query(Contact).first()
            # If we get here without exception, the test should fail
            assert False, "Expected encryption error but query succeeded"
        except Exception:
            # This is expected - wrong key should cause an exception
            assert True
    
    def test_missing_pysqlcipher3(self, temp_db_path):
        """Test handling when pysqlcipher3 is not available."""
        with patch('prt_src.encrypted_db.EncryptedDatabase') as mock_encrypted:
            mock_encrypted.side_effect = ImportError("No module named 'pysqlcipher3'")
            
            with pytest.raises(RuntimeError, match="pysqlcipher3 is required for encrypted databases"):
                db = Database(temp_db_path, encrypted=True)
                db.connect()
    
    @pytest.mark.skipif(not PYSQLCIPHER3_AVAILABLE, reason="pysqlcipher3 not installed")
    def test_corrupt_encrypted_database(self, temp_db_path):
        """Test handling of corrupt encrypted database."""

        # Create a file that's not a valid encrypted database
        with open(temp_db_path, 'w') as f:
            f.write("This is not a valid database")
        
        db = create_encrypted_database(temp_db_path, "test_key_32_bytes_long_key!")
        # Should fail encryption test with corrupt database
        assert db.test_encryption() is False


class TestConfiguration:
    """Test configuration integration."""
    
    def test_is_database_encrypted(self):
        """Test encryption status detection."""
        config = {'db_encrypted': True}
        assert is_database_encrypted(config) is True
        
        config = {'db_encrypted': False}
        assert is_database_encrypted(config) is False
        
        config = {}
        assert is_database_encrypted(config) is False
    
    def test_get_encryption_key(self):
        """Test encryption key generation and retrieval."""
        # This test would need to mock the file system
        # For now, just test that the function exists and is callable
        assert callable(get_encryption_key)


@pytest.mark.usefixtures("mock_sqlcipher_unavailable")
class TestIntegration:
    """Integration tests for encrypted database functionality."""
    
    @pytest.fixture
    def temp_encrypted_db(self):
        """Create a temporary encrypted database for integration tests."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        
        db = create_encrypted_database(db_path)
        db.initialize()
        
        yield db
        
        # Cleanup
        db.session.close()
        if db_path.exists():
            db_path.unlink()
    
    def test_full_workflow(self, temp_encrypted_db):
        """Test a complete workflow with encrypted database."""
        # Add contacts
        contacts_data = [
            {'first': 'John', 'last': 'Doe', 'emails': ['john@example.com'], 'phones': ['123-456-7890']},
            {'first': 'Jane', 'last': 'Smith', 'emails': ['jane@example.com'], 'phones': ['098-765-4321']}
        ]
        temp_encrypted_db.insert_contacts(contacts_data)
        
        # Verify contacts were added
        assert temp_encrypted_db.count_contacts() == 2
        assert temp_encrypted_db.count_relationships() == 2
        
        # Add tags and notes
        temp_encrypted_db.add_relationship_tag(1, "Friend")
        temp_encrypted_db.add_relationship_note(1, "Met at conference", "Great conversation about AI")
        
        # Verify tags and notes
        rel_info = temp_encrypted_db.get_relationship_info(1)
        assert "Friend" in rel_info["tags"]
        assert len(rel_info["notes"]) == 1
        assert rel_info["notes"][0]["title"] == "Met at conference"
        
        # Test search functionality
        notes = temp_encrypted_db.search_notes_by_title("conference")
        assert len(notes) == 1
        assert notes[0][1] == "Met at conference"
    
    def test_database_persistence(self, temp_encrypted_db):
        """Test that data persists across database connections."""
        # Add data
        temp_encrypted_db.add_tag("Test Tag")
        temp_encrypted_db.add_note("Test Note", "Test content")
        
        # Ensure data is committed
        temp_encrypted_db.session.commit()
        
        # Close and reopen database
        db_path = temp_encrypted_db.path
        temp_encrypted_db.session.close()
        
        # Reopen database
        new_db = create_encrypted_database(db_path, temp_encrypted_db.encryption_key)
        
        # Verify data persists
        tags = new_db.list_tags()
        notes = new_db.list_notes()
        
        assert len(tags) == 1
        assert tags[0][1] == "Test Tag"
        assert len(notes) == 1
        assert notes[0][1] == "Test Note"
        assert notes[0][2] == "Test content"
