"""Core UI-agnostic components for PRT.

These components provide reusable functionality for Textual and future Flet UIs.
"""

from .pagination import AlphabeticalIndex
from .pagination import Page
from .pagination import PaginationConfig
from .pagination import PaginationSystem
from .pagination import PositionMemory
from .validation import ContactValidator
from .validation import DataSanitizer
from .validation import DuplicateDetector
from .validation import NoteValidator
from .validation import RelationshipValidator
from .validation import TagValidator
from .validation import ValidationError
from .validation import ValidationResult
from .validation import ValidationSystem

__all__ = [
    # Pagination
    "PaginationSystem",
    "Page",
    "AlphabeticalIndex",
    "PositionMemory",
    "PaginationConfig",
    # Validation
    "ValidationSystem",
    "ValidationResult",
    "ValidationError",
    "ContactValidator",
    "TagValidator",
    "NoteValidator",
    "RelationshipValidator",
    "DuplicateDetector",
    "DataSanitizer",
]
