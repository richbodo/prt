"""
Test fixtures for PRT database.

This module provides test data and utilities for setting up test databases
with realistic sample data including contacts, relationships, tags, notes,
and profile images.
"""

import base64
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime, UTC

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
                "filename": "john_doe.jpg"
            }
        }

# Generate realistic 256x256 JPEG profile images
SAMPLE_IMAGES = _generate_profile_images()

# Sample contact data
SAMPLE_CONTACTS = [
    {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1-555-0101",
        "image_key": "john_doe.jpg"
    },
    {
        "name": "Jane Smith", 
        "email": "jane.smith@email.com",
        "phone": "+1-555-0102",
        "image_key": "jane_smith.jpg"
    },
    {
        "name": "Bob Wilson",
        "email": "bob@work.com", 
        "phone": "+1-555-0103",
        "image_key": "bob_wilson.jpg"
    },
    {
        "name": "Alice Johnson",
        "email": "alice.johnson@gmail.com",
        "phone": "+1-555-0104",
        "image_key": "alice_johnson.jpg"
    },
    {
        "name": "Charlie Brown",
        "email": "charlie@company.org",
        "phone": "+1-555-0105", 
        "image_key": "charlie_brown.jpg"
    },
    {
        "name": "Diana Prince",
        "email": "diana.prince@hero.com",
        "phone": "+1-555-0106",
        "image_key": "diana_prince.jpg"
    }
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
    "business_contact"
]

# Sample notes 
SAMPLE_NOTES = [
    {
        "title": "First Meeting",
        "content": "Met at the coffee shop downtown. Really nice person, we talked about work and hobbies."
    },
    {
        "title": "Birthday Reminder", 
        "content": "Birthday is in March. Likes chocolate cake and outdoor activities."
    },
    {
        "title": "Project Discussion",
        "content": "Discussed the new project timeline. Need to follow up next week about deliverables."
    },
    {
        "title": "Personal Note",
        "content": "Has two kids and a dog. Lives in the suburbs. Enjoys hiking on weekends."
    },
    {
        "title": "Work Contact",
        "content": "Works in marketing department. Good contact for future collaborations."
    },
    {
        "title": "Emergency Contact",
        "content": "Can be reached at work number during business hours. Backup emergency contact."
    }
]

# Relationships between contacts and tags/notes
SAMPLE_RELATIONSHIPS = [
    {
        "contact_name": "John Doe",
        "tags": ["friend", "colleague"],
        "notes": ["First Meeting", "Personal Note"]
    },
    {
        "contact_name": "Jane Smith", 
        "tags": ["family", "friend"],
        "notes": ["Birthday Reminder", "Personal Note"]
    },
    {
        "contact_name": "Bob Wilson",
        "tags": ["colleague", "business_contact"], 
        "notes": ["Project Discussion", "Work Contact"]
    },
    {
        "contact_name": "Alice Johnson",
        "tags": ["friend", "neighbor"],
        "notes": ["First Meeting", "Emergency Contact"]
    },
    {
        "contact_name": "Charlie Brown",
        "tags": ["client", "business_contact"],
        "notes": ["Project Discussion", "Work Contact"] 
    },
    {
        "contact_name": "Diana Prince",
        "tags": ["mentor", "colleague"],
        "notes": ["Work Contact", "Personal Note"]
    }
]


def create_sample_contacts(db):
    """Create sample contacts in the database."""
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
            email=contact_data["email"], 
            phone=contact_data["phone"],
            profile_image=profile_image,
            profile_image_filename=profile_image_filename,
            profile_image_mime_type=profile_image_mime_type
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
        note = Note(
            title=note_data["title"],
            content=note_data["content"]
        )
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


def setup_test_database(db):
    """Set up a complete test database with sample data."""
    # Initialize schema
    db.initialize()
    
    # Create sample data
    contacts = create_sample_contacts(db)
    tags = create_sample_tags(db)
    notes = create_sample_notes(db)
    relationships = create_sample_relationships(db, contacts, tags, notes)
    
    # Commit all changes
    db.session.commit()
    
    return {
        "contacts": contacts,
        "tags": tags, 
        "notes": notes,
        "relationships": relationships
    }


def get_sample_image_data(image_key: str) -> Dict[str, Any]:
    """Get sample image data for testing."""
    if image_key in SAMPLE_IMAGES:
        image_info = SAMPLE_IMAGES[image_key]
        return {
            "data": base64.b64decode(image_info["data"]),
            "filename": image_info["filename"],
            "mime_type": image_info["mime_type"]
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
    
    from prt_src.db import create_database
    from prt_src.config import data_dir
    
    # Create test database
    test_db_path = data_dir() / "test_fixtures.db"
    print(f"Creating test database at: {test_db_path}")
    
    # Remove existing test database
    if test_db_path.exists():
        test_db_path.unlink()
    
    # Create and setup database
    db = create_database(test_db_path)
    fixtures = setup_test_database(db)
    
    print(f"✅ Test database created successfully!")
    print_database_summary(db)
    
    print(f"\nTo use this database in tests:")
    print(f"  db = create_database(Path('{test_db_path}'))")
    print(f"  # Database already has sample data loaded")
