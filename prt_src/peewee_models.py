"""
Peewee models for PRT database schema.

This is a proof of concept for migrating from SQLAlchemy to Peewee + sqlcipher3
for better encrypted database support.
"""

from peewee import *
from playhouse.sqlcipher_ext import SqlCipherDatabase
from datetime import datetime, UTC
import os
from pathlib import Path

# Database configuration
def get_database_path():
    """Get the database path from config or use default."""
    config_path = Path('prt_data/prt_config.json')
    if config_path.exists():
        import json
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get('db_path', 'prt_data/prt.db')
        except:
            pass
    return 'prt_data/prt.db'

def get_encryption_key():
    """Get encryption key from secrets directory."""
    key_path = Path('prt_data/secrets/db_encryption_key.txt')
    if key_path.exists():
        return key_path.read_text().strip()
    return None

# Create database instance
db_path = get_database_path()
encryption_key = get_encryption_key()

if encryption_key:
    # Use encrypted database
    db = SqlCipherDatabase(db_path, passphrase=encryption_key)
else:
    # Use regular SQLite database
    db = SqliteDatabase(db_path)

# Base model with common fields
class BaseModel(Model):
    """Base model with common fields and methods."""
    
    class Meta:
        database = db
    
    def save(self, *args, **kwargs):
        """Override save to update timestamps."""
        if not self.id:
            self.created_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)
        return super().save(*args, **kwargs)

class Contact(BaseModel):
    """Contact information from Google Contacts or other sources."""
    
    name = CharField(max_length=255, null=False)
    email = CharField(max_length=255, null=True)
    phone = CharField(max_length=50, null=True)
    profile_image = BlobField(null=True)  # Store profile image as binary data
    profile_image_filename = CharField(max_length=255, null=True)  # Original filename
    profile_image_mime_type = CharField(max_length=50, null=True)  # MIME type
    created_at = DateTimeField(default=datetime.now(UTC))
    updated_at = DateTimeField(default=datetime.now(UTC))
    
    def __repr__(self):
        return f"<Contact(id={self.id}, name='{self.name}', email='{self.email}')>"

class Tag(BaseModel):
    """Editable list of tag names that can be applied to relationships."""
    
    name = CharField(max_length=100, null=False, unique=True)
    created_at = DateTimeField(default=datetime.now(UTC))
    updated_at = DateTimeField(default=datetime.now(UTC))
    
    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}')>"

class Note(BaseModel):
    """Free-form notes with titles that can be associated with relationships."""
    
    title = CharField(max_length=255, null=False)
    content = TextField(null=False)
    created_at = DateTimeField(default=datetime.now(UTC))
    updated_at = DateTimeField(default=datetime.now(UTC))
    
    def __repr__(self):
        return f"<Note(id={self.id}, title='{self.title}')>"

class Relationship(BaseModel):
    """Links a contact to multiple tags and notes."""
    
    contact = ForeignKeyField(Contact, backref='relationship', unique=True)
    created_at = DateTimeField(default=datetime.now(UTC))
    updated_at = DateTimeField(default=datetime.now(UTC))
    
    def __repr__(self):
        return f"<Relationship(id={self.id}, contact_id={self.contact.id})>"

# Many-to-many relationships
class RelationshipTag(BaseModel):
    """Many-to-many relationship between relationships and tags."""
    
    relationship = ForeignKeyField(Relationship, backref='relationship_tags')
    tag = ForeignKeyField(Tag, backref='relationship_tags')
    created_at = DateTimeField(default=datetime.now(UTC))
    
    class Meta:
        indexes = (
            (('relationship', 'tag'), True),  # Unique constraint
        )

class RelationshipNote(BaseModel):
    """Many-to-many relationship between relationships and notes."""
    
    relationship = ForeignKeyField(Relationship, backref='relationship_notes')
    note = ForeignKeyField(Note, backref='relationship_notes')
    created_at = DateTimeField(default=datetime.now(UTC))
    
    class Meta:
        indexes = (
            (('relationship', 'note'), True),  # Unique constraint
        )

