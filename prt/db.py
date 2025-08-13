import sqlite3
import shutil
import json
from pathlib import Path
from typing import List, Tuple, Dict, Any
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
        """Insert contacts from parsed CSV data."""
        from .models import Contact
        
        for contact_data in contacts:
            name = f"{contact_data.get('first', '')} {contact_data.get('last', '')}".strip()
            if not name:
                name = "(No name)"
            
            # Get first email and phone
            emails = contact_data.get('emails', [])
            phones = contact_data.get('phones', [])
            
            contact = Contact(
                name=name,
                email=emails[0] if emails else None,
                phone=phones[0] if phones else None
            )
            self.session.add(contact)
        
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

    def add_relationship(self, contact_id: int, tag: str, note: str):
        from .models import Relationship
        relationship = Relationship(
            contact_id=contact_id,
            tag=tag,
            note=note
        )
        self.session.add(relationship)
        self.session.commit()
