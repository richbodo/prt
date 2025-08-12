from pathlib import Path
from typer.testing import CliRunner
from setup_database import app


def test_corrupt_db_backup(tmp_path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        data_dir = Path(td) / "prt_data"
        data_dir.mkdir()
        db_file = data_dir / "prt.db"
        db_file.write_text("not a sqlite db")

        result = runner.invoke(app, ["setup"], input="n\n")
        assert result.exit_code == 0
        assert not db_file.exists()
        assert (data_dir / "prt.db.corrupt.bak").exists()
