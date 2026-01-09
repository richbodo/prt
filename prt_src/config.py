import json
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any

CONFIG_FILE = "prt_config.json"
DATA_DIR_NAME = "prt_data"
REQUIRED_FIELDS = ["google_api_key", "openai_api_key", "db_path", "db_username", "db_password"]

# Default tool flags until stability work is complete
DEFAULT_DISABLED_LLM_TOOLS = [
    "save_contacts_with_images",
    "list_memory",
]


def _get_logger():
    """Get logger lazily to avoid circular import."""
    from .logging_config import get_logger

    return get_logger(__name__)


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


def load_config() -> dict[str, Any]:
    path = config_path()
    if not path.exists():
        # Return default config with auto-populated credentials if they exist
        config = {"db_path": str(data_dir() / "prt.db"), "db_encrypted": False}
        try:
            # Try to auto-populate credentials from secrets file if they exist
            username, password = get_db_credentials()
            config["db_username"] = username
            config["db_password"] = password
        except RuntimeError as e:
            # Critical error (permissions, disk space, etc.) - user should know
            import sys

            print(f"Warning: Database credentials setup failed: {e}", file=sys.stderr)
            print("This may indicate a permissions or disk space issue.", file=sys.stderr)
            print("Setup wizard will handle credential generation.", file=sys.stderr)
            # Continue with minimal config - setup will handle it
        except Exception as e:
            # Unexpected error - log it but don't crash
            import sys

            print(f"Unexpected error accessing credentials: {e}", file=sys.stderr)
            print("Continuing with minimal configuration.", file=sys.stderr)
        return config
    try:
        with path.open("r") as f:
            config = json.load(f)
            # Ensure db_path is always present
            if "db_path" not in config:
                config["db_path"] = str(data_dir() / "prt.db")
            return config
    except json.JSONDecodeError as e:
        raise ValueError("Config file is corrupt") from e


def save_config(cfg: dict[str, Any]) -> None:
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


def get_database_url(config: dict[str, Any]) -> str:
    """Get the database URL."""
    db_path = config.get("db_path", "prt_data/prt.db")
    return f"sqlite:///{db_path}"


def get_current_database_mode() -> str:
    """Get the current database mode from the active configuration.

    Returns:
        Database mode: "real", "fixture", "debug", or "unknown"
    """
    try:
        config = load_config()
        return get_database_mode_from_config(config)
    except Exception:
        return "unknown"


def get_database_mode_from_config(config: dict[str, Any]) -> str:
    """Get the database mode from a configuration dictionary.

    Args:
        config: Configuration dictionary

    Returns:
        Database mode: "real", "fixture", "debug", or "unknown"
    """
    if not config:
        return "unknown"

    # Check explicit mode marker first
    explicit_mode = config.get("database_mode")
    if explicit_mode:
        return explicit_mode

    # Infer from database path
    db_path = str(config.get("db_path", ""))
    if "debug.db" in db_path:
        return "debug"
    elif "fixture.db" in db_path:
        return "fixture"
    elif "prt.db" in db_path:
        return "real"
    else:
        return "unknown"


def is_safe_mode() -> bool:
    """Check if the application is running in a safe mode (fixture or debug).

    Safe modes use isolated databases that don't affect user's real data.

    Returns:
        True if running in fixture or debug mode, False otherwise
    """
    mode = get_current_database_mode()
    return mode in ["fixture", "debug"]


# ============================================================================
# LLM Configuration Management
# ============================================================================


@dataclass
class LLMConfig:
    """LLM connection and model configuration.

    Supports multiple providers:
    - ollama: Uses Ollama API server (requires Ollama running)
    - llamacpp: Uses llama-cpp-python for local GGUF models
    """

    provider: str = "ollama"
    model: str = "gpt-oss:20b"

    # Model discovery and defaults
    default_model: str | None = None  # Model alias to use by default (e.g., "llama8")
    fallback_models: dict[str, dict[str, str]] | None = None  # Fallback configs when Ollama offline

    # Ollama-specific settings
    base_url: str = "http://localhost:11434"  # Native API (not /v1 OpenAI-compatible)
    keep_alive: str = "30m"

    # llama-cpp-python specific settings
    model_path: str | None = None  # Path to .gguf file (required for llamacpp provider)
    n_ctx: int = 4096  # Context window size
    n_gpu_layers: int = 0  # Number of layers to offload to GPU (0 = CPU only)
    n_threads: int | None = None  # Number of CPU threads (None = auto-detect)

    # Common settings
    timeout: int = 300  # Increased from 120s to handle large datasets (1800+ contacts)
    temperature: float = 0.1


@dataclass
class LLMPermissions:
    """LLM permission and safety controls."""

    allow_create: bool = True
    allow_update: bool = True
    allow_delete: bool = False
    require_confirmation_delete: bool = True
    require_confirmation_bulk_operations: bool = True
    max_bulk_operations: int = 100
    read_only_mode: bool = False


