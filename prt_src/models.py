"""
SQLAlchemy models for PRT database schema.

These models define the database structure and are used by Alembic
to generate and apply migrations.
"""

from datetime import UTC
from datetime import datetime

from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import LargeBinary
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy import Text
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Contact(Base):
    """Contact information from Google Contacts or other sources."""

    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    first_name = Column(String(100))  # First name for better contact management
    last_name = Column(String(100))  # Last name for better contact management
    email = Column(String(255))
    phone = Column(String(50))
    profile_image = Column(LargeBinary)  # Store profile image as binary data
    profile_image_filename = Column(String(255))  # Original filename for reference
    profile_image_mime_type = Column(String(50))  # MIME type (e.g., 'image/jpeg')
    is_you = Column(Boolean, default=False)  # Special flag for the "You" contact
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    # Relationships - updated to support both metadata and contact relationships
    metadata_rel = relationship(
        "ContactMetadata",
        back_populates="contact",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # Contact-to-contact relationships
    relationships_from = relationship(
        "ContactRelationship",
        foreign_keys="ContactRelationship.from_contact_id",
        back_populates="from_contact",
        cascade="all, delete-orphan",
    )
    relationships_to = relationship(
        "ContactRelationship",
        foreign_keys="ContactRelationship.to_contact_id",
        back_populates="to_contact",
        cascade="all, delete-orphan",
    )

    # For backward compatibility
    @property
    def relationship(self):
        """Backward compatibility property for old code expecting 'relationship'."""
        return self.metadata_rel

    def __repr__(self):
        return f"<Contact(id={self.id}, name='{self.name}', email='{self.email}')>"


class RelationshipType(Base):
    """Defines types of relationships between contacts (e.g., parent_of, friend_of)."""

    __tablename__ = "relationship_types"

    id = Column(Integer, primary_key=True)
    type_key = Column(String(50), nullable=False, unique=True)  # e.g., 'parent_of'
    description = Column(String(255))  # e.g., 'Is the parent of'
    inverse_type_key = Column(
        String(50), ForeignKey("relationship_types.type_key")
    )  # e.g., 'child_of'
    is_symmetrical = Column(Integer, default=0)  # Boolean: 0=false, 1=true
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    # Self-referential relationship for inverse type
    inverse_type = relationship(
        "RelationshipType", remote_side=[type_key], foreign_keys=[inverse_type_key]
    )

    # Relationships using this type
    contact_relationships = relationship(
        "ContactRelationship",
        back_populates="relationship_type",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<RelationshipType(id={self.id}, type_key='{self.type_key}', is_symmetrical={self.is_symmetrical})>"


class ContactRelationship(Base):
    """Represents a relationship between two contacts with a specific type."""

    __tablename__ = "contact_relationships"

    id = Column(Integer, primary_key=True)
    from_contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    to_contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    type_id = Column(Integer, ForeignKey("relationship_types.id"), nullable=False)
    start_date = Column(Date)  # Optional start date of relationship
    end_date = Column(Date)  # Optional end date of relationship
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    # Ensure unique combinations of from_contact, to_contact, and type
    __table_args__ = (
        UniqueConstraint(
            "from_contact_id",
            "to_contact_id",
            "type_id",
            name="unique_contact_relationship",
        ),
    )

    # Relationships
    from_contact = relationship(
        "Contact", foreign_keys=[from_contact_id], back_populates="relationships_from"
    )
    to_contact = relationship(
        "Contact", foreign_keys=[to_contact_id], back_populates="relationships_to"
    )
    relationship_type = relationship("RelationshipType", back_populates="contact_relationships")

    def __repr__(self):
        return f"<ContactRelationship(from={self.from_contact_id}, to={self.to_contact_id}, type={self.type_id})>"


class Tag(Base):
    """Editable list of tag names that can be applied to contact metadata."""

    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    # Many-to-many relationship with ContactMetadata via metadata_tags
    metadata_entries = relationship(
        "ContactMetadata", secondary="metadata_tags", back_populates="tags"
    )

    # For backward compatibility
    @property
    def relationships(self):
        """Backward compatibility property."""
        return self.metadata_entries

    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}')>"


class Note(Base):
    """Free-form notes with titles that can be associated with contact metadata."""

    __tablename__ = "notes"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    # Many-to-many relationship with ContactMetadata via metadata_notes
    metadata_entries = relationship(
        "ContactMetadata", secondary="metadata_notes", back_populates="notes"
    )

    # For backward compatibility
    @property
    def relationships(self):
        """Backward compatibility property."""
        return self.metadata_entries

    def __repr__(self):
        return f"<Note(id={self.id}, title='{self.title}')>"


class ContactMetadata(Base):
    """Links a contact to multiple tags and notes (formerly Relationship)."""

    __tablename__ = "contact_metadata"

    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False, unique=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    # One-to-one relationship with Contact
    contact = relationship("Contact", back_populates="metadata_rel")

    # Many-to-many relationship with Tag via metadata_tags
    tags = relationship("Tag", secondary="metadata_tags", back_populates="metadata_entries")

    # Many-to-many relationship with Note via metadata_notes
    notes = relationship("Note", secondary="metadata_notes", back_populates="metadata_entries")

    def __repr__(self):
        return f"<ContactMetadata(id={self.id}, contact_id={self.contact_id})>"


# Backward compatibility alias
Relationship = ContactMetadata


# Many-to-many join table between contact_metadata and tags
metadata_tags = Table(
    "metadata_tags",
    Base.metadata,
    Column("metadata_id", Integer, ForeignKey("contact_metadata.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
    Column("created_at", DateTime, default=lambda: datetime.now(UTC)),
)

# Many-to-many join table between contact_metadata and notes
metadata_notes = Table(
    "metadata_notes",
    Base.metadata,
    Column("metadata_id", Integer, ForeignKey("contact_metadata.id"), primary_key=True),
    Column("note_id", Integer, ForeignKey("notes.id"), primary_key=True),
    Column("created_at", DateTime, default=lambda: datetime.now(UTC)),
)

# Backward compatibility aliases for join tables
relationship_tags = metadata_tags
relationship_notes = metadata_notes


class Person(Base):
    """Google People API data with dynamic schema support."""

    __tablename__ = "people"

    id = Column(Integer, primary_key=True)
    # Dynamic columns will be added via migrations based on Google People schema
    # For now, we'll store the raw JSON data
    raw_data = Column(Text)  # JSON string of all Google People data
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    def __repr__(self):
        return f"<Person(id={self.id})>"


class BackupMetadata(Base):
    """Tracks database backups with timestamps and comments."""

    __tablename__ = "backup_metadata"

    id = Column(Integer, primary_key=True)
    backup_filename = Column(String(255), nullable=False, unique=True)
    backup_path = Column(Text, nullable=False)  # Full path to backup file
    comment = Column(Text)  # User or auto-generated comment
    is_auto = Column(Integer, default=0)  # Boolean: 0=manual, 1=automatic
    file_size = Column(Integer)  # Size in bytes
    schema_version = Column(Integer)  # Database schema version at backup time
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    def __repr__(self):
        return f"<BackupMetadata(id={self.id}, filename='{self.backup_filename}', auto={bool(self.is_auto)})>"


# This function can be used to dynamically add columns based on Google People schema
def add_google_people_columns(table, schema_properties):
    """
    Dynamically add columns to the people table based on Google People schema.

    This function can be called during migration generation to add
    specific columns for Google People API properties.
    """
    for prop_name, prop_info in schema_properties.items():
        # Convert property name to valid column name
        column_name = prop_name.lower().replace(" ", "_").replace("-", "_")

        # Determine column type based on property type
        if prop_info.get("type") == "array" or prop_info.get("type") == "object":
            column_type = Text  # Store as JSON string
        else:
            column_type = String(255)  # Default to string

        # Add column if it doesn't exist
        if not hasattr(table.c, column_name):
            Column(column_name, column_type)
