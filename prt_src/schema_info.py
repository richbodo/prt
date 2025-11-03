"""
Schema Information Module for PRT

This module provides functionality to extract and format database schema
information for LLM consumption, enabling the LLM to generate correct SQL
queries by understanding the actual table structure.
"""

import inspect
import re
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

from sqlalchemy import Column
from sqlalchemy.sql.sqltypes import TypeEngine

from .models import Contact
from .models import ContactMetadata
from .models import ContactRelationship
from .models import Note
from .models import RelationshipType
from .models import Tag


class SchemaInfoGenerator:
    """Generates schema information for the PRT database."""

    def __init__(self):
        """Initialize the schema info generator."""
        self.models = [Contact, Tag, Note, ContactMetadata, ContactRelationship, RelationshipType]

    def get_column_info(self, column: Column) -> Dict[str, Any]:
        """Extract information about a database column.

        Args:
            column: SQLAlchemy Column object

        Returns:
            Dictionary with column information
        """
        info = {
            "name": column.name,
            "type": self._get_type_name(column.type),
            "nullable": column.nullable,
            "primary_key": column.primary_key,
            "foreign_key": None,
            "description": None,
        }

        # Check for foreign key relationships
        if column.foreign_keys:
            fk = list(column.foreign_keys)[0]
            info["foreign_key"] = str(fk.column)

        # Add type-specific information
        if hasattr(column.type, "length") and column.type.length:
            info["max_length"] = column.type.length

        return info

    def _get_type_name(self, column_type: TypeEngine) -> str:
        """Get a human-readable type name for a column type.

        Args:
            column_type: SQLAlchemy column type

        Returns:
            Human-readable type name
        """
        type_mapping = {
            "INTEGER": "integer",
            "VARCHAR": "text",
            "TEXT": "text",
            "BOOLEAN": "boolean",
            "DATE": "date",
            "DATETIME": "datetime",
            "BLOB": "binary_data",
        }

        type_str = str(column_type).upper()
        for sql_type, readable_type in type_mapping.items():
            if sql_type in type_str:
                return readable_type

        return str(column_type).lower()

    def get_table_info(self, model_class) -> Dict[str, Any]:
        """Extract information about a database table from SQLAlchemy model.

        Args:
            model_class: SQLAlchemy model class

        Returns:
            Dictionary with table information
        """
        table_name = model_class.__tablename__

        # Get columns information
        columns = []
        for column_name in model_class.__table__.columns:
            column = model_class.__table__.columns[column_name]
            columns.append(self.get_column_info(column))

        # Get relationships information
        relationships = []
        for attr_name in dir(model_class):
            attr = getattr(model_class, attr_name, None)
            if hasattr(attr, "property") and hasattr(attr.property, "mapper"):
                # This is a relationship
                relationship_info = {
                    "name": attr_name,
                    "target_table": attr.property.mapper.class_.__tablename__,
                    "type": "one_to_many" if attr.property.uselist else "many_to_one",
                }
                relationships.append(relationship_info)

        # Get table documentation from docstring
        doc = inspect.getdoc(model_class) or f"{table_name.title()} table"

        return {
            "table_name": table_name,
            "description": doc,
            "columns": columns,
            "relationships": relationships,
        }

    def get_schema_summary(self) -> Dict[str, Any]:
        """Get a complete summary of the database schema.

        Returns:
            Dictionary with complete schema information
        """
        tables = []
        for model_class in self.models:
            tables.append(self.get_table_info(model_class))

        return {"database_type": "SQLite", "tables": tables, "total_tables": len(tables)}

    def format_schema_for_llm(self) -> str:
        """Format schema information for LLM consumption.

        Returns:
            Formatted string with schema information for LLM
        """
        schema = self.get_schema_summary()

        output = []
        output.append("## PRT DATABASE SCHEMA")
        output.append("")
        output.append(f"**Database Type**: {schema['database_type']}")
        output.append(f"**Total Tables**: {schema['total_tables']}")
        output.append("")

        for table in schema["tables"]:
            output.append(f"### Table: `{table['table_name']}`")
            output.append(f"**Description**: {table['description']}")
            output.append("")
            output.append("**Columns**:")

            for col in table["columns"]:
                col_desc = f"- `{col['name']}` ({col['type']})"

                # Add special context for profile image columns
                if col["name"] == "profile_image":
                    col_desc += " - **CONTACT PHOTO/AVATAR** (50-500KB binary data)"
                elif col["name"] == "profile_image_filename":
                    col_desc += " - **PHOTO FILENAME** (original image filename)"
                elif col["name"] == "profile_image_mime_type":
                    col_desc += " - **PHOTO FORMAT** (e.g., 'image/jpeg', 'image/png')"

                if col["primary_key"]:
                    col_desc += " - **PRIMARY KEY**"
                if col["foreign_key"]:
                    col_desc += f" - **FOREIGN KEY** → {col['foreign_key']}"
                if not col["nullable"]:
                    col_desc += " - **NOT NULL**"
                if col.get("max_length"):
                    col_desc += f" - **MAX LENGTH**: {col['max_length']}"

                output.append(col_desc)

            if table["relationships"]:
                output.append("")
                output.append("**Relationships**:")
                for rel in table["relationships"]:
                    output.append(f"- `{rel['name']}` → {rel['target_table']} ({rel['type']})")

            output.append("")

        # Add SQL query examples
        output.append("## COMMON SQL QUERY PATTERNS")
        output.append("")
        output.append("**Basic Contact Queries**:")
        output.append("```sql")
        output.append("-- Get all contacts")
        output.append("SELECT id, name, email, phone FROM contacts;")
        output.append("")
        output.append("-- Find contacts by name")
        output.append("SELECT * FROM contacts WHERE name LIKE '%John%';")
        output.append("")
        output.append("-- Get contacts without email")
        output.append("SELECT id, name, phone FROM contacts WHERE email IS NULL OR email = '';")
        output.append("")
        output.append("-- Random contacts")
        output.append("SELECT id, name, email, phone FROM contacts ORDER BY RANDOM() LIMIT 3;")
        output.append("```")
        output.append("")

        output.append("**Contact Tags and Notes** (via relationships):")
        output.append("```sql")
        output.append("-- Get all tags")
        output.append("SELECT id, name FROM tags;")
        output.append("")
        output.append("-- Get contacts with specific tag")
        output.append("SELECT c.name, t.name as tag_name")
        output.append("FROM contacts c")
        output.append("JOIN contact_metadata cm ON c.id = cm.contact_id")
        output.append("JOIN metadata_tags mt ON cm.id = mt.metadata_id")
        output.append("JOIN tags t ON mt.tag_id = t.id")
        output.append("WHERE t.name = 'family';")
        output.append("```")
        output.append("")

        output.append("**Profile Images (Contact Photos/Avatars)**:")
        output.append("```sql")
        output.append("-- Find contacts WITH profile images (contact photos)")
        output.append(
            "SELECT id, name, email FROM contacts WHERE profile_image IS NOT NULL LIMIT 50;"
        )
        output.append("")
        output.append("-- Count contacts with profile images")
        output.append("SELECT COUNT(*) FROM contacts WHERE profile_image IS NOT NULL;")
        output.append("")
        output.append("-- Get profile image metadata (filename, type) without binary data")
        output.append("SELECT id, name, profile_image_filename, profile_image_mime_type")
        output.append("FROM contacts WHERE profile_image IS NOT NULL;")
        output.append("")
        output.append("-- PERFORMANCE: Exclude profile_image from SELECT * for large datasets")
        output.append("-- ❌ SLOW: SELECT * FROM contacts WHERE profile_image IS NOT NULL;")
        output.append(
            "-- ✅ FAST: SELECT id, name, email, phone FROM contacts WHERE profile_image IS NOT NULL;"
        )
        output.append("```")
        output.append("")

        output.append("**PERFORMANCE OPTIMIZATION (Essential for 1000+ contacts)**:")
        output.append("")
        output.append("⚡ **Profile Images contain binary photo data (50-500KB each)**")
        output.append("- Always use `LIMIT` when querying contacts with images")
        output.append("- Exclude `profile_image` column from SELECT unless specifically needed")
        output.append("- Use `COUNT(*)` to check result size before full queries")
        output.append("- Prefer indexed columns: `name`, `email`, `created_at`")
        output.append("")

        output.append("**COMMON USER REQUESTS & OPTIMAL QUERIES**:")
        output.append("")
        output.append('🔍 **"Find contacts with profile images"**')
        output.append("```sql")
        output.append(
            "SELECT id, name, email FROM contacts WHERE profile_image IS NOT NULL LIMIT 50;"
        )
        output.append("```")
        output.append("")
        output.append('🔍 **"Show me contacts without photos"**')
        output.append("```sql")
        output.append("SELECT id, name, email FROM contacts WHERE profile_image IS NULL LIMIT 50;")
        output.append("```")
        output.append("")
        output.append('🔍 **"How many contacts have profile pictures?"**')
        output.append("```sql")
        output.append(
            "SELECT COUNT(*) as contacts_with_photos FROM contacts WHERE profile_image IS NOT NULL;"
        )
        output.append("```")
        output.append("")
        output.append('🔍 **"Make a directory of contacts with images"**')
        output.append("```sql")
        output.append("-- First get contact info (not binary image data)")
        output.append("SELECT id, name, email, phone, profile_image_filename")
        output.append("FROM contacts WHERE profile_image IS NOT NULL")
        output.append("ORDER BY name LIMIT 100;")
        output.append("```")
        output.append("")

        output.append(
            "**CRITICAL**: Only use columns that exist in the schema above. Common mistakes:"
        )
        output.append("- ❌ `address` column does NOT exist in contacts table")
        output.append("- ❌ Direct `tags` or `notes` columns do NOT exist (use relationships)")
        output.append("- ✅ Use `name`, `email`, `phone`, `first_name`, `last_name` for contacts")
        output.append("- ✅ Use relationship joins to access tags and notes")

        return "\n".join(output)

    def get_table_names(self) -> List[str]:
        """Get list of all table names in the schema.

        Returns:
            List of table names
        """
        return [model.__tablename__ for model in self.models]

    def get_table_columns(self, table_name: str) -> List[str]:
        """Get list of column names for a specific table.

        Args:
            table_name: Name of the table

        Returns:
            List of column names, or empty list if table not found
        """
        for model in self.models:
            if model.__tablename__ == table_name:
                return list(model.__table__.columns.keys())
        return []

    def validate_column_exists(self, table_name: str, column_name: str) -> bool:
        """Check if a column exists in a table.

        Args:
            table_name: Name of the table
            column_name: Name of the column

        Returns:
            True if column exists, False otherwise
        """
        columns = self.get_table_columns(table_name)
        return column_name in columns

    def suggest_similar_columns(self, table_name: str, invalid_column: str) -> List[str]:
        """Suggest similar column names for a table when an invalid column is used.

        Args:
            table_name: Name of the table
            invalid_column: The invalid column name that was attempted

        Returns:
            List of suggested column names
        """
        columns = self.get_table_columns(table_name)
        suggestions = []

        # Simple similarity based on substring matching
        invalid_lower = invalid_column.lower()
        for col in columns:
            col_lower = col.lower()
            # Check for partial matches
            if (
                invalid_lower in col_lower
                or col_lower in invalid_lower
                or invalid_lower == "fname"
                and "first_name" in col_lower
                or invalid_lower == "lname"
                and "last_name" in col_lower
                or invalid_lower == "mail"
                and "email" in col_lower
            ):
                suggestions.append(col)

        return suggestions

    def parse_sql_tables_and_columns(self, sql: str) -> Tuple[List[str], List[str]]:
        """Parse SQL to extract referenced tables and columns.

        Args:
            sql: SQL query string

        Returns:
            Tuple of (table_names, column_names) found in the SQL
        """
        sql_upper = sql.upper()
        tables = []
        columns = []

        # Extract table names from FROM and JOIN clauses
        from_pattern = r"\bFROM\s+(\w+)"
        join_pattern = r"\bJOIN\s+(\w+)"

        tables.extend(re.findall(from_pattern, sql_upper))
        tables.extend(re.findall(join_pattern, sql_upper))

        # Extract column names from SELECT clause (basic parsing)
        select_pattern = r"SELECT\s+(.*?)\s+FROM"
        select_match = re.search(select_pattern, sql_upper, re.DOTALL)
        if select_match:
            select_part = select_match.group(1)
            # Split by comma and clean up
            col_parts = [part.strip() for part in select_part.split(",")]
            for part in col_parts:
                # Remove table prefix (table.column -> column)
                if "." in part:
                    part = part.split(".")[-1]
                # Remove AS aliases
                if " AS " in part:
                    part = part.split(" AS ")[0]
                # Skip functions and special keywords
                if not any(func in part for func in ["COUNT", "MAX", "MIN", "AVG", "SUM", "*"]):
                    columns.append(part.strip())

        return tables, columns


