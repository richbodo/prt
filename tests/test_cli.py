"""CLI command tests using Typer's CliRunner."""

from pathlib import Path
import types
import sys
from typer.testing import CliRunner

from prt_src.config import load_config


def _get_app(monkeypatch):
    """Import the CLI app with google contacts stubbed out."""
    stub = types.ModuleType("prt_src.google_contacts")
    stub.fetch_contacts = lambda config: []
    monkeypatch.setitem(sys.modules, "prt_src.google_contacts", stub)
    monkeypatch.delitem(sys.modules, "prt_src.cli", raising=False)
    from prt_src.cli import app
    return app


def _mock_prompts(monkeypatch):
    """Make Prompt/Confirm and typer.confirm return non-interactive defaults."""
    monkeypatch.setattr("rich.prompt.Prompt.ask", lambda *a, **k: "")
    monkeypatch.setattr("rich.prompt.Confirm.ask", lambda *a, **k: True)
    monkeypatch.setattr("typer.confirm", lambda *a, **k: True)


def test_setup_creates_config_and_db(monkeypatch, tmp_path):
    """Running `setup` should create configuration and database files."""
    _mock_prompts(monkeypatch)
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        app = _get_app(monkeypatch)
        result = runner.invoke(app, ["setup"])
        assert result.exit_code == 0
        assert "PRT setup completed successfully" in result.stdout

        cfg_file = Path("prt_data/prt_config.json")
        db_file = Path("prt_data/prt.db")
        assert cfg_file.exists()
        assert db_file.exists()


def test_db_status_reports_ok(monkeypatch, tmp_path):
    """`db-status` should report on the created database."""
    _mock_prompts(monkeypatch)
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        app = _get_app(monkeypatch)
        runner.invoke(app, ["setup"])
        result = runner.invoke(app, ["db-status"])
        assert result.exit_code == 0
        assert "Database status" in result.stdout
        assert "Database path" in result.stdout


def test_encrypt_db_creates_backup(monkeypatch, tmp_path):
    """`encrypt-db` should succeed and create a backup of the database."""
    _mock_prompts(monkeypatch)
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        app = _get_app(monkeypatch)
        runner.invoke(app, ["setup"])

        result = runner.invoke(app, ["encrypt-db"])
        assert result.exit_code == 0
        assert "Database encryption completed successfully" in result.stdout

        backup = Path("prt_data/prt.db.pre_encryption")
        assert backup.exists()
        assert load_config().get("db_encrypted") is True


def test_decrypt_db_creates_backup(monkeypatch, tmp_path):
    """`decrypt-db` should succeed and create a pre-decryption backup."""
    _mock_prompts(monkeypatch)
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        app = _get_app(monkeypatch)
        runner.invoke(app, ["setup"])
        runner.invoke(app, ["encrypt-db"])

        result = runner.invoke(app, ["decrypt-db"])
        assert result.exit_code == 0
        assert "Database decryption completed successfully" in result.stdout

        backup = Path("prt_data/prt.db.pre_decryption")
        assert backup.exists()
        assert load_config().get("db_encrypted") is False

