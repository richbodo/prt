"""
Unit tests for JSONL file processing functionality.

Tests cover:
- JSON record flattening (nested objects and arrays)
- Schema inference across multiple records
- JSONL to SQLite conversion
- Error handling for malformed data
- Security validation of column names
"""

import os
import sys

import pytest

# Add parent directory to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.file_processor import convert_jsonl_to_sqlite
from core.file_processor import flatten_json_record
from core.file_processor import infer_jsonl_schema
from core.file_processor import sanitize_table_name
from core.file_processor import validate_identifier


class TestFlattenJsonRecord:
    """Tests for flatten_json_record function."""

    def test_flat_object_no_flattening_needed(self):
        """Test that flat objects pass through unchanged."""
        record = {"id": 1, "name": "John", "age": 30}
        result = flatten_json_record(record)
        assert result == {"id": 1, "name": "John", "age": 30}

    def test_nested_object_two_levels(self):
        """Test flattening of 2-level nested object."""
        record = {"user": {"name": "Alice", "age": 25}}
        result = flatten_json_record(record)
        assert result == {"user__name": "Alice", "user__age": 25}

    def test_deeply_nested_object(self):
        """Test flattening of deeply nested object (3+ levels)."""
        record = {"user": {"profile": {"contact": {"email": "alice@example.com"}}}}
        result = flatten_json_record(record)
        assert result == {"user__profile__contact__email": "alice@example.com"}

    def test_array_of_primitives(self):
        """Test flattening array of primitive values."""
        record = {"tags": ["python", "data", "ml"]}
        result = flatten_json_record(record)
        assert result == {"tags__0": "python", "tags__1": "data", "tags__2": "ml"}

    def test_array_of_objects(self):
        """Test flattening array of objects."""
        record = {"items": [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]}
        result = flatten_json_record(record)
        assert result == {
            "items__0__id": 1,
            "items__0__name": "A",
            "items__1__id": 2,
            "items__1__name": "B",
        }

    def test_mixed_nested_and_arrays(self):
        """Test complex structure with both nested objects and arrays."""
        record = {"id": 1, "user": {"name": "Bob"}, "scores": [85, 90, 95]}
        result = flatten_json_record(record)
        assert result == {
            "id": 1,
            "user__name": "Bob",
            "scores__0": 85,
            "scores__1": 90,
            "scores__2": 95,
        }

    def test_empty_object(self):
        """Test handling of empty nested object."""
        record = {"user": {}}
        result = flatten_json_record(record)
        assert result == {"user": None}

    def test_empty_array(self):
        """Test handling of empty array."""
        record = {"tags": []}
        result = flatten_json_record(record)
        assert result == {"tags": None}

    def test_null_values(self):
        """Test handling of null values."""
        record = {"id": 1, "name": None, "user": {"email": None}}
        result = flatten_json_record(record)
        assert result == {"id": 1, "name": None, "user__email": None}

    def test_boolean_values(self):
        """Test handling of boolean values."""
        record = {"active": True, "verified": False}
        result = flatten_json_record(record)
        assert result == {"active": True, "verified": False}


class TestInferJsonlSchema:
    """Tests for infer_jsonl_schema function."""

    def test_single_record(self):
        """Test schema inference from single record."""
        jsonl = b'{"id": 1, "name": "Alice"}'
        schema = infer_jsonl_schema(jsonl)
        assert schema == {"id", "name"}

    def test_multiple_records_same_schema(self):
        """Test schema inference from multiple records with same schema."""
        jsonl = b'{"id": 1, "name": "Alice"}\n{"id": 2, "name": "Bob"}'
        schema = infer_jsonl_schema(jsonl)
        assert schema == {"id", "name"}

    def test_multiple_records_varying_schema(self):
        """Test schema inference when records have different fields."""
        jsonl = b'{"id": 1, "name": "Alice"}\n{"id": 2, "age": 30}\n{"email": "bob@example.com"}'
        schema = infer_jsonl_schema(jsonl)
        assert schema == {"id", "name", "age", "email"}

    def test_nested_object_schema(self):
        """Test schema inference with nested objects."""
        jsonl = b'{"user": {"name": "Alice", "age": 25}}'
        schema = infer_jsonl_schema(jsonl)
        assert schema == {"user__name", "user__age"}

    def test_array_schema(self):
        """Test schema inference with arrays."""
        jsonl = b'{"tags": ["python", "data"]}\n{"tags": ["js", "web", "api"]}'
        schema = infer_jsonl_schema(jsonl)
        # Second record has 3 tags, so we should have tags__0, tags__1, tags__2
        assert schema == {"tags__0", "tags__1", "tags__2"}

    def test_malformed_line_skipped(self):
        """Test that malformed JSON lines are skipped gracefully."""
        jsonl = b'{"id": 1}\n{invalid json}\n{"id": 2}'
        schema = infer_jsonl_schema(jsonl)
        assert schema == {"id"}

    def test_empty_lines_ignored(self):
        """Test that empty lines are ignored."""
        jsonl = b'{"id": 1}\n\n{"id": 2}\n\n'
        schema = infer_jsonl_schema(jsonl)
        assert schema == {"id"}

    def test_empty_file(self):
        """Test handling of empty file."""
        jsonl = b""
        schema = infer_jsonl_schema(jsonl)
        assert schema == set()


