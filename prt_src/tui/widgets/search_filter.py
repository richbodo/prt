"""Search and Filter UI widgets for the PRT Textual TUI.

Provides search bar, filter panel, and searchable list functionality
with vim-style keybindings.
"""

from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.containers import ScrollableContainer
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import Button
from textual.widgets import Checkbox
from textual.widgets import Input
from textual.widgets import Label
from textual.widgets import Static

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


class SearchScopeFilter(Static):
    """Filter widget for search scope selection."""

    def __init__(self, on_scope_change: Optional[Callable] = None):
        """Initialize search scope filter.

        Args:
            on_scope_change: Callback when scope changes
        """
        super().__init__()
        self.on_scope_change = on_scope_change
        self.add_class("search-scope-filter")
        self.scope_options = {
            "all": True,  # Default to all
            "contacts": False,
            "relationships": False,
            "metadata": False,  # This includes notes and tags
        }

    def compose(self) -> ComposeResult:
        """Compose the scope filter layout."""
        with Vertical(classes="scope-filter-container"):
            yield Label("Search In:", classes="scope-title")
            yield Checkbox("All", value=True, id="scope_all", classes="scope-checkbox")
            yield Checkbox("Contacts", value=False, id="scope_contacts", classes="scope-checkbox")
            yield Checkbox(
                "Relationships", value=False, id="scope_relationships", classes="scope-checkbox"
            )
            yield Checkbox(
                "Metadata (Notes/Tags)", value=False, id="scope_metadata", classes="scope-checkbox"
            )

    def get_selected_scopes(self) -> List[str]:
        """Get list of selected scope types.

        Returns:
            List of selected scope strings
        """
        selected = []

        # If 'all' is selected, return None to search all types
        if self.scope_options.get("all", False):
            return []

        if self.scope_options.get("contacts", False):
            selected.append("contacts")
        if self.scope_options.get("relationships", False):
            selected.append("relationships")
        if self.scope_options.get("metadata", False):
            selected.extend(["notes", "tags"])

        return selected or []

    def on_checkbox_changed(self, event) -> None:
        """Handle checkbox state changes."""
        checkbox = event.checkbox

        # Update internal state
        if checkbox.id == "scope_all":
            self.scope_options["all"] = checkbox.value
            # If 'all' is checked, uncheck others
            if checkbox.value:
                for scope in ["contacts", "relationships", "metadata"]:
                    self.scope_options[scope] = False
                    try:
                        self.query_one(f"#scope_{scope}", Checkbox).value = False
                    except Exception:
                        pass
        else:
            scope_key = checkbox.id.replace("scope_", "")
            self.scope_options[scope_key] = checkbox.value

            # If any specific scope is checked, uncheck 'all'
            if checkbox.value:
                self.scope_options["all"] = False
                try:
                    self.query_one("#scope_all", Checkbox).value = False
                except Exception:
                    pass
            # If no specific scopes are selected, check 'all'
            elif not any(self.scope_options[k] for k in ["contacts", "relationships", "metadata"]):
                self.scope_options["all"] = True
                try:
                    self.query_one("#scope_all", Checkbox).value = True
                except Exception:
                    pass

        # Notify parent of scope change
        if self.on_scope_change:
            self.on_scope_change(self.get_selected_scopes())


