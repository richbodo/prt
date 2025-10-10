"""Unit tests for ResultsFormatter.

Tests all formatting modes: numbered_list, table, cards, tree, compact.
"""

import pytest

from tests.unit.conftest import fixture_contact
from tests.unit.conftest import fixture_contacts_batch


class TestResultsFormatterBasic:
    """Test basic ResultsFormatter functionality."""

    @pytest.mark.unit
    def test_formatter_instantiates(self):
        """Formatter can be instantiated."""
        from prt_src.tui.formatters.results import ResultsFormatter

        formatter = ResultsFormatter()
        assert formatter is not None


class TestNumberedListFormatting:
    """Test numbered list formatting mode."""

    @pytest.mark.unit
    def test_numbered_list_basic(self):
        """Format contacts as numbered list with basic info."""
        from prt_src.tui.formatters.results import ResultsFormatter

        formatter = ResultsFormatter()
        contacts = fixture_contacts_batch(count=3)

        result = formatter.render(contacts, result_type="contacts", mode="numbered_list")

        # Should have 3 numbered items
        assert "[1]" in result
        assert "[2]" in result
        assert "[3]" in result
        # Should show names
        assert "Alice Chen" in result
        assert "Bob Martinez" in result

    @pytest.mark.unit
    def test_numbered_list_with_selection_markers(self):
        """Show selection markers (checkbox style) for selected items."""
        from prt_src.tui.formatters.results import ResultsFormatter

        formatter = ResultsFormatter()
        contacts = fixture_contacts_batch(count=3)

        result = formatter.render(
            contacts,
            result_type="contacts",
            mode="numbered_list",
            show_selection=True,
            selected_ids={1, 3},  # Items 1 and 3 selected
        )

        # Should have checkboxes
        assert "[✓] [1]" in result or "[X] [1]" in result
        assert "[ ] [2]" in result
        assert "[✓] [3]" in result or "[X] [3]" in result

    @pytest.mark.unit
    def test_numbered_list_with_pagination(self):
        """Show pagination indicators when displaying partial results."""
        from prt_src.tui.formatters.results import ResultsFormatter

        formatter = ResultsFormatter()
        contacts = fixture_contacts_batch(count=50)  # Create 50 contacts

        # Display first 10 of 50
        result = formatter.render(
            contacts[:10],
            result_type="contacts",
            mode="numbered_list",
            pagination={"total": 50, "showing": 10, "offset": 0},
        )

        # Should indicate pagination
        assert "Showing 1-10 of 50" in result or "Results 1-10" in result

    @pytest.mark.unit
    def test_numbered_list_empty_results(self):
        """Handle empty results gracefully."""
        from prt_src.tui.formatters.results import ResultsFormatter

        formatter = ResultsFormatter()

        result = formatter.render([], result_type="contacts", mode="numbered_list")

        # Should return empty string or "No results" message
        assert result == "" or "No results" in result or "0 results" in result


class TestTableFormatting:
    """Test table formatting mode."""

    @pytest.mark.unit
    def test_table_contacts(self):
        """Format contacts as table with columns."""
        from prt_src.tui.formatters.results import ResultsFormatter

        formatter = ResultsFormatter()
        contacts = fixture_contacts_batch(count=3)

        result = formatter.render(contacts, result_type="contacts", mode="table")

        # Should have column headers
        assert "Name" in result or "NAME" in result
        assert "Email" in result or "EMAIL" in result
        # Should have data
        assert "Alice Chen" in result
        assert "alice.chen@example.com" in result

    @pytest.mark.unit
    def test_table_column_width_handling(self):
        """Handle long text in table columns."""
        pytest.skip("Table column width handling not yet implemented - future enhancement")
        # formatter = ResultsFormatter()
        # contacts = [
        #     fixture_contact(
        #         name="Very Long Name That Should Be Truncated Or Wrapped",
        #         email="verylongemailaddress@example.com"
        #     )
        # ]
        #
        # result = formatter.render(
        #     contacts,
        #     result_type='contacts',
        #     mode='table',
        #     max_column_width=30
        # )
        #
        # # Should not exceed max width (allowing for truncation/wrapping)
        # # Each line should be reasonable length
        # lines = result.split('\n')
        # for line in lines:
        #     if line.strip():
        #         assert len(line) < 100  # Reasonable table width


