"""Selection system for dual-select and multi-select operations.

Provides two modes:
- DUAL: For selecting exactly 2 items (e.g., relationship creation)
- MULTI: For selecting multiple items (e.g., bulk operations)

UI-agnostic and maintains selection state across pagination.
"""

from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from prt_src.logging_config import get_logger

logger = get_logger(__name__)


class SelectionMode(Enum):
    """Selection mode enumeration."""

    DUAL = "dual"  # Exactly 2 items
    MULTI = "multi"  # Multiple items


class SortOrder(Enum):
    """Sort order enumeration."""

    ASCENDING = "asc"
    DESCENDING = "desc"


@dataclass
class SelectionResult:
    """Result of a selection operation."""

    success: bool
    message: str = ""


@dataclass
class SelectionState:
    """Current state of selections."""

    mode: SelectionMode
    count: int
    is_complete: bool
    can_proceed: bool
    selected_items: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SelectionFilter:
    """Filter configuration for selections."""

    category: Optional[str] = None
    tags: Optional[List[str]] = None
    min_relationships: Optional[int] = None
    max_relationships: Optional[int] = None


@dataclass
class ValidationResult:
    """Result of selection validation."""

    is_valid: bool
    message: str = ""


@dataclass
class DualSelection:
    """Container for dual selection state."""

    first: Optional[Dict[str, Any]] = None
    second: Optional[Dict[str, Any]] = None

    def is_complete(self) -> bool:
        """Check if both selections are made."""
        return self.first is not None and self.second is not None

    def clear(self):
        """Clear both selections."""
        self.first = None
        self.second = None


@dataclass
class MultiSelection:
    """Container for multi-selection state."""

    items: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    max_selections: Optional[int] = None

    def add(self, item: Dict[str, Any]) -> bool:
        """Add an item to selection.

        Args:
            item: Item to add

        Returns:
            True if added, False if limit reached
        """
        if self.max_selections and len(self.items) >= self.max_selections:
            return False

        item_id = item.get("id")
        if item_id is not None:
            self.items[item_id] = item
            return True
        return False

    def remove(self, item: Dict[str, Any]) -> bool:
        """Remove an item from selection.

        Args:
            item: Item to remove

        Returns:
            True if removed, False if not found
        """
        item_id = item.get("id")
        if item_id in self.items:
            del self.items[item_id]
            return True
        return False

    def contains(self, item: Dict[str, Any]) -> bool:
        """Check if item is selected.

        Args:
            item: Item to check

        Returns:
            True if selected
        """
        item_id = item.get("id")
        return item_id in self.items if item_id is not None else False

    def clear(self):
        """Clear all selections."""
        self.items.clear()

    def get_all(self) -> List[Dict[str, Any]]:
        """Get all selected items."""
        return list(self.items.values())


