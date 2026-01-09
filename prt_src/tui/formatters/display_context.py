"""DisplayContext - Holds current display state for search results.

This dataclass encapsulates all display-related state including:
- Current search results
- Result type (contacts, relationships, notes, tags)
- Display mode (numbered_list, table, card, compact)
- Pagination information
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class DisplayContext:
    """Holds display state for search results.

    Attributes:
        current_results: List of result items (dicts) or None if no results
        result_type: Type of results ('contacts', 'relationships', 'notes', 'tags')
        display_mode: Formatting mode ('numbered_list', 'table', 'card', 'compact')
        pagination_info: Optional dict with 'total', 'showing', 'offset' keys
    """

    current_results: list[dict[str, Any]] | None = None
    result_type: str = "contacts"
    display_mode: str = "numbered_list"
    pagination_info: dict[str, int] | None = None

    def __post_init__(self):
        """Validate field values after initialization."""
        # Validate display_mode
        valid_modes = ["numbered_list", "table", "card", "compact"]
        if self.display_mode not in valid_modes:
            raise ValueError(
                f"Invalid display_mode '{self.display_mode}'. "
                f"Valid modes: {', '.join(valid_modes)}"
            )

        # Validate result_type
        valid_types = ["contacts", "relationships", "notes", "tags"]
        if self.result_type not in valid_types:
            raise ValueError(
                f"Invalid result_type '{self.result_type}'. "
                f"Valid types: {', '.join(valid_types)}"
            )

    def has_results(self) -> bool:
        """Check if context has any results.

        Returns:
            True if current_results is not None and has items
        """
        return self.current_results is not None and len(self.current_results) > 0

    def result_count(self) -> int:
        """Get count of current results.

        Returns:
            Number of results, or 0 if no results
        """
        if self.current_results is None:
            return 0
        return len(self.current_results)

    def clear_results(self) -> None:
        """Clear current results and pagination info."""
        self.current_results = None
        self.pagination_info = None

    def update_results(
        self, new_results: list[dict[str, Any]], pagination: dict[str, int] | None = None
    ) -> None:
        """Update results and optionally pagination info.

        Args:
            new_results: New list of result items
            pagination: Optional pagination info
        """
        self.current_results = new_results
        if pagination is not None:
            self.pagination_info = pagination