class TestConvertJsonlToSqlite:
    """Tests for convert_jsonl_to_sqlite function."""

    def test_basic_jsonl_conversion(self):
        """Test basic JSONL to SQLite conversion."""
        jsonl = b'{"id": 1, "name": "Alice"}\n{"id": 2, "name": "Bob"}'
        result = convert_jsonl_to_sqlite(jsonl, "test_table")

        assert result["table_name"] == "test_table"
        assert result["row_count"] == 2
        assert "id" in result["schema"]
        assert "name" in result["schema"]
        assert len(result["sample_data"]) == 2

    def test_nested_object_conversion(self):
        """Test conversion with nested objects."""
        jsonl = b'{"id": 1, "user": {"name": "Alice", "age": 30}}'
        result = convert_jsonl_to_sqlite(jsonl, "nested_test")

        assert result["table_name"] == "nested_test"
        assert result["row_count"] == 1
        assert "user__name" in result["schema"]
        assert "user__age" in result["schema"]

    def test_array_conversion(self):
        """Test conversion with arrays."""
        jsonl = b'{"id": 1, "tags": ["python", "data"]}'
        result = convert_jsonl_to_sqlite(jsonl, "array_test")

        assert result["table_name"] == "array_test"
        assert result["row_count"] == 1
        assert "tags__0" in result["schema"]
        assert "tags__1" in result["schema"]

    def test_missing_fields_filled_with_none(self):
        """Test that missing fields are filled with None."""
        jsonl = b'{"id": 1, "name": "Alice", "age": 30}\n{"id": 2, "name": "Bob"}'
        result = convert_jsonl_to_sqlite(jsonl, "missing_fields")

        assert result["row_count"] == 2
        # Both records should have all three fields
        assert "id" in result["schema"]
        assert "name" in result["schema"]
        assert "age" in result["schema"]

    def test_table_name_sanitization(self):
        """Test that table names are sanitized correctly."""
        jsonl = b'{"id": 1}'
        result = convert_jsonl_to_sqlite(jsonl, "Test-Table Name!")

        # Should be lowercase with underscores
        assert result["table_name"] == "test_table_name_"

    def test_column_name_cleaning(self):
        """Test that column names are cleaned (lowercase, underscores)."""
        jsonl = b'{"User Name": "Alice", "User-Age": 30}'
        result = convert_jsonl_to_sqlite(jsonl, "test")

        # Column names should be cleaned
        assert "user_name" in result["schema"]
        assert "user_age" in result["schema"]

    def test_empty_jsonl_raises_error(self):
        """Test that empty JSONL raises ValueError."""
        jsonl = b""
        with pytest.raises(ValueError, match="no valid records"):
            convert_jsonl_to_sqlite(jsonl, "test")

    def test_no_valid_records_raises_error(self):
        """Test that JSONL with only invalid lines raises ValueError."""
        jsonl = b"{invalid}\n{also invalid}"
        with pytest.raises(ValueError, match="no valid records"):
            convert_jsonl_to_sqlite(jsonl, "test")

    def test_sample_data_returned(self):
        """Test that sample data is returned correctly."""
        jsonl = b'{"id": 1, "name": "Alice"}\n{"id": 2, "name": "Bob"}'
        result = convert_jsonl_to_sqlite(jsonl, "test")

        sample_data = result["sample_data"]
        assert len(sample_data) == 2
        assert sample_data[0]["id"] == 1
        assert sample_data[0]["name"] == "Alice"
        assert sample_data[1]["id"] == 2
        assert sample_data[1]["name"] == "Bob"


class TestSanitizeTableName:
    """Tests for sanitize_table_name function."""

    def test_simple_name(self):
        """Test sanitization of simple name."""
        assert sanitize_table_name("users") == "users"

    def test_uppercase_to_lowercase(self):
        """Test conversion to lowercase."""
        assert sanitize_table_name("USERS") == "users"

    def test_spaces_to_underscores(self):
        """Test that spaces become underscores."""
        assert sanitize_table_name("user data") == "user_data"

    def test_special_characters_removed(self):
        """Test that special characters are replaced with underscores."""
        assert sanitize_table_name("user-data!@#") == "user_data___"

    def test_file_extension_removed(self):
        """Test that file extensions are removed."""
        assert sanitize_table_name("data.csv") == "data"
        assert sanitize_table_name("data.json") == "data"
        assert sanitize_table_name("data.jsonl") == "data"

    def test_starts_with_number_gets_prefix(self):
        """Test that names starting with numbers get 'table_' prefix."""
        assert sanitize_table_name("123data") == "table_123data"


