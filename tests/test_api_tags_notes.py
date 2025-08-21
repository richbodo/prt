import pytest
from prt_src.api import PRTAPI


@pytest.fixture
def api(tmp_path):
    """Create a PRTAPI instance with a temporary database."""
    db_path = tmp_path / "test.db"
    config = {"db_path": str(db_path), "db_encrypted": False}
    api = PRTAPI(config)
    api.db.initialize()

    contacts_data = [
        {
            "first": "Alice",
            "last": "Example",
            "emails": ["alice@example.com"],
            "phones": ["111"],
        },
        {
            "first": "Bob",
            "last": "Test",
            "emails": ["bob@test.com"],
            "phones": ["222"],
        },
    ]
    api.db.insert_contacts(contacts_data)
    return api


def test_create_search_and_delete_tag(api):
    tag = api.create_tag("friend")
    assert tag["name"] == "friend"
    assert tag["contact_count"] == 0

    assert api.create_tag("friend") is None

    results = api.search_tags("fri")
    assert len(results) == 1
    assert results[0]["name"] == "friend"

    assert api.search_tags("missing") == []

    assert api.delete_tag("friend") is True
    assert api.delete_tag("friend") is False
    assert api.search_tags("friend") == []


def test_get_contacts_by_tag(api):
    api.create_tag("colleague")
    contacts = api.db.list_contacts()
    contact_id = contacts[0][0]
    api.add_tag_to_contact(contact_id, "colleague")

    tagged = api.get_contacts_by_tag("colleague")
    assert len(tagged) == 1
    assert tagged[0]["id"] == contact_id

    results = api.search_tags("colleague")
    assert results[0]["contact_count"] == 1

    assert api.get_contacts_by_tag("missing") == []


def test_create_update_and_delete_note(api):
    note = api.create_note("Meeting", "Discussed project")
    assert note["title"] == "Meeting"
    assert note["contact_count"] == 0

    assert api.create_note("Meeting", "Another") is None

    results = api.search_notes("project")
    assert len(results) == 1
    assert results[0]["title"] == "Meeting"

    assert api.search_notes("missing") == []

    assert api.update_note("Meeting", "Updated") is True
    assert api.update_note("Missing", "content") is False

    assert api.delete_note("Meeting") is True
    assert api.delete_note("Meeting") is False
    assert api.search_notes("Meeting") == []


def test_get_contacts_by_note(api):
    api.create_note("Reminder", "Call Bob")
    contacts = api.db.list_contacts()
    contact_id = contacts[1][0]
    api.add_note_to_contact(contact_id, "Reminder", "Call Bob")

    noted = api.get_contacts_by_note("Reminder")
    assert len(noted) == 1
    assert noted[0]["id"] == contact_id

    results = api.search_notes("Reminder")
    assert results[0]["contact_count"] == 1

    assert api.get_contacts_by_note("missing") == []
