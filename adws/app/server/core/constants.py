"""
Configuration constants for the Natural Language SQL Interface application.

This module centralizes configuration values to ensure consistency across the application
and to provide a single source of truth for important settings.
"""

# Delimiter used for flattening nested objects in JSONL files
# Example: {"user": {"name": "John"}} becomes {"user__name": "John"}
NESTED_FIELD_DELIMITER = "__"

# Delimiter used for array indices in JSONL files (same as nested field delimiter for consistency)
# Example: {"tags": ["python", "data"]} becomes {"tags__0": "python", "tags__1": "data"}
ARRAY_INDEX_DELIMITER = "__"

# List of accepted file extensions for upload
ACCEPTED_FILE_EXTENSIONS = [".csv", ".json", ".jsonl"]
