import sys
import pytest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from prt_src.db import create_database
from tests.fixtures import setup_test_database


@pytest.fixture
def test_db(tmp_path):
    """Create a test database with sample data."""
    db_path = tmp_path / "test.db"
    db = create_database(db_path)
    fixtures = setup_test_database(db)
    return db, fixtures


@pytest.fixture 
def test_db_empty(tmp_path):
    """Create an empty test database."""
    db_path = tmp_path / "empty_test.db"
    db = create_database(db_path)
    db.initialize()  # Just create tables, no data
    return db


@pytest.fixture
def sample_config(tmp_path):
    """Create sample configuration for tests."""
    db_path = tmp_path / "config_test.db"
    return {
        "db_path": str(db_path),
        "db_encrypted": False,
        "db_type": "sqlite",
        "db_username": "test",
        "db_password": "test"
    }
