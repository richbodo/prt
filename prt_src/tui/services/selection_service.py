"""SelectionService - Manages selection state for search results.

Tracks which items are currently selected by ID, supporting:
- Individual selection/deselection
- Range selection
- Toggle selection
- Bulk selection
- Query selection state
"""

from typing import Any
from typing import Dict
from typing import List
from typing import Set


class SelectionService:
    """Manages selection state for search results.

    Attributes:
        selected_ids: Set of currently selected item IDs
    """

    def __init__(self):
        """Initialize selection service with empty selection."""
        self.selected_ids: Set[int] = set()

    def select(self, id: int) -> None:
        """Select an item by ID.

        Args:
            id: Item ID to select
        """
        self.selected_ids.add(id)

    def select_range(self, start_id: int, end_id: int) -> None:
        """Select a range of IDs (inclusive).

        Args:
            start_id: First ID in range
            end_id: Last ID in range (inclusive)
        """
        for id in range(start_id, end_id + 1):
            self.selected_ids.add(id)

    def deselect(self, id: int) -> None:
        """Deselect an item by ID.

        Args:
            id: Item ID to deselect (safe if not selected)
        """
        self.selected_ids.discard(id)

    def toggle(self, id: int) -> None:
        """Toggle selection state for an item.

        Args:
            id: Item ID to toggle
        """
        if id in self.selected_ids:
            self.selected_ids.remove(id)
        else:
            self.selected_ids.add(id)

    def clear(self) -> None:
        """Clear all selections."""
        self.selected_ids.clear()

    def is_selected(self, id: int) -> bool:
        """Check if an item is selected.

        Args:
            id: Item ID to check

        Returns:
            True if item is selected
        """
        return id in self.selected_ids

    def is_empty(self) -> bool:
        """Check if selection is empty.

        Returns:
            True if no items are selected
        """
        return len(self.selected_ids) == 0

    def count(self) -> int:
        """Get count of selected items.

        Returns:
            Number of selected items
        """
        return len(self.selected_ids)

    def get_selected_ids(self) -> Set[int]:
        """Get copy of selected IDs.

        Returns:
            Copy of selected IDs set
        """
        return self.selected_ids.copy()

    def select_all(self, ids: List[int]) -> None:
        """Select all IDs from a list.

        Args:
            ids: List of IDs to select
        """
        for id in ids:
            self.selected_ids.add(id)

    def select_all_from_results(self, results: List[Dict[str, Any]]) -> None:
        """Select all items from result list.

        Args:
            results: List of result dicts with 'id' keys
        """
        for item in results:
            if "id" in item:
                self.selected_ids.add(item["id"])
