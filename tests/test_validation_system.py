"""Test validation system for PRT entities.

TDD approach - writing tests first before implementation.
Tests cover success cases, failure cases, and edge cases for validation.
"""

from datetime import date
from datetime import timedelta

import pytest

# These imports will fail initially - that's expected in TDD
from prt_src.core.components.validation import ContactValidator
from prt_src.core.components.validation import DataSanitizer
from prt_src.core.components.validation import DuplicateDetector
from prt_src.core.components.validation import NoteValidator
from prt_src.core.components.validation import RelationshipValidator
from prt_src.core.components.validation import TagValidator
from prt_src.core.components.validation import ValidationSystem


class TestDataSanitizer:
    """Test data sanitization utilities."""

    def test_sanitize_whitespace(self):
        """Test that leading/trailing whitespace is removed."""
        sanitizer = DataSanitizer()

        assert sanitizer.clean_text("  John Doe  ") == "John Doe"
        assert sanitizer.clean_text("\n\tJane\n\t") == "Jane"
        assert sanitizer.clean_text("   ") == ""

    def test_normalize_phone(self):
        """Test phone number normalization."""
        sanitizer = DataSanitizer()

        # US phone formats
        assert sanitizer.normalize_phone("(555) 123-4567") == "+15551234567"
        assert sanitizer.normalize_phone("555-123-4567") == "+15551234567"
        assert sanitizer.normalize_phone("5551234567") == "+15551234567"
        assert sanitizer.normalize_phone("1-555-123-4567") == "+15551234567"

        # International format (already normalized)
        assert sanitizer.normalize_phone("+44 20 7946 0958") == "+442079460958"

        # Invalid phone
        assert sanitizer.normalize_phone("not a phone") is None
        assert sanitizer.normalize_phone("123") is None  # Too short

    def test_normalize_email(self):
        """Test email normalization (lowercase, trim)."""
        sanitizer = DataSanitizer()

        assert sanitizer.normalize_email("JOHN@EXAMPLE.COM") == "john@example.com"
        assert sanitizer.normalize_email("  jane@test.org  ") == "jane@test.org"
        assert sanitizer.normalize_email("invalid") is None


class TestContactValidator:
    """Test contact entity validation."""

    def test_valid_contact(self):
        """Test validation of a valid contact."""
        validator = ContactValidator()

        contact = {"name": "John Doe", "email": "john@example.com", "phone": "555-123-4567"}

        result = validator.validate(contact)
        assert result.is_valid is True
        assert result.errors == []

    def test_contact_missing_required_name(self):
        """Test that name is required."""
        validator = ContactValidator()

        contact = {"email": "john@example.com", "phone": "555-123-4567"}

        result = validator.validate(contact)
        assert result.is_valid is False
        assert "name is required" in result.errors[0].lower()

    def test_contact_invalid_email(self):
        """Test email format validation."""
        validator = ContactValidator()

        contact = {"name": "John Doe", "email": "not-an-email", "phone": "555-123-4567"}

        result = validator.validate(contact)
        assert result.is_valid is False
        assert "invalid email" in result.errors[0].lower()

    def test_contact_invalid_phone(self):
        """Test phone format validation."""
        validator = ContactValidator()

        contact = {"name": "John Doe", "email": "john@example.com", "phone": "123"}  # Too short

        result = validator.validate(contact)
        assert result.is_valid is False
        assert "invalid phone" in result.errors[0].lower()

    def test_contact_sanitization(self):
        """Test that contact data is sanitized during validation."""
        validator = ContactValidator()

        contact = {
            "name": "  John Doe  ",
            "email": "  JOHN@EXAMPLE.COM  ",
            "phone": "(555) 123-4567",
        }

        result = validator.validate(contact, sanitize=True)
        assert result.is_valid is True
        assert result.sanitized_data["name"] == "John Doe"
        assert result.sanitized_data["email"] == "john@example.com"
        assert result.sanitized_data["phone"] == "+15551234567"


