"""Unit tests for DisplayContext.

Tests the display context dataclass that holds current display state.
"""

import pytest

from tests.unit.conftest import fixture_contacts_batch


class TestDisplayContextBasic:
    """Test basic DisplayContext functionality."""

    @pytest.mark.unit
    def test_display_context_instantiates(self):
        """DisplayContext can be instantiated with defaults."""
        from prt_src.tui.formatters.display_context import DisplayContext

        ctx = DisplayContext()
        assert ctx is not None
        assert ctx.current_results is None
        assert ctx.result_type == "contacts"
        assert ctx.display_mode == "numbered_list"
        assert ctx.pagination_info is None

    @pytest.mark.unit
    def test_display_context_with_results(self):
        """DisplayContext can be instantiated with results."""
        from prt_src.tui.formatters.display_context import DisplayContext

        contacts = fixture_contacts_batch(count=5)
        ctx = DisplayContext(
            current_results=contacts,
            result_type="contacts",
            display_mode="table",
        )

        assert ctx.current_results == contacts
        assert ctx.result_type == "contacts"
        assert ctx.display_mode == "table"
        assert len(ctx.current_results) == 5

    @pytest.mark.unit
    def test_display_context_with_pagination(self):
        """DisplayContext can hold pagination information."""
        from prt_src.tui.formatters.display_context import DisplayContext

        contacts = fixture_contacts_batch(count=10)
        pagination = {"total": 50, "showing": 10, "offset": 0}

        ctx = DisplayContext(
            current_results=contacts, result_type="contacts", pagination_info=pagination
        )

        assert ctx.pagination_info == pagination
        assert ctx.pagination_info["total"] == 50
        assert ctx.pagination_info["showing"] == 10


class TestDisplayContextValidation:
    """Test DisplayContext validation."""

    @pytest.mark.unit
    def test_display_mode_valid_values(self):
        """DisplayContext validates display_mode values."""
        from prt_src.tui.formatters.display_context import DisplayContext

        # Valid modes
        valid_modes = ["numbered_list", "table", "card", "compact"]
        for mode in valid_modes:
            ctx = DisplayContext(display_mode=mode)
            assert ctx.display_mode == mode

    @pytest.mark.unit
    def test_result_type_valid_values(self):
        """DisplayContext validates result_type values."""
        from prt_src.tui.formatters.display_context import DisplayContext

        # Valid types
        valid_types = ["contacts", "relationships", "notes", "tags"]
        for result_type in valid_types:
            ctx = DisplayContext(result_type=result_type)
            assert ctx.result_type == result_type


class TestDisplayContextMethods:
    """Test DisplayContext helper methods."""

    @pytest.mark.unit
    def test_has_results(self):
        """DisplayContext can check if it has results."""
        from prt_src.tui.formatters.display_context import DisplayContext

        # Empty context
        ctx_empty = DisplayContext()
        assert not ctx_empty.has_results()

        # Context with results
        contacts = fixture_contacts_batch(count=3)
        ctx_with_results = DisplayContext(current_results=contacts)
        assert ctx_with_results.has_results()

    @pytest.mark.unit
    def test_result_count(self):
        """DisplayContext can return result count."""
        from prt_src.tui.formatters.display_context import DisplayContext

        # Empty context
        ctx_empty = DisplayContext()
        assert ctx_empty.result_count() == 0

        # Context with results
        contacts = fixture_contacts_batch(count=7)
        ctx_with_results = DisplayContext(current_results=contacts)
        assert ctx_with_results.result_count() == 7

    @pytest.mark.unit
    def test_clear_results(self):
        """DisplayContext can clear results."""
        from prt_src.tui.formatters.display_context import DisplayContext

        contacts = fixture_contacts_batch(count=5)
        ctx = DisplayContext(current_results=contacts)

        assert ctx.has_results()
        ctx.clear_results()
        assert not ctx.has_results()
        assert ctx.current_results is None

    @pytest.mark.unit
    def test_update_results(self):
        """DisplayContext can update results."""
        from prt_src.tui.formatters.display_context import DisplayContext

        initial_contacts = fixture_contacts_batch(count=3)
        ctx = DisplayContext(current_results=initial_contacts)

        assert ctx.result_count() == 3

        new_contacts = fixture_contacts_batch(count=5)
        ctx.update_results(new_contacts)

        assert ctx.result_count() == 5
        assert ctx.current_results == new_contacts


class TestDisplayContextCopyAndMutability:
    """Test DisplayContext copy and immutability patterns."""

    @pytest.mark.unit
    def test_copy_context(self):
        """DisplayContext can be copied."""
        from prt_src.tui.formatters.display_context import DisplayContext

        contacts = fixture_contacts_batch(count=3)
        ctx1 = DisplayContext(
            current_results=contacts, result_type="contacts", display_mode="table"
        )

        # Create a copy (using dataclass replace or copy method)
        from dataclasses import replace

        ctx2 = replace(ctx1, display_mode="card")

        # Original unchanged
        assert ctx1.display_mode == "table"
        # Copy has new value
        assert ctx2.display_mode == "card"
        # Both share same results list
        assert ctx2.current_results == ctx1.current_results
