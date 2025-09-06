"""Platform abstraction layer for PRT.

This module provides abstractions for platform-specific functionality,
allowing the same business logic to run on different platforms
(terminal, web, mobile).
"""

from .base import Platform
from .base import PlatformCapabilities

__all__ = ["Platform", "PlatformCapabilities"]
