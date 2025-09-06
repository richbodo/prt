"""Test pagination system for large datasets.

TDD approach - writing tests first before implementation.
Tests cover pagination, alphabetical jumping, position memory, and lazy loading.
"""

from typing import Any
from typing import Dict
from typing import List

# These imports will fail initially - that's expected in TDD
from prt_src.core.components.pagination import AlphabeticalIndex
from prt_src.core.components.pagination import PaginationSystem
from prt_src.core.components.pagination import PositionMemory


def create_test_contacts(count: int = 100) -> List[Dict[str, Any]]:
    """Create test contacts for pagination testing."""
    contacts = []
    names = [
        "Alice",
        "Bob",
        "Charlie",
        "David",
        "Eve",
        "Frank",
        "Grace",
        "Henry",
        "Iris",
        "Jack",
        "Kate",
        "Liam",
        "Mary",
        "Nathan",
        "Olivia",
        "Peter",
        "Quinn",
        "Rachel",
        "Sam",
        "Tina",
        "Uma",
        "Victor",
        "Wendy",
        "Xavier",
        "Yara",
        "Zoe",
    ]

    # Create multiple contacts for each starting letter
    for i in range(count):
        name_index = i % len(names)
        name = f"{names[name_index]} Test{i:03d}"
        contacts.append(
            {"id": i + 1, "name": name, "email": f"{name.lower().replace(' ', '')}@example.com"}
        )

    return sorted(contacts, key=lambda x: x["name"])


class TestPaginationSystem:
    """Test core pagination functionality."""

    def test_basic_pagination(self):
        """Test basic page creation and navigation."""
        paginator = PaginationSystem(page_size=10)
        items = create_test_contacts(25)

        # Initialize pagination
        paginator.set_items(items)

        # Should have 3 pages (25 items / 10 per page)
        assert paginator.total_pages == 3
        assert paginator.total_items == 25

        # Get first page
        page = paginator.get_page(1)
        assert page.page_number == 1
        assert len(page.items) == 10
        assert page.has_next is True
        assert page.has_previous is False

        # Get second page
        page = paginator.get_page(2)
        assert page.page_number == 2
        assert len(page.items) == 10
        assert page.has_next is True
        assert page.has_previous is True

        # Get last page
        page = paginator.get_page(3)
        assert page.page_number == 3
        assert len(page.items) == 5  # Only 5 items on last page
        assert page.has_next is False
        assert page.has_previous is True

    def test_navigation_methods(self):
        """Test next/previous page navigation."""
        paginator = PaginationSystem(page_size=5)
        items = create_test_contacts(20)
        paginator.set_items(items)

        # Start at first page
        page = paginator.get_current_page()
        assert page.page_number == 1

        # Go to next page
        page = paginator.next_page()
        assert page.page_number == 2

        # Go to next page again
        page = paginator.next_page()
        assert page.page_number == 3

        # Go to previous page
        page = paginator.previous_page()
        assert page.page_number == 2

        # Jump to specific page
        page = paginator.go_to_page(4)
        assert page.page_number == 4

        # Try to go beyond last page (should stay on last page)
        page = paginator.next_page()
        assert page.page_number == 4  # Still on last page

    def test_invalid_page_requests(self):
        """Test handling of invalid page numbers."""
        paginator = PaginationSystem(page_size=10)
        items = create_test_contacts(30)
        paginator.set_items(items)

        # Page 0 should return page 1
        page = paginator.get_page(0)
        assert page.page_number == 1

        # Negative page should return page 1
        page = paginator.get_page(-1)
        assert page.page_number == 1

        # Page beyond total should return last page
        page = paginator.get_page(10)
        assert page.page_number == 3  # Last page

    def test_empty_dataset(self):
        """Test pagination with no items."""
        paginator = PaginationSystem(page_size=10)
        paginator.set_items([])

        assert paginator.total_pages == 0
        assert paginator.total_items == 0

        page = paginator.get_current_page()
        assert page.items == []
        assert page.has_next is False
        assert page.has_previous is False


class TestAlphabeticalIndex:
    """Test alphabetical jumping functionality."""

    def test_alphabetical_index_creation(self):
        """Test creation of alphabetical index."""
        index = AlphabeticalIndex()
        items = create_test_contacts(100)

        # Build index from items (assuming 'name' field)
        index.build_index(items, key="name")

        # Should have entries for multiple letters
        letters = index.get_available_letters()
        assert len(letters) > 0
        assert "A" in letters  # Alice
        assert "Z" in letters  # Zoe

    def test_jump_to_letter(self):
        """Test jumping to a specific letter."""
        paginator = PaginationSystem(page_size=10)
        items = create_test_contacts(100)
        paginator.set_items(items)

        # Jump to letter 'M'
        page = paginator.jump_to_letter("M")
        assert page is not None
        # The page should contain at least one item starting with M
        has_m = any(item["name"][0].upper() == "M" for item in page.items)
        assert has_m, f"Page {page.page_number} doesn't contain items starting with M"

    def test_letter_with_no_items(self):
        """Test jumping to letter with no items."""
        paginator = PaginationSystem(page_size=10)
        items = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
            {"id": 3, "name": "Charlie"},
        ]
        paginator.set_items(items)

        # Jump to 'X' which has no items
        page = paginator.jump_to_letter("X")
        # Should go to the closest available letter or last page
        assert page is not None

    def test_case_insensitive_jump(self):
        """Test that letter jumping is case-insensitive."""
        paginator = PaginationSystem(page_size=10)
        items = create_test_contacts(50)
        paginator.set_items(items)

        # Both should work the same
        page1 = paginator.jump_to_letter("a")
        page2 = paginator.jump_to_letter("A")
        assert page1.page_number == page2.page_number


