"""Search infrastructure for PRT.

This module provides high-performance search capabilities using SQLite FTS5
and intelligent caching for the PRT application.
"""

from .indexer import EntityType
from .indexer import SearchIndexer
from .indexer import SearchResult

__all__ = ["EntityType", "SearchIndexer", "SearchResult"]
