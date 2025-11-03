# Bug: Execute SQL Tool Crashes and LLM Schema Awareness Issues

## Bug Description
The `execute_sql` tool in the LLM chat interface has two critical issues:

1. **Tool crashes when LLM uses incorrect schema**: The LLM attempts to query non-existent columns (e.g., "address" in contacts table) causing SQLAlchemy errors and tool crashes
2. **LLM has no knowledge of database schema**: The LLM system prompt provides no information about the actual database structure, table names, or column names, leading to invalid SQL queries

The specific error from the logs shows:
```
Error executing SQL: (sqlite3.OperationalError) no such column: address
[SQL: SELECT id, name, email, phone, address, tags, notes FROM contacts ORDER BY RANDOM() LIMIT 3;]
```

The LLM incorrectly assumes an "address" column exists in the contacts table, but according to the actual schema in `models.py`, the contacts table does not have an "address" column.

## Problem Statement
The execute_sql tool fails when the LLM generates SQL queries that reference non-existent columns or incorrect table structures. The root cause is that the LLM has no knowledge of the actual database schema and makes assumptions about table structure that are incorrect.

## Solution Statement
Implement two complementary fixes:

1. **Improve error handling**: Make the execute_sql tool more robust by providing better error messages and schema guidance when SQL fails
2. **Provide schema information**: Add database schema information to the LLM system prompt so it knows the actual table structure before generating SQL queries

## Steps to Reproduce
1. Start the TUI: `python -m prt_src`
2. Navigate to Chat screen
3. Send a message like "I would like you to select 3 contacts at random from my contact db and list all their data"
4. The LLM will attempt to use execute_sql with a query that references non-existent columns
5. The tool crashes with SQLAlchemy operational error

## Root Cause Analysis
1. **No schema awareness**: The LLM system prompt in `prt_src/llm_ollama.py` (lines 1005-1194) contains extensive tool documentation but no database schema information
2. **Poor error handling**: The `execute_sql` tool in `prt_src/api.py` (lines 161-205) returns raw SQLAlchemy errors without schema guidance
3. **Assumption mismatch**: The LLM assumes common database columns like "address" exist, but the actual schema only has: id, name, first_name, last_name, email, phone, profile_image fields

## Relevant Files
Use these files to fix the bug:

- **`prt_src/llm_ollama.py`**: Contains the system prompt that needs schema information added
  - Lines 1005-1194: System prompt creation method that needs database schema documentation
  - Lines 559-581: execute_sql tool definition that needs better error handling guidance

- **`prt_src/api.py`**: Contains execute_sql method that needs better error handling
  - Lines 161-205: execute_sql method that needs to provide schema information on errors
  - Lines 200-205: Current error handling that should be enhanced

- **`prt_src/models.py`**: Contains the actual database schema that needs to be documented
  - Lines 28-78: Contact model with actual column definitions
  - Lines 152-177: Tag model
  - Lines 179-205: Note model
  - Lines 207-230: ContactMetadata model

### New Files
- **`prt_src/schema_info.py`**: New module to generate schema documentation for the LLM

## Step by Step Tasks

### Create Schema Documentation Module
- Create `prt_src/schema_info.py` to generate database schema information
- Add function to extract table names, column names, and types from SQLAlchemy models
- Add function to format schema information for LLM consumption
- Include relationship information and table descriptions

### Enhance LLM System Prompt with Schema Information
- Modify `_create_system_prompt()` method in `prt_src/llm_ollama.py`
- Add database schema section to the system prompt using schema_info module
- Include table definitions, column names, data types, and relationships
- Add guidance on proper SQL query formation for the PRT schema

### Improve Execute SQL Error Handling
- Enhance the `execute_sql` method in `prt_src/api.py`
- When SQL errors occur, detect schema-related issues (column not found, table not found)
- Provide helpful error messages that include available columns/tables
- Add schema information to error responses to guide the LLM

### Add Schema Validation Helper
- Add method to validate SQL queries before execution
- Check if referenced tables and columns exist in the schema
- Provide suggestions for correct column names when mismatches are detected

### Update Execute SQL Tool Documentation
- Enhance the execute_sql tool description in `prt_src/llm_ollama.py`
- Add examples of correct SQL queries for the PRT schema
- Include common patterns and available tables/columns

### Add Tests for Schema Integration
- Create tests to verify schema information is correctly provided to LLM
- Test execute_sql error handling with invalid schemas
- Test that LLM can generate valid SQL with schema information

### Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `python -m prt_src` - Start TUI and verify no startup errors
- Navigate to Chat screen in TUI
- Send message: "Show me the database schema" - Should return schema information
- Send message: "Select 3 random contacts with all their data" - Should generate valid SQL
- Send message: "Find contacts without email addresses" - Should use correct column names
- `./prt_env/bin/pytest tests/ -v` - Run all tests to ensure no regressions
- `./prt_env/bin/pytest tests/test_api.py -v` - Test API functionality including execute_sql
- `./prt_env/bin/pytest tests/test_llm_*.py -v` - Test LLM integration if tests exist

## Notes
- The fix should maintain backward compatibility with existing functionality
- Schema information should be generated dynamically from the actual models to stay in sync
- Error messages should be helpful to both users and the LLM for learning
- Consider adding a dedicated "show_schema" tool as an alternative to embedding schema in system prompt
- The solution should prevent similar issues with future schema changes by making schema awareness automatic