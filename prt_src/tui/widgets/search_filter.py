"""Search and Filter UI widgets for the PRT Textual TUI.

Provides search bar, filter panel, and searchable list functionality
with vim-style keybindings.
"""

from typing import Callable, Dict, List, Optional, Set, Tuple

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Button, Input, Label, Static

from prt_src.tui.widgets.base import ModeAwareWidget


class SearchBar(Static):
    """Search bar widget with vim-style activation."""

    def __init__(self, on_search: Optional[Callable] = None, placeholder: str = "Search..."):
        """Initialize the search bar.

        Args:
            on_search: Callback when search is submitted
            placeholder: Placeholder text for the input
        """
        super().__init__()
        self.query = ""
        self.on_search = on_search
        self.placeholder = placeholder
        self.is_focused = False
        self.add_class("search-bar")

    def compose(self) -> ComposeResult:
        """Compose the search bar layout."""
        with Horizontal(classes="search-container"):
            yield Input(placeholder=self.placeholder, id="search-input", classes="search-input")
            yield Button("Search", id="search-btn", classes="search-button")
            yield Button("Clear", id="clear-btn", classes="clear-button")

    def set_query(self, query: str) -> None:
        """Set the search query.

        Args:
            query: The search query
        """
        self.query = query
        try:
            self.query_one("#search-input", Input).value = query
        except Exception:
            pass

    def clear(self) -> None:
        """Clear the search query."""
        self.query = ""
        self.set_query("")
        if self.on_search:
            self.on_search("")

    def submit(self) -> None:
        """Submit the search."""
        if self.on_search:
            self.on_search(self.query)

    def handle_key(self, key: str) -> bool:
        """Handle key press events.

        Args:
            key: The key that was pressed

        Returns:
            True if the key was handled
        """
        if key == "/":
            # Focus search input
            self.is_focused = True
            try:
                self.query_one("#search-input", Input).focus()
            except Exception:
                pass
            return True
        return False


class FilterPanel(Static):
    """Filter panel for managing active filters."""

    def __init__(self, on_filter_change: Optional[Callable] = None):
        """Initialize the filter panel.

        Args:
            on_filter_change: Callback when filters change
        """
        super().__init__()
        self.filters: Dict[str, Set[str]] = {}
        self.on_filter_change = on_filter_change
        self.add_class("filter-panel")

    def compose(self) -> ComposeResult:
        """Compose the filter panel layout."""
        with Vertical(classes="filter-container"):
            yield Label("Active Filters", classes="filter-title")
            yield Vertical(id="filter-list", classes="filter-list")
            yield Button("Clear All", id="clear-filters", classes="clear-filters-button")

    def add_filter(self, category: str, value: str) -> None:
        """Add a filter.

        Args:
            category: Filter category (e.g., "tag", "type")
            value: Filter value
        """
        if category not in self.filters:
            self.filters[category] = set()

        self.filters[category].add(value)
        self._update_display()

        if self.on_filter_change:
            self.on_filter_change(self.get_active_filters())

    def remove_filter(self, category: str, value: str) -> None:
        """Remove a filter.

        Args:
            category: Filter category
            value: Filter value
        """
        if category in self.filters:
            self.filters[category].discard(value)
            if not self.filters[category]:
                del self.filters[category]

            self._update_display()

            if self.on_filter_change:
                self.on_filter_change(self.get_active_filters())

    def clear_all(self) -> None:
        """Clear all filters."""
        self.filters.clear()
        self._update_display()

        if self.on_filter_change:
            self.on_filter_change([])

    def get_active_filters(self) -> List[Tuple[str, str]]:
        """Get list of active filters.

        Returns:
            List of (category, value) tuples
        """
        result = []
        for category, values in self.filters.items():
            for value in values:
                result.append((category, value))
        return result

    def _update_display(self) -> None:
        """Update the filter display."""
        try:
            filter_list = self.query_one("#filter-list", Vertical)
            filter_list.remove_children()

            for category, values in self.filters.items():
                for value in values:
                    filter_text = f"{category}: {value}"
                    filter_list.mount(Static(filter_text, classes="filter-item"))
        except Exception:
            pass