class TestTagValidator:
    """Test tag entity validation."""

    def test_valid_tag(self):
        """Test validation of a valid tag."""
        validator = TagValidator()

        tag = {"name": "family"}
        result = validator.validate(tag)
        assert result.is_valid is True

    def test_tag_special_characters(self):
        """Test that special characters are not allowed."""
        validator = TagValidator()

        invalid_tags = [
            {"name": "family@home"},
            {"name": "work#office"},
            {"name": "friends&family"},
            {"name": "test!"},
        ]

        for tag in invalid_tags:
            result = validator.validate(tag)
            assert result.is_valid is False
            assert "special characters" in result.errors[0].lower()

    def test_tag_max_length(self):
        """Test tag max length validation (50 chars)."""
        validator = TagValidator()

        # Valid length
        tag = {"name": "a" * 50}
        result = validator.validate(tag)
        assert result.is_valid is True

        # Too long
        tag = {"name": "a" * 51}
        result = validator.validate(tag)
        assert result.is_valid is False
        assert "too long" in result.errors[0].lower() or "max length" in result.errors[0].lower()

    def test_tag_sanitization(self):
        """Test tag sanitization."""
        validator = TagValidator()

        tag = {"name": "  Family  "}
        result = validator.validate(tag, sanitize=True)
        assert result.is_valid is True
        assert result.sanitized_data["name"] == "family"  # Lowercase and trimmed


class TestNoteValidator:
    """Test note entity validation."""

    def test_valid_note(self):
        """Test validation of a valid note."""
        validator = NoteValidator()

        note = {"title": "Meeting Notes", "content": "Discussed project timeline"}
        result = validator.validate(note)
        assert result.is_valid is True

    def test_note_missing_title(self):
        """Test that title is required."""
        validator = NoteValidator()

        note = {"content": "Some content"}
        result = validator.validate(note)
        assert result.is_valid is False
        assert "title is required" in result.errors[0].lower()

    def test_note_max_content_length(self):
        """Test note content max length (5000 chars)."""
        validator = NoteValidator()

        # Valid length
        note = {"title": "Test Note", "content": "a" * 5000}
        result = validator.validate(note)
        assert result.is_valid is True

        # Too long
        note = {"title": "Test Note", "content": "a" * 5001}
        result = validator.validate(note)
        assert result.is_valid is False
        assert (
            "content too long" in result.errors[0].lower()
            or "max length" in result.errors[0].lower()
        )


class TestRelationshipValidator:
    """Test relationship entity validation."""

    def test_valid_relationship(self):
        """Test validation of a valid relationship."""
        validator = RelationshipValidator()

        relationship = {
            "from_contact_id": 1,
            "to_contact_id": 2,
            "type": "friend",
            "start_date": date.today(),
        }
        result = validator.validate(relationship)
        assert result.is_valid is True

    def test_self_relationship_prevented(self):
        """Test that self-relationships are not allowed."""
        validator = RelationshipValidator()

        relationship = {"from_contact_id": 1, "to_contact_id": 1, "type": "friend"}  # Same as from
        result = validator.validate(relationship)
        assert result.is_valid is False
        assert (
            "self-relationship" in result.errors[0].lower()
            or "same contact" in result.errors[0].lower()
        )

    def test_invalid_date_range(self):
        """Test that end_date cannot be before start_date."""
        validator = RelationshipValidator()

        relationship = {
            "from_contact_id": 1,
            "to_contact_id": 2,
            "type": "colleague",
            "start_date": date.today(),
            "end_date": date.today() - timedelta(days=1),  # Before start
        }
        result = validator.validate(relationship)
        assert result.is_valid is False
        assert "end date" in result.errors[0].lower() and "before" in result.errors[0].lower()