class TestValidateIdentifier:
    """Tests for validate_identifier function."""

    def test_valid_identifier(self):
        """Test that valid identifiers pass."""
        assert validate_identifier("users")
        assert validate_identifier("user_data")
        assert validate_identifier("_private")
        assert validate_identifier("table123")

    def test_starts_with_number_invalid(self):
        """Test that identifiers starting with numbers are invalid."""
        assert not validate_identifier("123users")

    def test_special_characters_invalid(self):
        """Test that special characters make identifiers invalid."""
        assert not validate_identifier("user-data")
        assert not validate_identifier("user data")
        assert not validate_identifier("user@data")


class TestIntegrationWithTestFiles:
    """Integration tests using the test JSONL files."""

    def test_nested_jsonl_file(self):
        """Test processing test_nested.jsonl file."""
        test_file = os.path.join(os.path.dirname(__file__), "assets", "test_nested.jsonl")
        with open(test_file, "rb") as f:
            content = f.read()

        result = convert_jsonl_to_sqlite(content, "test_nested")

        assert result["table_name"] == "test_nested"
        assert result["row_count"] == 3
        assert "user__name" in result["schema"]
        assert "user__profile__age" in result["schema"]
        assert "user__profile__city" in result["schema"]
        assert "status" in result["schema"]

    def test_arrays_jsonl_file(self):
        """Test processing test_arrays.jsonl file."""
        test_file = os.path.join(os.path.dirname(__file__), "assets", "test_arrays.jsonl")
        with open(test_file, "rb") as f:
            content = f.read()

        result = convert_jsonl_to_sqlite(content, "test_arrays")

        assert result["table_name"] == "test_arrays"
        assert result["row_count"] == 3
        assert "tags__0" in result["schema"]
        assert "tags__1" in result["schema"]
        assert "tags__2" in result["schema"]
        assert "prices__0" in result["schema"]
        assert "prices__1" in result["schema"]

    def test_mixed_jsonl_file(self):
        """Test processing test_mixed.jsonl file."""
        test_file = os.path.join(os.path.dirname(__file__), "assets", "test_mixed.jsonl")
        with open(test_file, "rb") as f:
            content = f.read()

        result = convert_jsonl_to_sqlite(content, "test_mixed")

        assert result["table_name"] == "test_mixed"
        assert result["row_count"] == 2
        assert "data__metrics__0__name" in result["schema"]
        assert "data__metrics__0__value" in result["schema"]
        assert "data__metrics__1__name" in result["schema"]
        assert "data__metrics__1__value" in result["schema"]
        assert "data__extra__field" in result["schema"]
        assert "timestamp" in result["schema"]


class TestSecurityValidation:
    """Security tests for JSONL processing."""

    def test_sql_keywords_in_field_names(self):
        """Test that SQL keywords in field names are handled safely."""
        jsonl = b'{"select": 1, "from": 2, "where": 3}'
        result = convert_jsonl_to_sqlite(jsonl, "keywords_test")
        # Should work without SQL injection issues
        assert result["row_count"] == 1

    def test_special_characters_in_field_names(self):
        """Test that special characters in field names are sanitized."""
        jsonl = b'{"user-name": "Alice", "user email": "alice@test.com"}'
        result = convert_jsonl_to_sqlite(jsonl, "special_chars")
        # Column names should be cleaned
        assert "user_name" in result["schema"]
        assert "user_email" in result["schema"]

    def test_sql_injection_in_values(self):
        """Test that SQL injection attempts in values are handled safely."""
        jsonl = b'{"name": "Alice", "comment": "DROP TABLE users; --"}'
        result = convert_jsonl_to_sqlite(jsonl, "injection_test")
        # Should work without executing SQL injection
        assert result["row_count"] == 1

    def test_very_long_field_names(self):
        """Test handling of very long field names."""
        long_name = "a" * 1000
        jsonl = f'{{"{long_name}": "value"}}'.encode()
        result = convert_jsonl_to_sqlite(jsonl, "long_names")
        # Should work without issues
        assert result["row_count"] == 1

    def test_unicode_in_field_names(self):
        """Test handling of unicode characters in field names."""
        jsonl = '{"用户": "Alice", "année": 2024}'.encode()
        result = convert_jsonl_to_sqlite(jsonl, "unicode_test")
        # Should work with unicode
        assert result["row_count"] == 1
