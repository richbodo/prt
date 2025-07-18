import json
from pathlib import Path
from typing import Any, Dict

CONFIG_FILE = 'prt_config.json'
DATA_DIR_NAME = 'prt_data'
REQUIRED_FIELDS = ['google_api_key', 'openai_api_key', 'db_path']


def data_dir() -> Path:
    """Return the directory for local private data and ensure it exists."""
    path = Path.cwd() / DATA_DIR_NAME
    path.mkdir(exist_ok=True)
    return path


def config_path() -> Path:
    """Return path to config file inside the data directory."""
    return data_dir() / CONFIG_FILE


def load_config() -> Dict[str, Any]:
    path = config_path()
    if not path.exists():
        return {}
    with path.open('r') as f:
        return json.load(f)


def save_config(cfg: Dict[str, Any]) -> None:
    with config_path().open('w') as f:
        json.dump(cfg, f, indent=2)
