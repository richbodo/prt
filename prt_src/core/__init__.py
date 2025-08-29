"""Core business logic operations for PRT.

This module provides UI-agnostic operations that can be used by any frontend
(CLI, Textual, Flet, etc). All operations return data structures rather than
formatted output.
"""

from .contacts import ContactOperations
from .database import DatabaseOperations
from .operations import Operations
from .relationships import RelationshipOperations
from .search import SearchOperations

__all__ = [
    "Operations",
    "ContactOperations",
    "RelationshipOperations",
    "SearchOperations",
    "DatabaseOperations",
]
