"""Tests for PRTAPI tag and note management."""

import pytest
from prt_src.api import PRTAPI


@pytest.fixture
def api_with_data(tmp_path):
    """Create a PRTAPI instance backed by a temporary database with sample contacts."""
    db_path = tmp_path / "test.db"
    config = {"db_path": str(db_path), "db_encrypted": False}
    api = PRTAPI(config)
    api.db.initialize()

    contacts = [
        {"first": "Alice", "last": "Example", "emails": ["alice@example.com"]},
        {"first": "Bob", "last": "Test", "emails": ["bob@test.com"]},
    ]
    api.db.insert_contacts(contacts)
    return api


class TestAPITagsNotes:
    """Tests covering tag and note operations in the API."""

    def test_tag_operations(self, api_with_data):
        api = api_with_data
        contacts = {name: cid for cid, name, _ in api.db.list_contacts()}

        # create_tag
        tag = api.create_tag("friend")
        assert tag["name"] == "friend"
        assert tag["contact_count"] == 0

        # duplicate tag creation
        assert api.create_tag("friend") is None

        # add tag to contacts
        api.add_tag_to_contact(contacts["Alice Example"], "friend")
        api.add_tag_to_contact(contacts["Bob Test"], "friend")

        # search_tags
        results = api.search_tags("fri")
        assert any(t["name"] == "friend" and t["contact_count"] == 2 for t in results)
        assert api.search_tags("unknown") == []

        # get_contacts_by_tag
        contacts_by_tag = api.get_contacts_by_tag("friend")
        assert {c["name"] for c in contacts_by_tag} == {"Alice Example", "Bob Test"}
        assert api.get_contacts_by_tag("missing") == []

        # delete_tag
        assert api.delete_tag("friend") is True
        assert api.search_tags("friend") == []
        assert api.get_contacts_by_tag("friend") == []

        # delete_tag non-existent
        assert api.delete_tag("friend") is False

    def test_note_operations(self, api_with_data):
        api = api_with_data
        contacts = {name: cid for cid, name, _ in api.db.list_contacts()}

        # create_note
        note = api.create_note("Meeting", "Discuss project")
        assert note["title"] == "Meeting"
        assert note["content"] == "Discuss project"
        assert note["contact_count"] == 0

        # duplicate note creation
        assert api.create_note("Meeting", "Another") is None

        # add note to contacts
        api.add_note_to_contact(contacts["Alice Example"], "Meeting", "Discuss project")
        api.add_note_to_contact(contacts["Bob Test"], "Meeting", "Discuss project")

        # search_notes
        notes_results = api.search_notes("Meet")
        assert any(
            n["title"] == "Meeting" and n["contact_count"] == 2 and n["content"] == "Discuss project"
            for n in notes_results
        )
        assert api.search_notes("random") == []

        # get_contacts_by_note
        contacts_by_note = api.get_contacts_by_note("Meeting")
        assert {c["name"] for c in contacts_by_note} == {"Alice Example", "Bob Test"}
        assert api.get_contacts_by_note("Unknown") == []

        # update_note
        assert api.update_note("Meeting", "Updated content") is True
        updated = api.search_notes("updated")
        assert any(n["title"] == "Meeting" and n["content"] == "Updated content" for n in updated)

        # update_note non-existent
        assert api.update_note("Missing", "text") is False

        # delete_note
        assert api.delete_note("Meeting") is True
        assert api.search_notes("Meeting") == []
        assert api.get_contacts_by_note("Meeting") == []

        # delete_note non-existent
        assert api.delete_note("Meeting") is False
