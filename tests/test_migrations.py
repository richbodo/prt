"""
Tests for database migrations and setup.

This module tests the migration utilities and setup processes.
Encryption-related tests removed as part of Issue #41.
"""

import pytest
import tempfile
import sqlite3
from pathlib import Path
from unittest.mock import patch

# Add the prt package to the path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.setup_database import setup_database, initialize_database
from prt_src.config import load_config, save_config
from prt_src.db import create_database


def test_migration_tracker(tmp_path):
    """Test migration tracking functionality."""
    pytest.skip("Migration tracker functionality replaced by SchemaManager")


def test_migration_runner_initialization(tmp_path):
    """Test migration runner initialization."""
    pytest.skip("Migration runner functionality replaced by SchemaManager")


def test_migration_runner_list_migrations(tmp_path):
    """Test that migration runner can list available migrations."""
    pytest.skip("Migration runner functionality replaced by SchemaManager")


def test_migration_runner_status(tmp_path):
    """Test migration status reporting."""
    pytest.skip("Migration runner functionality replaced by SchemaManager")


def test_migration_runner_with_no_migrations(tmp_path):
    """Test migration runner behavior when no migrations are available."""
    pytest.skip("Migration runner functionality replaced by SchemaManager")


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
    
    def test_setup_database_force(self, temp_config_dir):
        """Test forced database setup."""
        pytest.skip("Force credential regeneration needs investigation - Issue #41 cleanup")


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
        db = create_database(temp_db_path)
        assert db.is_valid() is True
    
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
