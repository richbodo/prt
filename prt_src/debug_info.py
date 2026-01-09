"""
Debug information collection module for PRT.

This module orchestrates existing system information gathering functions
to provide comprehensive diagnostic information for troubleshooting.
"""

import platform
import subprocess
import sys
from typing import Any

from . import __version__
from .api import PRTAPI
from .config import load_config
from .llm_factory import check_model_availability
from .llm_factory import get_registry
from .llm_factory import resolve_model_alias
from .logging_config import get_logger
from .schema_manager import SchemaManager

logger = get_logger(__name__)


def collect_system_environment() -> dict[str, Any]:
    """Collect system environment information (OS, Python, Ollama versions)."""
    env_info = {
        "os": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "architecture": platform.architecture()[0],
        },
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "executable": sys.executable,
        },
        "prt_version": __version__,
    }

    # Try to get Ollama version
    try:
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            env_info["ollama"] = {
                "available": True,
                "version": result.stdout.strip(),
            }
        else:
            env_info["ollama"] = {
                "available": False,
                "error": "Command failed",
            }
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError) as e:
        env_info["ollama"] = {
            "available": False,
            "error": str(e),
        }

    return env_info


def collect_database_info() -> dict[str, Any]:
    """Collect database information using existing API functions."""
    db_info = {
        "status": "unknown",
        "error": None,
        "connection_test": False,
        "statistics": {},
        "schema_info": {},
    }

    try:
        # Load configuration and create API instance
        config = load_config()
        api = PRTAPI(config)

        # Test database connection using existing API method
        db_info["connection_test"] = api.test_database_connection()
        db_info["data_directory"] = str(api.get_data_directory())

        # Get database statistics using existing DB methods
        stats = {}
        try:
            stats["contacts"] = api.db.count_contacts()
        except AttributeError:
            stats["contacts"] = 0

        try:
            stats["tags"] = api.db.count_tags()
        except AttributeError:
            # If method doesn't exist, try to count manually
            try:
                with api.db.get_session() as session:
                    from .models import Tag

                    stats["tags"] = session.query(Tag).count()
            except Exception:
                stats["tags"] = 0

        try:
            stats["notes"] = api.db.count_notes()
        except AttributeError:
            # If method doesn't exist, try to count manually
            try:
                with api.db.get_session() as session:
                    from .models import Note

                    stats["notes"] = session.query(Note).count()
            except Exception:
                stats["notes"] = 0

        try:
            stats["relationships"] = api.db.count_relationships()
        except AttributeError:
            stats["relationships"] = 0

        db_info["statistics"] = stats

        # Get schema information using existing schema manager
        schema_manager = SchemaManager(api.db.path)
        db_info["schema_info"] = {
            "current_version": schema_manager.get_schema_version(),
            "migration_info": schema_manager.get_migration_info(),
        }

        db_info["status"] = "healthy" if db_info["connection_test"] else "connection_failed"

    except Exception as e:
        db_info["status"] = "error"
        db_info["error"] = str(e)
        logger.warning(f"Failed to collect database info: {e}")

    return db_info


def collect_llm_info() -> dict[str, Any]:
    """Collect LLM information using existing factory functions."""
    llm_info = {
        "status": "unknown",
        "error": None,
        "default_model": None,
        "registry_available": False,
        "available_models": [],
        "connectivity_test": {},
    }

    try:
        # Get registry using existing function
        registry = get_registry()
        llm_info["registry_available"] = registry.is_available()

        if llm_info["registry_available"]:
            # Get available models using existing registry method
            model_objects = registry.list_models()
            # Convert model objects to readable format using ModelInfo properties
            llm_info["available_models"] = [
                (
                    f"{model.name} ({model.size_human})"
                    if hasattr(model, "name") and hasattr(model, "size_human")
                    else str(model)
                )
                for model in model_objects
            ]

            # Resolve default model using existing function (don't pass "default" literally)
            try:
                llm_info["default_model"] = resolve_model_alias()  # Use default resolution strategy
            except Exception as e:
                llm_info["default_model"] = f"Error resolving default: {e}"

            # Test model availability using existing function
            if isinstance(llm_info["default_model"], tuple):
                # Default model is returned as tuple (provider, model_name)
                provider, model_name = llm_info["default_model"]
                if model_name != "default":
                    connectivity_result = check_model_availability(model_name)
                    # Map the result to expected format
                    llm_info["connectivity_test"] = {
                        "available": connectivity_result.get("available_in_ollama", False),
                        "error": connectivity_result.get("error", ""),
                        "resolved_name": connectivity_result.get("resolved_name", ""),
                    }
                else:
                    llm_info["connectivity_test"] = {
                        "available": False,
                        "error": "No specific model configured",
                    }
            elif isinstance(llm_info["default_model"], str) and not llm_info[
                "default_model"
            ].startswith("Error"):
                connectivity_result = check_model_availability(llm_info["default_model"])
                # Map the result to expected format
                llm_info["connectivity_test"] = {
                    "available": connectivity_result.get("available_in_ollama", False),
                    "error": connectivity_result.get("error", ""),
                    "resolved_name": connectivity_result.get("resolved_name", ""),
                }
            else:
                llm_info["connectivity_test"] = {
                    "available": False,
                    "error": "Cannot resolve default model",
                }

        llm_info["status"] = "healthy" if llm_info["registry_available"] else "registry_unavailable"

    except Exception as e:
        llm_info["status"] = "error"
        llm_info["error"] = str(e)
        logger.warning(f"Failed to collect LLM info: {e}")

    return llm_info


