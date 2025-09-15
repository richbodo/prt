import json
from pathlib import Path
from typing import Any
from typing import Dict

CONFIG_FILE = "prt_config.json"
DATA_DIR_NAME = "prt_data"
REQUIRED_FIELDS = ["google_api_key", "openai_api_key", "db_path", "db_username", "db_password"]


def data_dir() -> Path:
    """Return the directory for local private data and ensure it exists."""
    path = Path.cwd() / DATA_DIR_NAME
    try:
        path.mkdir(exist_ok=True)
    except OSError as e:
        raise RuntimeError(f"Failed to create data directory: {e}") from e
    return path


def config_path() -> Path:
    """Return path to config file inside the data directory."""
    return data_dir() / CONFIG_FILE


def load_config() -> Dict[str, Any]:
    path = config_path()
    if not path.exists():
        # Return default config
        return {"db_path": str(data_dir() / "prt.db"), "db_encrypted": False}
    try:
        with path.open("r") as f:
            config = json.load(f)
            # Ensure db_path is always present
            if "db_path" not in config:
                config["db_path"] = str(data_dir() / "prt.db")
            return config
    except json.JSONDecodeError as e:
        raise ValueError("Config file is corrupt") from e


def save_config(cfg: Dict[str, Any]) -> None:
    try:
        with config_path().open("w") as f:
            json.dump(cfg, f, indent=2)
    except OSError as e:
        raise RuntimeError(f"Failed to write config file: {e}") from e


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
    try:
        secrets_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise RuntimeError(f"Failed to create secrets directory: {e}") from e
    secrets_file = secrets_dir / "db_secrets.txt"

    if secrets_file.exists():
        try:
            with open(secrets_file) as f:
                lines = f.read().strip().split("\n")
                if len(lines) >= 2:
                    return lines[0], lines[1]
        except OSError as e:
            raise RuntimeError(f"Failed to read secrets file: {e}") from e

    # Generate new credentials
    import secrets as secrets_module
    import string

    username = "".join(secrets_module.choice(string.ascii_lowercase) for _ in range(8))
    password = "".join(
        secrets_module.choice(string.ascii_letters + string.digits) for _ in range(16)
    )

    try:
        with open(secrets_file, "w") as f:
            f.write(f"{username}\n{password}")
    except OSError as e:
        raise RuntimeError(f"Failed to write secrets file: {e}") from e

    return username, password


# Encryption-related functions removed as part of Issue #41
# These will be replaced with application-level encryption in Issue #42


def get_database_url(config: Dict[str, Any]) -> str:
    """Get the database URL."""
    db_path = config.get("db_path", "prt_data/prt.db")
    return f"sqlite:///{db_path}"