class SearchableList(ModeAwareWidget):
    """A list widget with search and filter capabilities."""

    filtered_count = reactive(0)

    def __init__(self):
        """Initialize the searchable list."""
        super().__init__()
        self.items: List[Dict] = []
        self.filtered_items: List[Dict] = []
        self.search_query = ""
        self.active_filters: List[Tuple[str, str]] = []
        self.add_class("searchable-list")

    def compose(self) -> ComposeResult:
        """Compose the searchable list layout."""
        with Vertical(classes="searchable-container"):
            # Search bar at top
            self.search_bar = SearchBar(on_search=self.search)
            yield self.search_bar

            # Filter panel on side
            with Horizontal(classes="content-area"):
                self.filter_panel = FilterPanel(on_filter_change=self.apply_filters)
                yield self.filter_panel

                # Items list
                yield Vertical(id="items-list", classes="items-list")

            # Status bar at bottom
            yield Static("", id="search-status", classes="search-status")

    def load_items(self, items: List[Dict]) -> None:
        """Load items into the list.

        Args:
            items: List of item dictionaries
        """
        self.items = items
        self.filtered_items = items.copy()
        self._update_display()

    def search(self, query: str) -> None:
        """Search items.

        Args:
            query: Search query string
        """
        self.search_query = query.lower()
        self._apply_filters_and_search()

    def apply_filters(self, filters: List[Tuple[str, str]]) -> None:
        """Apply filters to items.

        Args:
            filters: List of (category, value) filter tuples
        """
        self.active_filters = filters
        self._apply_filters_and_search()

    def _apply_filters_and_search(self) -> None:
        """Apply both search and filters to items."""
        self.filtered_items = self.items.copy()

        # Apply search
        if self.search_query:
            self.filtered_items = [
                item
                for item in self.filtered_items
                if self._item_matches_search(item, self.search_query)
            ]

        # Apply filters
        for category, value in self.active_filters:
            self.filtered_items = [
                item
                for item in self.filtered_items
                if self._item_matches_filter(item, category, value)
            ]

        self.filtered_count = len(self.filtered_items)
        self._update_display()
        self._update_status()

    def _item_matches_search(self, item: Dict, query: str) -> bool:
        """Check if an item matches the search query.

        Args:
            item: Item dictionary
            query: Search query (lowercase)

        Returns:
            True if item matches
        """
        # Search in name field
        if "name" in item and query in item["name"].lower():
            return True

        # Search in email field
        if "email" in item and query in item["email"].lower():
            return True

        # Search in other text fields
        for key, value in item.items():
            if isinstance(value, str) and query in value.lower():
                return True

        return False

    def _item_matches_filter(self, item: Dict, category: str, value: str) -> bool:
        """Check if an item matches a filter.

        Args:
            item: Item dictionary
            category: Filter category
            value: Filter value

        Returns:
            True if item matches
        """
        if category not in item:
            return False

        item_value = item[category]

        # Handle list values (like tags)
        if isinstance(item_value, list):
            return value in item_value

        # Handle string values
        return str(item_value) == value

    def _update_display(self) -> None:
        """Update the items display."""
        try:
            items_list = self.query_one("#items-list", Vertical)
            items_list.remove_children()

            for item in self.filtered_items:
                # Display item name and other info
                name = item.get("name", "Unknown")
                info = []
                if "email" in item:
                    info.append(item["email"])
                if "tags" in item:
                    info.append(f"Tags: {', '.join(item['tags'])}")

                item_text = name
                if info:
                    item_text += f"\n{' • '.join(info)}"

                items_list.mount(Static(item_text, classes="search-item"))
        except Exception:
            pass

    def _update_status(self) -> None:
        """Update the status bar."""
        try:
            status = self.query_one("#search-status", Static)

            if self.search_query or self.active_filters:
                status.update(f"Showing {len(self.filtered_items)} of {len(self.items)} items")
            else:
                status.update(f"{len(self.items)} items")
        except Exception:
            pass
