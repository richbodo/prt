"""Test selection system for both dual-select and multi-select modes.

TDD approach - writing tests first before implementation.
Tests cover dual selection for relationships and multi-selection for bulk operations.
"""

from typing import Any

# These imports will fail initially - that's expected in TDD
from prt_src.core.components.selection import SelectionFilter
from prt_src.core.components.selection import SelectionMode
from prt_src.core.components.selection import SelectionSystem
from prt_src.core.components.selection import SortOrder


def create_test_items(count: int = 50) -> list[dict[str, Any]]:
    """Create test items for selection testing."""
    items = []
    for i in range(count):
        items.append(
            {
                "id": i + 1,
                "name": f"Item {i + 1:03d}",
                "category": f"Category {(i % 5) + 1}",
                "tags": [f"tag{i % 3}", f"tag{i % 7}"],
                "relationship_count": i % 10,
                "date_added": f"2024-01-{(i % 28) + 1:02d}",
            }
        )
    return items


class TestDualSelection:
    """Test dual selection mode for relationship creation."""

    def test_basic_dual_selection(self):
        """Test selecting exactly two items."""
        selector = SelectionSystem(mode=SelectionMode.DUAL)
        items = create_test_items(10)

        # Should start with no selections
        assert selector.get_selected_count() == 0
        assert selector.get_selected_items() == []

        # Select first item
        result = selector.select_item(items[0])
        assert result.success is True
        assert selector.get_selected_count() == 1

        # Select second item
        result = selector.select_item(items[1])
        assert result.success is True
        assert selector.get_selected_count() == 2

        # Should not allow third selection in dual mode
        result = selector.select_item(items[2])
        assert result.success is False
        assert "maximum of 2 items" in result.message.lower()
        assert selector.get_selected_count() == 2

    def test_dual_selection_with_search(self):
        """Test dual selection with search/filter integration."""
        selector = SelectionSystem(mode=SelectionMode.DUAL)

        # Simulate selecting from search results
        search_result_1 = {"id": 101, "name": "John Doe", "email": "john@example.com"}
        search_result_2 = {"id": 202, "name": "Jane Smith", "email": "jane@example.com"}

        # Select from search
        selector.select_from_search(search_result_1, source="search")
        selector.select_from_search(search_result_2, source="search")

        selected = selector.get_selected_items()
        assert len(selected) == 2
        assert selected[0]["id"] == 101
        assert selected[1]["id"] == 202

    def test_dual_selection_replacement(self):
        """Test replacing selection in dual mode."""
        selector = SelectionSystem(mode=SelectionMode.DUAL)
        items = create_test_items(5)

        # Select two items
        selector.select_item(items[0])
        selector.select_item(items[1])

        # Replace first selection
        selector.replace_selection(0, items[2])
        selected = selector.get_selected_items()
        assert selected[0]["id"] == items[2]["id"]
        assert selected[1]["id"] == items[1]["id"]

    def test_dual_selection_clear(self):
        """Test clearing selections in dual mode."""
        selector = SelectionSystem(mode=SelectionMode.DUAL)
        items = create_test_items(5)

        selector.select_item(items[0])
        selector.select_item(items[1])
        assert selector.get_selected_count() == 2

        # Clear specific selection
        selector.deselect_item(items[0])
        assert selector.get_selected_count() == 1

        # Clear all
        selector.clear_all()
        assert selector.get_selected_count() == 0

    def test_dual_selection_state(self):
        """Test getting selection state for UI updates."""
        selector = SelectionSystem(mode=SelectionMode.DUAL)
        items = create_test_items(3)

        # Initial state
        state = selector.get_state()
        assert state.mode == SelectionMode.DUAL
        assert state.count == 0
        assert state.is_complete is False

        # After one selection
        selector.select_item(items[0])
        state = selector.get_state()
        assert state.count == 1
        assert state.is_complete is False
        assert state.can_proceed is False

        # After two selections (complete)
        selector.select_item(items[1])
        state = selector.get_state()
        assert state.count == 2
        assert state.is_complete is True
        assert state.can_proceed is True


