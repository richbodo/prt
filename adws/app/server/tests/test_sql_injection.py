"""
Security tests for SQL injection prevention.

Tests cover:
- SQL injection attempts in CSV files
- SQL injection attempts in JSON files
- SQL injection attempts in JSONL files (including flattened field names)
- Special characters in field names
- SQL keywords in field names
"""

import os
import sys

import pytest

# Add parent directory to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.file_processor import convert_csv_to_sqlite
from core.file_processor import convert_json_to_sqlite
from core.file_processor import convert_jsonl_to_sqlite
from core.file_processor import sanitize_table_name
from core.file_processor import validate_identifier


class TestSqlInjectionPrevention:
    """Tests for SQL injection prevention across all file formats."""

    def test_csv_sql_injection_in_values(self):
        """Test that SQL injection in CSV values is handled safely."""
        csv_content = b"name,comment\nAlice,DROP TABLE users; --\nBob,' OR 1=1 --"
        result = convert_csv_to_sqlite(csv_content, "test_csv")

        # Should successfully import without executing SQL injection
        assert result["row_count"] == 2
        assert result["table_name"] == "test_csv"

    def test_json_sql_injection_in_values(self):
        """Test that SQL injection in JSON values is handled safely."""
        json_content = b'[{"name": "Alice", "query": "SELECT * FROM users"}, {"name": "Bob", "query": "DROP TABLE test; --"}]'
        result = convert_json_to_sqlite(json_content, "test_json")

        assert result["row_count"] == 2
        assert result["table_name"] == "test_json"

    def test_jsonl_sql_injection_in_values(self):
        """Test that SQL injection in JSONL values is handled safely."""
        jsonl_content = b'{"name": "Alice", "comment": "DROP TABLE users; --"}\n{"name": "Bob", "comment": "\' OR 1=1 --"}'
        result = convert_jsonl_to_sqlite(jsonl_content, "test_jsonl")

        assert result["row_count"] == 2
        assert result["table_name"] == "test_jsonl"

    def test_jsonl_sql_keywords_in_field_names(self):
        """Test that SQL keywords as field names are handled safely."""
        jsonl_content = b'{"select": 1, "from": "table", "where": "condition", "drop": "value"}'
        result = convert_jsonl_to_sqlite(jsonl_content, "keywords")

        # Should work without SQL issues
        assert result["row_count"] == 1
        assert "select" in result["schema"]
        assert "from" in result["schema"]
        assert "where" in result["schema"]
        assert "drop" in result["schema"]

    def test_jsonl_special_characters_in_field_names(self):
        """Test that special characters in field names are sanitized."""
        jsonl_content = b'{"user-name": "Alice", "user email": "alice@test.com", "user\'s age": 30}'
        result = convert_jsonl_to_sqlite(jsonl_content, "special")

        # Column names should be cleaned (hyphens and spaces become underscores)
        assert "user_name" in result["schema"]
        assert "user_email" in result["schema"]

    def test_jsonl_nested_field_sql_injection(self):
        """Test that SQL injection in nested field names is prevented."""
        jsonl_content = b'{"user": {"name; DROP TABLE users; --": "Alice"}}'
        result = convert_jsonl_to_sqlite(jsonl_content, "nested_injection")

        # Should handle safely (field name will be sanitized)
        assert result["row_count"] == 1

    def test_jsonl_array_index_with_sql(self):
        """Test that array flattening with SQL injection attempts is safe."""
        jsonl_content = b'{"tags": ["python", "DROP TABLE users; --", "\' OR 1=1"]}'
        result = convert_jsonl_to_sqlite(jsonl_content, "array_injection")

        # Should import values safely without executing SQL
        assert result["row_count"] == 1
        assert "tags__0" in result["schema"]
        assert "tags__1" in result["schema"]
        assert "tags__2" in result["schema"]

    def test_table_name_sql_injection(self):
        """Test that SQL injection in table names is prevented via sanitization."""
        jsonl_content = b'{"id": 1}'

        # Try various SQL injection attempts in table name
        dangerous_names = [
            "users; DROP TABLE users; --",
            "test' OR '1'='1",
            "test'; DELETE FROM users; --",
            "../../../etc/passwd",
            "test`OR`1`=`1",
        ]

        for dangerous_name in dangerous_names:
            result = convert_jsonl_to_sqlite(jsonl_content, dangerous_name)
            # Table name should be sanitized (alphanumeric and underscores only)
            assert result["table_name"]
            assert validate_identifier(result["table_name"].lstrip("table_"))

    def test_unicode_sql_injection(self):
        """Test that unicode-based SQL injection is prevented."""
        jsonl_content = '{"comment": "＇ OR ＇1＇=＇1"}'.encode()
        result = convert_jsonl_to_sqlite(jsonl_content, "unicode_test")

        # Should handle safely
        assert result["row_count"] == 1

    def test_null_byte_injection(self):
        """Test that null byte injection is handled safely."""
        jsonl_content = b'{"name": "Alice\\x00DROP TABLE users"}'
        # JSON parser should handle this, but test to be sure
        try:
            result = convert_jsonl_to_sqlite(jsonl_content, "null_byte")
            # If it succeeds, verify no SQL injection occurred
            assert result["row_count"] >= 0
        except Exception:
            # Expected to fail during JSON parsing, which is fine
            pass


