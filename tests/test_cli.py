from pathlib import Path

import pytest
import typer
from rich.prompt import Prompt, Confirm
from typer.testing import CliRunner

from prt_src.cli import app


# Ensure commands run without waiting for interactive input
@pytest.fixture(autouse=True)
def _non_interactive(monkeypatch):
    monkeypatch.setattr(Prompt, "ask", lambda *a, **k: "y")
    monkeypatch.setattr(Confirm, "ask", lambda *a, **k: True)
    monkeypatch.setattr(typer, "confirm", lambda *a, **k: True)


def test_setup_creates_config(tmp_path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(app, ["setup"])
        assert result.exit_code == 0
        assert "PRT setup completed successfully" in result.output
        assert Path("prt_data/prt_config.json").exists()


def test_db_status_reports_ok(tmp_path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(app, ["setup"])
        result = runner.invoke(app, ["db-status"])
        assert result.exit_code == 0
        assert "Database status" in result.output


def test_encrypt_and_decrypt_db(tmp_path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(app, ["setup"])
        db_path = Path("prt_data/prt.db")

        enc_result = runner.invoke(app, ["encrypt-db", "--no-verify"])
        assert enc_result.exit_code == 0
        assert "Database encryption completed successfully" in enc_result.output
        assert db_path.with_name("prt.db.pre_encryption").exists()

        dec_result = runner.invoke(app, ["decrypt-db"])
        assert dec_result.exit_code == 0
        assert "Database decryption completed successfully" in dec_result.output
        assert db_path.with_name("prt.db.pre_decryption").exists()

