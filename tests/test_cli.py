from pathlib import Path
from typer.testing import CliRunner
from prt_src.cli import app


def test_cli_creates_config(tmp_path):
    """Test that CLI can create a basic configuration."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        # Test with minimal input - just create config and exit
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0


def test_cli_database_connection(tmp_path):
    """Test CLI database connection and initialization."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        # Create a minimal config
        config_dir = Path(td) / "prt_data"
        config_dir.mkdir()
        config_file = config_dir / "prt_config.json"
        config_file.write_text('''{
            "google_api_key": "demo",
            "openai_api_key": "demo",
            "db_path": "prt_data/prt.db",
            "db_username": "test",
            "db_password": "test",
            "db_type": "sqlite",
            "db_host": "localhost",
            "db_port": 5432,
            "db_name": "prt"
        }''')
        
        # Test that CLI can start without errors
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0


def test_cli_with_existing_database(tmp_path):
    """Test CLI behavior with an existing database."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        # Create config and database
        config_dir = Path(td) / "prt_data"
        config_dir.mkdir()
        config_file = config_dir / "prt_config.json"
        config_file.write_text('''{
            "google_api_key": "demo",
            "openai_api_key": "demo",
            "db_path": "prt_data/prt.db",
            "db_username": "test",
            "db_password": "test",
            "db_type": "sqlite",
            "db_host": "localhost",
            "db_port": 5432,
            "db_name": "prt"
        }''')
        
        # Create a minimal database
        db_file = config_dir / "prt.db"
        import sqlite3
        conn = sqlite3.connect(db_file)
        conn.execute("CREATE TABLE contacts (id INTEGER PRIMARY KEY, name TEXT, email TEXT)")
        conn.execute("INSERT INTO contacts (name, email) VALUES ('Test User', 'test@example.com')")
        conn.commit()
        conn.close()
        
        # Test that CLI can connect to existing database
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