class TestPositionMemory:
    """Test position memory functionality."""

    def test_remember_position(self):
        """Test that paginator remembers position for different lists."""
        memory = PositionMemory()

        # Remember position for contacts list
        memory.save_position("contacts", page=3, item_index=5)

        # Remember position for tags list
        memory.save_position("tags", page=1, item_index=2)

        # Retrieve positions
        contacts_pos = memory.get_position("contacts")
        assert contacts_pos["page"] == 3
        assert contacts_pos["item_index"] == 5

        tags_pos = memory.get_position("tags")
        assert tags_pos["page"] == 1
        assert tags_pos["item_index"] == 2

    def test_restore_position(self):
        """Test restoring to a remembered position."""
        paginator = PaginationSystem(page_size=10, enable_memory=True)
        items = create_test_contacts(50)
        paginator.set_items(items, list_id="contacts")

        # Navigate to page 3
        paginator.go_to_page(3)

        # Switch to different list
        other_items = create_test_contacts(30)
        paginator.set_items(other_items, list_id="other")

        # Go back to contacts - should restore position
        paginator.set_items(items, list_id="contacts")
        page = paginator.get_current_page()
        assert page.page_number == 3  # Restored to page 3

    def test_clear_memory(self):
        """Test clearing position memory."""
        memory = PositionMemory()

        memory.save_position("contacts", page=3, item_index=5)
        memory.save_position("tags", page=2, item_index=1)

        # Clear specific list memory
        memory.clear_position("contacts")
        assert memory.get_position("contacts") is None
        assert memory.get_position("tags") is not None

        # Clear all memory
        memory.clear_all()
        assert memory.get_position("tags") is None


class TestLazyLoading:
    """Test lazy loading functionality."""

    def test_lazy_load_on_demand(self):
        """Test that pages are loaded only when requested."""
        # Create paginator with lazy loading
        paginator = PaginationSystem(page_size=10, lazy_load=True)

        # Create a large dataset provider (simulating database)
        def data_provider(offset: int, limit: int):
            """Simulate loading data from database."""
            all_items = create_test_contacts(1000)
            return all_items[offset : offset + limit]

        # Set data provider instead of items
        paginator.set_data_provider(data_provider, total_count=1000)

        # Request page 5 - should only load items for that page
        page = paginator.get_page(5)
        assert len(page.items) == 10
        assert page.page_number == 5

        # Verify we got 10 items and they have the expected structure
        assert all("id" in item and "name" in item for item in page.items)

    def test_lazy_load_caching(self):
        """Test that lazy-loaded pages can be cached."""
        load_count = 0

        def data_provider(offset: int, limit: int):
            nonlocal load_count
            load_count += 1
            all_items = create_test_contacts(100)
            return all_items[offset : offset + limit]

        paginator = PaginationSystem(page_size=10, lazy_load=True, cache_pages=True)
        paginator.set_data_provider(data_provider, total_count=100)

        # Load page 2 twice
        page1 = paginator.get_page(2)
        page2 = paginator.get_page(2)

        # Should only load once due to caching
        assert load_count == 1
        assert page1.items == page2.items


class TestPaginationConfig:
    """Test pagination configuration options."""

    def test_custom_page_sizes(self):
        """Test different page size configurations."""
        # Small pages
        paginator = PaginationSystem(page_size=5)
        items = create_test_contacts(20)
        paginator.set_items(items)
        assert paginator.total_pages == 4

        # Large pages
        paginator = PaginationSystem(page_size=50)
        paginator.set_items(items)
        assert paginator.total_pages == 1

    def test_dynamic_page_size_change(self):
        """Test changing page size dynamically."""
        paginator = PaginationSystem(page_size=10)
        items = create_test_contacts(30)
        paginator.set_items(items)

        assert paginator.total_pages == 3

        # Change page size
        paginator.set_page_size(15)
        assert paginator.total_pages == 2

        # Change to larger page size
        paginator.set_page_size(30)
        assert paginator.total_pages == 1

    def test_pagination_info(self):
        """Test getting pagination metadata."""
        paginator = PaginationSystem(page_size=10)
        items = create_test_contacts(45)
        paginator.set_items(items)

        paginator.go_to_page(2)
        info = paginator.get_pagination_info()

        assert info["current_page"] == 2
        assert info["total_pages"] == 5
        assert info["total_items"] == 45
        assert info["page_size"] == 10
        assert info["start_index"] == 11  # Page 2 starts at item 11
        assert info["end_index"] == 20  # Page 2 ends at item 20
        assert info["has_next"] is True
        assert info["has_previous"] is True
