"""
Test fixtures for PRT database.

This module provides test data and utilities for setting up test databases
with realistic sample data including contacts, relationships, tags, notes,
and profile images.

Schema Compatibility: v6
- Supports first_name, last_name fields
- Supports is_you flag for identifying the user's contact
- Includes 7 contacts (6 regular + 1 "You" contact)
- Compatible with all current database operations

Last Updated: 2025-10-13 (Phase 1: Quick fix for schema v6 compatibility)
"""

import base64
from pathlib import Path
from typing import Any


def _generate_profile_images():
    """Generate realistic 256x256 JPEG profile images for test fixtures."""
    try:
        import sys

        sys.path.insert(0, str(Path(__file__).parent.parent))
        from utils.generate_profile_images import generate_profile_images

        return generate_profile_images()
    except ImportError:
        # Fallback to simple base64 images if Pillow is not available
        return {
            "john_doe.jpg": {
                "data": "/9j/4AAQSkZJRgABAQEAAQABAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/8A8A",
                "mime_type": "image/jpeg",
                "filename": "john_doe.jpg",
            }
        }


# Generate realistic 256x256 JPEG profile images
SAMPLE_IMAGES = _generate_profile_images()

# Sample contact data (schema v6 compatible)
SAMPLE_CONTACTS = [
    {
        "name": "John Doe",
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "phone": "+1-555-0101",
        "is_you": False,
        "image_key": "john_doe.jpg",
    },
    {
        "name": "Jane Smith",
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane.smith@email.com",
        "phone": "+1-555-0102",
        "is_you": False,
        "image_key": "jane_smith.jpg",
    },
    {
        "name": "Bob Wilson",
        "first_name": "Bob",
        "last_name": "Wilson",
        "email": "bob@work.com",
        "phone": "+1-555-0103",
        "is_you": False,
        "image_key": "bob_wilson.jpg",
    },
    {
        "name": "Alice Johnson",
        "first_name": "Alice",
        "last_name": "Johnson",
        "email": "alice.johnson@gmail.com",
        "phone": "+1-555-0104",
        "is_you": False,
        "image_key": "alice_johnson.jpg",
    },
    {
        "name": "Charlie Brown",
        "first_name": "Charlie",
        "last_name": "Brown",
        "email": "charlie@company.org",
        "phone": "+1-555-0105",
        "is_you": False,
        "image_key": "charlie_brown.jpg",
    },
    {
        "name": "Diana Prince",
        "first_name": "Diana",
        "last_name": "Prince",
        "email": "diana.prince@hero.com",
        "phone": "+1-555-0106",
        "is_you": False,
        "image_key": "diana_prince.jpg",
    },
    {
        "name": "You",
        "first_name": "You",
        "last_name": "",
        "email": None,
        "phone": None,
        "is_you": True,
        "image_key": None,
    },
]

# Sample tags
SAMPLE_TAGS = [
    "family",
    "friend",
    "colleague",
    "client",
    "neighbor",
    "classmate",
    "mentor",
    "business_contact",
]

# Sample notes
SAMPLE_NOTES = [
    {
        "title": "First Meeting",
        "content": "Met at the coffee shop downtown. Really nice person, we talked about work and hobbies.",
    },
    {
        "title": "Birthday Reminder",
        "content": "Birthday is in March. Likes chocolate cake and outdoor activities.",
    },
    {
        "title": "Project Discussion",
        "content": "Discussed the new project timeline. Need to follow up next week about deliverables.",
    },
    {
        "title": "Personal Note",
        "content": "Has two kids and a dog. Lives in the suburbs. Enjoys hiking on weekends.",
    },
    {
        "title": "Work Contact",
        "content": "Works in marketing department. Good contact for future collaborations.",
    },
    {
        "title": "Emergency Contact",
        "content": "Can be reached at work number during business hours. Backup emergency contact.",
    },
]

# Relationships between contacts and tags/notes
SAMPLE_RELATIONSHIPS = [
    {
        "contact_name": "John Doe",
        "tags": ["friend", "colleague"],
        "notes": ["First Meeting", "Personal Note"],
    },
    {
        "contact_name": "Jane Smith",
        "tags": ["family", "friend"],
        "notes": ["Birthday Reminder", "Personal Note"],
    },
    {
        "contact_name": "Bob Wilson",
        "tags": ["colleague", "business_contact"],
        "notes": ["Project Discussion", "Work Contact"],
    },
    {
        "contact_name": "Alice Johnson",
        "tags": ["friend", "neighbor"],
        "notes": ["First Meeting", "Emergency Contact"],
    },
    {
        "contact_name": "Charlie Brown",
        "tags": ["client", "business_contact"],
        "notes": ["Project Discussion", "Work Contact"],
    },
    {
        "contact_name": "Diana Prince",
        "tags": ["mentor", "colleague"],
        "notes": ["Work Contact", "Personal Note"],
    },
]

