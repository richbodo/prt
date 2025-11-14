"""Pagination system for handling large datasets.

Provides pagination, alphabetical jumping, position memory, and lazy loading
for efficient navigation through large contact lists. UI-agnostic.
"""

import math
from dataclasses import dataclass
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional

from prt_src.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class Page:
    """Represents a single page of results."""

    page_number: int
    items: List[Dict[str, Any]]
    total_pages: int
    total_items: int
    has_next: bool
    has_previous: bool
    page_size: int


@dataclass
class PaginationConfig:
    """Configuration for pagination behavior."""

    page_size: int = 10
    cache_pages: bool = False
    lazy_load: bool = False
    enable_memory: bool = False


class AlphabeticalIndex:
    """Manage alphabetical index for quick jumping."""

    def __init__(self):
        self.index: Dict[str, int] = {}
        self.available_letters: List[str] = []

    def build_index(self, items: List[Dict[str, Any]], key: str = "name") -> None:
        """Build alphabetical index from items.

        Args:
            items: List of items to index
            key: Field to use for alphabetical sorting
        """
        self.index.clear()
        letters_seen = set()

        for i, item in enumerate(items):
            value = item.get(key, "")
            if value:
                first_letter = value[0].upper()
                if first_letter not in self.index:
                    self.index[first_letter] = i
                    letters_seen.add(first_letter)

        self.available_letters = sorted(letters_seen)

    def get_available_letters(self) -> List[str]:
        """Get list of available letters in the index."""
        return self.available_letters

    def get_position_for_letter(self, letter: str) -> Optional[int]:
        """Get the item index for a given letter.

        Args:
            letter: Letter to jump to

        Returns:
            Index of first item starting with that letter, or None
        """
        letter = letter.upper()
        return self.index.get(letter)

    def get_closest_letter(self, letter: str) -> Optional[str]:
        """Find the closest available letter.

        Args:
            letter: Target letter

        Returns:
            Closest available letter or None
        """
        letter = letter.upper()
        if letter in self.available_letters:
            return letter

        # Find the next available letter
        for available in self.available_letters:
            if available > letter:
                return available

        # If no letter after, return the last available
        return self.available_letters[-1] if self.available_letters else None


class PositionMemory:
    """Remember position in different lists."""

    def __init__(self):
        self.positions: Dict[str, Dict[str, Any]] = {}

    def save_position(self, list_id: str, page: int, item_index: Optional[int] = None) -> None:
        """Save current position for a list.

        Args:
            list_id: Identifier for the list
            page: Current page number
            item_index: Optional index of selected item on page
        """
        self.positions[list_id] = {"page": page, "item_index": item_index}

    def get_position(self, list_id: str) -> Optional[Dict[str, Any]]:
        """Get saved position for a list.

        Args:
            list_id: Identifier for the list

        Returns:
            Saved position or None
        """
        return self.positions.get(list_id)

    def clear_position(self, list_id: str) -> None:
        """Clear saved position for a list.

        Args:
            list_id: Identifier for the list
        """
        if list_id in self.positions:
            del self.positions[list_id]

    def clear_all(self) -> None:
        """Clear all saved positions."""
        self.positions.clear()


