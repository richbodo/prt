from pathlib import Path
from typer.testing import CliRunner
from prt.cli import app


def test_cli_creates_config(tmp_path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        result = runner.invoke(app, [], input="y\ndemo\ndemo\nprt.db\nn\nn\n")
        assert result.exit_code == 0
        assert (Path(td) / "prt_config.json").exists()
