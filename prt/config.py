import json
from pathlib import Path
from typing import Any, Dict

CONFIG_FILE = 'prt_config.json'
DATA_DIR_NAME = 'prt_data'
REQUIRED_FIELDS = ['google_api_key', 'openai_api_key', 'db_path', 'db_username', 'db_password']


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
    try:
        with path.open('r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError("Config file is corrupt") from e


def save_config(cfg: Dict[str, Any]) -> None:
    with config_path().open('w') as f:
        json.dump(cfg, f, indent=2)


def get_db_credentials() -> tuple[str, str]:
    """Get database credentials from secrets file or generate new ones."""
    secrets_dir = Path.cwd() / "secrets"
    secrets_dir.mkdir(exist_ok=True)
    secrets_file = secrets_dir / "db_secrets.txt"
    
    if secrets_file.exists():
        with open(secrets_file, 'r') as f:
            lines = f.read().strip().split('\n')
            if len(lines) >= 2:
                return lines[0], lines[1]
    
    # Generate new credentials
    import secrets as secrets_module
    import string
    
    username = ''.join(secrets_module.choice(string.ascii_lowercase) for _ in range(8))
    password = ''.join(secrets_module.choice(string.ascii_letters + string.digits) for _ in range(16))
    
    with open(secrets_file, 'w') as f:
        f.write(f"{username}\n{password}")
    
    return username, password