# Contact-to-contact relationship types
SAMPLE_RELATIONSHIP_TYPES = [
    {
        "type_key": "mother",
        "description": "Is the mother of",
        "inverse_type_key": None,
        "is_symmetrical": 0,
    },
    {
        "type_key": "coworker",
        "description": "Is a coworker of",
        "inverse_type_key": "coworker",
        "is_symmetrical": 1,
    },
    {
        "type_key": "friend",
        "description": "Is a friend of",
        "inverse_type_key": "friend",
        "is_symmetrical": 1,
    },
]

# Sample contact-to-contact relationships
SAMPLE_CONTACT_RELATIONSHIPS = [
    {"from": "Jane Smith", "to": "John Doe", "type": "mother"},
    {"from": "Bob Wilson", "to": "Alice Johnson", "type": "coworker"},
    {"from": "Alice Johnson", "to": "Bob Wilson", "type": "coworker"},
    {"from": "John Doe", "to": "Charlie Brown", "type": "friend"},
    {"from": "Charlie Brown", "to": "John Doe", "type": "friend"},
]


def get_fixture_spec():
    """Get fixture specification for test verification.

    Tests should use this instead of hardcoding expectations.
    Single source of truth for what fixtures contain.

    Returns:
        dict: Comprehensive specification of fixture data including:
            - contacts: count, items, names, emails, etc.
            - tags: count, items
            - notes: count, items, titles
            - relationships: contact-to-tag/note relationships
            - relationship_types: contact-to-contact relationship types
            - contact_relationships: specific contact-to-contact links

    Example:
        spec = get_fixture_spec()
        expected_count = spec["contacts"]["count"]
        assert len(api.list_all_contacts()) == expected_count
    """
    return {
        "contacts": {
            "count": len(SAMPLE_CONTACTS),
            "items": SAMPLE_CONTACTS,
            "names": [c["name"] for c in SAMPLE_CONTACTS],
            "with_email": [c for c in SAMPLE_CONTACTS if c.get("email")],
            "without_email": [c for c in SAMPLE_CONTACTS if not c.get("email")],
            "is_you_contact": [c for c in SAMPLE_CONTACTS if c.get("is_you")],
            "regular_contacts": [c for c in SAMPLE_CONTACTS if not c.get("is_you")],
            "with_images": [c for c in SAMPLE_CONTACTS if c.get("image_key")],
            "without_images": [c for c in SAMPLE_CONTACTS if not c.get("image_key")],
            "expected_with_images_count": len([c for c in SAMPLE_CONTACTS if c.get("image_key")]),
        },
        "tags": {
            "count": len(SAMPLE_TAGS),
            "items": SAMPLE_TAGS,
        },
        "notes": {
            "count": len(SAMPLE_NOTES),
            "items": SAMPLE_NOTES,
            "titles": [n["title"] for n in SAMPLE_NOTES],
        },
        "relationships": {
            "count": len(SAMPLE_RELATIONSHIPS),
            "items": SAMPLE_RELATIONSHIPS,
            # Helper: Get contacts by tag
            "by_tag": {
                tag: [r["contact_name"] for r in SAMPLE_RELATIONSHIPS if tag in r.get("tags", [])]
                for tag in SAMPLE_TAGS
            },
        },
        "relationship_types": {
            "count": len(SAMPLE_RELATIONSHIP_TYPES),
            "items": SAMPLE_RELATIONSHIP_TYPES,
            "type_keys": [rt["type_key"] for rt in SAMPLE_RELATIONSHIP_TYPES],
        },
        "contact_relationships": {
            "count": len(SAMPLE_CONTACT_RELATIONSHIPS),
            "items": SAMPLE_CONTACT_RELATIONSHIPS,
        },
    }


def create_sample_contacts(db):
    """Create sample contacts in the database (schema v6 compatible)."""
    from prt_src.models import Contact

    contacts = {}
    for contact_data in SAMPLE_CONTACTS:
        # Handle profile image
        profile_image = None
        profile_image_filename = None
        profile_image_mime_type = None

        if contact_data.get("image_key") and contact_data["image_key"] in SAMPLE_IMAGES:
            image_info = SAMPLE_IMAGES[contact_data["image_key"]]
            profile_image = base64.b64decode(image_info["data"])
            profile_image_filename = image_info["filename"]
            profile_image_mime_type = image_info["mime_type"]

        contact = Contact(
            name=contact_data["name"],
            first_name=contact_data.get("first_name"),
            last_name=contact_data.get("last_name"),
            email=contact_data.get("email"),
            phone=contact_data.get("phone"),
            is_you=contact_data.get("is_you", False),
            profile_image=profile_image,
            profile_image_filename=profile_image_filename,
            profile_image_mime_type=profile_image_mime_type,
        )
        db.session.add(contact)
        contacts[contact_data["name"]] = contact

    db.session.flush()  # Get IDs
    return contacts


def create_sample_tags(db):
    """Create sample tags in the database."""
    from prt_src.models import Tag

    tags = {}
    for tag_name in SAMPLE_TAGS:
        tag = Tag(name=tag_name)
        db.session.add(tag)
        tags[tag_name] = tag

    db.session.flush()  # Get IDs
    return tags


