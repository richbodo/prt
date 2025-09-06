"""Tests for relationship management CLI functionality."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from rich.console import Console

from prt_src.cli import handle_add_relationship
from prt_src.cli import handle_delete_relationship
from prt_src.cli import handle_list_relationship_types
from prt_src.cli import handle_relationships_menu
from prt_src.cli import handle_view_relationships


@pytest.fixture
def mock_api():
    """Create a mock API instance with test data."""
    api = MagicMock()

    # Mock contacts
    api.list_all_contacts.return_value = [
        {"id": 1, "name": "Alice Smith", "email": "alice@example.com"},
        {"id": 2, "name": "Bob Jones", "email": "bob@example.com"},
        {"id": 3, "name": "Charlie Brown", "email": "charlie@example.com"},
    ]

    # Mock relationship types
    api.db.list_relationship_types.return_value = [
        {
            "id": 1,
            "type_key": "mother",
            "description": "Is the mother of",
            "inverse_type_key": None,
            "is_symmetrical": False,
        },
        {
            "id": 2,
            "type_key": "friend",
            "description": "Is a friend of",
            "inverse_type_key": "friend",
            "is_symmetrical": True,
        },
        {
            "id": 3,
            "type_key": "coworker",
            "description": "Is a coworker of",
            "inverse_type_key": "coworker",
            "is_symmetrical": True,
        },
    ]

    # Mock relationships for a contact
    api.db.get_contact_relationships.return_value = [
        {
            "relationship_id": 1,
            "type": "mother",
            "description": "Is the mother of",
            "other_contact_id": 2,
            "other_contact_name": "Bob Jones",
            "other_contact_email": "bob@example.com",
            "direction": "from",
            "start_date": None,
            "end_date": None,
        },
        {
            "relationship_id": 2,
            "type": "friend",
            "description": "Is a friend of",
            "other_contact_id": 3,
            "other_contact_name": "Charlie Brown",
            "other_contact_email": "charlie@example.com",
            "direction": "from",
            "start_date": None,
            "end_date": None,
        },
    ]

    return api


@pytest.fixture
def mock_console():
    """Create a mock console for output testing."""
    return MagicMock(spec=Console)


class TestViewRelationships:
    """Test viewing relationships for a contact."""

    def test_view_relationships_success(self, mock_api, mock_console):
        """Test successfully viewing relationships."""
        with patch("prt_src.cli.console", mock_console):
            with patch("prt_src.cli.Prompt.ask") as mock_prompt:
                # Mock the search prompt (empty to see all) then contact ID selection
                mock_prompt.side_effect = ["", "1"]
                handle_view_relationships(mock_api)

                # Verify API calls
                mock_api.list_all_contacts.assert_called_once()
                mock_api.db.get_contact_relationships.assert_called_once_with(1)

                # Verify some output was printed
                assert mock_console.print.called

    def test_view_relationships_no_contacts(self, mock_api, mock_console):
        """Test viewing relationships when no contacts exist."""
        mock_api.list_all_contacts.return_value = []

        with patch("prt_src.cli.console", mock_console):
            handle_view_relationships(mock_api)

            # Should show warning message
            mock_console.print.assert_called_with("No contacts found in database.", style="yellow")

    def test_view_relationships_invalid_id(self, mock_api, mock_console):
        """Test viewing relationships with invalid contact ID."""
        with patch("prt_src.cli.console", mock_console):
            with patch("prt_src.cli.Prompt.ask") as mock_prompt:
                # Mock search (empty to see all) then invalid contact ID
                mock_prompt.side_effect = ["", "invalid"]
                handle_view_relationships(mock_api)

                # Should show error message about invalid input
                mock_console.print.assert_any_call(
                    "Invalid input. Please enter a number or 'q' to quit.", style="red"
                )

    def test_view_relationships_no_relationships(self, mock_api, mock_console):
        """Test viewing when contact has no relationships."""
        mock_api.db.get_contact_relationships.return_value = []

        with patch("prt_src.cli.console", mock_console):
            with patch("prt_src.cli.Prompt.ask") as mock_prompt:
                # Mock search (empty to see all) then contact ID selection
                mock_prompt.side_effect = ["", "1"]
                handle_view_relationships(mock_api)

                # Should show no relationships message
                mock_console.print.assert_any_call(
                    "No relationships found for contact ID 1", style="yellow"
                )


class TestAddRelationship:
    """Test adding new relationships."""

    def test_add_relationship_success(self, mock_api, mock_console):
        """Test successfully adding a relationship."""
        with patch("prt_src.cli.console", mock_console):
            with patch("prt_src.cli.Prompt.ask") as mock_prompt:
                with patch("prt_src.cli.Confirm.ask", return_value=True):
                    mock_prompt.side_effect = [
                        "mother",  # relationship type
                        "",  # search for first contact (empty to see all)
                        "1",  # from contact ID
                        "",  # search for second contact (empty to see all)
                        "2",  # to contact ID
                        "",  # no start date
                    ]

                    handle_add_relationship(mock_api)

                    # Verify relationship was created
                    mock_api.db.create_contact_relationship.assert_called_once_with(
                        1, 2, "mother", start_date=None
                    )

                    # Verify success message
                    assert mock_console.print.called

    def test_add_relationship_same_contact(self, mock_api, mock_console):
        """Test error when trying to relate contact to itself."""
        with patch("prt_src.cli.console", mock_console):
            with patch("prt_src.cli.Prompt.ask") as mock_prompt:
                mock_prompt.side_effect = [
                    "friend",  # relationship type
                    "",  # search for first contact (empty to see all)
                    "1",  # from contact ID
                    "",  # search for second contact (empty to see all)
                    "1",  # same contact ID
                ]

                handle_add_relationship(mock_api)

                # Should show error message
                mock_console.print.assert_any_call(
                    "Cannot create relationship with same contact", style="red"
                )

                # Should not create relationship
                mock_api.db.create_contact_relationship.assert_not_called()

    def test_add_relationship_insufficient_contacts(self, mock_api, mock_console):
        """Test error when there aren't enough contacts."""
        mock_api.list_all_contacts.return_value = [
            {"id": 1, "name": "Only One", "email": "only@example.com"}
        ]

        with patch("prt_src.cli.console", mock_console):
            with patch("prt_src.cli.Prompt.ask", return_value="friend"):
                handle_add_relationship(mock_api)

                # Should show error message
                mock_console.print.assert_any_call(
                    "Need at least 2 contacts to create a relationship.", style="yellow"
                )

    def test_add_relationship_with_date(self, mock_api, mock_console):
        """Test adding relationship with start date."""
        from datetime import datetime

        with patch("prt_src.cli.console", mock_console):
            with patch("prt_src.cli.Prompt.ask") as mock_prompt:
                mock_prompt.side_effect = [
                    "coworker",  # relationship type
                    "",  # search for first contact (empty to see all)
                    "1",  # from contact ID
                    "",  # search for second contact (empty to see all)
                    "3",  # to contact ID
                    "2024-01-01",  # start date
                ]

                handle_add_relationship(mock_api)

                # Verify relationship was created with date
                expected_date = datetime.strptime("2024-01-01", "%Y-%m-%d").date()
                mock_api.db.create_contact_relationship.assert_called_once_with(
                    1, 3, "coworker", start_date=expected_date
                )