class TestMultiSelection:
    """Test multi-selection mode for bulk operations."""

    def test_basic_multi_selection(self):
        """Test selecting multiple items."""
        selector = SelectionSystem(mode=SelectionMode.MULTI)
        items = create_test_items(20)

        # Select multiple items
        for i in range(5):
            result = selector.select_item(items[i])
            assert result.success is True

        assert selector.get_selected_count() == 5

        # Should allow many selections
        for i in range(5, 15):
            selector.select_item(items[i])

        assert selector.get_selected_count() == 15

    def test_multi_selection_toggle(self):
        """Test toggle selection (select/deselect)."""
        selector = SelectionSystem(mode=SelectionMode.MULTI)
        items = create_test_items(10)

        # Toggle item on
        selector.toggle_item(items[0])
        assert selector.is_selected(items[0]) is True

        # Toggle same item off
        selector.toggle_item(items[0])
        assert selector.is_selected(items[0]) is False

        # Toggle multiple items
        for item in items[:5]:
            selector.toggle_item(item)
        assert selector.get_selected_count() == 5

    def test_multi_selection_across_pages(self):
        """Test that selections persist across pagination."""
        selector = SelectionSystem(mode=SelectionMode.MULTI)

        # Simulate page 1 items
        page1_items = [{"id": i, "name": f"Page1 Item {i}"} for i in range(1, 11)]

        # Select some from page 1
        selector.select_item(page1_items[0])
        selector.select_item(page1_items[2])
        selector.select_item(page1_items[5])

        # Simulate moving to page 2
        page2_items = [{"id": i, "name": f"Page2 Item {i}"} for i in range(11, 21)]

        # Select some from page 2
        selector.select_item(page2_items[1])
        selector.select_item(page2_items[3])

        # All selections should be preserved
        assert selector.get_selected_count() == 5

        # Check that page 1 selections are still there
        assert selector.is_selected(page1_items[0]) is True
        assert selector.is_selected(page1_items[2]) is True

    def test_select_all_deselect_all(self):
        """Test select all and deselect all operations."""
        selector = SelectionSystem(mode=SelectionMode.MULTI)
        items = create_test_items(25)

        # Select all items
        selector.select_all(items)
        assert selector.get_selected_count() == 25

        # Deselect all
        selector.clear_all()
        assert selector.get_selected_count() == 0

        # Select all on current page only
        page_items = items[:10]  # Simulate first page
        selector.select_page(page_items)
        assert selector.get_selected_count() == 10

    def test_selection_limits(self):
        """Test maximum selection limits."""
        selector = SelectionSystem(mode=SelectionMode.MULTI, max_selections=10)
        items = create_test_items(20)

        # Select up to limit
        for i in range(10):
            result = selector.select_item(items[i])
            assert result.success is True

        # Try to exceed limit
        result = selector.select_item(items[10])
        assert result.success is False
        assert "maximum" in result.message.lower()
        assert selector.get_selected_count() == 10

    def test_get_selected_ids(self):
        """Test getting just the IDs of selected items."""
        selector = SelectionSystem(mode=SelectionMode.MULTI)
        items = create_test_items(10)

        # Select some items
        selector.select_item(items[1])  # id = 2
        selector.select_item(items[3])  # id = 4
        selector.select_item(items[7])  # id = 8

        ids = selector.get_selected_ids()
        assert ids == [2, 4, 8]


class TestSelectionFiltering:
    """Test filtering and sorting in selection system."""

    def test_filter_by_category(self):
        """Test filtering selections by category."""
        selector = SelectionSystem(mode=SelectionMode.MULTI)
        items = create_test_items(20)

        # Select items from different categories
        for item in items[:10]:
            selector.select_item(item)

        # Filter selected items by category
        filter_config = SelectionFilter(category="Category 1")
        filtered = selector.get_filtered_selections(filter_config)

        # Should only return selected items from Category 1
        assert all(item["category"] == "Category 1" for item in filtered)
        assert len(filtered) > 0

    def test_filter_by_tags(self):
        """Test filtering selections by tags."""
        selector = SelectionSystem(mode=SelectionMode.MULTI)
        items = create_test_items(20)

        # Select some items
        for item in items[:10]:
            selector.select_item(item)

        # Filter by tag
        filter_config = SelectionFilter(tags=["tag0"])
        filtered = selector.get_filtered_selections(filter_config)

        assert all("tag0" in item["tags"] for item in filtered)

    def test_sort_selections(self):
        """Test sorting selected items."""
        selector = SelectionSystem(mode=SelectionMode.MULTI)
        items = create_test_items(10)

        # Select items in random order
        selector.select_item(items[5])
        selector.select_item(items[2])
        selector.select_item(items[8])
        selector.select_item(items[1])

        # Sort by name
        sorted_items = selector.get_sorted_selections(key="name", order=SortOrder.ASCENDING)
        assert sorted_items[0]["name"] < sorted_items[-1]["name"]

        # Sort by relationship count descending
        sorted_items = selector.get_sorted_selections(
            key="relationship_count", order=SortOrder.DESCENDING
        )
        assert sorted_items[0]["relationship_count"] >= sorted_items[-1]["relationship_count"]

    def test_filter_and_sort_combined(self):
        """Test combining filter and sort operations."""
        selector = SelectionSystem(mode=SelectionMode.MULTI)
        items = create_test_items(30)

        # Select many items
        for item in items[:20]:
            selector.select_item(item)

        # Filter by category and sort by name
        filter_config = SelectionFilter(category="Category 2")
        filtered = selector.get_filtered_selections(filter_config)
        sorted_filtered = selector.sort_items(filtered, key="name", order=SortOrder.ASCENDING)

        # Check both filter and sort applied
        assert all(item["category"] == "Category 2" for item in sorted_filtered)
        if len(sorted_filtered) > 1:
            assert sorted_filtered[0]["name"] <= sorted_filtered[-1]["name"]


