"""
Tests for the PRT API layer.
"""

import pytest
from pathlib import Path
from prt_src.api import PRTAPI
from prt_src.config import load_config


class TestPRTAPI:
    """Test the PRT API functionality."""
    
    def test_api_initialization(self, tmp_path):
        """Test API initialization with custom database path."""
        db_path = tmp_path / "test.db"
        config = {"db_path": str(db_path), "db_encrypted": False}
        api = PRTAPI(config)
        assert api.db.path == db_path
    
    def test_api_initialization_default(self):
        """Test API initialization with default database path."""
        api = PRTAPI()
        config = load_config()
        expected_path = Path(config["db_path"])
        assert api.db.path == expected_path
    
    def test_get_database_stats(self):
        """Test getting database statistics."""
        api = PRTAPI()
        stats = api.get_database_stats()
        
        assert isinstance(stats, dict)
        assert "contacts" in stats
        assert "relationships" in stats
        assert isinstance(stats["contacts"], int)
        assert isinstance(stats["relationships"], int)
        assert stats["contacts"] >= 0
        assert stats["relationships"] >= 0
    
    def test_validate_database(self):
        """Test database validation."""
        api = PRTAPI()
        is_valid = api.validate_database()
        assert isinstance(is_valid, bool)
    
    def test_backup_database(self, tmp_path):
        """Test database backup functionality."""
        # Create a test database
        db_path = tmp_path / "test.db"
        config = {"db_path": str(db_path), "db_encrypted": False}
        api = PRTAPI(config)
        api.db.initialize()  # Create the database
        
        # Test backup
        backup_path = api.backup_database()
        assert backup_path.exists()
        assert backup_path.suffix == ".bak"
    
    def test_get_config(self):
        """Test getting configuration."""
        api = PRTAPI()
        config = api.get_config()
        
        assert isinstance(config, dict)
        assert "db_path" in config
    
    def test_get_data_directory(self):
        """Test getting data directory."""
        api = PRTAPI()
        data_dir = api.get_data_directory()
        
        assert isinstance(data_dir, Path)
        assert data_dir.exists()
    
    def test_test_database_connection(self):
        """Test database connection testing."""
        api = PRTAPI()
        is_connected = api.test_database_connection()
        assert isinstance(is_connected, bool)
    
    def test_get_csv_files(self):
        """Test getting CSV files from data directory."""
        api = PRTAPI()
        csv_files = api.get_csv_files()
        
        assert isinstance(csv_files, list)
        for file_path in csv_files:
            assert isinstance(file_path, Path)
            assert file_path.suffix == ".csv"
    
    def test_parse_csv_contacts_empty_file(self, tmp_path):
        """Test parsing empty CSV file."""
        # Create an empty CSV file
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("")
        
        api = PRTAPI()
        contacts = api.parse_csv_contacts(str(csv_file))
        
        assert isinstance(contacts, list)
        # Empty file should return empty list or handle gracefully
    
    def test_search_contacts(self):
        """Test contact search functionality."""
        api = PRTAPI()
        results = api.search_contacts("test")
        
        assert isinstance(results, list)
        for contact in results:
            assert isinstance(contact, dict)
            assert "id" in contact
            assert "name" in contact
            assert "email" in contact
            assert "phone" in contact
            assert "relationship_info" in contact
    
    def test_list_all_contacts(self):
        """Test listing all contacts."""
        api = PRTAPI()
        contacts = api.list_all_contacts()
        
        assert isinstance(contacts, list)
        for contact in contacts:
            assert isinstance(contact, dict)
            assert "id" in contact
            assert "name" in contact
            assert "email" in contact
            assert "phone" in contact
            assert "relationship_info" in contact
    
    def test_list_all_tags(self):
        """Test listing all tags."""
        api = PRTAPI()
        tags = api.list_all_tags()
        
        assert isinstance(tags, list)
        for tag in tags:
            assert isinstance(tag, dict)
            assert "id" in tag
            assert "name" in tag
            assert "contact_count" in tag
    
    def test_list_all_notes(self):
        """Test listing all notes."""
        api = PRTAPI()
        notes = api.list_all_notes()
        
        assert isinstance(notes, list)
        for note in notes:
            assert isinstance(note, dict)
            assert "id" in note
            assert "title" in note
            assert "content" in note
            assert "contact_count" in note
