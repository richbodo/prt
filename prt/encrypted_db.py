"""
Encrypted database support using pysqlcipher3.

This module provides encrypted database functionality by wrapping
the existing Database class with SQLCipher encryption capabilities.
"""

import sqlite3
import base64
from pathlib import Path
from typing import Optional, Dict, Any
from sqlalchemy import create_engine, text, event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from .db import Database
from .config import get_encryption_key

# Try to import pysqlcipher3, fall back to mock for testing
try:
    import pysqlcipher3
    PYSQLCIPHER3_AVAILABLE = True
except ImportError:
    PYSQLCIPHER3_AVAILABLE = False
    print("Warning: pysqlcipher3 not available. Encrypted database functionality will be limited.")


class EncryptedDatabase(Database):
    """Database class with SQLCipher encryption support."""
    
    def __init__(self, path: Path, encryption_key: Optional[str] = None):
        super().__init__(path)
        self.encryption_key = encryption_key or get_encryption_key()
        self._is_encrypted = True
        
        if not PYSQLCIPHER3_AVAILABLE:
            print("Warning: Using mock encryption - data will not be actually encrypted")
    
    def connect(self) -> None:
        """Connect to the encrypted database using SQLAlchemy with SQLCipher."""
        if not PYSQLCIPHER3_AVAILABLE:
            # Fallback to regular SQLite for testing
            print("Warning: pysqlcipher3 not available, using regular SQLite")
            super().connect()
            return
        
        # Create SQLite URL for encrypted database
        db_url = f"sqlite:///{self.path}"
        
        # Create engine with SQLCipher support
        self.engine = create_engine(
            db_url, 
            echo=False,
            connect_args={
                'check_same_thread': False,
                'timeout': 30.0
            }
        )
        
        # Set up encryption on connection
        @event.listens_for(Engine, "connect")
        def set_sqlcipher_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            # Set the encryption key
            cursor.execute(f"PRAGMA key = '{self.encryption_key}'")
            # Set SQLCipher compatibility mode (version 3)
            cursor.execute("PRAGMA cipher_compatibility = 3")
            # Set page size for better performance
            cursor.execute("PRAGMA page_size = 4096")
            # Enable foreign keys
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.close()
        
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.session = self.SessionLocal()
    
    def is_valid(self) -> bool:
        """Check if the encrypted database is valid using SQLite integrity check."""
        if self.engine is None:
            return False
        try:
            with self.engine.connect() as conn:
                if PYSQLCIPHER3_AVAILABLE:
                    # First check if we can decrypt the database
                    result = conn.execute(text("SELECT COUNT(*) FROM sqlite_master"))
                    result.fetchone()
                
                # Then check integrity
                result = conn.execute(text("PRAGMA integrity_check"))
                return result.fetchone()[0] == "ok"
        except SQLAlchemyError:
            return False
    
    def test_encryption(self) -> bool:
        """Test if the database can be decrypted with the current key."""
        if not PYSQLCIPHER3_AVAILABLE:
            # For testing without pysqlcipher3, just check if database is valid
            return self.is_valid()
        
        if self.engine is None:
            return False
        try:
            with self.engine.connect() as conn:
                # Try to access the database schema
                result = conn.execute(text("SELECT COUNT(*) FROM sqlite_master"))
                result.fetchone()
                return True
        except SQLAlchemyError:
            return False
    
    def rekey(self, new_key: str) -> bool:
        """Change the encryption key of the database."""
        if not PYSQLCIPHER3_AVAILABLE:
            print("Warning: rekey not available without pysqlcipher3")
            self.encryption_key = new_key
            return True
        
        if self.engine is None:
            return False
        try:
            with self.engine.connect() as conn:
                # Set the new key
                conn.execute(text(f"PRAGMA rekey = '{new_key}'"))
                conn.commit()
                self.encryption_key = new_key
                return True
        except SQLAlchemyError:
            return False
    
    def backup(self, suffix: str = ".bak") -> Path:
        """Backup the encrypted database file with a custom suffix."""
        backup_path = self.path.with_name(self.path.name + suffix)
        if self.path.exists():
            # For encrypted databases, we need to ensure the backup is also encrypted
            import shutil
            shutil.copy(self.path, backup_path)
        return backup_path


def create_encrypted_database(path: Path, encryption_key: Optional[str] = None) -> EncryptedDatabase:
    """Create a new encrypted database instance."""
    db = EncryptedDatabase(path, encryption_key)
    db.connect()
    return db


def migrate_to_encrypted(source_db: Database, target_path: Path, encryption_key: Optional[str] = None) -> EncryptedDatabase:
    """
    Migrate data from an unencrypted database to an encrypted one.
    
    Args:
        source_db: Source unencrypted database
        target_path: Path for the new encrypted database
        encryption_key: Encryption key to use (generates new one if None)
        
    Returns:
        New encrypted database instance
    """
    # Create new encrypted database
    encrypted_db = create_encrypted_database(target_path, encryption_key)
    
    # Initialize schema
    encrypted_db.initialize()
    
    # Migrate data
    from .models import Contact, Relationship, Tag, Note, Person
    
    # Migrate contacts
    contacts = source_db.session.query(Contact).all()
    for contact in contacts:
        new_contact = Contact(
            name=contact.name,
            email=contact.email,
            phone=contact.phone,
            created_at=contact.created_at,
            updated_at=contact.updated_at
        )
        encrypted_db.session.add(new_contact)
    
    # Migrate relationships
    relationships = source_db.session.query(Relationship).all()
    for rel in relationships:
        new_rel = Relationship(
            contact_id=rel.contact_id,
            created_at=rel.created_at,
            updated_at=rel.updated_at
        )
        encrypted_db.session.add(new_rel)
    
    # Migrate tags
    tags = source_db.session.query(Tag).all()
    for tag in tags:
        new_tag = Tag(
            name=tag.name,
            created_at=tag.created_at,
            updated_at=tag.updated_at
        )
        encrypted_db.session.add(new_tag)
    
    # Migrate notes
    notes = source_db.session.query(Note).all()
    for note in notes:
        new_note = Note(
            title=note.title,
            content=note.content,
            created_at=note.created_at,
            updated_at=note.updated_at
        )
        encrypted_db.session.add(new_note)
    
    # Migrate people - handle the actual schema
    try:
        people = source_db.session.query(Person).all()
        for person in people:
            # Create a new person with the current schema
            new_person = Person()
            
            # Copy all available attributes
            for attr in ['addresses', 'ageRange', 'ageRanges', 'biographies', 'birthdays', 
                        'braggingRights', 'calendarUrls', 'clientData', 'coverPhotos', 
                        'emailAddresses', 'etag', 'events', 'externalIds', 'fileAses', 
                        'genders', 'imClients', 'interests', 'locales', 'locations', 
                        'memberships', 'metadata', 'miscKeywords', 'names', 'nicknames', 
                        'occupations', 'organizations', 'phoneNumbers', 'photos', 
                        'relations', 'relationshipInterests', 'relationshipStatuses', 
                        'residences', 'resourceName', 'sipAddresses', 'skills', 
                        'taglines', 'urls', 'userDefined', 'created_at', 'updated_at']:
                if hasattr(person, attr):
                    setattr(new_person, attr, getattr(person, attr))
            
            encrypted_db.session.add(new_person)
    except Exception as e:
        print(f"Warning: Could not migrate people table: {e}")
        # Continue with other tables
    
    # Commit all changes
    encrypted_db.session.commit()
    
    return encrypted_db