class SelectionSystem:
    """Main selection system supporting dual and multi modes."""

    def __init__(
        self, mode: SelectionMode = SelectionMode.MULTI, max_selections: Optional[int] = None
    ):
        """Initialize selection system.

        Args:
            mode: Selection mode (DUAL or MULTI)
            max_selections: Maximum selections allowed (for MULTI mode)
        """
        self.mode = mode

        if mode == SelectionMode.DUAL:
            self.selection = DualSelection()
            self.max_selections = 2
        else:
            self.selection = MultiSelection(max_selections=max_selections)
            self.max_selections = max_selections

        # Track selection sources for dual mode
        self._selection_sources: Dict[int, str] = {}

    def select_item(self, item: Dict[str, Any]) -> SelectionResult:
        """Select an item.

        Args:
            item: Item to select

        Returns:
            SelectionResult indicating success/failure
        """
        if self.mode == SelectionMode.DUAL:
            return self._select_dual(item)
        else:
            return self._select_multi(item)

    def _select_dual(self, item: Dict[str, Any]) -> SelectionResult:
        """Handle dual mode selection.

        Args:
            item: Item to select

        Returns:
            SelectionResult
        """
        dual_sel = self.selection

        if dual_sel.first is None:
            dual_sel.first = item
            return SelectionResult(success=True)
        elif dual_sel.second is None:
            dual_sel.second = item
            return SelectionResult(success=True)
        else:
            return SelectionResult(
                success=False, message="Maximum of 2 items can be selected in dual mode"
            )

    def _select_multi(self, item: Dict[str, Any]) -> SelectionResult:
        """Handle multi mode selection.

        Args:
            item: Item to select

        Returns:
            SelectionResult
        """
        if self.selection.add(item):
            return SelectionResult(success=True)
        else:
            return SelectionResult(
                success=False, message=f"Maximum of {self.max_selections} items can be selected"
            )

    def deselect_item(self, item: Dict[str, Any]) -> SelectionResult:
        """Deselect an item.

        Args:
            item: Item to deselect

        Returns:
            SelectionResult
        """
        if self.mode == SelectionMode.DUAL:
            dual_sel = self.selection
            if dual_sel.first and dual_sel.first.get("id") == item.get("id"):
                dual_sel.first = None
                return SelectionResult(success=True)
            elif dual_sel.second and dual_sel.second.get("id") == item.get("id"):
                dual_sel.second = None
                return SelectionResult(success=True)
            return SelectionResult(success=False, message="Item not selected")
        else:
            if self.selection.remove(item):
                return SelectionResult(success=True)
            return SelectionResult(success=False, message="Item not selected")

    def toggle_item(self, item: Dict[str, Any]) -> SelectionResult:
        """Toggle item selection.

        Args:
            item: Item to toggle

        Returns:
            SelectionResult
        """
        if self.is_selected(item):
            return self.deselect_item(item)
        else:
            return self.select_item(item)

    def is_selected(self, item: Dict[str, Any]) -> bool:
        """Check if an item is selected.

        Args:
            item: Item to check

        Returns:
            True if selected
        """
        if self.mode == SelectionMode.DUAL:
            dual_sel = self.selection
            item_id = item.get("id")
            return (dual_sel.first and dual_sel.first.get("id") == item_id) or (
                dual_sel.second and dual_sel.second.get("id") == item_id
            )
        else:
            return self.selection.contains(item)

    def select_all(self, items: List[Dict[str, Any]]) -> SelectionResult:
        """Select all provided items (MULTI mode only).

        Args:
            items: Items to select

        Returns:
            SelectionResult
        """
        if self.mode != SelectionMode.MULTI:
            return SelectionResult(success=False, message="Select all only available in multi mode")

        for item in items:
            if not self.selection.add(item):
                return SelectionResult(
                    success=False, message=f"Selection limit reached at {self.max_selections} items"
                )

        return SelectionResult(success=True)

    def select_page(self, items: List[Dict[str, Any]]) -> SelectionResult:
        """Select all items on current page (MULTI mode only).

        Args:
            items: Page items to select

        Returns:
            SelectionResult
        """
        return self.select_all(items)

    def clear_all(self):
        """Clear all selections."""
        self.selection.clear()

    def get_selected_count(self) -> int:
        """Get count of selected items.

        Returns:
            Number of selected items
        """
        if self.mode == SelectionMode.DUAL:
            dual_sel = self.selection
            count = 0
            if dual_sel.first is not None:
                count += 1
            if dual_sel.second is not None:
                count += 1
            return count
        else:
            return len(self.selection.items)

    def get_selected_items(self) -> List[Dict[str, Any]]:
        """Get all selected items.

        Returns:
            List of selected items
        """
        if self.mode == SelectionMode.DUAL:
            dual_sel = self.selection
            items = []
            if dual_sel.first is not None:
                items.append(dual_sel.first)
            if dual_sel.second is not None:
                items.append(dual_sel.second)
            return items
        else:
            return self.selection.get_all()

    def get_selected_ids(self) -> List[int]:
        """Get IDs of selected items.

        Returns:
            List of selected item IDs
        """
        items = self.get_selected_items()
        return [item["id"] for item in items if "id" in item]

    def replace_selection(self, index: int, new_item: Dict[str, Any]) -> SelectionResult:
        """Replace a selection at index (DUAL mode only).

        Args:
            index: Index to replace (0 or 1)
            new_item: New item to select

        Returns:
            SelectionResult
        """
        if self.mode != SelectionMode.DUAL:
            return SelectionResult(success=False, message="Replace only available in dual mode")

        dual_sel = self.selection
        if index == 0:
            dual_sel.first = new_item
            return SelectionResult(success=True)
        elif index == 1:
            dual_sel.second = new_item
            return SelectionResult(success=True)
        else:
            return SelectionResult(success=False, message="Invalid index for dual selection")

    def select_from_search(self, item: Dict[str, Any], source: str = "search") -> SelectionResult:
        """Select an item from search results.

        Args:
            item: Item from search
            source: Source of selection

        Returns:
            SelectionResult
        """
        result = self.select_item(item)
        if result.success and item.get("id"):
            self._selection_sources[item["id"]] = source
        return result

    def get_state(self) -> SelectionState:
        """Get current selection state.

        Returns:
            SelectionState object
        """
        count = self.get_selected_count()

        if self.mode == SelectionMode.DUAL:
            is_complete = count == 2
            can_proceed = is_complete
        else:
            is_complete = False  # Multi mode doesn't have "complete" state
            can_proceed = count > 0

        return SelectionState(
            mode=self.mode,
            count=count,
            is_complete=is_complete,
            can_proceed=can_proceed,
            selected_items=self.get_selected_items(),
        )

    def get_filtered_selections(self, filter_config: SelectionFilter) -> List[Dict[str, Any]]:
        """Get filtered selected items.

        Args:
            filter_config: Filter configuration

        Returns:
            Filtered list of selected items
        """
        items = self.get_selected_items()
        filtered = items

        # Filter by category
        if filter_config.category:
            filtered = [item for item in filtered if item.get("category") == filter_config.category]

        # Filter by tags
        if filter_config.tags:
            filtered = [
                item
                for item in filtered
                if any(tag in item.get("tags", []) for tag in filter_config.tags)
            ]

        # Filter by relationship count
        if filter_config.min_relationships is not None:
            filtered = [
                item
                for item in filtered
                if item.get("relationship_count", 0) >= filter_config.min_relationships
            ]

        if filter_config.max_relationships is not None:
            filtered = [
                item
                for item in filtered
                if item.get("relationship_count", 0) <= filter_config.max_relationships
            ]

        return filtered

    def get_sorted_selections(
        self, key: str = "name", order: SortOrder = SortOrder.ASCENDING
    ) -> List[Dict[str, Any]]:
        """Get sorted selected items.

        Args:
            key: Field to sort by
            order: Sort order

        Returns:
            Sorted list of selected items
        """
        items = self.get_selected_items()
        return self.sort_items(items, key, order)

    def sort_items(
        self, items: List[Dict[str, Any]], key: str = "name", order: SortOrder = SortOrder.ASCENDING
    ) -> List[Dict[str, Any]]:
        """Sort a list of items.

        Args:
            items: Items to sort
            key: Field to sort by
            order: Sort order

        Returns:
            Sorted list of items
        """
        reverse = order == SortOrder.DESCENDING
        return sorted(items, key=lambda x: x.get(key, ""), reverse=reverse)

    def get_summary(self) -> Dict[str, Any]:
        """Get selection summary for UI display.

        Returns:
            Summary dictionary
        """
        items = self.get_selected_items()
        categories = {}

        # Count by category
        for item in items:
            category = item.get("category", "Uncategorized")
            categories[category] = categories.get(category, 0) + 1

        return {
            "total_selected": len(items),
            "mode": self.mode.value,
            "categories": categories,
            "has_selections": len(items) > 0,
        }

    def validate_for_operation(self, operation: str) -> ValidationResult:
        """Validate selections for a specific operation.

        Args:
            operation: Operation to validate for

        Returns:
            ValidationResult
        """
        count = self.get_selected_count()

        if operation == "create_relationship":
            if self.mode != SelectionMode.DUAL:
                return ValidationResult(
                    is_valid=False, message="Relationship creation requires dual selection mode"
                )
            if count != 2:
                return ValidationResult(
                    is_valid=False, message="Relationship creation requires exactly 2 contacts"
                )
            return ValidationResult(is_valid=True)

        if operation in ["bulk_export", "bulk_tag", "bulk_delete"]:
            if count == 0:
                return ValidationResult(
                    is_valid=False, message=f"{operation} requires at least one selection"
                )
            return ValidationResult(is_valid=True)

        return ValidationResult(is_valid=True)

    def export_state(self) -> Dict[str, Any]:
        """Export selection state for persistence.

        Returns:
            State dictionary
        """
        return {
            "mode": self.mode.value,
            "selected_ids": self.get_selected_ids(),
            "count": self.get_selected_count(),
        }

    def import_state(self, state: Dict[str, Any], items: List[Dict[str, Any]]):
        """Import selection state.

        Args:
            state: Exported state
            items: Available items to select from
        """
        self.clear_all()

        # Create ID to item mapping
        item_map = {item["id"]: item for item in items if "id" in item}

        # Restore selections
        for item_id in state.get("selected_ids", []):
            if item_id in item_map:
                self.select_item(item_map[item_id])
