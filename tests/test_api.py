"""
Tests for the PRT API layer.
"""

from pathlib import Path
from prt_src.api import PRTAPI


class TestPRTAPI:
    """Test the PRT API functionality."""
    
    def test_api_initialization(self, tmp_path):
        """Test API initialization with custom database path."""
        db_path = tmp_path / "test.db"
        config = {"db_path": str(db_path), "db_encrypted": False}
        api = PRTAPI(config)
        assert api.db.path == db_path
    
    def test_api_initialization_default(self, sample_config):
        """Test API initialization with sample config."""
        api = PRTAPI(sample_config)
        expected_path = Path(sample_config["db_path"])
        assert api.db.path == expected_path
    
    def test_get_database_stats(self, test_db):
        """Test getting database statistics."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config)
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
    
    def test_search_contacts(self, test_db):
        """Test contact search functionality."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config)
        results = api.search_contacts("John")
        
        assert isinstance(results, list)
        for contact in results:
            assert isinstance(contact, dict)
            assert "id" in contact
            assert "name" in contact
            assert "email" in contact
            assert "phone" in contact
            assert "relationship_info" in contact
    
    def test_list_all_contacts(self, test_db):
        """Test listing all contacts."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config)
        contacts = api.list_all_contacts()
        
        assert isinstance(contacts, list)
        for contact in contacts:
            assert isinstance(contact, dict)
            assert "id" in contact
            assert "name" in contact
            assert "email" in contact
            assert "phone" in contact
            assert "relationship_info" in contact
    
    def test_list_all_tags(self, test_db):
        """Test listing all tags."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config)
        tags = api.list_all_tags()
        
        assert isinstance(tags, list)
        for tag in tags:
            assert isinstance(tag, dict)
            assert "id" in tag
            assert "name" in tag
            assert "contact_count" in tag
    
    def test_list_all_notes(self, test_db):
        """Test listing all notes."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config)
        notes = api.list_all_notes()
        
        assert isinstance(notes, list)
        for note in notes:
            assert isinstance(note, dict)
            assert "id" in note
            assert "title" in note
            assert "content" in note
            assert "contact_count" in note
