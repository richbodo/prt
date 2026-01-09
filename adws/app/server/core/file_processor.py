"""
File processing utilities for converting various file formats to SQLite databases.

This module handles CSV, JSON, and JSONL file uploads, converting them to SQLite tables
for natural language querying. Includes flattening logic for nested structures in JSONL files.
"""

import io
import json
import re
import sqlite3
from typing import Any

import pandas as pd

from .constants import NESTED_FIELD_DELIMITER


def sanitize_table_name(name: str) -> str:
    """
    Sanitize table name to be SQL-safe.

    Args:
        name: Raw table name from filename

    Returns:
        Sanitized table name (lowercase, alphanumeric and underscores only)
    """
    # Remove file extension if present
    name = re.sub(r"\.(csv|json|jsonl)$", "", name, flags=re.IGNORECASE)
    # Replace non-alphanumeric characters with underscores
    name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    # Ensure it starts with a letter (prepend 'table_' if it doesn't)
    if not name[0].isalpha():
        name = "table_" + name
    return name.lower()


def validate_identifier(identifier: str) -> bool:
    """
    Validate that an identifier (table/column name) is safe to use in SQL.

    Args:
        identifier: The identifier to validate

    Returns:
        True if valid, False otherwise
    """
    # Must start with letter or underscore
    if not identifier[0].isalpha() and identifier[0] != "_":
        return False
    # Can only contain alphanumeric and underscores
    return re.match(r"^[a-zA-Z0-9_]+$", identifier)


def flatten_json_record(
    record: dict[str, Any], parent_key: str = "", delimiter: str = NESTED_FIELD_DELIMITER
) -> dict[str, Any]:
    """
    Recursively flatten a nested JSON object.

    Nested objects are flattened using a delimiter (default: '__').
    Arrays are flattened by creating separate columns with index notation.

    Examples:
        {"user": {"name": "John"}} -> {"user__name": "John"}
        {"tags": ["python", "data"]} -> {"tags__0": "python", "tags__1": "data"}
        {"user": {"profile": {"age": 30}}} -> {"user__profile__age": 30}

    Args:
        record: The JSON object to flatten
        parent_key: The parent key path (used in recursion)
        delimiter: Delimiter to use for concatenating keys

    Returns:
        Flattened dictionary with no nested structures
    """
    items = []

    for key, value in record.items():
        # Build the new key with parent path
        new_key = f"{parent_key}{delimiter}{key}" if parent_key else key

        if isinstance(value, dict):
            # Recursively flatten nested objects
            if value:  # Non-empty dict
                items.extend(flatten_json_record(value, new_key, delimiter).items())
            else:  # Empty dict
                items.append((new_key, None))
        elif isinstance(value, list):
            # Flatten arrays with index notation
            if value:  # Non-empty list
                for i, item in enumerate(value):
                    array_key = f"{new_key}{delimiter}{i}"
                    if isinstance(item, dict):
                        # Array of objects - flatten each object
                        items.extend(flatten_json_record(item, array_key, delimiter).items())
                    else:
                        # Array of primitives
                        items.append((array_key, item))
            else:  # Empty list
                items.append((new_key, None))
        else:
            # Primitive value (string, number, boolean, null)
            items.append((new_key, value))

    return dict(items)


def infer_jsonl_schema(jsonl_content: bytes) -> set[str]:
    """
    Infer the complete schema from a JSONL file by scanning all records.

    This function performs a first pass through the JSONL file to discover
    all possible field names across all records. This ensures that when we
    create the SQLite table, we have all columns even if some records don't
    have all fields.

    Args:
        jsonl_content: Raw bytes of the JSONL file

    Returns:
        Set of all field names (flattened) found across all records
    """
    schema_fields = set()
    content_str = jsonl_content.decode("utf-8")

    for line_num, line in enumerate(content_str.strip().split("\n"), start=1):
        line = line.strip()
        if not line:
            continue

        try:
            record = json.loads(line)
            flattened = flatten_json_record(record)
            schema_fields.update(flattened.keys())
        except json.JSONDecodeError as e:
            print(f"Warning: Skipping malformed JSON on line {line_num}: {e}")
            continue

    return schema_fields


