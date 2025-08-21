from pathlib import Path
import pytest
from prt_src.db import Database
from prt_src.models import Contact, Relationship, Tag, Note


def test_database_initialization(tmp_path):
    """Test database initialization and table creation."""
    db_path = tmp_path / "test.db"
    db = Database(db_path)
    db.connect()
    db.initialize()

    # Check that tables exist
    from sqlalchemy import text
    cur = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
    tables = {row[0] for row in cur.fetchall()}
    
    expected_tables = {'contacts', 'relationships', 'tags', 'notes', 'relationship_tags', 'relationship_notes'}
    assert expected_tables.issubset(tables)


def test_contact_operations(tmp_path):
    """Test contact creation and retrieval."""
    db_path = tmp_path / "test.db"
    db = Database(db_path)
    db.connect()
    db.initialize()

    # Test contact insertion
    contacts_data = [
        {
            'first': 'Alice',
            'last': 'Example',
            'emails': ['alice@example.com'],
            'phones': ['+1234567890']
        },
        {
            'first': 'Bob',
            'last': 'Test',
            'emails': ['bob@test.com'],
            'phones': ['+0987654321']
        }
    ]
    
    db.insert_contacts(contacts_data)
    
    # Verify contacts were inserted
    contact_count = db.count_contacts()
    assert contact_count == 2
    
    # Verify relationships were created
    relationship_count = db.count_relationships()
    assert relationship_count == 2


def test_relationship_operations(tmp_path):
    """Test relationship, tag, and note operations."""
    db_path = tmp_path / "test.db"
    db = Database(db_path)
    db.connect()
    db.initialize()

    # Insert a contact first
    contacts_data = [{'first': 'Test', 'last': 'User', 'emails': ['test@example.com']}]
    db.insert_contacts(contacts_data)
    
    # Get the contact ID
    contacts = db.list_contacts()
    assert len(contacts) == 1
    contact_id = contacts[0][0]
    
    # Test adding tags
    db.add_relationship_tag(contact_id, "friend")
    db.add_relationship_tag(contact_id, "colleague")
    
    # Test adding notes
    db.add_relationship_note(contact_id, "Meeting notes", "Had a great meeting about the project")
    
    # Verify relationship info
    rel_info = db.get_relationship_info(contact_id)
    assert "friend" in rel_info["tags"]
    assert "colleague" in rel_info["tags"]
    assert len(rel_info["notes"]) == 1
    assert rel_info["notes"][0]["title"] == "Meeting notes"


def test_add_tag_returns_existing_id(tmp_path):
    """add_tag should return existing tag ID when duplicate."""
    db_path = tmp_path / "test.db"
    db = Database(db_path)
    db.connect()
    db.initialize()

    first_id = db.add_tag("friend")
    second_id = db.add_tag("friend")

    assert first_id == second_id
    tags = db.list_tags()
    assert len(tags) == 1
    assert tags[0][0] == first_id


def test_add_relationship_tag_invalid_contact(tmp_path):
    """add_relationship_tag should raise ValueError for bad contact IDs."""
    db_path = tmp_path / "test.db"
    db = Database(db_path)
    db.connect()
    db.initialize()

    with pytest.raises(ValueError):
        db.add_relationship_tag(999, "friend")


def test_add_note_duplicate_handling(tmp_path):
    """add_note should return existing note ID when title duplicates."""
    db_path = tmp_path / "test.db"
    db = Database(db_path)
    db.connect()
    db.initialize()

    first_id = db.add_note("Meeting", "Discussed project.")
    second_id = db.add_note("Meeting", "Different content")

    assert first_id == second_id
    notes = db.list_notes()
    assert len(notes) == 1
    assert notes[0][0] == first_id
    assert notes[0][2] == "Discussed project."


def test_search_notes_by_title_case_insensitive(tmp_path):
    """search_notes_by_title should match titles regardless of case."""
    db_path = tmp_path / "test.db"
    db = Database(db_path)
    db.connect()
    db.initialize()

    meeting_id = db.add_note("Meeting Notes", "Content")
    db.add_note("Other", "Other content")
    db.session.commit()

    lower_results = db.search_notes_by_title("meeting")
    upper_results = db.search_notes_by_title("MEETING")

    assert len(lower_results) == 1
    assert len(upper_results) == 1
    assert lower_results[0][0] == meeting_id
    assert upper_results[0][0] == meeting_id
