from pathlib import Path

from utils.setup_database import initialize_database, setup_database


def test_setup_database_functions(tmp_path):
    """Test setup database functions work correctly."""
    # Test setup_database function
    result = setup_database(quiet=True)
    assert isinstance(result, dict)
    assert "db_path" in result


def test_initialize_database(tmp_path):
    """Test database initialization."""
    config = {
        "google_api_key": "demo",
        "openai_api_key": "demo",
        "db_path": str(tmp_path / "prt.db"),
        "db_username": "test",
        "db_password": "test",
        "db_type": "sqlite",
        "db_host": "localhost",
        "db_port": 5432,
        "db_name": "prt",
    }

    # Test that initialize_database works
    success = initialize_database(config, quiet=True)
    assert success

    # Check that database file was created
    db_file = Path(config["db_path"])
    assert db_file.exists()