def convert_jsonl_to_sqlite(jsonl_content: bytes, table_name: str) -> dict[str, Any]:
    """
    Convert JSONL content to a SQLite table.

    This function:
    1. Sanitizes the table name
    2. Infers the schema by scanning all records
    3. Flattens all records (handling nested objects and arrays)
    4. Fills missing fields with None for consistent schema
    5. Creates a pandas DataFrame
    6. Writes to SQLite database
    7. Returns metadata about the created table

    Args:
        jsonl_content: Raw bytes of the JSONL file
        table_name: Desired table name (will be sanitized)

    Returns:
        Dictionary containing:
            - table_name: Sanitized table name
            - row_count: Number of rows imported
            - schema: Dictionary of column names and types
            - sample_data: First 5 rows as list of dicts

    Raises:
        ValueError: If JSONL file is empty or has no valid records
    """
    # Sanitize table name
    sanitized_table_name = sanitize_table_name(table_name)

    # First pass: infer schema
    all_fields = infer_jsonl_schema(jsonl_content)

    if not all_fields:
        raise ValueError("JSONL file contains no valid records")

    # Second pass: parse and flatten all records
    records = []
    content_str = jsonl_content.decode("utf-8")

    for _line_num, line in enumerate(content_str.strip().split("\n"), start=1):
        line = line.strip()
        if not line:
            continue

        try:
            record = json.loads(line)
            flattened = flatten_json_record(record)

            # Ensure all fields are present (fill missing with None)
            complete_record = {field: flattened.get(field) for field in all_fields}
            records.append(complete_record)
        except json.JSONDecodeError:
            # Already warned in schema inference pass
            continue

    if not records:
        raise ValueError("JSONL file contains no valid records")

    # Convert to pandas DataFrame
    df = pd.DataFrame(records)

    # Clean column names (lowercase, replace spaces and hyphens with underscores)
    df.columns = [col.lower().replace(" ", "_").replace("-", "_") for col in df.columns]

    # Connect to SQLite database (in-memory for this example, but could be file-based)
    # For a real application, you'd use a persistent database file
    conn = sqlite3.connect(":memory:")

    # Write DataFrame to SQLite
    df.to_sql(sanitized_table_name, conn, if_exists="replace", index=False)

    # Get schema information
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({sanitized_table_name})")
    schema_info = cursor.fetchall()
    schema = {col[1]: col[2] for col in schema_info}  # {column_name: type}

    # Get sample data (first 5 rows)
    cursor.execute(f"SELECT * FROM {sanitized_table_name} LIMIT 5")
    sample_rows = cursor.fetchall()
    column_names = [desc[0] for desc in cursor.description]
    sample_data = [dict(zip(column_names, row, strict=False)) for row in sample_rows]

    # Get row count
    row_count = len(df)

    conn.close()

    return {
        "table_name": sanitized_table_name,
        "row_count": row_count,
        "schema": schema,
        "sample_data": sample_data,
    }


def convert_csv_to_sqlite(csv_content: bytes, table_name: str) -> dict[str, Any]:
    """
    Convert CSV content to a SQLite table.

    Args:
        csv_content: Raw bytes of the CSV file
        table_name: Desired table name (will be sanitized)

    Returns:
        Dictionary containing table metadata
    """
    sanitized_table_name = sanitize_table_name(table_name)

    # Read CSV into DataFrame
    df = pd.read_csv(io.BytesIO(csv_content))

    # Clean column names
    df.columns = [col.lower().replace(" ", "_").replace("-", "_") for col in df.columns]

    # Connect to SQLite
    conn = sqlite3.connect(":memory:")
    df.to_sql(sanitized_table_name, conn, if_exists="replace", index=False)

    # Get metadata
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({sanitized_table_name})")
    schema_info = cursor.fetchall()
    schema = {col[1]: col[2] for col in schema_info}

    cursor.execute(f"SELECT * FROM {sanitized_table_name} LIMIT 5")
    sample_rows = cursor.fetchall()
    column_names = [desc[0] for desc in cursor.description]
    sample_data = [dict(zip(column_names, row, strict=False)) for row in sample_rows]

    row_count = len(df)
    conn.close()

    return {
        "table_name": sanitized_table_name,
        "row_count": row_count,
        "schema": schema,
        "sample_data": sample_data,
    }


def convert_json_to_sqlite(json_content: bytes, table_name: str) -> dict[str, Any]:
    """
    Convert JSON array content to a SQLite table.

    Args:
        json_content: Raw bytes of the JSON file (must be an array)
        table_name: Desired table name (will be sanitized)

    Returns:
        Dictionary containing table metadata
    """
    sanitized_table_name = sanitize_table_name(table_name)

    # Parse JSON
    data = json.loads(json_content.decode("utf-8"))

    if not isinstance(data, list):
        raise ValueError("JSON file must contain an array of objects")

    # Convert to DataFrame
    df = pd.DataFrame(data)

    # Clean column names
    df.columns = [col.lower().replace(" ", "_").replace("-", "_") for col in df.columns]

    # Connect to SQLite
    conn = sqlite3.connect(":memory:")
    df.to_sql(sanitized_table_name, conn, if_exists="replace", index=False)

    # Get metadata
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({sanitized_table_name})")
    schema_info = cursor.fetchall()
    schema = {col[1]: col[2] for col in schema_info}

    cursor.execute(f"SELECT * FROM {sanitized_table_name} LIMIT 5")
    sample_rows = cursor.fetchall()
    column_names = [desc[0] for desc in cursor.description]
    sample_data = [dict(zip(column_names, row, strict=False)) for row in sample_rows]

    row_count = len(df)
    conn.close()

    return {
        "table_name": sanitized_table_name,
        "row_count": row_count,
        "schema": schema,
        "sample_data": sample_data,
    }
