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


def _migrate_secrets_if_needed():
    """Migrate secrets from old /secrets/ to new /prt_data/secrets/ location."""
    old_secrets_dir = Path.cwd() / "secrets"
    new_secrets_dir = data_dir() / "secrets"
    
    if old_secrets_dir.exists() and not new_secrets_dir.exists():
        print(f"Migrating secrets from {old_secrets_dir} to {new_secrets_dir}")
        new_secrets_dir.mkdir(parents=True, exist_ok=True)
        
        # Migrate all files from old to new location
        for file in old_secrets_dir.iterdir():
            if file.is_file():
                (new_secrets_dir / file.name).write_text(file.read_text())
                print(f"Migrated {file.name}")
        
        print("✅ Secret files migrated successfully!")
        print(f"Old directory {old_secrets_dir} can be safely removed after verification")


def get_db_credentials() -> tuple[str, str]:
    """Get database credentials from secrets file or generate new ones."""
    _migrate_secrets_if_needed()
    
    secrets_dir = data_dir() / "secrets"
    secrets_dir.mkdir(parents=True, exist_ok=True)
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


def get_encryption_key() -> str:
    """Get database encryption key from secrets file or generate new one."""
    _migrate_secrets_if_needed()
    
    secrets_dir = data_dir() / "secrets"
    secrets_dir.mkdir(parents=True, exist_ok=True)
    encryption_file = secrets_dir / "db_encryption_key.txt"
    
    if encryption_file.exists():
        with open(encryption_file, 'r') as f:
            return f.read().strip()
    
    # Generate new encryption key (32 bytes = 256 bits)
    import secrets as secrets_module
    import base64
    
    key_bytes = secrets_module.token_bytes(32)
    key_b64 = base64.b64encode(key_bytes).decode('utf-8')
    
    with open(encryption_file, 'w') as f:
        f.write(key_b64)
    
    return key_b64


def is_database_encrypted(config: Dict[str, Any]) -> bool:
    """Check if the database is configured to use encryption."""
    return config.get('db_encrypted', False)


def get_database_url(config: Dict[str, Any]) -> str:
    """Get the appropriate database URL based on encryption settings."""
    db_path = config.get('db_path', 'prt_data/prt.db')
    
    if is_database_encrypted(config):
        # For encrypted databases, we'll use a custom URL format
        # that will be handled by our encrypted database class
        return f"sqlite:///{db_path}?encrypted=true"
    else:
        return f"sqlite:///{db_path}"
