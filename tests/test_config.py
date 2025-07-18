import os
from prt.config import save_config, load_config


def test_config_roundtrip(tmp_path):
    cfg = {
        "google_api_key": "g",
        "openai_api_key": "o",
        "db_path": str(tmp_path / "db.sqlite"),
    }
    os.chdir(tmp_path)
    save_config(cfg)
    assert (tmp_path / 'prt_config.json').exists()
    assert load_config() == cfg
