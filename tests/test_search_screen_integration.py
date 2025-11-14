"""Integration tests for Search screen database integration.

Tests the Search screen with real database operations for all 5 search types:
1. Contacts
2. Relationships
3. Relationship Types
4. Notes
5. Tags

Uses Textual Pilot for headless testing.
"""

import pytest

from prt_src.api import PRTAPI
from prt_src.tui.screens.search import SearchScreen
from prt_src.tui.services.data import DataService
from prt_src.tui.services.navigation import NavigationService


def create_test_services(db):
    """Create services configured with test database.

    Args:
        db: Test database instance

    Returns:
        dict: Services dictionary for passing to screen
    """
    test_config = {
        "db_path": str(db.path),
        "db_encrypted": False,
        "db_type": "sqlite",
    }
    api = PRTAPI(config=test_config)
    data_service = DataService(api)
    nav_service = NavigationService()

    return {
        "data_service": data_service,
        "nav_service": nav_service,
        "notification_service": None,
        "llm_service": None,
        "selection_service": None,
        "validation_service": None,
    }


@pytest.mark.integration
async def test_search_contacts_integration(test_db, pilot_screen):
    """Test contacts search with real database."""
    db, fixtures = test_db
    services = create_test_services(db)

    # Test searching for "John" - should find "John Doe"
    async with pilot_screen(SearchScreen, **services) as pilot:
        # Focus and type into search input
        search_input = pilot.app.screen.query_one("#search-input")
        search_input.focus()
        await pilot.press(*"John")

        # Click "Contacts" search button
        await pilot.click("#btn-contacts")

        # Wait for async search to complete
        await pilot.pause(1.0)

        # Verify results contain "John Doe"
        results_content = pilot.app.screen.query_one("#search-results-content")
        results_text = str(results_content.renderable)

        assert "John Doe" in results_text
        assert "john.doe@example.com" in results_text


@pytest.mark.integration
async def test_search_tags_integration(test_db, pilot_screen):
    """Test tags search with real database."""
    db, fixtures = test_db
    services = create_test_services(db)

    # Test searching for "friend" - should find "friend" tag
    async with pilot_screen(SearchScreen, **services) as pilot:
        # Focus and type into search input
        search_input = pilot.app.screen.query_one("#search-input")
        search_input.focus()
        await pilot.press(*"friend")

        # Click "Tags" search button
        await pilot.click("#btn-tags")

        # Wait for async search to complete
        await pilot.pause(1.0)

        # Verify results contain "friend" tag
        results_content = pilot.app.screen.query_one("#search-results-content")
        results_text = str(results_content.renderable)

        assert "friend" in results_text.lower()


@pytest.mark.integration
async def test_search_notes_integration(test_db, pilot_screen):
    """Test notes search with real database."""
    db, fixtures = test_db
    services = create_test_services(db)

    # Test searching for "Birthday" - should find "Birthday Reminder" note
    async with pilot_screen(SearchScreen, **services) as pilot:
        # Focus and type into search input
        search_input = pilot.app.screen.query_one("#search-input")
        search_input.focus()
        await pilot.press(*"Birthday")

        # Click "Notes" search button
        await pilot.click("#btn-notes")

        # Wait for async search to complete
        await pilot.pause(1.0)

        # Verify results contain "Birthday Reminder"
        results_content = pilot.app.screen.query_one("#search-results-content")
        results_text = str(results_content.renderable)

        assert "Birthday Reminder" in results_text


@pytest.mark.integration
async def test_search_relationships_integration(test_db, pilot_screen):
    """Test relationships search with real database."""
    db, fixtures = test_db
    services = create_test_services(db)

    # Test searching for "mother" - should find Jane Smith -> John Doe (mother)
    async with pilot_screen(SearchScreen, **services) as pilot:
        # Focus and type into search input
        search_input = pilot.app.screen.query_one("#search-input")
        search_input.focus()
        await pilot.press(*"mother")

        # Click "Relationships" search button
        await pilot.click("#btn-relationships")

        # Wait for async search to complete
        await pilot.pause(1.0)

        # Verify results contain the mother relationship
        results_content = pilot.app.screen.query_one("#search-results-content")
        results_text = str(results_content.renderable)

        # Should show the relationship: Jane Smith -> mother -> John Doe
        assert "mother" in results_text.lower()
        # Should show one of the contact names
        assert "Jane Smith" in results_text or "John Doe" in results_text