class TestSelectionState:
    """Test selection state management."""

    def test_selection_summary(self):
        """Test getting selection summary for UI display."""
        selector = SelectionSystem(mode=SelectionMode.MULTI)
        items = create_test_items(30)

        # Select items from different categories
        for i in range(15):
            selector.select_item(items[i])

        summary = selector.get_summary()
        assert summary["total_selected"] == 15
        assert summary["mode"] == "multi"
        assert "categories" in summary
        assert len(summary["categories"]) > 0

    def test_selection_validation(self):
        """Test validating selections before operations."""
        selector = SelectionSystem(mode=SelectionMode.DUAL)
        items = create_test_items(5)

        # Incomplete dual selection
        selector.select_item(items[0])
        validation = selector.validate_for_operation("create_relationship")
        assert validation.is_valid is False
        assert "exactly 2" in validation.message.lower()

        # Complete dual selection
        selector.select_item(items[1])
        validation = selector.validate_for_operation("create_relationship")
        assert validation.is_valid is True

    def test_selection_export(self):
        """Test exporting selection state for persistence."""
        selector = SelectionSystem(mode=SelectionMode.MULTI)
        items = create_test_items(10)

        # Make some selections
        selector.select_item(items[1])
        selector.select_item(items[3])
        selector.select_item(items[7])

        # Export state
        state = selector.export_state()
        assert state["mode"] == "multi"
        assert state["selected_ids"] == [2, 4, 8]
        assert state["count"] == 3

        # Create new selector and import state
        new_selector = SelectionSystem(mode=SelectionMode.MULTI)
        new_selector.import_state(state, items)

        assert new_selector.get_selected_count() == 3
        assert new_selector.is_selected(items[1]) is True
        assert new_selector.is_selected(items[3]) is True
        assert new_selector.is_selected(items[7]) is True


class TestSelectionIntegration:
    """Test integration with other components."""

    def test_selection_with_pagination(self):
        """Test that selection system works with pagination."""
        from prt_src.core.components.pagination import PaginationSystem

        selector = SelectionSystem(mode=SelectionMode.MULTI)
        paginator = PaginationSystem(page_size=10)

        items = create_test_items(50)
        paginator.set_items(items)

        # Select items from page 1
        page1 = paginator.get_page(1)
        for item in page1.items[:3]:
            selector.select_item(item)

        # Move to page 2 and select more
        page2 = paginator.get_page(2)
        for item in page2.items[:2]:
            selector.select_item(item)

        # Go back to page 1 - selections should persist
        page1_again = paginator.get_page(1)
        assert selector.is_selected(page1_again.items[0]) is True
        assert selector.get_selected_count() == 5

    def test_selection_with_validation(self):
        """Test validating selected items before operations."""
        from prt_src.core.components.validation import ValidationSystem

        selector = SelectionSystem(mode=SelectionMode.MULTI)
        validator = ValidationSystem()

        # Select some contacts
        contacts = [
            {"id": 1, "name": "John Doe", "email": "john@example.com"},
            {"id": 2, "name": "", "email": "invalid"},  # Invalid
            {"id": 3, "name": "Jane Smith", "email": "jane@example.com"},
        ]

        for contact in contacts:
            selector.select_item(contact)

        # Validate selected items
        selected = selector.get_selected_items()
        validation_results = []
        for item in selected:
            result = validator.validate_entity("contact", item)
            validation_results.append(result)

        # Should have one invalid item
        valid_count = sum(1 for r in validation_results if r.is_valid)
        assert valid_count == 2
        invalid_count = sum(1 for r in validation_results if not r.is_valid)
        assert invalid_count == 1
