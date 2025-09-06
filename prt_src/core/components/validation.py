"""Validation system for PRT entities.

Provides validation, sanitization, and duplicate detection for contacts,
tags, notes, and relationships. UI-agnostic and reusable across platforms.
"""

import re
from dataclasses import dataclass
from dataclasses import field
from datetime import date
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from prt_src.logging_config import get_logger

logger = get_logger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors."""


@dataclass
class ValidationResult:
    """Result of a validation operation."""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    sanitized_data: Optional[Dict[str, Any]] = None


class DataSanitizer:
    """Sanitize and normalize data for validation."""

    def clean_text(self, text: Optional[str]) -> str:
        """Remove leading/trailing whitespace and normalize."""
        if not text:
            return ""
        return text.strip()

    def normalize_phone(self, phone: Optional[str]) -> Optional[str]:
        """Normalize phone number to international format.

        Args:
            phone: Phone number in various formats

        Returns:
            Normalized phone in +1XXXXXXXXXX format or None if invalid
        """
        if not phone:
            return None

        # Remove all non-numeric characters
        digits = re.sub(r"\D", "", phone)

        # Check for valid length (10 digits US, 11 with country code)
        if len(digits) == 10:
            return f"+1{digits}"
        elif len(digits) == 11 and digits[0] == "1":
            return f"+{digits}"
        elif digits.startswith("44") and len(digits) >= 11:
            # UK format
            return f"+{digits}"
        elif len(digits) < 10:
            return None

        # Already in international format
        if phone.startswith("+"):
            return f"+{digits}"

        return None

    def normalize_email(self, email: Optional[str]) -> Optional[str]:
        """Normalize email address (lowercase, trim).

        Args:
            email: Email address

        Returns:
            Normalized email or None if invalid
        """
        if not email:
            return None

        email = email.strip().lower()

        # Basic email validation
        if "@" not in email or "." not in email:
            return None

        return email


class ContactValidator:
    """Validate contact entities."""

    def __init__(self):
        self.sanitizer = DataSanitizer()
        self.email_pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    def validate(self, contact: Dict[str, Any], sanitize: bool = False) -> ValidationResult:
        """Validate a contact entity.

        Args:
            contact: Contact data dictionary
            sanitize: Whether to sanitize data during validation

        Returns:
            ValidationResult with errors and sanitized data
        """
        errors = []
        sanitized = {}

        # Check required field: name
        name = contact.get("name", "").strip() if sanitize else contact.get("name", "")
        if not name:
            errors.append("Name is required")
        else:
            sanitized["name"] = self.sanitizer.clean_text(name) if sanitize else name

        # Validate email if provided
        email = contact.get("email", "")
        if email:
            if sanitize:
                email = self.sanitizer.normalize_email(email)
                if email:
                    sanitized["email"] = email
                else:
                    errors.append("Invalid email format")
            else:
                if not self.email_pattern.match(email):
                    errors.append("Invalid email format")
                else:
                    sanitized["email"] = email

        # Validate phone if provided
        phone = contact.get("phone", "")
        if phone:
            if sanitize:
                normalized_phone = self.sanitizer.normalize_phone(phone)
                if normalized_phone:
                    sanitized["phone"] = normalized_phone
                else:
                    errors.append("Invalid phone number")
            else:
                # Basic phone validation - at least 10 digits
                digits = re.sub(r"\D", "", phone)
                if len(digits) < 10:
                    errors.append("Invalid phone number")
                else:
                    sanitized["phone"] = phone

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, sanitized_data=sanitized if sanitize else None
        )


class TagValidator:
    """Validate tag entities."""

    MAX_LENGTH = 50
    INVALID_CHARS_PATTERN = re.compile(r"[^a-zA-Z0-9\s\-_]")

    def __init__(self):
        self.sanitizer = DataSanitizer()

    def validate(self, tag: Dict[str, Any], sanitize: bool = False) -> ValidationResult:
        """Validate a tag entity.

        Args:
            tag: Tag data dictionary
            sanitize: Whether to sanitize data during validation

        Returns:
            ValidationResult with errors and sanitized data
        """
        errors = []
        sanitized = {}

        name = tag.get("name", "")

        if not name:
            errors.append("Tag name is required")
            return ValidationResult(is_valid=False, errors=errors)

        # Sanitize if requested
        if sanitize:
            name = self.sanitizer.clean_text(name).lower()

        # Check for special characters
        if self.INVALID_CHARS_PATTERN.search(name):
            errors.append("Tag name contains special characters")

        # Check max length
        if len(name) > self.MAX_LENGTH:
            errors.append(f"Tag name too long (max {self.MAX_LENGTH} characters)")

        if sanitize:
            sanitized["name"] = name

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, sanitized_data=sanitized if sanitize else None
        )


class NoteValidator:
    """Validate note entities."""

    MAX_CONTENT_LENGTH = 5000

    def __init__(self):
        self.sanitizer = DataSanitizer()

    def validate(self, note: Dict[str, Any], sanitize: bool = False) -> ValidationResult:
        """Validate a note entity.

        Args:
            note: Note data dictionary
            sanitize: Whether to sanitize data during validation

        Returns:
            ValidationResult with errors and sanitized data
        """
        errors = []
        sanitized = {}

        # Check required field: title
        title = note.get("title", "")
        if not title:
            errors.append("Title is required")
        else:
            if sanitize:
                title = self.sanitizer.clean_text(title)
                sanitized["title"] = title

        # Check content length
        content = note.get("content", "")
        if len(content) > self.MAX_CONTENT_LENGTH:
            errors.append(f"Content too long (max {self.MAX_CONTENT_LENGTH} characters)")
        else:
            if sanitize:
                content = self.sanitizer.clean_text(content)
                sanitized["content"] = content

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, sanitized_data=sanitized if sanitize else None
        )


class RelationshipValidator:
    """Validate relationship entities."""

    def validate(self, relationship: Dict[str, Any], sanitize: bool = False) -> ValidationResult:
        """Validate a relationship entity.

        Args:
            relationship: Relationship data dictionary
            sanitize: Whether to sanitize data during validation

        Returns:
            ValidationResult with errors and sanitized data
        """
        errors = []

        from_id = relationship.get("from_contact_id")
        to_id = relationship.get("to_contact_id")
        rel_type = relationship.get("type")

        # Check required fields
        if not from_id:
            errors.append("from_contact_id is required")
        if not to_id:
            errors.append("to_contact_id is required")
        if not rel_type:
            errors.append("Relationship type is required")

        # Check for self-relationship
        if from_id and to_id and from_id == to_id:
            errors.append("Cannot create self-relationship (same contact)")

        # Validate date range if provided
        start_date = relationship.get("start_date")
        end_date = relationship.get("end_date")

        if start_date and end_date:
            # Convert to date objects if necessary
            if isinstance(start_date, str):
                try:
                    start_date = date.fromisoformat(start_date)
                except ValueError:
                    errors.append("Invalid start_date format")

            if isinstance(end_date, str):
                try:
                    end_date = date.fromisoformat(end_date)
                except ValueError:
                    errors.append("Invalid end_date format")

            # Check date order
            if isinstance(start_date, date) and isinstance(end_date, date):
                if end_date < start_date:
                    errors.append("End date cannot be before start date")

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)


class DuplicateDetector:
    """Detect potential duplicate entities."""

    def __init__(self):
        self.sanitizer = DataSanitizer()

    def _normalize_name(self, name: str) -> str:
        """Normalize name for comparison."""
        return " ".join(name.lower().split())

    def find_duplicates(
        self,
        new_contact: Dict[str, Any],
        existing_contacts: List[Dict[str, Any]],
        normalize_phone: bool = False,
    ) -> List[Dict[str, Any]]:
        """Find potential duplicates of a contact.

        Args:
            new_contact: Contact to check for duplicates
            existing_contacts: List of existing contacts
            normalize_phone: Whether to normalize phone numbers for comparison

        Returns:
            List of potential duplicates with match information
        """
        duplicates = []

        new_name = self._normalize_name(new_contact.get("name", ""))
        new_email = (new_contact.get("email", "") or "").lower()
        new_phone = new_contact.get("phone", "")

        if normalize_phone and new_phone:
            new_phone = self.sanitizer.normalize_phone(new_phone)

        for existing in existing_contacts:
            match_info = {
                "id": existing["id"],
                "name": existing.get("name", ""),
                "match_type": None,
                "match_score": 0,
            }

            # Check exact name match
            existing_name = self._normalize_name(existing.get("name", ""))
            if new_name and existing_name and new_name == existing_name:
                match_info["match_type"] = "exact_name"
                match_info["match_score"] = 100
                duplicates.append(match_info)
                continue

            # Check email match
            existing_email = (existing.get("email", "") or "").lower()
            if new_email and existing_email and new_email == existing_email:
                match_info["match_type"] = "email"
                match_info["match_score"] = 90
                duplicates.append(match_info)
                continue

            # Check phone match
            existing_phone = existing.get("phone", "")
            if normalize_phone and existing_phone:
                existing_phone = self.sanitizer.normalize_phone(existing_phone)

            if new_phone and existing_phone and new_phone == existing_phone:
                match_info["match_type"] = "phone"
                match_info["match_score"] = 85
                duplicates.append(match_info)

        return duplicates


class ValidationSystem:
    """Unified validation system for all entity types."""

    def __init__(self):
        self.contact_validator = ContactValidator()
        self.tag_validator = TagValidator()
        self.note_validator = NoteValidator()
        self.relationship_validator = RelationshipValidator()
        self.duplicate_detector = DuplicateDetector()

        self.validators = {
            "contact": self.contact_validator,
            "tag": self.tag_validator,
            "note": self.note_validator,
            "relationship": self.relationship_validator,
        }

    def validate_entity(
        self, entity_type: str, entity_data: Dict[str, Any], sanitize: bool = False
    ) -> ValidationResult:
        """Validate an entity of specified type.

        Args:
            entity_type: Type of entity (contact, tag, note, relationship)
            entity_data: Entity data to validate
            sanitize: Whether to sanitize data during validation

        Returns:
            ValidationResult

        Raises:
            ValueError: If entity_type is unknown
        """
        validator = self.validators.get(entity_type)
        if not validator:
            raise ValueError(f"Unknown entity type: {entity_type}")

        return validator.validate(entity_data, sanitize=sanitize)

    def validate_batch(
        self, entities: List[Dict[str, Any]], sanitize: bool = False
    ) -> List[ValidationResult]:
        """Validate multiple entities in batch.

        Args:
            entities: List of entities with 'type' and 'data' keys
            sanitize: Whether to sanitize data during validation

        Returns:
            List of ValidationResults in same order as input
        """
        results = []

        for entity in entities:
            entity_type = entity.get("type")
            entity_data = entity.get("data", {})

            try:
                result = self.validate_entity(entity_type, entity_data, sanitize=sanitize)
                results.append(result)
            except ValueError as e:
                # Unknown entity type
                results.append(ValidationResult(is_valid=False, errors=[str(e)]))
            except Exception as e:
                logger.error(f"Validation error: {e}", exc_info=True)
                results.append(
                    ValidationResult(is_valid=False, errors=[f"Validation failed: {str(e)}"])
                )

        return results

    def check_duplicates(
        self, entity_type: str, entity_data: Dict[str, Any], existing_entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Check for duplicates of an entity.

        Args:
            entity_type: Type of entity
            entity_data: Entity to check
            existing_entities: List of existing entities

        Returns:
            List of potential duplicates
        """
        if entity_type == "contact":
            return self.duplicate_detector.find_duplicates(
                entity_data, existing_entities, normalize_phone=True
            )

        # For other entity types, could implement similar logic
        return []
