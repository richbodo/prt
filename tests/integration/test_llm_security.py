"""Integration tests for LLM security features.

Tests that security validations work correctly:
1. SQL injection attempts are blocked
2. Relationship tools handle ambiguous contacts properly
3. Prompt injection doesn't bypass safety features

These tests call tool methods directly to validate security without LLM dependencies.
"""

import pytest

from prt_src.api import PRTAPI
from prt_src.llm_ollama import OllamaLLM


@pytest.mark.integration
class TestLLMSecurity:
    """Test security features of LLM tools."""

    def test_sql_injection_multiple_statements(self, test_db):
        """Test that multiple SQL statements are blocked."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config)
        llm = OllamaLLM(api=api)

        # Try SQL injection with multiple statements
        dangerous_sql = "SELECT * FROM contacts; DROP TABLE contacts;"

        result = llm._call_tool(
            "execute_sql", {"sql": dangerous_sql, "confirm": True, "reason": "Test"}
        )

        # Verify injection is blocked (either by our validation or by SQLite)
        assert isinstance(result, dict)
        assert result["success"] is False
        # Accept either our validation message or SQLite's error
        assert (
            "multiple" in result["message"].lower()
            or "multiple" in result.get("error", "").lower()
            or "one statement at a time" in result.get("error", "").lower()
        )

    def test_sql_injection_comments(self, test_db):
        """Test that SQL comments are blocked."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config)
        llm = OllamaLLM(api=api)

        # Try SQL with comments
        dangerous_queries = [
            "SELECT * FROM contacts -- comment",
            "SELECT * FROM contacts /* comment */",
            "SELECT * FROM contacts WHERE id=1 --",
        ]

        for sql in dangerous_queries:
            result = llm._call_tool("execute_sql", {"sql": sql, "confirm": True, "reason": "Test"})

            # Verify comment is blocked
            assert result["success"] is False
            assert "comment" in result["message"].lower() or "comment" in result["error"].lower()

    def test_sql_injection_dangerous_operations(self, test_db):
        """Test that dangerous SQL operations are blocked."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config)
        llm = OllamaLLM(api=api)

        # Try dangerous SQLite-specific operations
        dangerous_queries = [
            "ATTACH DATABASE '/tmp/malicious.db' AS evil",
            "PRAGMA table_info(contacts)",
        ]

        for sql in dangerous_queries:
            result = llm._call_tool("execute_sql", {"sql": sql, "confirm": True, "reason": "Test"})

            # Verify dangerous operation is blocked
            assert result["success"] is False
            assert (
                "dangerous" in result["message"].lower() or "dangerous" in result["error"].lower()
            )

    def test_sql_single_trailing_semicolon_allowed(self, test_db):
        """Test that single trailing semicolon is allowed."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config)
        llm = OllamaLLM(api=api)

        # Valid SQL with trailing semicolon
        sql = "SELECT id, name FROM contacts LIMIT 1;"

        result = llm._call_tool("execute_sql", {"sql": sql, "confirm": True, "reason": "Test"})

        # Verify query is allowed
        assert result["success"] is True
        assert "rows" in result

    def test_relationship_ambiguous_from_contact(self, test_db):
        """Test relationship tool handles multiple matching 'from' contacts."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config)
        llm = OllamaLLM(api=api)

        # Create two contacts with similar names using db directly
        from prt_src.models import Contact

        contact1 = Contact(name="John Smith", email="john1@example.com")
        contact2 = Contact(name="John Doe", email="john2@example.com")
        db.session.add(contact1)
        db.session.add(contact2)
        db.session.commit()

        # Get any existing contact for the 'to' side
        all_contacts = api.list_all_contacts()
        to_contact_name = all_contacts[0]["name"] if all_contacts else "Test Person"

        # Try to add relationship with ambiguous name
        result = llm._call_tool(
            "add_contact_relationship",
            {
                "from_contact_name": "John",  # Matches both
                "to_contact_name": to_contact_name,
                "type_key": "friend",
            },
        )

        # Verify ambiguous match is handled
        assert isinstance(result, dict)
        # The safety wrapper wraps the result
        inner_result = result.get("result", result)

        assert inner_result["success"] is False
        assert "multiple" in inner_result["message"].lower()
        assert "John" in inner_result["message"]

    def test_relationship_ambiguous_to_contact(self, test_db):
        """Test relationship tool handles multiple matching 'to' contacts."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config)
        llm = OllamaLLM(api=api)

        # Create two contacts with similar names using db directly
        from prt_src.models import Contact

        contact1 = Contact(name="Bob Smith", email="bob1@example.com")
        contact2 = Contact(name="Bob Jones", email="bob2@example.com")
        db.session.add(contact1)
        db.session.add(contact2)
        db.session.commit()

        # Get any existing contact for the 'from' side
        all_contacts = api.list_all_contacts()
        from_contact_name = all_contacts[0]["name"] if all_contacts else "Test Person"

        # Try to add relationship with ambiguous name
        result = llm._call_tool(
            "add_contact_relationship",
            {
                "from_contact_name": from_contact_name,
                "to_contact_name": "Bob",  # Matches both
                "type_key": "friend",
            },
        )

        # Verify ambiguous match is handled
        assert isinstance(result, dict)
        inner_result = result.get("result", result)

        assert inner_result["success"] is False
        assert "multiple" in inner_result["message"].lower()

    def test_relationship_contact_not_found(self, test_db):
        """Test relationship tool handles non-existent contacts."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config)
        llm = OllamaLLM(api=api)

        # Get any existing contact for the 'to' side
        all_contacts = api.list_all_contacts()
        to_contact_name = all_contacts[0]["name"] if all_contacts else "Test Person"

        # Try to add relationship with non-existent contact
        result = llm._call_tool(
            "add_contact_relationship",
            {
                "from_contact_name": "NonExistentPerson12345",
                "to_contact_name": to_contact_name,
                "type_key": "friend",
            },
        )

        # Verify not found error
        assert isinstance(result, dict)
        inner_result = result.get("result", result)

        assert inner_result["success"] is False
        # Accept either "not found" or "no contacts match"
        assert (
            "not found" in inner_result["message"].lower()
            or "no contacts match" in inner_result["message"].lower()
        )
        assert "NonExistentPerson12345" in inner_result["message"]

    def test_sql_validation_preserves_legitimate_queries(self, test_db):
        """Test that legitimate SQL queries still work after validation."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config)
        llm = OllamaLLM(api=api)

        # Legitimate queries that should work
        legitimate_queries = [
            "SELECT COUNT(*) FROM contacts",
            "SELECT id, name, email FROM contacts WHERE email LIKE '%@example.com%'",
            "SELECT * FROM contacts ORDER BY name LIMIT 10",
            "INSERT INTO tags (name) VALUES ('test-security-tag')",
        ]

        for sql in legitimate_queries:
            result = llm._call_tool(
                "execute_sql", {"sql": sql, "confirm": True, "reason": "Legitimate query"}
            )

            # Verify query is allowed
            assert result["success"] is True, f"Legitimate query was blocked: {sql}"

    def test_relationship_remove_with_ambiguous_contacts(self, test_db):
        """Test remove relationship handles ambiguous contacts correctly."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        api = PRTAPI(config)
        llm = OllamaLLM(api=api)

        # Create two contacts with similar names using db directly
        from prt_src.models import Contact

        contact1 = Contact(name="Alice Smith", email="alice1@example.com")
        contact2 = Contact(name="Alice Jones", email="alice2@example.com")
        db.session.add(contact1)
        db.session.add(contact2)
        db.session.commit()

        # Get any existing contact for the 'to' side
        all_contacts = api.list_all_contacts()
        to_contact_name = all_contacts[0]["name"] if all_contacts else "Test Person"

        # Try to remove relationship with ambiguous name
        result = llm._call_tool(
            "remove_contact_relationship",
            {
                "from_contact_name": "Alice",
                "to_contact_name": to_contact_name,
                "type_key": "friend",
            },
        )

        # Verify ambiguous match is handled
        assert isinstance(result, dict)
        inner_result = result.get("result", result)

        assert inner_result["success"] is False
        assert "multiple" in inner_result["message"].lower()