def create_sample_notes(db):
    """Create sample notes in the database."""
    from prt_src.models import Note

    notes = {}
    for note_data in SAMPLE_NOTES:
        note = Note(title=note_data["title"], content=note_data["content"])
        db.session.add(note)
        notes[note_data["title"]] = note

    db.session.flush()  # Get IDs
    return notes


def create_sample_relationships(db, contacts, tags, notes):
    """Create sample relationships between contacts, tags, and notes."""
    from prt_src.models import Relationship

    relationships = {}

    # First create relationships for each contact
    for contact_name, contact in contacts.items():
        relationship = Relationship(contact_id=contact.id)
        db.session.add(relationship)
        relationships[contact_name] = relationship

    db.session.flush()  # Get relationship IDs

    # Now add tags and notes to relationships
    for rel_data in SAMPLE_RELATIONSHIPS:
        contact_name = rel_data["contact_name"]
        if contact_name in relationships:
            relationship = relationships[contact_name]

            # Add tags
            for tag_name in rel_data.get("tags", []):
                if tag_name in tags:
                    relationship.tags.append(tags[tag_name])

            # Add notes
            for note_title in rel_data.get("notes", []):
                if note_title in notes:
                    relationship.notes.append(notes[note_title])

    return relationships


def create_sample_relationship_types(db):
    """Create sample relationship types."""
    from prt_src.models import RelationshipType

    rel_types = {}
    for rt in SAMPLE_RELATIONSHIP_TYPES:
        rel_type = RelationshipType(
            type_key=rt["type_key"],
            description=rt["description"],
            inverse_type_key=rt["inverse_type_key"],
            is_symmetrical=rt["is_symmetrical"],
        )
        db.session.add(rel_type)
        rel_types[rt["type_key"]] = rel_type

    db.session.flush()  # Get IDs
    return rel_types


def create_sample_contact_relationships(db, contacts, relationship_types):
    """Create sample contact-to-contact relationships."""
    from prt_src.models import ContactRelationship

    rels = []
    for rel in SAMPLE_CONTACT_RELATIONSHIPS:
        from_contact = contacts.get(rel["from"])
        to_contact = contacts.get(rel["to"])
        rel_type = relationship_types.get(rel["type"])
        if from_contact and to_contact and rel_type:
            relationship = ContactRelationship(
                from_contact=from_contact,
                to_contact=to_contact,
                relationship_type=rel_type,
            )
            db.session.add(relationship)
            rels.append(relationship)

    db.session.flush()  # Get IDs
    return rels


def setup_test_database(db):
    """Set up a complete test database with sample data."""
    # Initialize schema
    db.initialize()

    # Create sample data
    contacts = create_sample_contacts(db)
    tags = create_sample_tags(db)
    notes = create_sample_notes(db)
    relationships = create_sample_relationships(db, contacts, tags, notes)
    relationship_types = create_sample_relationship_types(db)
    contact_relationships = create_sample_contact_relationships(db, contacts, relationship_types)

    # Commit all changes
    db.session.commit()

    return {
        "contacts": contacts,
        "tags": tags,
        "notes": notes,
        "relationships": relationships,
        "relationship_types": relationship_types,
        "contact_relationships": contact_relationships,
    }


def get_sample_image_data(image_key: str) -> dict[str, Any]:
    """Get sample image data for testing."""
    if image_key in SAMPLE_IMAGES:
        image_info = SAMPLE_IMAGES[image_key]
        return {
            "data": base64.b64decode(image_info["data"]),
            "filename": image_info["filename"],
            "mime_type": image_info["mime_type"],
        }
    return None


def print_database_summary(db):
    """Print a summary of database contents."""
    print("\nDatabase Summary:")
    print("=" * 40)
    print(f"Contacts: {db.count_contacts()}")
    print(f"Relationships: {db.count_relationships()}")

    # List contacts
    contacts = db.list_contacts()
    print(f"\nContacts ({len(contacts)}):")
    for contact_id, name, email in contacts:
        print(f"  {contact_id}: {name} ({email})")

    # List tags
    tags = db.list_tags()
    print(f"\nTags ({len(tags)}):")
    for tag_id, name in tags:
        print(f"  {tag_id}: {name}")

    # List notes
    notes = db.list_notes()
    print(f"\nNotes ({len(notes)}):")
    for note_id, title, content in notes:
        print(f"  {note_id}: {title}")
        print(f"     {content[:50]}...")


if __name__ == "__main__":
    """Script to set up test database with sample data."""
    import sys
    from pathlib import Path

    # Add project root to path
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from prt_src.config import data_dir
    from prt_src.db import create_database

    # Create test database
    test_db_path = data_dir() / "test_fixtures.db"
    print(f"Creating test database at: {test_db_path}")

    # Remove existing test database
    if test_db_path.exists():
        test_db_path.unlink()

    # Create and setup database
    db = create_database(test_db_path)
    fixtures = setup_test_database(db)

    print("✅ Test database created successfully!")
    print_database_summary(db)

    print("\nTo use this database in tests:")
    print(f"  db = create_database(Path('{test_db_path}'))")
    print("  # Database already has sample data loaded")
