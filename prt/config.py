import json
from pathlib import Path
from typing import Any, Dict

CONFIG_FILE = 'prt_config.json'
REQUIRED_FIELDS = ['google_api_key', 'openai_api_key', 'db_path']


def config_path() -> Path:
    """Return path to config file in current working directory."""
    return Path.cwd() / CONFIG_FILE


def load_config() -> Dict[str, Any]:
    path = config_path()
    if not path.exists():
        return {}
    with path.open('r') as f:
        return json.load(f)


def save_config(cfg: Dict[str, Any]) -> None:
    with config_path().open('w') as f:
        json.dump(cfg, f, indent=2)