class PaginationSystem:
    """Main pagination system for handling large datasets."""

    def __init__(
        self,
        page_size: int = 10,
        lazy_load: bool = False,
        cache_pages: bool = False,
        enable_memory: bool = False,
    ):
        """Initialize pagination system.

        Args:
            page_size: Number of items per page
            lazy_load: Whether to load pages on demand
            cache_pages: Whether to cache loaded pages
            enable_memory: Whether to remember positions
        """
        self.page_size = page_size
        self.lazy_load = lazy_load
        self.cache_pages = cache_pages
        self.enable_memory = enable_memory

        self.items: List[Dict[str, Any]] = []
        self.total_items = 0
        self.current_page = 1
        self.total_pages = 0

        self.alphabetical_index = AlphabeticalIndex()
        self.position_memory = PositionMemory() if enable_memory else None

        # For lazy loading
        self.data_provider: Optional[Callable] = None
        self.page_cache: Dict[int, List[Dict[str, Any]]] = {}

        # Current list identifier for position memory
        self.current_list_id: Optional[str] = None

    def set_items(self, items: List[Dict[str, Any]], list_id: Optional[str] = None) -> None:
        """Set items for pagination.

        Args:
            items: List of items to paginate
            list_id: Optional identifier for position memory
        """
        self.items = items
        self.total_items = len(items)
        self.total_pages = (
            math.ceil(self.total_items / self.page_size) if self.total_items > 0 else 0
        )

        # Build alphabetical index
        if items:
            self.alphabetical_index.build_index(items)

        # Handle position memory
        if self.enable_memory and list_id:
            # Restore position if switching back to a known list
            if self.current_list_id and self.current_list_id != list_id and self.position_memory:
                # Save current position before switching
                self.position_memory.save_position(self.current_list_id, self.current_page)

            self.current_list_id = list_id

            # Restore previous position
            if self.position_memory:
                saved_pos = self.position_memory.get_position(list_id)
                if saved_pos:
                    self.current_page = saved_pos["page"]
        else:
            self.current_page = 1

        # Clear cache when items change
        self.page_cache.clear()

    def set_data_provider(
        self, provider: Callable[[int, int], List[Dict[str, Any]]], total_count: int
    ) -> None:
        """Set a data provider for lazy loading.

        Args:
            provider: Function that returns items (offset, limit) -> items
            total_count: Total number of items available
        """
        self.data_provider = provider
        self.total_items = total_count
        self.total_pages = math.ceil(total_count / self.page_size) if total_count > 0 else 0
        self.current_page = 1
        self.page_cache.clear()

    def get_page(self, page_number: int) -> Page:
        """Get a specific page of results.

        Args:
            page_number: Page number (1-indexed)

        Returns:
            Page object with items and metadata
        """
        # Handle invalid page numbers
        if page_number < 1:
            page_number = 1
        elif self.total_pages > 0 and page_number > self.total_pages:
            page_number = self.total_pages

        # Handle empty dataset
        if self.total_pages == 0:
            return Page(
                page_number=1,
                items=[],
                total_pages=0,
                total_items=0,
                has_next=False,
                has_previous=False,
                page_size=self.page_size,
            )

        # Get items for this page
        if self.lazy_load and self.data_provider:
            items = self._load_page_lazy(page_number)
        else:
            items = self._get_page_items(page_number)

        self.current_page = page_number

        return Page(
            page_number=page_number,
            items=items,
            total_pages=self.total_pages,
            total_items=self.total_items,
            has_next=page_number < self.total_pages,
            has_previous=page_number > 1,
            page_size=self.page_size,
        )

    def _get_page_items(self, page_number: int) -> List[Dict[str, Any]]:
        """Get items for a specific page from loaded items.

        Args:
            page_number: Page number (1-indexed)

        Returns:
            List of items for the page
        """
        start_index = (page_number - 1) * self.page_size
        end_index = start_index + self.page_size
        return self.items[start_index:end_index]

    def _load_page_lazy(self, page_number: int) -> List[Dict[str, Any]]:
        """Load a page using the data provider.

        Args:
            page_number: Page number (1-indexed)

        Returns:
            List of items for the page
        """
        # Check cache first
        if self.cache_pages and page_number in self.page_cache:
            return self.page_cache[page_number]

        # Load from data provider
        if self.data_provider:
            offset = (page_number - 1) * self.page_size
            items = self.data_provider(offset, self.page_size)

            # Cache if enabled
            if self.cache_pages:
                self.page_cache[page_number] = items

            return items

        return []

    def get_current_page(self) -> Page:
        """Get the current page."""
        return self.get_page(self.current_page)

    def next_page(self) -> Page:
        """Navigate to the next page."""
        if self.current_page < self.total_pages:
            return self.get_page(self.current_page + 1)
        return self.get_current_page()

    def previous_page(self) -> Page:
        """Navigate to the previous page."""
        if self.current_page > 1:
            return self.get_page(self.current_page - 1)
        return self.get_current_page()

    def go_to_page(self, page_number: int) -> Page:
        """Jump to a specific page."""
        return self.get_page(page_number)

    def jump_to_letter(self, letter: str) -> Optional[Page]:
        """Jump to the page containing items starting with a letter.

        Args:
            letter: Letter to jump to

        Returns:
            Page containing first item with that letter, or None
        """
        # Handle lazy loading - can't jump to letter
        if self.lazy_load:
            logger.warning("Letter jumping not supported with lazy loading")
            return self.get_current_page()

        letter = letter.upper()

        # Find position for letter
        position = self.alphabetical_index.get_position_for_letter(letter)

        if position is None:
            # Try to find closest letter
            closest = self.alphabetical_index.get_closest_letter(letter)
            if closest:
                position = self.alphabetical_index.get_position_for_letter(closest)

        if position is not None:
            # Calculate which page this position is on
            page_number = (position // self.page_size) + 1
            return self.get_page(page_number)

        return self.get_current_page()

    def set_page_size(self, new_size: int) -> None:
        """Change the page size dynamically.

        Args:
            new_size: New page size
        """
        if new_size < 1:
            raise ValueError("Page size must be at least 1")

        self.page_size = new_size
        self.total_pages = (
            math.ceil(self.total_items / self.page_size) if self.total_items > 0 else 0
        )

        # Adjust current page if necessary
        if self.current_page > self.total_pages and self.total_pages > 0:
            self.current_page = self.total_pages

        # Clear cache as pagination has changed
        self.page_cache.clear()

    def get_pagination_info(self) -> Dict[str, Any]:
        """Get detailed pagination information.

        Returns:
            Dictionary with pagination metadata
        """
        start_index = (self.current_page - 1) * self.page_size + 1 if self.total_items > 0 else 0
        end_index = min(start_index + self.page_size - 1, self.total_items)

        return {
            "current_page": self.current_page,
            "total_pages": self.total_pages,
            "total_items": self.total_items,
            "page_size": self.page_size,
            "start_index": start_index,
            "end_index": end_index,
            "has_next": self.current_page < self.total_pages,
            "has_previous": self.current_page > 1,
            "available_letters": self.alphabetical_index.get_available_letters(),
        }
