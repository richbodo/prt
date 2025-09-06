from prt_src.db import Database


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

    # Updated expected tables to reflect schema v3
    expected_tables = {
        "contacts",
        "contact_metadata",  # renamed from 'relationships'
        "tags",
        "notes",
        "metadata_tags",  # renamed from 'relationship_tags'
        "metadata_notes",  # renamed from 'relationship_notes'
        "relationship_types",
        "contact_relationships",
    }
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
            "first": "Alice",
            "last": "Example",
            "emails": ["alice@example.com"],
            "phones": ["+1234567890"],
        },
        {"first": "Bob", "last": "Test", "emails": ["bob@test.com"], "phones": ["+0987654321"]},
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
    contacts_data = [{"first": "Test", "last": "User", "emails": ["test@example.com"]}]
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