class SearchResultList(Static):
    """Widget for displaying search results."""

    def __init__(self, on_result_select: Optional[Callable] = None):
        """Initialize search result list.

        Args:
            on_result_select: Callback when a result is selected
        """
        super().__init__()
        self.on_result_select = on_result_select
        self.add_class("search-result-list")
        self.results = {}
        self.selected_index = 0
        self.flattened_results = []  # For navigation

    def compose(self) -> ComposeResult:
        """Compose the result list layout."""
        with Vertical(classes="result-list-container"):
            with ScrollableContainer(id="results-scroll", classes="results-scroll"):
                yield Vertical(id="results-content", classes="results-content")
            yield Static("", id="result-status", classes="result-status")

    def update_results(self, search_data: Dict[str, Any]) -> None:
        """Update the displayed results.

        Args:
            search_data: Search results from unified search API
        """
        self.results = search_data
        self.selected_index = 0
        self._build_flattened_results()
        self._update_display()
        self._update_status()

    def _build_flattened_results(self) -> None:
        """Build flattened list of results for navigation."""
        self.flattened_results = []
        results = self.results.get("results", {})

        # Add results in order: contacts, relationships, notes, tags
        for entity_type in ["contacts", "relationships", "notes", "tags"]:
            if entity_type in results:
                for result in results[entity_type]:
                    self.flattened_results.append((entity_type, result))

    def _update_display(self) -> None:
        """Update the results display."""
        try:
            content = self.query_one("#results-content", Vertical)
            content.remove_children()

            results = self.results.get("results", {})

            # Display results grouped by type
            for entity_type, items in results.items():
                if not items:
                    continue

                # Section header
                header_text = f"{entity_type.title()} ({len(items)})"
                content.mount(Static(header_text, classes="result-section-header"))

                # Results in this section
                for i, result in enumerate(items):
                    result_widget = self._create_result_item(entity_type, result, i)
                    content.mount(result_widget)

                # Add spacing between sections
                content.mount(Static("", classes="section-spacer"))

        except Exception as e:
            # Fallback display
            try:
                content = self.query_one("#results-content", Vertical)
                content.mount(Static(f"Error displaying results: {e}", classes="error-message"))
            except Exception:
                pass

    def _create_result_item(self, entity_type: str, result: Any, index: int) -> Static:
        """Create a result item widget.

        Args:
            entity_type: Type of entity
            result: Result data
            index: Index within this entity type

        Returns:
            Static widget for the result item
        """
        # Calculate global index
        global_index = self._get_global_index(entity_type, index)

        if entity_type == "contacts":
            title = getattr(result, "title", "Unknown Contact")
            subtitle = getattr(result, "subtitle", "")
            snippet = getattr(result, "snippet", "")

            text = f"📧 {title}"
            if subtitle:
                text += f"\n   {subtitle}"
            if snippet:
                text += f"\n   {snippet}"

        elif entity_type == "relationships":
            title = getattr(result, "title", "Unknown Relationship")
            snippet = getattr(result, "snippet", "")

            text = f"🔗 {title}"
            if snippet:
                text += f"\n   {snippet}"

        elif entity_type == "notes":
            title = getattr(result, "title", "Unknown Note")
            snippet = getattr(result, "snippet", "")

            text = f"📝 {title}"
            if snippet:
                text += f"\n   {snippet[:100]}{'...' if len(snippet) > 100 else ''}"

        elif entity_type == "tags":
            title = getattr(result, "title", "Unknown Tag")
            metadata = getattr(result, "metadata", {})
            contact_count = metadata.get("contact_count", 0)

            text = f"🏷️  {title}"
            if contact_count:
                text += f"\n   Used by {contact_count} contact{'s' if contact_count != 1 else ''}"
        else:
            title = getattr(result, "title", "Unknown")
            text = f"❓ {title}"

        classes = "result-item"
        if global_index == self.selected_index:
            classes += " selected"

        return Static(text, classes=classes, id=f"result_{global_index}")

    def _get_global_index(self, entity_type: str, local_index: int) -> int:
        """Get global index for a result."""
        global_index = 0
        results = self.results.get("results", {})

        for etype in ["contacts", "relationships", "notes", "tags"]:
            if etype == entity_type:
                return global_index + local_index
            if etype in results:
                global_index += len(results[etype])

        return global_index

    def _update_status(self) -> None:
        """Update the status bar."""
        try:
            status = self.query_one("#result-status", Static)

            total = self.results.get("total", 0)
            query = self.results.get("query", "")
            search_time = self.results.get("stats", {}).get("search_time", 0.0)

            if total > 0:
                status_text = f"Found {total} result{'s' if total != 1 else ''} for '{query}' in {search_time:.2f}s"
            else:
                status_text = f"No results found for '{query}'"

            status.update(status_text)
        except Exception:
            pass

    def navigate_results(self, direction: str) -> bool:
        """Navigate through results.

        Args:
            direction: 'up' or 'down'

        Returns:
            True if navigation was successful
        """
        if not self.flattened_results:
            return False

        old_index = self.selected_index

        if direction == "up":
            self.selected_index = max(0, self.selected_index - 1)
        elif direction == "down":
            self.selected_index = min(len(self.flattened_results) - 1, self.selected_index + 1)

        if old_index != self.selected_index:
            self._update_selection_display()
            return True

        return False

    def _update_selection_display(self) -> None:
        """Update the visual selection in the display."""
        try:
            # Remove old selection
            content = self.query_one("#results-content", Vertical)
            for child in content.children:
                if hasattr(child, "remove_class"):
                    child.remove_class("selected")

            # Add new selection
            try:
                selected_item = self.query_one(f"#result_{self.selected_index}", Static)
                selected_item.add_class("selected")
            except Exception:
                pass

        except Exception:
            pass

    def get_selected_result(self) -> Optional[Tuple[str, Any]]:
        """Get the currently selected result.

        Returns:
            Tuple of (entity_type, result) or None
        """
        if 0 <= self.selected_index < len(self.flattened_results):
            return self.flattened_results[self.selected_index]
        return None

    def select_current_result(self) -> bool:
        """Select the current result.

        Returns:
            True if a result was selected
        """
        result = self.get_selected_result()
        if result and self.on_result_select:
            entity_type, result_data = result
            self.on_result_select(entity_type, result_data)
            return True
        return False
