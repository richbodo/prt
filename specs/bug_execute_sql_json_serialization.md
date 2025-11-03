# Bug: Execute SQL Tool JSON Serialization Error with Profile Images

## Bug Description
When using the LLM chat interface to execute SQL queries that return contacts with profile images, the execute_sql tool crashes with a TypeError: "Object of type bytes is not JSON serializable". This occurs because profile images are stored as binary data (LargeBinary/BLOB) in the database, and the enhanced logging code attempts to serialize the entire tool result to JSON without handling the binary data properly.

The error manifests when:
- User asks the LLM to find contacts with profile images
- LLM generates SQL query like `SELECT * FROM contacts WHERE profile_image IS NOT NULL`
- execute_sql tool executes successfully and returns results with binary profile_image data
- The logging code at line 1339 in llm_ollama.py attempts `json.dumps(tool_result)` without a custom serializer
- Python's json module cannot serialize bytes objects, causing the crash

Expected behavior: The execute_sql tool should complete successfully and log the results with binary data appropriately handled (e.g., showing "<binary data: 123456 bytes>" instead of raw bytes).

Actual behavior: The tool crashes with a JSON serialization error, preventing users from querying contacts with profile images.

## Problem Statement
The enhanced logging code added for the execute_sql tool does not use the existing custom JSON serializer that handles bytes objects, causing crashes when SQL queries return binary profile image data.

## Solution Statement
Use the existing `_json_serializer` method in the `json.dumps()` call for execute_sql tool logging. This method already exists in the class and properly handles bytes objects by converting them to a readable string representation like "<binary data: N bytes>".

## Steps to Reproduce
1. Set up PRT development environment: `source ./init.sh`
2. Launch the TUI: `python -m prt_src`
3. Navigate to chat mode (press 'c' from home screen)
4. Send a message asking to find contacts with profile images, such as:
   - "Show me all contacts that have profile images"
   - "Find contacts where profile_image is not null"
5. The LLM will generate and execute SQL that selects profile_image column
6. The execute_sql tool will crash with JSON serialization error

## Root Cause Analysis
The root cause is in `/Users/richardbodo/src/prt/prt_src/llm_ollama.py` at line 1339:

```python
logger.info(f"[LLM] Tool {tool_name} FULL result: {json.dumps(tool_result, indent=2)}")
```

This code was recently added to provide better debugging for execute_sql tools but lacks the `default` parameter that handles non-JSON-serializable objects. The same file already has:

1. A proper `_json_serializer` method (lines 1486-1501) that handles bytes objects
2. Correct usage of this serializer in other locations (line 1360)

The profile images are stored as `LargeBinary` columns in the database (models.py line 39), which SQLAlchemy returns as Python bytes objects. When the execute_sql API method converts SQL results to dictionaries, these bytes objects are included directly in the result structure, making the entire result non-JSON-serializable.

## Relevant Files
Use these files to fix the bug:

- `/Users/richardbodo/src/prt/prt_src/llm_ollama.py` - Contains the buggy logging code (line 1339) and the existing _json_serializer method (lines 1486-1501)
- `/Users/richardbodo/src/prt/prt_src/models.py` - Defines the Contact model with profile_image as LargeBinary (line 39), showing why bytes objects are returned
- `/Users/richardbodo/src/prt/prt_src/api.py` - Contains execute_sql method that returns dictionary results including bytes data (lines 191-196)
- `/Users/richardbodo/src/prt/tests/test_execute_sql.py` - Existing tests for execute_sql functionality that should be extended
- `/Users/richardbodo/src/prt/tests/integration/test_llm_phase4_tools.py` - Integration tests for LLM tools that should be extended

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Fix the JSON Serialization Issue
- Modify line 1339 in `/Users/richardbodo/src/prt/prt_src/llm_ollama.py` to use the existing `_json_serializer` method
- Change from: `json.dumps(tool_result, indent=2)`
- Change to: `json.dumps(tool_result, indent=2, default=self._json_serializer)`
- This is a one-line fix that uses the existing, tested serializer

### Step 2: Add Test Coverage for Profile Image Queries
- Create a test in `/Users/richardbodo/src/prt/tests/test_execute_sql.py` that verifies execute_sql works with profile image data
- Test should execute SQL that returns contacts with profile images
- Verify the result contains the expected number of contacts and that profile_image data is handled correctly
- Test should ensure no JSON serialization errors occur

### Step 3: Add Integration Test for LLM Tool Usage
- Add a test in `/Users/richardbodo/src/prt/tests/integration/test_llm_phase4_tools.py` that tests the execute_sql tool via the LLM interface
- Test should simulate the exact user scenario: asking LLM to find contacts with profile images
- Verify the tool executes successfully and logs properly without crashes
- Test should use the existing test fixtures that include contacts with profile images

### Step 4: Verify Existing Serializer Behavior
- Review the `_json_serializer` method to ensure it handles bytes objects correctly
- Confirm it returns a readable string representation like "<binary data: N bytes>"
- Ensure the serializer is robust and doesn't cause other issues

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `source ./init.sh` - Set up the development environment
- `./prt_env/bin/pytest tests/test_execute_sql.py -v` - Run execute_sql tests to ensure basic functionality works
- `./prt_env/bin/pytest tests/integration/test_llm_phase4_tools.py -v` - Run LLM integration tests to ensure tool calling works
- `./prt_env/bin/pytest tests/ -k "profile_image" -v` - Run any tests specifically related to profile images
- `python -m prt_src --debug` - Launch TUI with debug data to test manually
- Manual test: In chat mode, ask "Show me all contacts that have profile images" and verify it completes successfully
- `./prt_env/bin/ruff check prt_src/ tests/` - Ensure code quality standards are maintained
- `./prt_env/bin/black prt_src/ tests/` - Ensure code formatting is correct

## Notes
- This is a minimal fix that leverages existing, tested infrastructure (_json_serializer method)
- The serializer converts bytes objects to human-readable strings like "<binary data: 123456 bytes>"
- This fix maintains the debugging functionality while preventing crashes
- The existing serializer is already used correctly in other parts of the codebase (line 1360)
- Profile images are typically 50-500KB each, so the serializer's byte count representation is useful for debugging
- No new dependencies are required - this uses existing code
- The fix is surgical and doesn't change the core execute_sql functionality, only the logging