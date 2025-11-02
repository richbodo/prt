"""
Fixture Database Manager for PRT.

Provides safe database isolation for fixture data loading without affecting
the user's real database. This module follows the same pattern as debug mode
but is specifically designed for setup wizard fixture loading.
"""

from typing import Any
from typing import Dict

from rich.console import Console

from .config import data_dir
from .logging_config import get_logger

console = Console()
logger = get_logger(__name__)


def setup_fixture_mode(regenerate: bool = False, quiet: bool = False) -> Dict[str, Any]:
    """Set up fixture mode with isolated database.

    Creates a separate fixture.db file that doesn't touch the user's real database.
    This ensures complete data safety when users want to try demo data.

    Args:
        regenerate: If True, force regeneration of fixture.db even if it exists.
                   If False, reuse existing fixture.db if present.
        quiet: If True, suppress console output (useful for automated testing)

    Returns:
        Configuration dictionary pointing to the isolated fixture database
    """
    from tests.fixtures import setup_test_database

    logger.info("[FIXTURE] Setting up fixture mode with isolated database")

    # Create a separate fixture database in the data directory
    fixture_db_path = data_dir() / "fixture.db"

    # Check if fixture database already exists
    if fixture_db_path.exists() and not regenerate:
        if not quiet:
            console.print(f"📂 Using existing fixture database: {fixture_db_path}", style="blue")
            console.print("   (Demo data preserved from previous session)", style="dim")
            console.print()
        logger.info(f"[FIXTURE] Reusing existing fixture database: {fixture_db_path}")
    else:
        # Remove existing fixture database if regenerating
        if fixture_db_path.exists():
            fixture_db_path.unlink()
            if not quiet:
                console.print("🔄 Regenerating fixture database...", style="yellow")
            logger.info("[FIXTURE] Removed existing fixture database for regeneration")

        if not quiet:
            console.print(f"🔧 Creating fixture database at: {fixture_db_path}", style="blue")
        logger.info(f"[FIXTURE] Creating new fixture database: {fixture_db_path}")

        # Create database with fixture data
        from .db import create_database

        db = create_database(fixture_db_path)
        fixtures = setup_test_database(db)

        if not quiet:
            console.print("📊 Loaded fixture data:", style="green")
            console.print(
                f"   • {len(fixtures['contacts'])} contacts with profile images", style="green"
            )
            console.print(f"   • {len(fixtures['tags'])} tags", style="green")
            console.print(f"   • {len(fixtures['notes'])} notes", style="green")
            console.print(f"   • {len(fixtures['relationships'])} relationships", style="green")
            console.print()

        logger.info(
            f"[FIXTURE] Fixture database created successfully: "
            f"{len(fixtures['contacts'])} contacts, {len(fixtures['tags'])} tags, "
            f"{len(fixtures['notes'])} notes, {len(fixtures['relationships'])} relationships"
        )

    # Return fixture configuration (isolated from real database)
    config = {
        "db_path": str(fixture_db_path),
        "db_encrypted": False,
        "db_username": "fixture_user",
        "db_password": "fixture_pass",
        "db_type": "sqlite",
        "database_mode": "fixture",  # Track that this is fixture mode
    }

    logger.info(f"[FIXTURE] Fixture mode configuration: {config}")
    return config


def is_fixture_mode(config: Dict[str, Any]) -> bool:
    """Check if the given configuration is for fixture mode.

    Args:
        config: Configuration dictionary

    Returns:
        True if config points to fixture database, False otherwise
    """
    if not config:
        return False

    # Check if db_path points to fixture database
    db_path = config.get("db_path", "")
    if "fixture.db" in str(db_path):
        return True

    # Check explicit mode marker
    return config.get("database_mode") == "fixture"


def get_database_mode(config: Dict[str, Any]) -> str:
    """Get the current database mode from configuration.

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


def cleanup_fixture_database() -> bool:
    """Clean up the fixture database file.

    This is useful for testing or when users want to start fresh.

    Returns:
        True if cleanup was successful or file didn't exist, False on error
    """
    try:
        fixture_db_path = data_dir() / "fixture.db"
        if fixture_db_path.exists():
            fixture_db_path.unlink()
            logger.info("[FIXTURE] Fixture database cleaned up successfully")
            return True
        else:
            logger.info("[FIXTURE] No fixture database to clean up")
            return True
    except Exception as e:
        logger.error(f"[FIXTURE] Error cleaning up fixture database: {e}", exc_info=True)
        return False


def get_fixture_summary() -> Dict[str, Any]:
    """Get summary of fixture data without loading a database.

    This provides information about what fixture data contains,
    useful for displaying to users before they choose to load it.

    Returns:
        Dictionary with fixture data summary
    """
    from tests.fixtures import get_fixture_spec

    try:
        spec = get_fixture_spec()
        return {
            "contacts": spec["contacts"]["count"],
            "tags": spec["tags"]["count"],
            "notes": spec["notes"]["count"],
            "relationships": spec["relationships"]["count"],
            "has_images": True,
            "description": "Demo data with realistic sample contacts, tags, and notes",
        }
    except Exception as e:
        logger.error(f"[FIXTURE] Error getting fixture summary: {e}", exc_info=True)
        return {
            "contacts": 0,
            "tags": 0,
            "notes": 0,
            "relationships": 0,
            "has_images": False,
            "description": "Error loading fixture summary",
        }
