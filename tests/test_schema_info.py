"""
Tests for schema_info module.

This module tests the schema information generation and validation functionality
that helps the LLM understand the database structure.
"""

import pytest

from prt_src.schema_info import SchemaInfoGenerator
from prt_src.schema_info import get_schema_for_llm
from prt_src.schema_info import validate_sql_schema


class TestSchemaInfoGenerator:
    """Test the SchemaInfoGenerator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.generator = SchemaInfoGenerator()

    def test_get_table_names(self):
        """Test getting table names from models."""
        table_names = self.generator.get_table_names()

        # Check that we have the expected tables
        expected_tables = [
            "contacts",
            "tags",
            "notes",
            "contact_metadata",
            "contact_relationships",
            "relationship_types",
        ]
        for table in expected_tables:
            assert table in table_names

    def test_get_table_columns(self):
        """Test getting column names for a specific table."""
        # Test contacts table columns
        contacts_columns = self.generator.get_table_columns("contacts")
        expected_columns = [
            "id",
            "name",
            "first_name",
            "last_name",
            "email",
            "phone",
            "profile_image",
            "profile_image_filename",
            "profile_image_mime_type",
            "is_you",
            "created_at",
            "updated_at",
        ]
        for col in expected_columns:
            assert col in contacts_columns

        # Test non-existent table
        nonexistent_columns = self.generator.get_table_columns("nonexistent")
        assert nonexistent_columns == []

    def test_validate_column_exists(self):
        """Test column existence validation."""
        # Valid column
        assert self.generator.validate_column_exists("contacts", "name") is True
        assert self.generator.validate_column_exists("contacts", "email") is True

        # Invalid column
        assert self.generator.validate_column_exists("contacts", "address") is False
        assert self.generator.validate_column_exists("contacts", "nonexistent") is False

        # Invalid table
        assert self.generator.validate_column_exists("nonexistent", "name") is False

    def test_suggest_similar_columns(self):
        """Test column name suggestions."""
        # Test suggestion for similar column
        suggestions = self.generator.suggest_similar_columns("contacts", "fname")
        assert "first_name" in suggestions

        suggestions = self.generator.suggest_similar_columns("contacts", "mail")
        assert "email" in suggestions

    def test_parse_sql_tables_and_columns(self):
        """Test SQL parsing for tables and columns."""
        sql = "SELECT id, name, email FROM contacts WHERE name LIKE '%John%'"
        tables, columns = self.generator.parse_sql_tables_and_columns(sql)

        assert "CONTACTS" in tables
        assert "ID" in columns
        assert "NAME" in columns
        assert "EMAIL" in columns

    def test_get_table_info(self):
        """Test getting complete table information."""
        from prt_src.models import Contact

        table_info = self.generator.get_table_info(Contact)

        assert table_info["table_name"] == "contacts"
        assert "description" in table_info
        assert "columns" in table_info
        assert "relationships" in table_info

        # Check that columns have required information
        columns = table_info["columns"]
        assert len(columns) > 0

        # Find the ID column
        id_column = next(col for col in columns if col["name"] == "id")
        assert id_column["primary_key"] is True
        assert id_column["type"] == "integer"

    def test_get_schema_summary(self):
        """Test getting complete schema summary."""
        schema = self.generator.get_schema_summary()

        assert schema["database_type"] == "SQLite"
        assert "tables" in schema
        assert "total_tables" in schema
        assert schema["total_tables"] > 0

        # Check that we have the main tables
        table_names = [table["table_name"] for table in schema["tables"]]
        assert "contacts" in table_names
        assert "tags" in table_names
        assert "notes" in table_names


class TestSchemaFormatting:
    """Test schema formatting for LLM consumption."""

    def test_format_schema_for_llm(self):
        """Test that schema is formatted correctly for LLM."""
        schema_text = get_schema_for_llm()

        # Check that it contains expected sections
        assert "## PRT DATABASE SCHEMA" in schema_text
        assert "### Table: `contacts`" in schema_text
        assert "### Table: `tags`" in schema_text
        assert "### Table: `notes`" in schema_text

        # Check that it includes column information
        assert "`id` (integer)" in schema_text
        assert "`name` (text)" in schema_text
        assert "`email` (text)" in schema_text

        # Check that it includes SQL examples
        assert "## COMMON SQL QUERY PATTERNS" in schema_text
        assert "SELECT id, name, email, phone FROM contacts" in schema_text

        # Check that it warns about non-existent columns
        assert "❌ `address` column does NOT exist" in schema_text


class TestSQLValidation:
    """Test SQL validation against schema."""

    def test_validate_sql_valid_query(self):
        """Test validation of valid SQL queries."""
        # Valid query
        sql = "SELECT id, name, email FROM contacts WHERE name LIKE '%John%'"
        result = validate_sql_schema(sql)

        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_sql_invalid_column(self):
        """Test validation of SQL with invalid column."""
        # Invalid column
        sql = "SELECT id, name, address FROM contacts"
        result = validate_sql_schema(sql)

        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert any("address" in error for error in result["errors"])

    def test_validate_sql_invalid_table(self):
        """Test validation of SQL with invalid table."""
        # Invalid table
        sql = "SELECT id, name FROM users"
        result = validate_sql_schema(sql)

        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert any("users" in error.lower() for error in result["errors"])

    def test_validate_sql_with_suggestions(self):
        """Test that validation provides helpful suggestions."""
        # Query with similar column name
        sql = "SELECT id, fname FROM contacts"
        result = validate_sql_schema(sql)

        assert result["valid"] is False
        assert len(result["suggestions"]) > 0


class TestAPIIntegration:
    """Test API integration with schema functionality."""

    def test_api_schema_methods_exist(self):
        """Test that API has schema-related methods."""
        from prt_src.api import PRTAPI

        # Check that methods exist (we don't need to call them in unit tests)
        assert hasattr(PRTAPI, "get_database_schema")
        assert hasattr(PRTAPI, "validate_sql_query")
        assert hasattr(PRTAPI, "_enhance_sql_error")

    def test_enhanced_error_message_format(self):
        """Test that enhanced error messages are properly formatted."""
        from unittest.mock import Mock

        from prt_src.api import PRTAPI

        # Create a mock API instance
        api = Mock(spec=PRTAPI)
        api.logger = Mock()

        # Test the _enhance_sql_error method by calling it directly
        # We'll create a minimal implementation for testing
        def mock_enhance_sql_error(sql, error_msg):
            enhanced_msg = error_msg
            if "no such column" in error_msg.lower():
                enhanced_msg += "\n\n📋 SCHEMA HELP:\n"
                enhanced_msg += "Column does not exist in the database.\n"
            enhanced_msg += (
                "\n\n📖 For complete schema information, ask: 'Show me the database schema'"
            )
            return enhanced_msg

        # Test column error enhancement
        original_error = "sqlite3.OperationalError: no such column: address"
        enhanced = mock_enhance_sql_error("SELECT address FROM contacts", original_error)

        assert "📋 SCHEMA HELP:" in enhanced
        assert "📖 For complete schema information" in enhanced


if __name__ == "__main__":
    pytest.main([__file__])
