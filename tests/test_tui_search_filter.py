"""Test Search & Filter UI for the Textual TUI.

Lightweight TDD for search and filter functionality.
"""

from prt_src.tui.widgets.search_filter import FilterPanel, SearchableList, SearchBar


class TestSearchBar:
    """Test the SearchBar widget."""

    def test_search_bar_creation(self):
        """Test that SearchBar can be created."""
        search_bar = SearchBar()
        assert search_bar is not None
        assert hasattr(search_bar, "query")

    def test_search_bar_input(self):
        """Test search input handling."""
        on_search_called = False
        search_query = None

        def on_search(query):
            nonlocal on_search_called, search_query
            on_search_called = True
            search_query = query

        search_bar = SearchBar(on_search=on_search)
        search_bar.set_query("test search")
        search_bar.submit()

        assert on_search_called
        assert search_query == "test search"

    def test_search_bar_clear(self):
        """Test clearing search."""
        search_bar = SearchBar()
        search_bar.set_query("something")

        assert search_bar.query == "something"

        search_bar.clear()
        assert search_bar.query == ""

    def test_search_bar_vim_bindings(self):
        """Test vim-style search bindings."""
        search_bar = SearchBar()

        # Test '/' to focus search
        assert search_bar.handle_key("/")
        assert search_bar.is_focused


class TestFilterPanel:
    """Test the FilterPanel widget."""

    def test_filter_panel_creation(self):
        """Test that FilterPanel can be created."""
        panel = FilterPanel()
        assert panel is not None
        assert hasattr(panel, "filters")

    def test_filter_panel_add_filter(self):
        """Test adding filters."""
        panel = FilterPanel()

        # Add tag filter
        panel.add_filter("tag", "work")
        assert "tag" in panel.filters
        assert "work" in panel.filters["tag"]

        # Add another tag
        panel.add_filter("tag", "personal")
        assert len(panel.filters["tag"]) == 2

    def test_filter_panel_remove_filter(self):
        """Test removing filters."""
        panel = FilterPanel()
        panel.add_filter("tag", "work")
        panel.add_filter("tag", "personal")

        panel.remove_filter("tag", "work")
        assert "work" not in panel.filters["tag"]
        assert "personal" in panel.filters["tag"]

    def test_filter_panel_clear_all(self):
        """Test clearing all filters."""
        panel = FilterPanel()
        panel.add_filter("tag", "work")
        panel.add_filter("type", "family")

        panel.clear_all()
        assert len(panel.filters) == 0

    def test_filter_panel_get_active_filters(self):
        """Test getting active filters."""
        panel = FilterPanel()
        panel.add_filter("tag", "work")
        panel.add_filter("type", "friend")

        active = panel.get_active_filters()
        assert len(active) == 2
        assert ("tag", "work") in active
        assert ("type", "friend") in active


class TestSearchableList:
    """Test the SearchableList widget."""

    def test_searchable_list_creation(self):
        """Test that SearchableList can be created."""
        searchable = SearchableList()
        assert searchable is not None
        assert hasattr(searchable, "items")
        assert hasattr(searchable, "filtered_items")

    def test_searchable_list_load_items(self):
        """Test loading items."""
        items = [
            {"id": 1, "name": "Alice", "tags": ["work"]},
            {"id": 2, "name": "Bob", "tags": ["personal"]},
            {"id": 3, "name": "Charlie", "tags": ["work", "friend"]},
        ]

        searchable = SearchableList()
        searchable.load_items(items)

        assert len(searchable.items) == 3
        assert len(searchable.filtered_items) == 3

    def test_searchable_list_search(self):
        """Test search functionality."""
        items = [
            {"id": 1, "name": "Alice Anderson"},
            {"id": 2, "name": "Bob Brown"},
            {"id": 3, "name": "Charlie Anderson"},
        ]

        searchable = SearchableList()
        searchable.load_items(items)

        # Search for "Anderson"
        searchable.search("Anderson")
        assert len(searchable.filtered_items) == 2
        assert searchable.filtered_items[0]["name"] == "Alice Anderson"
        assert searchable.filtered_items[1]["name"] == "Charlie Anderson"

    def test_searchable_list_filter(self):
        """Test filter functionality."""
        items = [
            {"id": 1, "name": "Alice", "tags": ["work"]},
            {"id": 2, "name": "Bob", "tags": ["personal"]},
            {"id": 3, "name": "Charlie", "tags": ["work", "friend"]},
        ]

        searchable = SearchableList()
        searchable.load_items(items)

        # Filter by work tag
        searchable.apply_filters([("tags", "work")])
        assert len(searchable.filtered_items) == 2
        assert searchable.filtered_items[0]["name"] == "Alice"
        assert searchable.filtered_items[1]["name"] == "Charlie"

    def test_searchable_list_combined_search_filter(self):
        """Test combined search and filter."""
        items = [
            {"id": 1, "name": "Alice Anderson", "tags": ["work"]},
            {"id": 2, "name": "Bob Anderson", "tags": ["personal"]},
            {"id": 3, "name": "Charlie Brown", "tags": ["work"]},
        ]

        searchable = SearchableList()
        searchable.load_items(items)

        # Search for "Anderson" and filter by "work"
        searchable.search("Anderson")
        searchable.apply_filters([("tags", "work")])

        assert len(searchable.filtered_items) == 1
        assert searchable.filtered_items[0]["name"] == "Alice Anderson"
