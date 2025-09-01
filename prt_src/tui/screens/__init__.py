"""Screen registry and exports for PRT TUI screens.

Pre-registers all screens to enable parallel development
without conflicts.
"""

from typing import Dict, Optional, Type

from prt_src.logging_config import get_logger
from prt_src.tui.screens.base import BaseScreen, EscapeIntent

logger = get_logger(__name__)

# Screen registry - will be populated with actual implementations
SCREEN_REGISTRY: Dict[str, Type[BaseScreen]] = {}


def register_screen(name: str, screen_class: Type[BaseScreen]) -> None:
    """Register a screen class.

    Args:
        name: Unique screen identifier
        screen_class: Screen class (must inherit from BaseScreen)
    """
    if name in SCREEN_REGISTRY:
        logger.warning(f"Overriding existing screen registration: {name}")

    SCREEN_REGISTRY[name] = screen_class
    logger.debug(f"Registered screen: {name}")


def get_screen_class(name: str) -> Optional[Type[BaseScreen]]:
    """Get a screen class by name.

    Args:
        name: Screen identifier

    Returns:
        Screen class or None if not found
    """
    return SCREEN_REGISTRY.get(name)


def create_screen(name: str, **kwargs) -> Optional[BaseScreen]:
    """Create a screen instance with services.

    Args:
        name: Screen identifier
        **kwargs: Services and parameters to inject

    Returns:
        Screen instance or None if not found
    """
    screen_class = get_screen_class(name)
    if not screen_class:
        logger.error(f"Screen not found in registry: {name}")
        return None

    try:
        return screen_class(**kwargs)
    except Exception as e:
        logger.error(f"Failed to create screen {name}: {e}")
        return None


def list_screens() -> list[str]:
    """List all registered screen names.

    Returns:
        List of screen identifiers
    """
    return list(SCREEN_REGISTRY.keys())


# Pre-register screens (will be replaced with actual implementations)
# This allows parallel development without __init__.py conflicts

# Placeholder imports - these will be created as stubs in Task 4A.5
# When screens are implemented, they'll auto-register themselves

__all__ = [
    "BaseScreen",
    "EscapeIntent",
    "register_screen",
    "get_screen_class",
    "create_screen",
    "list_screens",
    "SCREEN_REGISTRY",
]

# Screen imports will be added here as they're implemented
# Each screen module will call register_screen() when imported

# Import screens to register them (Phase 5 Contact Management Forms)
try:
    from . import (
        contact_detail,  # Contact Detail Screen (Task 5.3)
        contact_form,  # Contact Form Screen (Task 5.4)
    )

    # Make imports accessible
    _ = contact_detail
    _ = contact_form
except ImportError as e:
    # Handle import errors gracefully during development
    import logging

    logging.getLogger(__name__).warning(f"Failed to import contact screens: {e}")

# Import screens to register them (Phase 5 Relationship Management - Task 5.5 & 5.6)
try:
    from . import (
        relationship_form,  # Relationship Form Screen (Task 5.5)
        relationship_types,  # Relationship Types Screen (Task 5.6)
    )

    # Make imports accessible
    _ = relationship_form
    _ = relationship_types
except ImportError as e:
    # Handle import errors gracefully during development
    import logging

    logging.getLogger(__name__).warning(f"Failed to import relationship screens: {e}")

# Import screens to register them (Phase 5 Import/Export - Task 5.7 & 5.8)
try:
    # Import needs special handling due to 'import' keyword
    import importlib

    import_module = importlib.import_module("prt_src.tui.screens.import")
    from . import export  # Export Screen (Task 5.8)

    # Make imports accessible
    _ = import_module
    _ = export
except ImportError as e:
    # Handle import errors gracefully during development
    import logging

    logging.getLogger(__name__).warning(f"Failed to import import/export screens: {e}")

# Import screens to register them (Phase 5 Track D - First-Run Wizard)
try:
    from . import wizard  # First-Run Wizard Screen (Task 5.9)

    # Make import accessible
    _ = wizard
except ImportError as e:
    # Handle import errors gracefully during development
    import logging

    logging.getLogger(__name__).warning(f"Failed to import wizard screen: {e}")
