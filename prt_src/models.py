"""
SQLAlchemy models for PRT database schema.

These models define the database structure and are used by Alembic
to generate and apply migrations.
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Table, LargeBinary
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, UTC

Base = declarative_base()


class Contact(Base):
    """Contact information from Google Contacts or other sources."""
    __tablename__ = 'contacts'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    profile_image = Column(LargeBinary)  # Store profile image as binary data
    profile_image_filename = Column(String(255))  # Original filename for reference
    profile_image_mime_type = Column(String(50))  # MIME type (e.g., 'image/jpeg')
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    # One-to-one relationship with Relationship
    relationship = relationship("Relationship", back_populates="contact", uselist=False)
    
    def __repr__(self):
        return f"<Contact(id={self.id}, name='{self.name}', email='{self.email}')>"


class Tag(Base):
    """Editable list of tag names that can be applied to relationships."""
    __tablename__ = 'tags'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    # Many-to-many relationship with Relationship via relationship_tags
    relationships = relationship("Relationship", secondary="relationship_tags", back_populates="tags")
    
    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}')>"


class Note(Base):
    """Free-form notes with titles that can be associated with relationships."""
    __tablename__ = 'notes'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    # Many-to-many relationship with Relationship via relationship_notes
    relationships = relationship("Relationship", secondary="relationship_notes", back_populates="notes")
    
    def __repr__(self):
        return f"<Note(id={self.id}, title='{self.title}')>"


class Relationship(Base):
    """Links a contact to multiple tags and notes."""
    __tablename__ = 'relationships'
    
    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey('contacts.id'), nullable=False, unique=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    # One-to-one relationship with Contact
    contact = relationship("Contact", back_populates="relationship")
    
    # Many-to-many relationship with Tag via relationship_tags
    tags = relationship("Tag", secondary="relationship_tags", back_populates="relationships")
    
    # Many-to-many relationship with Note via relationship_notes
    notes = relationship("Note", secondary="relationship_notes", back_populates="relationships")
    
    def __repr__(self):
        return f"<Relationship(id={self.id}, contact_id={self.contact_id})>"


# Many-to-many join table between relationships and tags
relationship_tags = Table(
    'relationship_tags',
    Base.metadata,
    Column('relationship_id', Integer, ForeignKey('relationships.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True),
    Column('created_at', DateTime, default=lambda: datetime.now(UTC))
)

# Many-to-many join table between relationships and notes
relationship_notes = Table(
    'relationship_notes',
    Base.metadata,
    Column('relationship_id', Integer, ForeignKey('relationships.id'), primary_key=True),
    Column('note_id', Integer, ForeignKey('notes.id'), primary_key=True),
    Column('created_at', DateTime, default=lambda: datetime.now(UTC))
)


class Person(Base):
    """Google People API data with dynamic schema support."""
    __tablename__ = 'people'
    
    id = Column(Integer, primary_key=True)
    # Dynamic columns will be added via migrations based on Google People schema
    # For now, we'll store the raw JSON data
    raw_data = Column(Text)  # JSON string of all Google People data
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    def __repr__(self):
        return f"<Person(id={self.id})>"


# This function can be used to dynamically add columns based on Google People schema
def add_google_people_columns(table, schema_properties):
    """
    Dynamically add columns to the people table based on Google People schema.
    
    This function can be called during migration generation to add
    specific columns for Google People API properties.
    """
    for prop_name, prop_info in schema_properties.items():
        # Convert property name to valid column name
        column_name = prop_name.lower().replace(' ', '_').replace('-', '_')
        
        # Determine column type based on property type
        if prop_info.get('type') == 'array':
            column_type = Text  # Store as JSON string
        elif prop_info.get('type') == 'object':
            column_type = Text  # Store as JSON string
        else:
            column_type = String(255)  # Default to string
        
        # Add column if it doesn't exist
        if not hasattr(table.c, column_name):
            Column(column_name, column_type)
