"""Core UI-agnostic components for PRT.

These components provide reusable functionality for Textual and future Flet UIs.
"""

from .pagination import (
    AlphabeticalIndex,
    Page,
    PaginationConfig,
    PaginationSystem,
    PositionMemory,
)
from .validation import (
    ContactValidator,
    DataSanitizer,
    DuplicateDetector,
    NoteValidator,
    RelationshipValidator,
    TagValidator,
    ValidationError,
    ValidationResult,
    ValidationSystem,
)

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