class TestListRelationshipTypes:
    """Test listing relationship types."""

    def test_list_types_success(self, mock_api, mock_console):
        """Test successfully listing relationship types."""
        with patch("prt_src.cli.console", mock_console):
            handle_list_relationship_types(mock_api)

            # Verify API call
            mock_api.db.list_relationship_types.assert_called_once()

            # Verify output
            assert mock_console.print.called

    def test_list_types_empty(self, mock_api, mock_console):
        """Test listing when no types exist."""
        mock_api.db.list_relationship_types.return_value = []

        with patch("prt_src.cli.console", mock_console):
            handle_list_relationship_types(mock_api)

            # Should show no types message
            mock_console.print.assert_called_with("No relationship types found", style="yellow")


class TestDeleteRelationship:
    """Test deleting relationships."""

    def test_delete_relationship_success(self, mock_api, mock_console):
        """Test successfully deleting a relationship."""
        with patch("prt_src.cli.console", mock_console):
            with patch("prt_src.cli.Prompt.ask") as mock_prompt:
                with patch("prt_src.cli.Confirm.ask", return_value=True):
                    mock_prompt.side_effect = [
                        "",  # search for contact (empty to see all)
                        "1",  # contact ID
                        "1",  # relationship number to delete
                    ]

                    handle_delete_relationship(mock_api)

                    # Verify deletion
                    mock_api.db.delete_contact_relationship.assert_called_once_with(1, 2, "mother")

                    # Verify success message
                    mock_console.print.assert_any_call(
                        "✅ Relationship deleted successfully", style="green"
                    )

    def test_delete_relationship_cancelled(self, mock_api, mock_console):
        """Test cancelling relationship deletion."""
        with patch("prt_src.cli.console", mock_console):
            with patch("prt_src.cli.Prompt.ask") as mock_prompt:
                with patch("prt_src.cli.Confirm.ask", return_value=False):
                    mock_prompt.side_effect = [
                        "",  # search for contact (empty to see all)
                        "1",  # contact ID
                        "1",  # relationship number
                    ]

                    handle_delete_relationship(mock_api)

                    # Should not delete
                    mock_api.db.delete_contact_relationship.assert_not_called()

                    # Should show cancellation message
                    mock_console.print.assert_any_call("Deletion cancelled", style="yellow")

    def test_delete_relationship_invalid_selection(self, mock_api, mock_console):
        """Test invalid relationship selection."""
        with patch("prt_src.cli.console", mock_console):
            with patch("prt_src.cli.Prompt.ask") as mock_prompt:
                mock_prompt.side_effect = [
                    "",  # search for contact (empty to see all)
                    "1",  # contact ID
                    "99",  # invalid relationship number
                ]

                handle_delete_relationship(mock_api)

                # Should show error message
                mock_console.print.assert_any_call("Invalid selection", style="red")

                # Should not attempt deletion
                mock_api.db.delete_contact_relationship.assert_not_called()


