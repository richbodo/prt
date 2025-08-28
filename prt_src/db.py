import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Tuple

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker


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
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
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

    def create_backup_with_metadata(
        self, comment: str = None, is_auto: bool = False
    ) -> Dict[str, Any]:
        """Create a timestamped backup with metadata tracking.

        Parameters
        ----------
        comment: str
            User comment or auto-generated description
        is_auto: bool
            Whether this is an automatic backup (True) or manual (False)

        Returns
        -------
        Dict containing backup details
        """
        import os
        from datetime import datetime

        from .models import BackupMetadata
        from .schema_manager import SchemaManager

        # Generate unique backup filename with microseconds to avoid collisions
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backup_filename = f"{self.path.stem}_backup_{timestamp}.db"
        backup_path = self.path.parent / backup_filename

        # Copy database file
        if self.path.exists():
            shutil.copy2(self.path, backup_path)

            # Get file size
            file_size = os.path.getsize(backup_path)

            # Get current schema version
            try:
                from .schema_manager import SchemaManager

                schema_mgr = SchemaManager(self)
                current_version = schema_mgr.get_schema_version()
            except Exception:
                # Default to 0 if we can't determine version
                current_version = 0

            # Store metadata
            metadata = BackupMetadata(
                backup_filename=backup_filename,
                backup_path=str(backup_path),
                comment=comment,
                is_auto=1 if is_auto else 0,
                file_size=file_size,
                schema_version=current_version,
            )
            self.session.add(metadata)
            self.session.commit()

            return {
                "id": metadata.id,
                "filename": backup_filename,
                "path": str(backup_path),
                "comment": comment,
                "is_auto": is_auto,
                "size": file_size,
                "schema_version": current_version,
                "created_at": metadata.created_at,
            }
        else:
            raise FileNotFoundError(f"Database file not found: {self.path}")

    def list_backups(self) -> List[Dict[str, Any]]:
        """List all tracked backups with metadata.

        Returns
        -------
        List of backup dictionaries sorted by creation date (newest first)
        """
        from .models import BackupMetadata

        backups = (
            self.session.query(BackupMetadata)
            .order_by(BackupMetadata.created_at.desc())
            .all()
        )

        result = []
        for backup in backups:
            # Check if backup file still exists
            backup_exists = Path(backup.backup_path).exists()

            result.append(
                {
                    "id": backup.id,
                    "filename": backup.backup_filename,
                    "path": backup.backup_path,
                    "exists": backup_exists,
                    "comment": backup.comment,
                    "is_auto": bool(backup.is_auto),
                    "size": backup.file_size,
                    "schema_version": backup.schema_version,
                    "created_at": backup.created_at,
                }
            )

        return result

    def restore_backup(self, backup_id: int) -> bool:
        """Restore database from a specific backup.

        Parameters
        ----------
        backup_id: int
            ID of the backup to restore

        Returns
        -------
        bool
            True if restoration was successful
        """
        from .models import BackupMetadata

        backup = (
            self.session.query(BackupMetadata)
            .filter(BackupMetadata.id == backup_id)
            .first()
        )

        if not backup:
            raise ValueError(f"Backup with ID {backup_id} not found")

        backup_path = Path(backup.backup_path)
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")

        # Create a safety backup of current database before restore
        safety_backup = self.path.with_suffix(".pre_restore.bak")
        if self.path.exists():
            shutil.copy2(self.path, safety_backup)

        # Restore the backup
        shutil.copy2(backup_path, self.path)

        return True

    def cleanup_old_auto_backups(self, keep_count: int = 10):
        """Remove old automatic backups, keeping the most recent ones.

        Parameters
        ----------
        keep_count: int
            Number of automatic backups to keep
        """
        import os

        from .models import BackupMetadata

        # Get automatic backups ordered by date
        auto_backups = (
            self.session.query(BackupMetadata)
            .filter(BackupMetadata.is_auto == 1)
            .order_by(BackupMetadata.created_at.desc())
            .all()
        )

        # Delete old backups beyond keep_count
        for backup in auto_backups[keep_count:]:
            # Delete file if it exists
            if Path(backup.backup_path).exists():
                os.remove(backup.backup_path)

            # Delete metadata record
            self.session.delete(backup)

        self.session.commit()

    def count_contacts(self) -> int:
        from .models import Contact

        return self.session.query(Contact).count()

    def count_relationships(self) -> int:
        from .models import Relationship

        return self.session.query(Relationship).count()

    def insert_contacts(self, contacts: List[Dict[str, str]]):
        """Insert contacts from parsed data (CSV or Google Takeout)."""
        from .models import Contact

        for contact_data in contacts:
            name = f"{contact_data.get('first', '')} {contact_data.get('last', '')}".strip()
            if not name:
                name = "(No name)"

            # Get first email and phone
            emails = contact_data.get("emails", [])
            phones = contact_data.get("phones", [])

            # Handle profile image data
            profile_image = contact_data.get("profile_image")
            profile_image_filename = contact_data.get("profile_image_filename")
            profile_image_mime_type = contact_data.get("profile_image_mime_type")

            contact = Contact(
                name=name,
                email=emails[0] if emails else None,
                phone=phones[0] if phones else None,
                profile_image=profile_image,
                profile_image_filename=profile_image_filename,
                profile_image_mime_type=profile_image_mime_type,
            )
            self.session.add(contact)
            self.session.flush()  # Get the contact ID

            # Create metadata entry for this contact (formerly called relationship)
            from .models import ContactMetadata

            metadata = ContactMetadata(contact_id=contact.id)
            self.session.add(metadata)

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
        return [(c.id, c.name, c.email or "") for c in contacts]

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
        from .models import Contact, Tag

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

    def add_relationship_note(
        self, contact_id: int, note_title: str, note_content: str
    ):
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
            "notes": [
                {"title": note.title, "content": note.content}
                for note in contact.relationship.notes
            ],
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

        notes = (
            self.session.query(Note)
            .filter(Note.title.ilike(f"%{title_search}%"))
            .order_by(Note.title)
            .all()
        )
        return [(n.id, n.title, n.content) for n in notes]

    # ========== New Relationship Type Management Functions ==========

    def create_relationship_type(
        self,
        type_key: str,
        description: str,
        inverse_key: str,
        is_symmetrical: bool = False,
    ) -> int:
        """Create a new relationship type with its inverse."""
        from .models import RelationshipType

        # Check if type already exists
        existing = (
            self.session.query(RelationshipType)
            .filter(RelationshipType.type_key == type_key)
            .first()
        )
        if existing:
            return existing.id

        # Create the relationship type
        rel_type = RelationshipType(
            type_key=type_key,
            description=description,
            inverse_type_key=inverse_key,
            is_symmetrical=1 if is_symmetrical else 0,
        )
        self.session.add(rel_type)
        self.session.flush()
        return rel_type.id

    def list_relationship_types(self) -> List[Dict[str, Any]]:
        """List all relationship types with their properties."""
        from .models import RelationshipType

        types = (
            self.session.query(RelationshipType)
            .order_by(RelationshipType.type_key)
            .all()
        )
        return [
            {
                "id": t.id,
                "type_key": t.type_key,
                "description": t.description,
                "inverse_type_key": t.inverse_type_key,
                "is_symmetrical": bool(t.is_symmetrical),
            }
            for t in types
        ]

    def create_contact_relationship(
        self,
        from_contact_id: int,
        to_contact_id: int,
        type_key: str,
        start_date=None,
        end_date=None,
    ):
        """Create a relationship between two contacts."""
        from .models import ContactRelationship, RelationshipType

        # Get the relationship type
        rel_type = (
            self.session.query(RelationshipType)
            .filter(RelationshipType.type_key == type_key)
            .first()
        )
        if not rel_type:
            raise ValueError(f"Relationship type '{type_key}' not found")

        # Check if relationship already exists
        existing = (
            self.session.query(ContactRelationship)
            .filter(
                ContactRelationship.from_contact_id == from_contact_id,
                ContactRelationship.to_contact_id == to_contact_id,
                ContactRelationship.type_id == rel_type.id,
            )
            .first()
        )
        if existing:
            return  # Relationship already exists

        # Create the relationship
        relationship = ContactRelationship(
            from_contact_id=from_contact_id,
            to_contact_id=to_contact_id,
            type_id=rel_type.id,
            start_date=start_date,
            end_date=end_date,
        )
        self.session.add(relationship)

        # For non-symmetrical relationships, create the inverse
        if not rel_type.is_symmetrical and rel_type.inverse_type_key:
            # Get inverse type
            inverse_type = (
                self.session.query(RelationshipType)
                .filter(RelationshipType.type_key == rel_type.inverse_type_key)
                .first()
            )
            if inverse_type:
                # Check if inverse doesn't already exist
                existing_inverse = (
                    self.session.query(ContactRelationship)
                    .filter(
                        ContactRelationship.from_contact_id == to_contact_id,
                        ContactRelationship.to_contact_id == from_contact_id,
                        ContactRelationship.type_id == inverse_type.id,
                    )
                    .first()
                )
                if not existing_inverse:
                    inverse_relationship = ContactRelationship(
                        from_contact_id=to_contact_id,
                        to_contact_id=from_contact_id,
                        type_id=inverse_type.id,
                        start_date=start_date,
                        end_date=end_date,
                    )
                    self.session.add(inverse_relationship)

        self.session.commit()

    def get_contact_relationships(self, contact_id: int) -> List[Dict[str, Any]]:
        """Get all relationships for a contact."""
        from .models import Contact, ContactRelationship, RelationshipType

        # Get relationships where contact is 'from'
        relationships_from = (
            self.session.query(ContactRelationship, RelationshipType, Contact)
            .join(RelationshipType, ContactRelationship.type_id == RelationshipType.id)
            .join(Contact, ContactRelationship.to_contact_id == Contact.id)
            .filter(ContactRelationship.from_contact_id == contact_id)
            .all()
        )

        # Get relationships where contact is 'to' (for symmetrical relationships)
        relationships_to = (
            self.session.query(ContactRelationship, RelationshipType, Contact)
            .join(RelationshipType, ContactRelationship.type_id == RelationshipType.id)
            .join(Contact, ContactRelationship.from_contact_id == Contact.id)
            .filter(
                ContactRelationship.to_contact_id == contact_id,
                RelationshipType.is_symmetrical == 1,  # Only include symmetrical
            )
            .all()
        )

        results = []

        # Process 'from' relationships
        for rel, rel_type, other_contact in relationships_from:
            results.append(
                {
                    "relationship_id": rel.id,
                    "type": rel_type.type_key,
                    "description": rel_type.description,
                    "other_contact_id": other_contact.id,
                    "other_contact_name": other_contact.name,
                    "other_contact_email": other_contact.email,
                    "direction": "from",
                    "start_date": rel.start_date,
                    "end_date": rel.end_date,
                }
            )

        # Process 'to' relationships (only symmetrical)
        for rel, rel_type, other_contact in relationships_to:
            # Skip if we already have this relationship from the other direction
            if not any(
                r["other_contact_id"] == other_contact.id
                and r["type"] == rel_type.type_key
                for r in results
            ):
                results.append(
                    {
                        "relationship_id": rel.id,
                        "type": rel_type.type_key,
                        "description": rel_type.description,
                        "other_contact_id": other_contact.id,
                        "other_contact_name": other_contact.name,
                        "other_contact_email": other_contact.email,
                        "direction": "to",
                        "start_date": rel.start_date,
                        "end_date": rel.end_date,
                    }
                )

        return sorted(results, key=lambda x: (x["type"], x["other_contact_name"]))

    def delete_contact_relationship(
        self, from_contact_id: int, to_contact_id: int, type_key: str
    ):
        """Delete a relationship between two contacts (and its inverse if applicable)."""
        from .models import ContactRelationship, RelationshipType

        # Get the relationship type
        rel_type = (
            self.session.query(RelationshipType)
            .filter(RelationshipType.type_key == type_key)
            .first()
        )
        if not rel_type:
            raise ValueError(f"Relationship type '{type_key}' not found")

        # Delete the primary relationship
        self.session.query(ContactRelationship).filter(
            ContactRelationship.from_contact_id == from_contact_id,
            ContactRelationship.to_contact_id == to_contact_id,
            ContactRelationship.type_id == rel_type.id,
        ).delete()

        # For non-symmetrical relationships, also delete the inverse
        if not rel_type.is_symmetrical and rel_type.inverse_type_key:
            inverse_type = (
                self.session.query(RelationshipType)
                .filter(RelationshipType.type_key == rel_type.inverse_type_key)
                .first()
            )
            if inverse_type:
                self.session.query(ContactRelationship).filter(
                    ContactRelationship.from_contact_id == to_contact_id,
                    ContactRelationship.to_contact_id == from_contact_id,
                    ContactRelationship.type_id == inverse_type.id,
                ).delete()

        # For symmetrical relationships, delete both directions
        if rel_type.is_symmetrical:
            self.session.query(ContactRelationship).filter(
                ContactRelationship.from_contact_id == to_contact_id,
                ContactRelationship.to_contact_id == from_contact_id,
                ContactRelationship.type_id == rel_type.id,
            ).delete()

        self.session.commit()


def create_database(path: Path) -> Database:
    """Create a database instance."""
    db = Database(path)
    db.connect()
    return db