class TestDuplicateDetector:
    """Test duplicate detection functionality."""

    def test_exact_name_duplicate(self):
        """Test detection of exact name matches."""
        detector = DuplicateDetector()

        existing_contacts = [
            {"id": 1, "name": "John Doe", "email": "john@example.com"},
            {"id": 2, "name": "Jane Smith", "email": "jane@example.com"},
        ]

        new_contact = {"name": "John Doe", "email": "different@example.com"}

        duplicates = detector.find_duplicates(new_contact, existing_contacts)
        assert len(duplicates) == 1
        assert duplicates[0]["id"] == 1
        assert duplicates[0]["match_type"] == "exact_name"

    def test_similar_name_duplicate(self):
        """Test detection of similar names (case-insensitive, extra spaces)."""
        detector = DuplicateDetector()

        existing_contacts = [
            {"id": 1, "name": "John Doe", "email": "john@example.com"},
        ]

        similar_names = [
            {"name": "john doe"},  # Different case
            {"name": "  John  Doe  "},  # Extra spaces
            {"name": "JOHN DOE"},  # All caps
        ]

        for new_contact in similar_names:
            duplicates = detector.find_duplicates(new_contact, existing_contacts)
            assert len(duplicates) == 1
            assert duplicates[0]["id"] == 1

    def test_email_duplicate(self):
        """Test detection of duplicate emails."""
        detector = DuplicateDetector()

        existing_contacts = [
            {"id": 1, "name": "John Doe", "email": "john@example.com"},
            {"id": 2, "name": "Jane Smith", "email": "jane@example.com"},
        ]

        new_contact = {"name": "Jonathan Doe", "email": "john@example.com"}

        duplicates = detector.find_duplicates(new_contact, existing_contacts)
        assert len(duplicates) == 1
        assert duplicates[0]["id"] == 1
        assert duplicates[0]["match_type"] == "email"

    def test_phone_duplicate(self):
        """Test detection of duplicate phone numbers."""
        detector = DuplicateDetector()

        existing_contacts = [
            {"id": 1, "name": "John Doe", "phone": "+15551234567"},
        ]

        # Different formats of same phone number
        new_contact = {"name": "J. Doe", "phone": "(555) 123-4567"}

        duplicates = detector.find_duplicates(new_contact, existing_contacts, normalize_phone=True)
        assert len(duplicates) == 1
        assert duplicates[0]["id"] == 1
        assert duplicates[0]["match_type"] == "phone"

    def test_no_duplicates(self):
        """Test when there are no duplicates."""
        detector = DuplicateDetector()

        existing_contacts = [
            {"id": 1, "name": "John Doe", "email": "john@example.com"},
        ]

        new_contact = {"name": "Jane Smith", "email": "jane@example.com", "phone": "555-999-8888"}

        duplicates = detector.find_duplicates(new_contact, existing_contacts)
        assert len(duplicates) == 0


class TestValidationSystem:
    """Test the unified validation system."""

    def test_validate_entity_routing(self):
        """Test that validation system routes to correct validator."""
        system = ValidationSystem()

        # Test contact validation
        contact = {"name": "John Doe", "email": "john@example.com"}
        result = system.validate_entity("contact", contact)
        assert result.is_valid is True

        # Test tag validation
        tag = {"name": "family"}
        result = system.validate_entity("tag", tag)
        assert result.is_valid is True

        # Test note validation
        note = {"title": "Test", "content": "Content"}
        result = system.validate_entity("note", note)
        assert result.is_valid is True

        # Test relationship validation
        relationship = {"from_contact_id": 1, "to_contact_id": 2, "type": "friend"}
        result = system.validate_entity("relationship", relationship)
        assert result.is_valid is True

    def test_unknown_entity_type(self):
        """Test handling of unknown entity type."""
        system = ValidationSystem()

        with pytest.raises(ValueError) as exc_info:
            system.validate_entity("unknown", {})
        assert "unknown entity type" in str(exc_info.value).lower()

    def test_batch_validation(self):
        """Test validating multiple entities at once."""
        system = ValidationSystem()

        entities = [
            {"type": "contact", "data": {"name": "John", "email": "john@example.com"}},
            {"type": "contact", "data": {"name": "Jane", "email": "invalid-email"}},  # Invalid
            {"type": "tag", "data": {"name": "family"}},
            {"type": "tag", "data": {"name": "work@office"}},  # Invalid
        ]

        results = system.validate_batch(entities)

        assert len(results) == 4
        assert results[0].is_valid is True
        assert results[1].is_valid is False  # Invalid email
        assert results[2].is_valid is True
        assert results[3].is_valid is False  # Special characters

    def test_sanitize_and_validate(self):
        """Test combined sanitization and validation."""
        system = ValidationSystem()

        dirty_contact = {
            "name": "  John Doe  ",
            "email": "  JOHN@EXAMPLE.COM  ",
            "phone": "(555) 123-4567",
        }

        result = system.validate_entity("contact", dirty_contact, sanitize=True)
        assert result.is_valid is True
        assert result.sanitized_data["name"] == "John Doe"
        assert result.sanitized_data["email"] == "john@example.com"
        assert result.sanitized_data["phone"] == "+15551234567"


# Triggering workflow