@dataclass
class LLMPrompts:
    """LLM system prompt configuration."""

    override_system_prompt: str | None = None
    use_file: bool = False
    file_path: str | None = None


@dataclass
class LLMContext:
    """LLM context management configuration."""

    mode: str = "adaptive"  # minimal | detailed | adaptive
    max_conversation_history: int = 3
    max_context_tokens: int = 4000


@dataclass
class LLMDeveloper:
    """LLM developer tools and debugging."""

    debug_mode: bool = False
    log_prompts: bool = False
    log_responses: bool = False
    log_timing: bool = False


@dataclass
class LLMToolsConfig:
    """LLM tool availability and feature toggles."""

    disabled_tools: list[str] = field(default_factory=list)


class LLMConfigManager:
    """Manager for LLM configuration with validation and defaults."""

    def __init__(self, config_dict: dict[str, Any] | None = None):
        """Initialize LLM config manager.

        Args:
            config_dict: Optional config dictionary. If None, loads from config file.
        """
        if config_dict is None:
            config_dict = load_config()

        self.llm = self._load_llm_config(config_dict.get("llm", {}))
        self.permissions = self._load_permissions_config(config_dict.get("llm_permissions", {}))
        self.prompts = self._load_prompts_config(config_dict.get("llm_prompts", {}))
        self.context = self._load_context_config(config_dict.get("llm_context", {}))
        self.developer = self._load_developer_config(config_dict.get("llm_developer", {}))
        self.tools = self._load_tools_config(config_dict.get("llm_tools", {}))

    def _load_llm_config(self, llm_dict: dict[str, Any]) -> LLMConfig:
        """Load LLM connection configuration with validation."""
        return LLMConfig(
            provider=llm_dict.get("provider", "ollama"),
            model=llm_dict.get("model", "gpt-oss:20b"),
            # Model discovery and defaults
            default_model=llm_dict.get("default_model"),
            fallback_models=llm_dict.get("fallback_models"),
            # Ollama-specific
            base_url=llm_dict.get("base_url", "http://localhost:11434"),
            keep_alive=llm_dict.get("keep_alive", "30m"),
            # llama-cpp-python specific
            model_path=llm_dict.get("model_path"),
            n_ctx=llm_dict.get("n_ctx", 4096),
            n_gpu_layers=llm_dict.get("n_gpu_layers", 0),
            n_threads=llm_dict.get("n_threads"),
            # Common settings
            timeout=llm_dict.get(
                "timeout", 300
            ),  # Increased from 120s to handle large datasets (1800+ contacts)
            temperature=llm_dict.get("temperature", 0.1),
        )

    def _load_permissions_config(self, perm_dict: dict[str, Any]) -> LLMPermissions:
        """Load LLM permissions configuration with validation."""
        require_confirmation = perm_dict.get("require_confirmation", {})

        return LLMPermissions(
            allow_create=perm_dict.get("allow_create", True),
            allow_update=perm_dict.get("allow_update", True),
            allow_delete=perm_dict.get("allow_delete", False),
            require_confirmation_delete=require_confirmation.get("delete", True),
            require_confirmation_bulk_operations=require_confirmation.get("bulk_operations", True),
            max_bulk_operations=perm_dict.get("max_bulk_operations", 100),
            read_only_mode=perm_dict.get("read_only_mode", False),
        )

    def _load_prompts_config(self, prompts_dict: dict[str, Any]) -> LLMPrompts:
        """Load LLM prompts configuration with validation."""
        return LLMPrompts(
            override_system_prompt=prompts_dict.get("override_system_prompt"),
            use_file=prompts_dict.get("use_file", False),
            file_path=prompts_dict.get("file_path"),
        )

    def _load_context_config(self, context_dict: dict[str, Any]) -> LLMContext:
        """Load LLM context configuration with validation."""
        mode = context_dict.get("mode", "adaptive")
        if mode not in ["minimal", "detailed", "adaptive"]:
            _get_logger().warning(
                f"Invalid context mode '{mode}', using 'adaptive'. Valid: minimal, detailed, adaptive"
            )
            mode = "adaptive"

        return LLMContext(
            mode=mode,
            max_conversation_history=context_dict.get("max_conversation_history", 3),
            max_context_tokens=context_dict.get("max_context_tokens", 4000),
        )

    def _load_developer_config(self, dev_dict: dict[str, Any]) -> LLMDeveloper:
        """Load LLM developer tools configuration."""
        return LLMDeveloper(
            debug_mode=dev_dict.get("debug_mode", False),
            log_prompts=dev_dict.get("log_prompts", False),
            log_responses=dev_dict.get("log_responses", False),
            log_timing=dev_dict.get("log_timing", False),
        )

    def _load_tools_config(self, tools_dict: dict[str, Any]) -> LLMToolsConfig:
        """Load LLM tool enable/disable configuration."""

        disabled = tools_dict.get("disabled")
        if disabled is None:
            disabled = DEFAULT_DISABLED_LLM_TOOLS.copy()
        if not isinstance(disabled, list):
            _get_logger().warning(
                "Invalid llm_tools.disabled configuration. Expected list of tool names."
            )
            disabled = []

        # Normalise tool names to strings for safety
        normalized = [str(tool_name) for tool_name in disabled]

        return LLMToolsConfig(disabled_tools=normalized)

    def get_system_prompt(self) -> str | None:
        """Get the system prompt from configuration.

        Returns:
            System prompt string if configured, None otherwise
        """
        if self.prompts.use_file and self.prompts.file_path:
            try:
                prompt_path = Path(self.prompts.file_path)
                if not prompt_path.is_absolute():
                    # Resolve relative to data directory
                    prompt_path = data_dir() / self.prompts.file_path

                if prompt_path.exists():
                    return prompt_path.read_text()
                else:
                    _get_logger().warning(f"System prompt file not found: {prompt_path}")
                    return None
            except Exception as e:
                _get_logger().error(f"Failed to load system prompt from file: {e}")
                return None

        return self.prompts.override_system_prompt

    def validate(self) -> bool:
        """Validate configuration.

        Returns:
            True if configuration is valid
        """
        logger = _get_logger()

        # Validate provider
        if self.llm.provider not in ["ollama", "llamacpp"]:
            logger.warning(
                f"Unsupported LLM provider '{self.llm.provider}'. Supported providers: 'ollama', 'llamacpp'"
            )
            return False

        # Validate llamacpp-specific settings
        if self.llm.provider == "llamacpp":
            if not self.llm.model_path:
                logger.warning(
                    "llamacpp provider requires model_path to be set. "
                    "Specify path to .gguf file in config or via --llm-model flag"
                )
                return False

            from pathlib import Path

            model_file = Path(self.llm.model_path)
            if not model_file.exists():
                logger.warning(f"Model file not found: {self.llm.model_path}")
                return False

            if self.llm.n_ctx < 512:
                logger.warning(f"n_ctx ({self.llm.n_ctx}) is too small, minimum recommended: 512")

            if self.llm.n_gpu_layers < 0:
                logger.warning(f"n_gpu_layers must be >= 0, got: {self.llm.n_gpu_layers}")
                return False

        # Validate timeout
        if self.llm.timeout < 10 or self.llm.timeout > 600:
            logger.warning(f"LLM timeout {self.llm.timeout}s is outside recommended range (10-600)")

        # Validate temperature
        if self.llm.temperature < 0.0 or self.llm.temperature > 2.0:
            logger.warning(
                f"LLM temperature {self.llm.temperature} is outside valid range (0.0-2.0)"
            )
            return False

        # Validate max_bulk_operations
        if self.permissions.max_bulk_operations < 1:
            logger.warning("max_bulk_operations must be at least 1")
            return False

        # Check for conflicting permissions
        if self.permissions.read_only_mode and (
            self.permissions.allow_create
            or self.permissions.allow_update
            or self.permissions.allow_delete
        ):
            logger.warning(
                "read_only_mode is enabled but write permissions are also enabled. read_only_mode will take precedence."
            )

        return True

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary for saving.

        Returns:
            Dictionary representation of configuration
        """
        return {
            "llm": {
                "provider": self.llm.provider,
                "model": self.llm.model,
                # Ollama-specific
                "base_url": self.llm.base_url,
                "keep_alive": self.llm.keep_alive,
                # llama-cpp-python specific
                "model_path": self.llm.model_path,
                "n_ctx": self.llm.n_ctx,
                "n_gpu_layers": self.llm.n_gpu_layers,
                "n_threads": self.llm.n_threads,
                # Common settings
                "timeout": self.llm.timeout,
                "temperature": self.llm.temperature,
            },
            "llm_permissions": {
                "allow_create": self.permissions.allow_create,
                "allow_update": self.permissions.allow_update,
                "allow_delete": self.permissions.allow_delete,
                "require_confirmation": {
                    "delete": self.permissions.require_confirmation_delete,
                    "bulk_operations": self.permissions.require_confirmation_bulk_operations,
                },
                "max_bulk_operations": self.permissions.max_bulk_operations,
                "read_only_mode": self.permissions.read_only_mode,
            },
            "llm_prompts": {
                "override_system_prompt": self.prompts.override_system_prompt,
                "use_file": self.prompts.use_file,
                "file_path": self.prompts.file_path,
            },
            "llm_context": {
                "mode": self.context.mode,
                "max_conversation_history": self.context.max_conversation_history,
                "max_context_tokens": self.context.max_context_tokens,
            },
            "llm_developer": {
                "debug_mode": self.developer.debug_mode,
                "log_prompts": self.developer.log_prompts,
                "log_responses": self.developer.log_responses,
                "log_timing": self.developer.log_timing,
            },
        }
