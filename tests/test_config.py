import os
import pytest
from prt_src.config import save_config, load_config


def test_config_roundtrip(tmp_path):
    cfg = {
        "google_api_key": "g",
        "openai_api_key": "o",
        "db_path": str(tmp_path / "db.sqlite"),
    }
    os.chdir(tmp_path)
    save_config(cfg)
    assert (tmp_path / 'prt_data' / 'prt_config.json').exists()
    assert load_config() == cfg


def test_corrupt_config(tmp_path):
    os.chdir(tmp_path)
    cfg_dir = tmp_path / 'prt_data'
    cfg_dir.mkdir()
    cfg_path = cfg_dir / 'prt_config.json'
    cfg_path.write_text('{bad json')
    with pytest.raises(ValueError):
        load_config()