def collect_system_prompt() -> dict[str, Any]:
    """Collect system prompt information using existing LLM methods."""
    prompt_info = {
        "status": "unknown",
        "error": None,
        "prompt_preview": None,
        "prompt_length": 0,
    }

    try:
        # Try to create LLM instance and get system prompt
        config = load_config()
        api = PRTAPI(config)

        # Import here to avoid circular imports
        from .config import LLMConfigManager
        from .llm_ollama import OllamaLLM

        # Create LLM instance to get system prompt
        config_manager = LLMConfigManager()

        # Resolve the actual default model (don't pass "default" as literal string)
        try:
            default_model = resolve_model_alias()  # Let it use default resolution strategy
            if isinstance(default_model, tuple) and len(default_model) > 1:
                # Extract model name from tuple
                config_manager.llm.model = default_model[1]
            elif isinstance(default_model, str):
                config_manager.llm.model = default_model
        except Exception as e:
            # If model resolution fails, keep the original model
            logger.warning(f"Failed to resolve default model, using config model: {e}")

        llm = OllamaLLM(
            api=api,
            config_manager=config_manager,
        )

        # Get system prompt using existing method
        system_prompt = llm._create_system_prompt()
        # Store the full system prompt
        prompt_info["full_prompt"] = system_prompt
        prompt_info["prompt_length"] = len(system_prompt)
        # For --prt-debug-info, show the full prompt (unlimited length)
        prompt_info["prompt_preview"] = system_prompt
        prompt_info["status"] = "available"

    except Exception as e:
        prompt_info["status"] = "error"
        prompt_info["error"] = str(e)
        logger.warning(f"Failed to collect system prompt: {e}")

    return prompt_info


def collect_config_info() -> dict[str, Any]:
    """Collect configuration information using existing config functions."""
    config_info = {
        "status": "unknown",
        "error": None,
        "config_loaded": False,
        "config_path": None,
        "llm_config": {},
    }

    try:
        # Load configuration using existing function
        config = load_config()
        config_info["config_loaded"] = True

        # Get configuration file path
        from .config import data_dir

        config_path = data_dir() / "prt_config.json"
        if config_path.exists():
            config_info["config_path"] = str(config_path)
        else:
            config_info["config_path"] = f"Not found (expected at: {config_path})"

        # Extract LLM configuration (without sensitive data)
        llm_config = config.get("llm", {})
        safe_llm_config = {}
        for key, value in llm_config.items():
            if key.lower() in ["password", "token", "key", "secret"]:
                safe_llm_config[key] = "[REDACTED]"
            else:
                safe_llm_config[key] = value

        config_info["llm_config"] = safe_llm_config
        config_info["status"] = "loaded"

    except Exception as e:
        config_info["status"] = "error"
        config_info["error"] = str(e)
        logger.warning(f"Failed to collect config info: {e}")

    return config_info