# Singleton instance for easy access
schema_generator = SchemaInfoGenerator()


def get_schema_for_llm() -> str:
    """Get formatted schema information for LLM.

    Returns:
        Formatted schema string for LLM consumption
    """
    return schema_generator.format_schema_for_llm()


def validate_sql_schema(sql: str) -> Dict[str, Any]:
    """Validate SQL query against the database schema.

    Args:
        sql: SQL query to validate

    Returns:
        Dictionary with validation results
    """
    result = {"valid": True, "errors": [], "warnings": [], "suggestions": []}

    try:
        tables, columns = schema_generator.parse_sql_tables_and_columns(sql)

        # Validate tables
        valid_tables = schema_generator.get_table_names()
        for table in tables:
            if table.lower() not in [t.lower() for t in valid_tables]:
                result["valid"] = False
                result["errors"].append(f"Table '{table}' does not exist")
                result["suggestions"].append(f"Available tables: {', '.join(valid_tables)}")

        # Validate columns against all referenced tables
        for table in tables:
            if table.lower() in [t.lower() for t in valid_tables]:
                # Find the correct case for the table name
                correct_table = next(t for t in valid_tables if t.lower() == table.lower())
                table_columns = schema_generator.get_table_columns(correct_table)

                for column in columns:
                    # Convert to lowercase for comparison
                    column_lower = column.lower()
                    if not schema_generator.validate_column_exists(correct_table, column_lower):
                        result["valid"] = False
                        result["errors"].append(
                            f"Column '{column_lower}' does not exist in table '{correct_table}'"
                        )

                        # Suggest similar columns
                        suggestions = schema_generator.suggest_similar_columns(
                            correct_table, column_lower
                        )
                        if suggestions:
                            result["suggestions"].append(
                                f"Similar columns in {correct_table}: {', '.join(suggestions)}"
                            )
                        else:
                            result["suggestions"].append(
                                f"Available columns in {correct_table}: {', '.join(table_columns)}"
                            )

    except Exception as e:
        result["valid"] = False
        result["errors"].append(f"Error parsing SQL: {str(e)}")

    return result