class TestCardFormatting:
    """Test card formatting mode (detailed view)."""

    @pytest.mark.unit
    def test_card_contact_detailed(self):
        """Format contact as detailed card showing all fields."""
        from prt_src.tui.formatters.results import ResultsFormatter

        formatter = ResultsFormatter()
        contact = fixture_contact(
            name="Alice Chen",
            email="alice@example.com",
            location="San Francisco",
            tags=["tech", "python"],
            phone="+1-555-0100",
        )

        result = formatter.render([contact], result_type="contacts", mode="card")

        # Should show all fields
        assert "Alice Chen" in result
        assert "alice@example.com" in result
        assert "San Francisco" in result
        assert "tech" in result
        assert "python" in result
        assert "+1-555-0100" in result

    @pytest.mark.unit
    def test_card_multiple_items(self):
        """Format multiple items as separate cards."""
        pytest.skip("Card separator formatting not yet implemented - future enhancement")
        # formatter = ResultsFormatter()
        # contacts = fixture_contacts_batch(count=3)
        #
        # result = formatter.render(
        #     contacts,
        #     result_type='contacts',
        #     mode='card'
        # )
        #
        # # Should have visual separation between cards
        # assert result.count('---') >= 2 or result.count('═') >= 2


class TestCompactFormatting:
    """Test compact formatting mode (one-line summaries)."""

    @pytest.mark.unit
    def test_compact_comma_separated(self):
        """Format contacts as comma-separated names."""
        from prt_src.tui.formatters.results import ResultsFormatter

        formatter = ResultsFormatter()
        contacts = fixture_contacts_batch(count=3)

        result = formatter.render(contacts, result_type="contacts", mode="compact")

        # Should be comma-separated
        assert "Alice Chen" in result
        assert "," in result
        assert "Bob Martinez" in result

    @pytest.mark.unit
    def test_compact_one_line_per_item(self):
        """Format contacts as one line per item (alternative compact mode)."""
        from prt_src.tui.formatters.results import ResultsFormatter

        formatter = ResultsFormatter()
        contacts = fixture_contacts_batch(count=3)

        result = formatter.render(
            contacts, result_type="contacts", mode="compact", style="lines"  # One line per item
        )

        lines = [line for line in result.split("\n") if line.strip()]
        assert len(lines) == 3


class TestTreeFormatting:
    """Test tree formatting mode (hierarchical)."""

    @pytest.mark.unit
    def test_tree_hierarchical_relationships(self):
        """Format relationships as hierarchical tree."""
        pytest.skip("ResultsFormatter not yet implemented - tree mode is future enhancement")
        # This is a more advanced feature, can be implemented later


class TestFormatterErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.unit
    def test_invalid_mode_raises_error(self):
        """Raise error for invalid formatting mode."""
        from prt_src.tui.formatters.results import ResultsFormatter

        formatter = ResultsFormatter()
        contacts = fixture_contacts_batch(count=1)

        with pytest.raises(ValueError, match="Invalid mode"):
            formatter.render(contacts, result_type="contacts", mode="invalid_mode")

    @pytest.mark.unit
    def test_none_input_handled(self):
        """Handle None input gracefully."""
        from prt_src.tui.formatters.results import ResultsFormatter

        formatter = ResultsFormatter()

        result = formatter.render(None, result_type="contacts", mode="numbered_list")

        # Should return empty string or appropriate message
        assert result == "" or "No results" in result


class TestFormatterHelpers:
    """Test helper methods."""

    @pytest.mark.unit
    def test_truncate_text(self):
        """Truncate text to max length with ellipsis."""
        from prt_src.tui.formatters.results import ResultsFormatter

        formatter = ResultsFormatter()

        long_text = "This is a very long text that should be truncated"
        result = formatter._truncate(long_text, max_length=20)

        assert len(result) <= 23  # 20 + "..."
        assert result.endswith("...")

    @pytest.mark.unit
    def test_format_contact_one_line(self):
        """Format contact as one-line summary."""
        from prt_src.tui.formatters.results import ResultsFormatter

        formatter = ResultsFormatter()
        contact = fixture_contact(name="Alice Chen", email="alice@example.com")

        result = formatter._format_contact_one_line(contact)

        # Should include name and email
        assert "Alice Chen" in result
        assert "alice@example.com" in result
        # Should be single line
        assert "\n" not in result