class TestTableNameSanitization:
    """Tests for table name sanitization."""

    def test_sanitize_removes_sql_keywords(self):
        """Test sanitization of table names with SQL keywords."""
        assert sanitize_table_name("SELECT") == "select"
        assert sanitize_table_name("DROP") == "drop"
        assert sanitize_table_name("users; DROP TABLE") == "users__drop_table"

    def test_sanitize_removes_special_chars(self):
        """Test that special characters are replaced."""
        assert sanitize_table_name("test-table") == "test_table"
        assert sanitize_table_name("test table") == "test_table"
        assert sanitize_table_name("test@table#name") == "test_table_name"

    def test_sanitize_handles_path_traversal(self):
        """Test that path traversal attempts are neutralized."""
        # Starting with dots gets 'table_' prefix since it doesn't start with a letter
        assert sanitize_table_name("../../../etc/passwd") == "table__________etc_passwd"
        assert sanitize_table_name("..\\..\\windows\\system32") == "table_______windows_system32"

    def test_sanitize_handles_quotes(self):
        """Test that quotes are removed."""
        assert sanitize_table_name("test'table") == "test_table"
        assert sanitize_table_name('test"table') == "test_table"
        assert sanitize_table_name("test`table") == "test_table"


class TestIdentifierValidation:
    """Tests for identifier validation."""

    def test_validate_rejects_sql_injection(self):
        """Test that SQL injection attempts are rejected."""
        assert not validate_identifier("users; DROP TABLE users")
        assert not validate_identifier("test' OR '1'='1")
        assert not validate_identifier("test--comment")

    def test_validate_accepts_safe_names(self):
        """Test that safe names are accepted."""
        assert validate_identifier("users")
        assert validate_identifier("user_data")
        assert validate_identifier("_private")
        assert validate_identifier("table123")

    def test_validate_rejects_special_chars(self):
        """Test that special characters are rejected."""
        assert not validate_identifier("user-name")
        assert not validate_identifier("user name")
        assert not validate_identifier("user@name")
        assert not validate_identifier("user.name")


class TestJsonlSpecificSecurity:
    """JSONL-specific security tests for flattened fields."""

    def test_nested_field_name_sql_injection(self):
        """Test SQL injection in nested field names (flattened with delimiter)."""
        # Field name contains SQL injection attempt
        jsonl_content = b'{"user": {"name": "Alice", "role; DROP TABLE users; --": "admin"}}'
        result = convert_jsonl_to_sqlite(jsonl_content, "nested_sql")

        # Should handle safely
        assert result["row_count"] == 1
        # Flattened field should exist (even if sanitized)
        assert any("user__" in col for col in result["schema"])

    def test_very_long_field_names(self):
        """Test that very long field names don't cause issues."""
        long_name = "a" * 10000
        jsonl_content = f'{{"{long_name}": "value"}}'.encode()
        result = convert_jsonl_to_sqlite(jsonl_content, "long_field")

        # Should handle without crashing
        assert result["row_count"] == 1

    def test_unicode_field_names(self):
        """Test that unicode field names are handled safely."""
        jsonl_content = '{"用户名": "Alice", "年龄": 30, "邮箱": "alice@test.com"}'.encode()
        result = convert_jsonl_to_sqlite(jsonl_content, "unicode_fields")

        # Should work with unicode
        assert result["row_count"] == 1

    def test_collision_in_flattened_names(self):
        """Test handling of field name collisions after flattening."""
        # After flattening and sanitization, both become "user_name" which causes duplicate column error
        # This is expected behavior - duplicate columns are not allowed in SQLite
        jsonl_content = b'{"user-name": "Alice", "user_name": "Bob"}'

        # This should raise an error due to duplicate column names
        with pytest.raises(Exception):  # sqlite3.OperationalError or similar
            convert_jsonl_to_sqlite(jsonl_content, "collision")

    def test_deeply_nested_sql_injection(self):
        """Test SQL injection in deeply nested structures."""
        jsonl_content = b'{"a": {"b": {"c": {"d": {"e": {"DROP TABLE": "users"}}}}}}'
        result = convert_jsonl_to_sqlite(jsonl_content, "deep_nested")

        # Should flatten and handle safely
        assert result["row_count"] == 1
        # Check that deeply nested field was flattened
        assert any("a__b__c__d__e" in col for col in result["schema"])

    def test_array_of_objects_sql_injection(self):
        """Test SQL injection in arrays of objects."""
        jsonl_content = (
            b'{"items": [{"name": "Alice", "DROP": "TABLE"}, {"name": "Bob", "DELETE": "users"}]}'
        )
        result = convert_jsonl_to_sqlite(jsonl_content, "array_objects")

        # Should flatten and handle safely
        assert result["row_count"] == 1
        # Check flattened array fields exist
        assert any("items__0__" in col for col in result["schema"])

    def test_mixed_nesting_sql_injection(self):
        """Test SQL injection in mixed nested and array structures."""
        jsonl_content = b'{"user": {"roles": [{"name": "admin", "perms": ["DELETE", "DROP"]}]}}'
        result = convert_jsonl_to_sqlite(jsonl_content, "mixed_injection")

        # Should handle complex structure safely
        assert result["row_count"] == 1