@pytest.mark.integration
async def test_search_relationship_types_integration(test_db, pilot_screen):
    """Test relationship types search with real database."""
    db, fixtures = test_db
    services = create_test_services(db)

    # Test searching for "friend" - should find "friend" relationship type
    async with pilot_screen(SearchScreen, **services) as pilot:
        # Focus and type into search input
        search_input = pilot.app.screen.query_one("#search-input")
        search_input.focus()
        await pilot.press(*"friend")

        # Click "Relationship Types" search button
        await pilot.click("#btn-relationship-types")

        # Wait for async search to complete
        await pilot.pause(1.0)

        # Verify results contain "friend" relationship type
        results_content = pilot.app.screen.query_one("#search-results-content")
        results_text = str(results_content.renderable)

        assert "friend" in results_text.lower()
        assert "Is a friend of" in results_text  # Description from fixtures


@pytest.mark.integration
async def test_search_empty_returns_all_contacts(test_db, pilot_screen):
    """Test that empty query returns all contacts."""
    db, fixtures = test_db
    services = create_test_services(db)

    async with pilot_screen(SearchScreen, **services) as pilot:
        # Leave search input empty - don't type anything

        # Click "Contacts" search button
        await pilot.click("#btn-contacts")

        # Wait for async search to complete
        await pilot.pause(1.0)

        # Verify results show all contacts from fixtures
        results_content = pilot.app.screen.query_one("#search-results-content")
        results_text = str(results_content.renderable)

        # Should show fixture contacts
        assert "John Doe" in results_text
        assert "Jane Smith" in results_text
        # Should show result count - fixtures['contacts'] is a dict of Contact objects
        contact_count = len(fixtures["contacts"])
        assert f"({contact_count}" in results_text or f"{contact_count} total" in results_text


@pytest.mark.integration
async def test_search_empty_returns_all_tags(test_db, pilot_screen):
    """Test that empty query returns all tags."""
    db, fixtures = test_db
    services = create_test_services(db)

    async with pilot_screen(SearchScreen, **services) as pilot:
        # Click "Tags" search button with empty input
        await pilot.click("#btn-tags")
        await pilot.pause(1.0)

        results_content = pilot.app.screen.query_one("#search-results-content")
        results_text = str(results_content.renderable)

        # Should show fixture tags
        assert "friend" in results_text.lower()
        assert "family" in results_text.lower()


@pytest.mark.integration
async def test_search_empty_returns_all_notes(test_db, pilot_screen):
    """Test that empty query returns all notes."""
    db, fixtures = test_db
    services = create_test_services(db)

    async with pilot_screen(SearchScreen, **services) as pilot:
        # Click "Notes" search button with empty input
        await pilot.click("#btn-notes")
        await pilot.pause(1.0)

        results_content = pilot.app.screen.query_one("#search-results-content")
        results_text = str(results_content.renderable)

        # Should show fixture notes
        assert "Birthday Reminder" in results_text
        assert "First Meeting" in results_text


@pytest.mark.integration
async def test_search_empty_returns_all_relationships(test_db, pilot_screen):
    """Test that empty query returns all relationships."""
    db, fixtures = test_db
    services = create_test_services(db)

    async with pilot_screen(SearchScreen, **services) as pilot:
        # Click "Relationships" search button with empty input
        await pilot.click("#btn-relationships")
        await pilot.pause(1.0)

        results_content = pilot.app.screen.query_one("#search-results-content")
        results_text = str(results_content.renderable)

        # Should show fixture relationships
        assert (
            "mother" in results_text.lower()
            or "coworker" in results_text.lower()
            or "friend" in results_text.lower()
        )


@pytest.mark.integration
async def test_search_empty_returns_all_relationship_types(test_db, pilot_screen):
    """Test that empty query returns all relationship types."""
    db, fixtures = test_db
    services = create_test_services(db)

    async with pilot_screen(SearchScreen, **services) as pilot:
        # Click "Relationship Types" search button with empty input
        await pilot.click("#btn-relationship-types")
        await pilot.pause(1.0)

        results_content = pilot.app.screen.query_one("#search-results-content")
        results_text = str(results_content.renderable)

        # Should show all relationship types from fixtures
        assert "mother" in results_text.lower()
        assert "coworker" in results_text.lower()
        assert "friend" in results_text.lower()


@pytest.mark.integration
async def test_search_no_results(test_db, pilot_screen):
    """Test that nonexistent query returns no results message."""
    db, fixtures = test_db
    services = create_test_services(db)

    # Test query that won't match anything
    async with pilot_screen(SearchScreen, **services) as pilot:
        # Focus and type into search input
        search_input = pilot.app.screen.query_one("#search-input")
        search_input.focus()
        await pilot.press(*"XYZNONEXISTENT123")

        # Click "Contacts" search button
        await pilot.click("#btn-contacts")

        # Wait for async search to complete
        await pilot.pause(1.0)

        # Verify results show no results message
        results_content = pilot.app.screen.query_one("#search-results-content")
        results_text = str(results_content.renderable)

        assert (
            "No contacts found" in results_text
            or "0" in results_text
            or "no" in results_text.lower()
        )
