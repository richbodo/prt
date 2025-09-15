"""Search cache infrastructure for PRT.

This module provides high-performance caching for search operations,
including LRU caching and prefix tries for autocomplete.
"""

from .contact_cache import CachedContact
from .contact_cache import ContactSearchCache

__all__ = ["CachedContact", "ContactSearchCache"]