def format_debug_output(debug_data: dict[str, Any]) -> str:
    """Format debug information for display."""
    lines = []

    # Header
    lines.append("=" * 60)
    lines.append("PRT DEBUG INFORMATION")
    lines.append("=" * 60)
    lines.append("")

    # System Environment
    lines.append("📱 SYSTEM ENVIRONMENT")
    lines.append("-" * 30)
    env = debug_data["system_environment"]

    os_info = env["os"]
    lines.append(f"OS: {os_info['system']} {os_info['release']} ({os_info['architecture']})")

    python_info = env["python"]
    lines.append(f"Python: {python_info['version']} ({python_info['implementation']})")
    lines.append(f"Python Executable: {python_info['executable']}")

    lines.append(f"PRT Version: {env['prt_version']}")

    ollama_info = env["ollama"]
    if ollama_info["available"]:
        lines.append(f"✅ Ollama: {ollama_info['version']}")
    else:
        lines.append(f"❌ Ollama: Not available ({ollama_info['error']})")

    lines.append("")

    # Configuration
    lines.append("⚙️  CONFIGURATION")
    lines.append("-" * 30)
    config = debug_data["configuration"]

    if config["status"] == "loaded":
        if config["config_path"].startswith("Not found"):
            lines.append(f"✅ Configuration: Using defaults ({config['config_path']})")
        else:
            lines.append(f"✅ Configuration: Loaded from {config['config_path']}")
        if config["llm_config"]:
            lines.append("LLM Settings:")
            for key, value in config["llm_config"].items():
                lines.append(f"  - {key}: {value}")
    else:
        lines.append(f"❌ Configuration: {config.get('error', 'Unknown error')}")

    lines.append("")

    # Database
    lines.append("🗃️  DATABASE")
    lines.append("-" * 30)
    db = debug_data["database"]

    if db["status"] == "healthy":
        lines.append("✅ Database: Connected")
        lines.append(f"Data Directory: {db.get('data_directory', 'Unknown')}")

        stats = db["statistics"]
        lines.append("Statistics:")
        lines.append(f"  - Contacts: {stats.get('contacts', 0)}")
        lines.append(f"  - Tags: {stats.get('tags', 0)}")
        lines.append(f"  - Notes: {stats.get('notes', 0)}")
        lines.append(f"  - Relationships: {stats.get('relationships', 0)}")

        schema = db["schema_info"]
        lines.append(f"Schema Version: {schema.get('current_version', 'Unknown')}")
    else:
        lines.append(f"❌ Database: {db.get('error', 'Connection failed')}")

    lines.append("")

    # LLM Status
    lines.append("🤖 LLM STATUS")
    lines.append("-" * 30)
    llm = debug_data["llm"]

    if llm["status"] == "healthy":
        lines.append("✅ LLM Service: Available")
        lines.append(f"Default Model: {llm.get('default_model', 'Unknown')}")
        lines.append(f"Available Models: {len(llm.get('available_models', []))}")

        if llm.get("available_models"):
            for model in llm["available_models"][:5]:  # Show first 5 models
                lines.append(f"  - {model}")
            if len(llm["available_models"]) > 5:
                lines.append(f"  - ... and {len(llm['available_models']) - 5} more")

        connectivity = llm.get("connectivity_test", {})
        if connectivity.get("available"):
            lines.append("✅ Model Connectivity: Working")
        else:
            lines.append(f"⚠️  Model Connectivity: {connectivity.get('error', 'Test failed')}")
    else:
        lines.append(f"❌ LLM Service: {llm.get('error', 'Not available')}")

    lines.append("")

    # System Prompt
    lines.append("📄 SYSTEM PROMPT")
    lines.append("-" * 30)
    prompt = debug_data["system_prompt"]

    if prompt["status"] == "available":
        lines.append(f"✅ System Prompt: Generated ({prompt['prompt_length']} characters)")
        lines.append("Full System Prompt:")
        lines.append("-" * 50)
        lines.append(prompt["prompt_preview"])
        lines.append("-" * 50)
    else:
        lines.append(f"❌ System Prompt: {prompt.get('error', 'Not available')}")

    lines.append("")

    # Summary
    lines.append("📊 SUMMARY")
    lines.append("-" * 30)

    status_indicators = []
    if env["ollama"]["available"]:
        status_indicators.append("✅ Ollama")
    else:
        status_indicators.append("❌ Ollama")

    if config["status"] == "loaded":
        status_indicators.append("✅ Config")
    else:
        status_indicators.append("❌ Config")

    if db["status"] == "healthy":
        status_indicators.append("✅ Database")
    else:
        status_indicators.append("❌ Database")

    if llm["status"] == "healthy":
        status_indicators.append("✅ LLM")
    else:
        status_indicators.append("❌ LLM")

    lines.append(f"Overall Status: {' | '.join(status_indicators)}")
    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)


def collect_debug_info() -> dict[str, Any]:
    """Main orchestration function to collect all debug information."""
    logger.info("Starting debug info collection")

    debug_data = {
        "system_environment": collect_system_environment(),
        "configuration": collect_config_info(),
        "database": collect_database_info(),
        "llm": collect_llm_info(),
        "system_prompt": collect_system_prompt(),
    }

    logger.info("Debug info collection completed")
    return debug_data


def generate_debug_report() -> str:
    """Generate a complete debug report as formatted string."""
    try:
        debug_data = collect_debug_info()
        return format_debug_output(debug_data)
    except Exception as e:
        logger.error(f"Failed to generate debug report: {e}")
        return f"Error generating debug report: {e}"
