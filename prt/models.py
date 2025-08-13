"""
SQLAlchemy models for PRT database schema.

These models define the database structure and are used by Alembic
to generate and apply migrations.
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Contact(Base):
    """Contact information from Google Contacts or other sources."""
    __tablename__ = 'contacts'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    relationships = relationship("Relationship", back_populates="contact")
    
    def __repr__(self):
        return f"<Contact(id={self.id}, name='{self.name}', email='{self.email}')>"


class Relationship(Base):
    """Relationship data and notes for contacts."""
    __tablename__ = 'relationships'
    
    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey('contacts.id'), nullable=False)
    tag = Column(String(100), nullable=False)
    note = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    contact = relationship("Contact", back_populates="relationships")
    
    def __repr__(self):
        return f"<Relationship(id={self.id}, contact_id={self.contact_id}, tag='{self.tag}')>"


class Person(Base):
    """Google People API data with dynamic schema support."""
    __tablename__ = 'people'
    
    id = Column(Integer, primary_key=True)
    # Dynamic columns will be added via migrations based on Google People schema
    # For now, we'll store the raw JSON data
    raw_data = Column(Text)  # JSON string of all Google People data
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
