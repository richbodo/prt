"""Fixtures for unit tests.

Provides fast, deterministic fixtures for testing components without database or LLM dependencies.
"""

from datetime import datetime
from datetime import timedelta
from typing import List
from typing import Optional

import pytest

# ============================================================================
# Contact Fixtures
# ============================================================================


def fixture_contact(
    id: Optional[int] = None,
    name: str = "Test User",
    email: str = "test@example.com",
    location: Optional[str] = None,
    tags: Optional[List[str]] = None,
    phone: Optional[str] = None,
    company: Optional[str] = None,
) -> dict:
    """Create a test contact fixture.

    Args:
        id: Contact ID (auto-generated if None)
        name: Contact name
        email: Contact email
        location: Contact location
        tags: List of tag names
        phone: Phone number
        company: Company name

    Returns:
        Dictionary representing a contact
    """
    import random

    if id is None:
        id = random.randint(1, 10000)

    contact = {
        "id": id,
        "name": name,
        "email": email,
        "created_at": datetime.now().isoformat(),
    }

    if location:
        contact["location"] = location
    if phone:
        contact["phone"] = phone
    if company:
        contact["company"] = company
    if tags:
        contact["tags"] = tags

    return contact


def fixture_contacts_batch(count: int = 10, **kwargs) -> List[dict]:
    """Create a batch of test contacts.

    Args:
        count: Number of contacts to create
        **kwargs: Passed to fixture_contact for all contacts

    Returns:
        List of contact dictionaries
    """
    names = [
        "Alice Chen",
        "Bob Martinez",
        "Carol White",
        "David Park",
        "Eve Johnson",
        "Frank Lee",
        "Grace Kim",
        "Henry Wilson",
        "Iris Brown",
        "Jack Davis",
    ]
    emails = [f"{name.lower().replace(' ', '.')}@example.com" for name in names]
    locations = ["San Francisco", "Oakland", "Berkeley", "Palo Alto", "San Jose"]

    contacts = []
    for i in range(min(count, len(names))):
        contact_kwargs = {
            "id": i + 1,
            "name": names[i],
            "email": emails[i],
            "location": locations[i % len(locations)],
            **kwargs,
        }
        contacts.append(fixture_contact(**contact_kwargs))

    return contacts


# ============================================================================
# Relationship Fixtures
# ============================================================================


def fixture_relationship(
    id: Optional[int] = None,
    from_contact: str = "Alice Chen",
    to_contact: str = "Bob Martinez",
    relationship_type: str = "colleague",
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> dict:
    """Create a test relationship fixture.

    Args:
        id: Relationship ID
        from_contact: Source contact name
        to_contact: Target contact name
        relationship_type: Type of relationship
        start_date: When relationship started
        end_date: When relationship ended (None if active)

    Returns:
        Dictionary representing a relationship
    """
    import random

    if id is None:
        id = random.randint(1, 10000)
    if start_date is None:
        start_date = datetime.now() - timedelta(days=365)

    relationship = {
        "id": id,
        "from_contact": from_contact,
        "to_contact": to_contact,
        "type": relationship_type,
        "start_date": start_date.isoformat(),
    }

    if end_date:
        relationship["end_date"] = end_date.isoformat()

    return relationship


# ============================================================================
# Note Fixtures
# ============================================================================


def fixture_note(
    id: Optional[int] = None,
    title: str = "Meeting Notes",
    content: str = "Discussed project timeline and deliverables.",
    date: Optional[datetime] = None,
    contact_id: Optional[int] = None,
) -> dict:
    """Create a test note fixture.

    Args:
        id: Note ID
        title: Note title
        content: Note content
        date: Note date
        contact_id: Associated contact ID

    Returns:
        Dictionary representing a note
    """
    import random

    if id is None:
        id = random.randint(1, 10000)
    if date is None:
        date = datetime.now()

    note = {
        "id": id,
        "title": title,
        "content": content,
        "date": date.isoformat(),
    }

    if contact_id:
        note["contact_id"] = contact_id

    return note


# ============================================================================
# Tag Fixtures
# ============================================================================


def fixture_tag(id: Optional[int] = None, name: str = "tech", label: Optional[str] = None) -> dict:
    """Create a test tag fixture.

    Args:
        id: Tag ID
        name: Tag name (key)
        label: Human-readable label

    Returns:
        Dictionary representing a tag
    """
    import random

    if id is None:
        id = random.randint(1, 10000)

    return {
        "id": id,
        "name": name,
        "label": label or name.capitalize(),
    }


# ============================================================================
# Search Result Fixtures
# ============================================================================


@pytest.fixture
def search_result_contacts():
    """Fixture: Search results with 5 tech contacts in SF."""
    return fixture_contacts_batch(
        count=5,
        tags=["tech"],
        location="San Francisco",
    )


@pytest.fixture
def search_result_empty():
    """Fixture: Empty search results."""
    return []


@pytest.fixture
def search_result_large():
    """Fixture: Large search results (50 contacts)."""
    contacts = []
    for i in range(50):
        contacts.append(
            fixture_contact(
                id=i + 1,
                name=f"Contact {i+1}",
                email=f"contact{i+1}@example.com",
                location="San Francisco" if i % 2 == 0 else "Oakland",
                tags=["tech"] if i % 3 == 0 else ["business"],
            )
        )
    return contacts


# ============================================================================
# LLM Command Fixtures (for testing parsers)
# ============================================================================


@pytest.fixture
def llm_command_search():
    """Fixture: Valid search command from LLM."""
    return {
        "intent": "search",
        "parameters": {
            "entity_type": "contacts",
            "filters": {
                "tags": ["tech"],
                "location": ["San Francisco"],
            },
        },
        "explanation": "Searching for tech contacts in San Francisco",
    }


@pytest.fixture
def llm_command_select():
    """Fixture: Valid selection command from LLM."""
    return {
        "intent": "select",
        "parameters": {
            "selection_type": "ids",
            "ids": [1, 2, 5],
        },
        "explanation": "Selected 3 contacts",
    }


@pytest.fixture
def llm_command_export():
    """Fixture: Valid export command from LLM."""
    return {
        "intent": "export",
        "parameters": {
            "format": "json",
        },
        "explanation": "Exporting selected items to JSON",
    }


@pytest.fixture
def llm_command_invalid():
    """Fixture: Invalid command (missing required fields)."""
    return {
        "intent": "search",
        # Missing parameters field
    }
