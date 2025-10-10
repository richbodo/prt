"""Unit tests for SelectionService.

Tests selection state management for search results.
"""

import pytest


class TestSelectionServiceBasic:
    """Test basic SelectionService functionality."""

    @pytest.mark.unit
    def test_selection_service_instantiates(self):
        """SelectionService can be instantiated."""
        from prt_src.tui.services.selection_service import SelectionService

        service = SelectionService()
        assert service is not None
        assert len(service.selected_ids) == 0

    @pytest.mark.unit
    def test_is_empty_on_creation(self):
        """Selection is empty on creation."""
        from prt_src.tui.services.selection_service import SelectionService

        service = SelectionService()
        assert service.is_empty()
        assert service.count() == 0


class TestSelectingItems:
    """Test selecting individual items."""

    @pytest.mark.unit
    def test_select_single_id(self):
        """Can select a single item by ID."""
        from prt_src.tui.services.selection_service import SelectionService

        service = SelectionService()
        service.select(1)

        assert 1 in service.selected_ids
        assert service.count() == 1
        assert not service.is_empty()

    @pytest.mark.unit
    def test_select_multiple_ids(self):
        """Can select multiple items."""
        from prt_src.tui.services.selection_service import SelectionService

        service = SelectionService()
        service.select(1)
        service.select(2)
        service.select(5)

        assert 1 in service.selected_ids
        assert 2 in service.selected_ids
        assert 5 in service.selected_ids
        assert service.count() == 3

    @pytest.mark.unit
    def test_select_duplicate_id(self):
        """Selecting same ID twice doesn't duplicate."""
        from prt_src.tui.services.selection_service import SelectionService

        service = SelectionService()
        service.select(1)
        service.select(1)

        assert service.count() == 1

    @pytest.mark.unit
    def test_select_range(self):
        """Can select a range of IDs."""
        from prt_src.tui.services.selection_service import SelectionService

        service = SelectionService()
        service.select_range(1, 5)

        assert 1 in service.selected_ids
        assert 2 in service.selected_ids
        assert 3 in service.selected_ids
        assert 4 in service.selected_ids
        assert 5 in service.selected_ids
        assert service.count() == 5


class TestDeselectingItems:
    """Test deselecting items."""

    @pytest.mark.unit
    def test_deselect_single_id(self):
        """Can deselect a single item."""
        from prt_src.tui.services.selection_service import SelectionService

        service = SelectionService()
        service.select(1)
        service.select(2)

        service.deselect(1)

        assert 1 not in service.selected_ids
        assert 2 in service.selected_ids
        assert service.count() == 1

    @pytest.mark.unit
    def test_deselect_nonexistent_id(self):
        """Deselecting non-selected ID is safe."""
        from prt_src.tui.services.selection_service import SelectionService

        service = SelectionService()
        service.select(1)

        # Should not raise error
        service.deselect(999)

        assert service.count() == 1


class TestToggleSelection:
    """Test toggling selection state."""

    @pytest.mark.unit
    def test_toggle_unselected_item(self):
        """Toggling unselected item selects it."""
        from prt_src.tui.services.selection_service import SelectionService

        service = SelectionService()
        service.toggle(1)

        assert 1 in service.selected_ids

    @pytest.mark.unit
    def test_toggle_selected_item(self):
        """Toggling selected item deselects it."""
        from prt_src.tui.services.selection_service import SelectionService

        service = SelectionService()
        service.select(1)

        service.toggle(1)

        assert 1 not in service.selected_ids


class TestClearSelection:
    """Test clearing selection."""

    @pytest.mark.unit
    def test_clear_selection(self):
        """Can clear all selections."""
        from prt_src.tui.services.selection_service import SelectionService

        service = SelectionService()
        service.select(1)
        service.select(2)
        service.select(3)

        assert service.count() == 3

        service.clear()

        assert service.count() == 0
        assert service.is_empty()


class TestQueryingSelection:
    """Test querying selection state."""

    @pytest.mark.unit
    def test_is_selected(self):
        """Can check if an ID is selected."""
        from prt_src.tui.services.selection_service import SelectionService

        service = SelectionService()
        service.select(1)
        service.select(3)

        assert service.is_selected(1)
        assert not service.is_selected(2)
        assert service.is_selected(3)

    @pytest.mark.unit
    def test_get_selected_ids(self):
        """Can get set of selected IDs."""
        from prt_src.tui.services.selection_service import SelectionService

        service = SelectionService()
        service.select(1)
        service.select(2)
        service.select(5)

        ids = service.get_selected_ids()

        assert ids == {1, 2, 5}

    @pytest.mark.unit
    def test_get_selected_ids_returns_copy(self):
        """get_selected_ids returns a copy, not the internal set."""
        from prt_src.tui.services.selection_service import SelectionService

        service = SelectionService()
        service.select(1)

        ids = service.get_selected_ids()
        ids.add(999)  # Modify returned set

        # Internal selection unchanged
        assert 999 not in service.selected_ids


class TestBulkOperations:
    """Test bulk selection operations."""

    @pytest.mark.unit
    def test_select_all_from_list(self):
        """Can select all IDs from a list."""
        from prt_src.tui.services.selection_service import SelectionService

        service = SelectionService()
        ids = [1, 2, 3, 4, 5]

        service.select_all(ids)

        assert service.count() == 5
        for id_ in ids:
            assert id_ in service.selected_ids

    @pytest.mark.unit
    def test_select_from_results_dicts(self):
        """Can select all from list of result dicts."""
        from prt_src.tui.services.selection_service import SelectionService
        from tests.unit.conftest import fixture_contacts_batch

        service = SelectionService()
        contacts = fixture_contacts_batch(count=5)

        service.select_all_from_results(contacts)

        assert service.count() == 5
        # Contacts have IDs 1-5
        for i in range(1, 6):
            assert i in service.selected_ids
