import sqlite3
import shutil
import json
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError


class Database:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.engine = None
        self.SessionLocal = None
        self.session = None

    def connect(self) -> None:
        """Connect to the database using SQLAlchemy."""
        # Create SQLite URL
        db_url = f"sqlite:///{self.path}"
        
        # Standard SQLite connection
        self.engine = create_engine(db_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.session = self.SessionLocal()

    def is_valid(self) -> bool:
        """Check if the database is valid using SQLite integrity check."""
        if self.engine is None:
            return False
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("PRAGMA integrity_check"))
                return result.fetchone()[0] == "ok"
        except SQLAlchemyError:
            return False

    def initialize(self) -> None:
        """Initialize database tables using Alembic migrations.
        
        Note: This method should only be used for testing or development.
        In production, use Alembic migrations to manage schema changes.
        """
        from .models import Base
        Base.metadata.create_all(bind=self.engine)

    def backup(self, suffix: str = ".bak") -> Path:
        """Backup the database file with a custom suffix.

        Parameters
        ----------
        suffix: str
            Suffix to append to the database filename. Defaults to ".bak".

        Returns
        -------
        Path
            Path to the backup file.
        """
        backup_path = self.path.with_name(self.path.name + suffix)
        if self.path.exists():
            shutil.copy(self.path, backup_path)
        return backup_path

    def count_contacts(self) -> int:
        from .models import Contact
        return self.session.query(Contact).count()

    def count_relationships(self) -> int:
        from .models import Relationship
        return self.session.query(Relationship).count()

    def insert_contacts(self, contacts: List[Dict[str, str]]):
        """Insert contacts from parsed data (CSV or Google Takeout)."""
        from .models import Contact, Relationship
        
        for contact_data in contacts:
            name = f"{contact_data.get('first', '')} {contact_data.get('last', '')}".strip()
            if not name:
                name = "(No name)"
            
            # Get first email and phone
            emails = contact_data.get('emails', [])
            phones = contact_data.get('phones', [])
            
            # Handle profile image data
            profile_image = contact_data.get('profile_image')
            profile_image_filename = contact_data.get('profile_image_filename')
            profile_image_mime_type = contact_data.get('profile_image_mime_type')
            
            contact = Contact(
                name=name,
                email=emails[0] if emails else None,
                phone=phones[0] if phones else None,
                profile_image=profile_image,
                profile_image_filename=profile_image_filename,
                profile_image_mime_type=profile_image_mime_type
            )
            self.session.add(contact)
            self.session.flush()  # Get the contact ID
            
            # Create a relationship for this contact
            relationship = Relationship(contact_id=contact.id)
            self.session.add(relationship)
        
        self.session.commit()

    def insert_people(self, people: List[Dict[str, Any]]):
        """Insert list of people dictionaries into the people table."""
        from .models import Person
        
        for person_data in people:
            person = Person(raw_data=json.dumps(person_data))
            self.session.add(person)
        
        self.session.commit()

    def list_contacts(self) -> List[Tuple[int, str, str]]:
        from .models import Contact
        contacts = self.session.query(Contact).order_by(Contact.name).all()
        return [(c.id, c.name, c.email or '') for c in contacts]

    def add_tag(self, tag_name: str) -> int:
        """Add a new tag and return its ID."""
        from .models import Tag
        
        # Check if tag already exists
        existing_tag = self.session.query(Tag).filter(Tag.name == tag_name).first()
        if existing_tag:
            return existing_tag.id
        
        # Create new tag
        tag = Tag(name=tag_name)
        self.session.add(tag)
        self.session.flush()  # Get the tag ID
        return tag.id

    def add_relationship_tag(self, contact_id: int, tag_name: str):
        """Add a tag to a contact's relationship."""
        from .models import Contact, Tag, Relationship
        
        # Get or create the tag
        tag_id = self.add_tag(tag_name)
        
        # Get the contact's relationship
        contact = self.session.query(Contact).filter(Contact.id == contact_id).first()
        if not contact or not contact.relationship:
            raise ValueError(f"No relationship found for contact {contact_id}")
        
        # Add tag to relationship if not already present
        tag = self.session.query(Tag).filter(Tag.id == tag_id).first()
        if tag not in contact.relationship.tags:
            contact.relationship.tags.append(tag)
            self.session.commit()

    def add_note(self, title: str, content: str) -> int:
        """Add a new note and return its ID."""
        from .models import Note
        
        # Check if note with same title already exists
        existing_note = self.session.query(Note).filter(Note.title == title).first()
        if existing_note:
            return existing_note.id
        
        # Create new note
        note = Note(title=title, content=content)
        self.session.add(note)
        self.session.flush()  # Get the note ID
        return note.id

    def add_relationship_note(self, contact_id: int, note_title: str, note_content: str):
        """Add a note to a contact's relationship."""
        from .models import Contact, Note
        
        # Get or create the note
        note_id = self.add_note(note_title, note_content)
        
        # Get the contact's relationship
        contact = self.session.query(Contact).filter(Contact.id == contact_id).first()
        if not contact or not contact.relationship:
            raise ValueError(f"No relationship found for contact {contact_id}")
        
        # Add note to relationship if not already present
        note = self.session.query(Note).filter(Note.id == note_id).first()
        if note not in contact.relationship.notes:
            contact.relationship.notes.append(note)
            self.session.commit()

    def get_relationship_info(self, contact_id: int) -> Dict[str, Any]:
        """Get all relationship information for a contact."""
        from .models import Contact
        
        contact = self.session.query(Contact).filter(Contact.id == contact_id).first()
        if not contact or not contact.relationship:
            return {"tags": [], "notes": []}
        
        return {
            "tags": [tag.name for tag in contact.relationship.tags],
            "notes": [{"title": note.title, "content": note.content} for note in contact.relationship.notes]
        }

    def list_tags(self) -> List[Tuple[int, str]]:
        """List all available tags."""
        from .models import Tag
        tags = self.session.query(Tag).order_by(Tag.name).all()
        return [(t.id, t.name) for t in tags]

    def list_notes(self) -> List[Tuple[int, str, str]]:
        """List all available notes with titles and content."""
        from .models import Note
        notes = self.session.query(Note).order_by(Note.title).all()
        return [(n.id, n.title, n.content) for n in notes]

    def search_notes_by_title(self, title_search: str) -> List[Tuple[int, str, str]]:
        """Search notes by title (case-insensitive partial match)."""
        from .models import Note
        notes = self.session.query(Note).filter(
            Note.title.ilike(f"%{title_search}%")
        ).order_by(Note.title).all()
        return [(n.id, n.title, n.content) for n in notes]


def create_database(path: Path) -> Database:
    """Create a database instance."""
    db = Database(path)
    db.connect()
    return db