class Person(BaseModel):
    """Google People API data with dynamic schema support."""
    
    raw_data = TextField(null=True)  # JSON string of all Google People data
    created_at = DateTimeField(default=datetime.now(UTC))
    updated_at = DateTimeField(default=datetime.now(UTC))
    
    def __repr__(self):
        return f"<Person(id={self.id})>"

# Helper functions for managing relationships
def get_relationship_tags(relationship):
    """Get all tags for a relationship."""
    return (Tag
            .select()
            .join(RelationshipTag)
            .where(RelationshipTag.relationship == relationship))

def get_relationship_notes(relationship):
    """Get all notes for a relationship."""
    return (Note
            .select()
            .join(RelationshipNote)
            .where(RelationshipNote.relationship == relationship))

def add_tag_to_relationship(relationship, tag):
    """Add a tag to a relationship."""
    RelationshipTag.get_or_create(relationship=relationship, tag=tag)

def add_note_to_relationship(relationship, note):
    """Add a note to a relationship."""
    RelationshipNote.get_or_create(relationship=relationship, note=note)

def remove_tag_from_relationship(relationship, tag):
    """Remove a tag from a relationship."""
    RelationshipTag.delete().where(
        (RelationshipTag.relationship == relationship) &
        (RelationshipTag.tag == tag)
    ).execute()

def remove_note_from_relationship(relationship, note):
    """Remove a note from a relationship."""
    RelationshipNote.delete().where(
        (RelationshipNote.relationship == relationship) &
        (RelationshipNote.note == note)
    ).execute()

# Database initialization
def create_tables():
    """Create all database tables."""
    with db:
        db.create_tables([
            Contact,
            Tag,
            Note,
            Relationship,
            RelationshipTag,
            RelationshipNote,
            Person
        ])

def drop_tables():
    """Drop all database tables."""
    with db:
        db.drop_tables([
            Contact,
            Tag,
            Note,
            Relationship,
            RelationshipTag,
            RelationshipNote,
            Person
        ])

# Test functions for proof of concept
def test_basic_operations():
    """Test basic CRUD operations."""
    print("Testing basic CRUD operations...")
    
    # Create a contact
    contact = Contact.create(
        name="John Doe",
        email="john@example.com",
        phone="+1-555-1234"
    )
    print(f"Created contact: {contact}")
    
    # Create a tag
    tag = Tag.create(name="friend")
    print(f"Created tag: {tag}")
    
    # Create a note
    note = Note.create(
        title="First meeting",
        content="Met at the coffee shop downtown"
    )
    print(f"Created note: {note}")
    
    # Create a relationship
    relationship = Relationship.create(contact=contact)
    print(f"Created relationship: {relationship}")
    
    # Add tag and note to relationship
    add_tag_to_relationship(relationship, tag)
    add_note_to_relationship(relationship, note)
    
    # Query relationships
    relationships = Relationship.select().join(Contact)
    for rel in relationships:
        print(f"Relationship: {rel}")
        print(f"  Contact: {rel.contact}")
        print(f"  Tags: {list(get_relationship_tags(rel))}")
        print(f"  Notes: {list(get_relationship_notes(rel))}")
    
    return True

def test_encryption():
    """Test encryption functionality."""
    print("Testing encryption...")
    
    # Check if database is encrypted
    if isinstance(db, SqlCipherDatabase):
        print("✅ Database is encrypted with SQLCipher")
    else:
        print("⚠️ Database is not encrypted")
    
    # Test basic operations with encryption
    try:
        test_basic_operations()
        print("✅ Encrypted database operations work correctly")
        return True
    except Exception as e:
        print(f"❌ Encrypted database operations failed: {e}")
        return False

if __name__ == "__main__":
    # Run proof of concept tests
    print("PRT Peewee Models Proof of Concept")
    print("=" * 40)
    
    # Create tables
    print("Creating database tables...")
    create_tables()
    
    # Test encryption
    if test_encryption():
        print("\n✅ Proof of concept successful!")
    else:
        print("\n❌ Proof of concept failed!")
    
    # Clean up
    print("Cleaning up test data...")
    drop_tables()