class TestRelationshipsMenu:
    """Test the relationships menu navigation."""

    def test_menu_navigation_view(self, mock_api, mock_console):
        """Test navigating to view relationships."""
        with patch("prt_src.cli.console", mock_console):
            with patch("prt_src.cli.Prompt.ask") as mock_prompt:
                mock_prompt.side_effect = [
                    "1",  # view from menu
                    "",  # search for contact (empty to see all)
                    "1",  # contact ID
                    "b",  # back
                ]

                handle_relationships_menu(mock_api)

                # Should call view relationships
                mock_api.list_all_contacts.assert_called()

    def test_menu_navigation_add(self, mock_api, mock_console):
        """Test navigating to add relationship."""
        with patch("prt_src.cli.console", mock_console):
            with patch("prt_src.cli.Prompt.ask") as mock_prompt:
                # Need more mock values for the add relationship flow
                mock_prompt.side_effect = [
                    "2",  # select add from menu
                    "friend",  # select relationship type
                    "",  # search for first contact (empty to see all)
                    "1",  # first contact
                    "",  # search for second contact (empty to see all)
                    "2",  # second contact
                    "",  # no start date
                    "b",  # back to exit menu
                ]

                handle_relationships_menu(mock_api)

                # Should call list relationship types (part of add flow)
                mock_api.db.list_relationship_types.assert_called()

    def test_menu_navigation_back(self, mock_api, mock_console):
        """Test going back to main menu."""
        with patch("prt_src.cli.console", mock_console):
            with patch("prt_src.cli.Prompt.ask", return_value="b"):
                handle_relationships_menu(mock_api)

                # Should exit without errors
                assert True  # Menu exited successfully


class TestRelationshipDisplayFormatting:
    """Test the display formatting of relationships."""

    def test_relationship_display_with_dates(self, mock_api, mock_console):
        """Test displaying relationships with start/end dates."""
        from datetime import date

        mock_api.db.get_contact_relationships.return_value = [
            {
                "relationship_id": 1,
                "type": "coworker",
                "description": "Is a coworker of",
                "other_contact_id": 2,
                "other_contact_name": "Bob Jones",
                "other_contact_email": "bob@example.com",
                "start_date": date(2020, 1, 1),
                "end_date": date(2023, 12, 31),
            }
        ]

        with patch("prt_src.cli.console", mock_console):
            with patch("prt_src.cli.Prompt.ask") as mock_prompt:
                mock_prompt.side_effect = ["", "1"]  # search (empty), then contact ID
                handle_view_relationships(mock_api)

                # Verify dates are displayed
                assert mock_console.print.called

    def test_relationship_display_symmetrical(self, mock_api, mock_console):
        """Test displaying symmetrical relationships."""
        mock_api.db.list_relationship_types.return_value = [
            {
                "type_key": "friend",
                "description": "Is a friend of",
                "inverse_type_key": "friend",
                "is_symmetrical": True,
            }
        ]

        with patch("prt_src.cli.console", mock_console):
            with patch("prt_src.cli.Prompt.ask") as mock_prompt:
                mock_prompt.side_effect = [
                    "friend",  # relationship type
                    "",  # search for first contact (empty to see all)
                    "1",  # first contact
                    "",  # search for second contact (empty to see all)
                    "2",  # second contact
                    "",  # no start date
                ]

                handle_add_relationship(mock_api)

                # Should show symmetrical relationship message
                assert mock_console.print.called
