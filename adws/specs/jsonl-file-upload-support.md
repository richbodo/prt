# Feature: JSONL File Upload Support

## Feature Description
Add support for uploading JSONL (JSON Lines) files to the Natural Language SQL Interface application. JSONL files contain one JSON object per line and are commonly used for streaming data, logs, and large datasets. This feature will enable users to upload JSONL files alongside the existing CSV and JSON formats, with intelligent handling of nested fields and lists through a flattening strategy using configurable delimiters.

## User Story
As a data analyst or developer
I want to upload JSONL files containing structured data with nested objects and arrays
So that I can query complex data structures using natural language without manual data transformation

## Problem Statement
The application currently only supports CSV and JSON array formats for data uploads. Many real-world datasets, especially from APIs, logs, and streaming sources, are distributed in JSONL format where each line is a valid JSON object. Additionally, nested objects and arrays within these records cannot be handled by the flat table structure of SQLite without a transformation strategy. Users must currently convert JSONL files to JSON arrays or CSV manually before uploading, which is time-consuming and error-prone.

## Solution Statement
Implement JSONL file parsing that:
1. Reads the file line-by-line to handle large files efficiently
2. Scans the entire file first to discover all possible fields across all records (schema inference)
3. Flattens nested objects using a configurable delimiter (default: `__`) stored in a constants file
4. Flattens arrays by concatenating with index notation using the delimiter (e.g., `items__0`, `items__1`)
5. Creates a single SQLite table per JSONL file, similar to existing CSV/JSON uploads
6. Updates the UI to indicate JSONL support alongside CSV and JSON
7. Provides test JSONL files in the test directory for validation

## Relevant Files
Use these files to implement the feature:

- **app/server/core/file_processor.py** - Contains CSV and JSON file processing logic. Will add `convert_jsonl_to_sqlite()` function following the same pattern as existing converters. This is where the JSONL parsing, schema inference, and flattening logic will be implemented.

- **app/server/server.py:72-109** - The `/api/upload` endpoint that validates file types and routes to appropriate processors. Will update line 77 to accept `.jsonl` files and add routing logic for JSONL processing.

- **app/server/core/data_models.py** - Contains Pydantic models for API requests/responses. May need review to ensure `FileUploadResponse` model handles all JSONL-specific metadata appropriately.

- **app/client/index.html:79-83** - The file upload drop zone and file input that currently accept `.csv,.json`. Will update accept attribute to include `.jsonl` and update the display text to inform users of JSONL support.

- **app/client/src/main.ts:93-106** - The `handleFileUpload()` function that processes file uploads. No changes needed, but will verify error handling works correctly with JSONL files.

- **app/server/tests/test_sql_injection.py** - Existing test file for SQL security. Will add JSONL-specific security tests to ensure flattened column names are properly validated.

### New Files

- **app/server/core/constants.py** - New constants file to store configurable values:
  - `NESTED_FIELD_DELIMITER` = `"__"` (for concatenating nested object fields)
  - `ARRAY_INDEX_DELIMITER` = `"__"` (for array indices, same as nested fields)
  - Accepted file extensions list (to centralize configuration)

- **app/server/tests/assets/test_nested.jsonl** - Test file with nested objects to validate flattening logic. Contains records with nested objects like `{"user": {"name": "John", "profile": {"age": 30}}}`.

- **app/server/tests/assets/test_arrays.jsonl** - Test file with arrays to validate array flattening logic. Contains records with arrays like `{"id": 1, "tags": ["python", "data"], "items": [{"id": 1}, {"id": 2}]}`.

- **app/server/tests/assets/test_mixed.jsonl** - Test file with mixed nested objects and arrays to validate complex flattening scenarios.

- **app/server/tests/test_jsonl_processor.py** - Unit tests for JSONL processing functionality including:
  - Basic JSONL parsing
  - Nested object flattening
  - Array flattening with indices
  - Schema inference across multiple records
  - Error handling for malformed JSONL
  - Security validation of generated column names

## Implementation Plan

### Phase 1: Foundation
Create the constants file to centralize configuration for delimiters and file type support. This allows the delimiter to be easily updated across the entire application and provides a single source of truth for accepted file extensions. Implement the core JSONL parsing utility that handles line-by-line reading and JSON parsing with proper error handling.

### Phase 2: Core Implementation
Implement the schema inference algorithm that scans all records in the JSONL file to discover all possible fields. Build the field flattening logic for nested objects using the delimiter pattern (e.g., `user.name` becomes `user__name`). Implement array flattening logic that uses index notation with the delimiter (e.g., `tags[0]` becomes `tags__0`). Create the main `convert_jsonl_to_sqlite()` function that orchestrates parsing, flattening, and database insertion following the same pattern as existing CSV/JSON converters.

### Phase 3: Integration
Integrate JSONL processing into the upload endpoint by updating file type validation and adding routing logic. Update the client UI to accept `.jsonl` files and inform users of the new capability. Create comprehensive test files (nested objects, arrays, mixed scenarios) and implement unit tests to validate all functionality. Ensure security validation works correctly with flattened column names.

## Step by Step Tasks

### Step 1: Create Constants Configuration File
- Create `app/server/core/constants.py`
- Define `NESTED_FIELD_DELIMITER = "__"`
- Define `ARRAY_INDEX_DELIMITER = "__"` (same as nested field delimiter for consistency)
- Define `ACCEPTED_FILE_EXTENSIONS = [".csv", ".json", ".jsonl"]`
- Add docstring explaining the purpose of each constant
- Document that these delimiters are used for flattening nested structures in JSONL files

### Step 2: Implement JSONL Field Flattening Utilities
- In `app/server/core/file_processor.py`, add import for constants: `from .constants import NESTED_FIELD_DELIMITER, ARRAY_INDEX_DELIMITER`
- Create helper function `flatten_json_record(record: Dict[str, Any], parent_key: str = "", delimiter: str = NESTED_FIELD_DELIMITER) -> Dict[str, Any]`
- Implement recursive flattening logic:
  - For nested dicts: concatenate keys with delimiter (e.g., `user.name` → `user__name`)
  - For lists: create separate columns with index notation (e.g., `tags[0]` → `tags__0`, `tags[1]` → `tags__1`)
  - For primitive values: keep as-is
  - Handle edge cases: empty objects, null values, deeply nested structures
- Add comprehensive docstring with examples

### Step 3: Implement Schema Inference for JSONL
- In `app/server/core/file_processor.py`, create function `infer_jsonl_schema(jsonl_content: bytes) -> set`
- Parse JSONL content line by line
- For each line:
  - Parse JSON object
  - Flatten the record using `flatten_json_record()`
  - Collect all field names into a set
- Return the complete set of all possible field names across all records
- Handle errors for malformed JSON lines gracefully (log warning, skip line)
- Add docstring explaining the two-pass approach (schema inference, then data processing)

### Step 4: Implement JSONL to SQLite Conversion
- In `app/server/core/file_processor.py`, create function `convert_jsonl_to_sqlite(jsonl_content: bytes, table_name: str) -> Dict[str, Any]`
- Sanitize table name using existing `sanitize_table_name()` function
- Call `infer_jsonl_schema()` to get all possible fields
- Parse JSONL content line by line again:
  - For each line, flatten the record
  - Ensure all inferred fields are present (fill missing fields with `None`)
  - Collect flattened records into a list
- Convert list of flattened records to pandas DataFrame
- Clean column names using existing pattern: `df.columns = [col.lower().replace(' ', '_').replace('-', '_') for col in df.columns]`
- Write DataFrame to SQLite using `df.to_sql()` with `if_exists='replace'`
- Get schema, sample data, and row count using existing pattern (lines 134-162 from JSON converter)
- Return dictionary with table metadata matching existing converters
- Add comprehensive error handling with descriptive messages

### Step 5: Add Unit Tests for JSONL Processing
- Create `app/server/tests/test_jsonl_processor.py`
- Import necessary modules: `pytest`, `file_processor` functions, `constants`
- Test `flatten_json_record()`:
  - Test simple flat object (no flattening needed)
  - Test nested object (2 levels deep)
  - Test deeply nested object (3+ levels)
  - Test object with array of primitives
  - Test object with array of objects
  - Test mixed nested objects and arrays
  - Test edge cases: empty object, null values, empty arrays
- Test `infer_jsonl_schema()`:
  - Test single record
  - Test multiple records with same schema
  - Test multiple records with varying schemas (some fields missing)
  - Test with malformed line (should skip and continue)
- Test `convert_jsonl_to_sqlite()`:
  - Test basic JSONL file conversion
  - Test schema inference correctness
  - Test data integrity after flattening
  - Test table creation and metadata
- Run tests: `cd app/server && uv run pytest tests/test_jsonl_processor.py -v`

### Step 6: Create Test JSONL Files
- Create `app/server/tests/assets/test_nested.jsonl` with nested objects:
  ```jsonl
  {"id": 1, "user": {"name": "Alice", "profile": {"age": 30, "city": "NYC"}}, "status": "active"}
  {"id": 2, "user": {"name": "Bob", "profile": {"age": 25, "city": "LA"}}, "status": "inactive"}
  {"id": 3, "user": {"name": "Charlie"}, "status": "active"}
  ```
- Create `app/server/tests/assets/test_arrays.jsonl` with arrays:
  ```jsonl
  {"id": 1, "name": "Item A", "tags": ["python", "data", "ml"], "prices": [10.5, 20.0]}
  {"id": 2, "name": "Item B", "tags": ["javascript", "web"], "prices": [15.0]}
  {"id": 3, "name": "Item C", "tags": ["rust"], "prices": []}
  ```
- Create `app/server/tests/assets/test_mixed.jsonl` with complex nested structures:
  ```jsonl
  {"id": 1, "data": {"metrics": [{"name": "cpu", "value": 80}, {"name": "memory", "value": 60}]}, "timestamp": "2024-01-01"}
  {"id": 2, "data": {"metrics": [{"name": "cpu", "value": 90}], "extra": {"field": "value"}}, "timestamp": "2024-01-02"}
  ```
- Validate files are valid JSONL format (one JSON object per line)

### Step 7: Update Server Upload Endpoint
- In `app/server/server.py`, add import: `from core.file_processor import convert_csv_to_sqlite, convert_json_to_sqlite, convert_jsonl_to_sqlite`
- In `app/server/server.py`, add import: `from core.constants import ACCEPTED_FILE_EXTENSIONS`
- Update line 77 file validation to use constants: `if not any(file.filename.endswith(ext) for ext in ACCEPTED_FILE_EXTENSIONS):`
- Update line 77 error message: `raise HTTPException(400, f"Only {', '.join(ACCEPTED_FILE_EXTENSIONS)} files are supported")`
- Add JSONL routing logic after line 90:
  ```python
  elif file.filename.endswith('.jsonl'):
      result = convert_jsonl_to_sqlite(content, table_name)
  ```
- Test endpoint manually with curl or Postman to verify JSONL uploads work

### Step 8: Update Client UI for JSONL Support
- In `app/client/index.html`, update line 80-81:
  - Change text from `"Drag and drop .csv or .json files here"` to `"Drag and drop .csv, .json, or .jsonl files here"`
  - Update file input accept attribute from `accept=".csv,.json"` to `accept=".csv,.json,.jsonl"`
- Add a small informational note or tooltip explaining JSONL format
- Verify UI displays the updated file type information correctly

### Step 9: Add Integration Tests
- In `app/server/tests/test_jsonl_processor.py`, add integration tests:
  - Test full upload flow with `test_nested.jsonl`
  - Test full upload flow with `test_arrays.jsonl`
  - Test full upload flow with `test_mixed.jsonl`
  - Verify table creation in SQLite
  - Verify schema correctness (flattened column names)
  - Verify data integrity (values correctly placed in flattened columns)
  - Verify sample data returned matches expectations
- Test error scenarios:
  - Invalid JSONL (no valid JSON lines)
  - Empty file
  - File with only blank lines
  - File with mix of valid and invalid lines
- Run all tests: `cd app/server && uv run pytest tests/test_jsonl_processor.py -v`

### Step 10: Add Security Tests for JSONL
- In `app/server/tests/test_sql_injection.py`, add JSONL-specific security tests:
  - Test that flattened column names with special characters are properly sanitized
  - Test that nested field names containing SQL keywords are handled safely
  - Test that column names generated from array indices are validated
  - Test SQL injection attempts in JSONL field names
  - Test SQL injection attempts in JSONL field values
- Verify all security tests pass: `cd app/server && uv run pytest tests/test_sql_injection.py -v`

### Step 11: Test End-to-End JSONL Upload
- Start the development server: `cd /Users/richardbodo/src/tac/tac-4/adws && uv run scripts/start.sh` (with timeout if needed)
- Manually test JSONL upload through the UI:
  - Upload `test_nested.jsonl` and verify table creation
  - Upload `test_arrays.jsonl` and verify array flattening
  - Upload `test_mixed.jsonl` and verify complex structure handling
- Verify tables appear in the "Available Tables" section
- Test querying the uploaded JSONL data using natural language
- Verify sample data displays correctly with flattened column names
- Test error handling by uploading invalid JSONL file

### Step 12: Run Full Test Suite and Validation
- Run all server tests: `cd app/server && uv run pytest -v`
- Verify zero test failures and zero regressions
- Check that existing CSV and JSON uploads still work correctly
- Verify no breaking changes to existing functionality
- Review test coverage and add any missing edge cases

## Testing Strategy

### Unit Tests
- **Flattening Logic Tests** (`test_flatten_json_record()`):
  - Simple nested objects (2 levels)
  - Deeply nested objects (3+ levels)
  - Arrays of primitives (strings, numbers, booleans)
  - Arrays of objects
  - Mixed nested objects and arrays
  - Edge cases: empty objects, null values, empty arrays, very long field names

- **Schema Inference Tests** (`test_infer_jsonl_schema()`):
  - Single record (baseline)
  - Multiple records with identical schema
  - Multiple records with varying schemas (test union of all fields)
  - Records with completely different structures
  - Malformed lines (should be skipped without crashing)
  - Empty file
  - File with only whitespace

- **Conversion Tests** (`test_convert_jsonl_to_sqlite()`):
  - Basic JSONL with flat objects
  - JSONL with nested objects
  - JSONL with arrays
  - JSONL with mixed nested and array structures
  - Schema correctness (all columns present)
  - Data integrity (values in correct columns)
  - Metadata validation (table name, row count, schema dict)

### Integration Tests
- **Full Upload Flow**:
  - Upload `test_nested.jsonl` via API endpoint
  - Upload `test_arrays.jsonl` via API endpoint
  - Upload `test_mixed.jsonl` via API endpoint
  - Verify SQLite table exists with correct name
  - Verify schema matches flattened structure
  - Verify all rows imported correctly
  - Verify sample data returned correctly

- **Cross-Format Compatibility**:
  - Upload CSV, JSON, and JSONL files in sequence
  - Verify each creates separate table
  - Verify no interference between formats
  - Query each table successfully

- **UI Integration**:
  - Drag and drop JSONL file
  - Browse and select JSONL file
  - Verify success message displays
  - Verify table appears in tables list
  - Verify table is queryable

### Edge Cases
- **Malformed Data**:
  - JSONL file with invalid JSON on some lines
  - JSONL file with no valid JSON lines
  - Empty JSONL file
  - JSONL file with only whitespace lines
  - Mixed valid and invalid lines
  - Very large JSONL file (performance test)

- **Complex Nesting**:
  - 5+ levels of nesting
  - Arrays within arrays
  - Objects within arrays within objects
  - Null values at various nesting levels
  - Missing fields at various nesting levels
  - Field name collisions after flattening (e.g., `user_name` vs `user.name`)

- **Security**:
  - Field names with SQL keywords
  - Field names with special characters
  - Field names with injection attempts
  - Very long field names
  - Unicode characters in field names
  - Field values with SQL injection attempts

- **Column Name Conflicts**:
  - Test what happens when `user_name` and `user.name` both exist
  - Ensure sanitization handles collisions gracefully
  - Verify data integrity when collisions occur

## Acceptance Criteria
1. **Core Functionality**:
   - [ ] Users can upload `.jsonl` files through the UI (drag-drop or browse)
   - [ ] JSONL files are parsed line-by-line successfully
   - [ ] Schema inference correctly identifies all fields across all records
   - [ ] Nested objects are flattened using `__` delimiter (e.g., `user__name`)
   - [ ] Arrays are flattened with index notation using `__` delimiter (e.g., `tags__0`, `tags__1`)
   - [ ] One SQLite table is created per JSONL file
   - [ ] Table naming follows existing conventions (sanitized, lowercase, underscores)

2. **Data Integrity**:
   - [ ] All records from JSONL file are imported successfully
   - [ ] Flattened data maintains correct values in correct columns
   - [ ] Missing fields in some records are handled gracefully (NULL values)
   - [ ] Data types are inferred correctly by pandas

3. **Configuration**:
   - [ ] Delimiters (`__` for nested fields and arrays) are stored in `constants.py`
   - [ ] Delimiters can be easily updated in one place
   - [ ] Accepted file extensions are centralized in constants

4. **UI/UX**:
   - [ ] Upload modal text indicates `.jsonl` support alongside `.csv` and `.json`
   - [ ] File input accepts `.jsonl` files
   - [ ] Success message displays after successful JSONL upload
   - [ ] Uploaded JSONL tables appear in "Available Tables" section
   - [ ] Sample data displays correctly with flattened column names

5. **Testing**:
   - [ ] Three test JSONL files exist in `tests/assets/` directory
   - [ ] Test files cover nested objects, arrays, and mixed scenarios
   - [ ] Unit tests for flattening, schema inference, and conversion all pass
   - [ ] Integration tests for full upload flow pass
   - [ ] Security tests for JSONL-specific scenarios pass
   - [ ] All existing tests continue to pass (zero regressions)

6. **Security**:
   - [ ] Flattened column names are validated using existing `validate_identifier()` function
   - [ ] SQL injection attempts in field names are prevented
   - [ ] Table names are sanitized using existing `sanitize_table_name()` function
   - [ ] No new security vulnerabilities introduced

7. **Error Handling**:
   - [ ] Malformed JSONL lines are handled gracefully (skip line, log warning)
   - [ ] Empty JSONL files return appropriate error message
   - [ ] Files with no valid JSON lines return appropriate error message
   - [ ] Descriptive error messages for parsing failures
   - [ ] Backend errors are communicated to frontend clearly

8. **Performance**:
   - [ ] Large JSONL files (1000+ lines) are processed efficiently
   - [ ] Memory usage is reasonable (line-by-line processing)
   - [ ] Processing time is acceptable (< 5 seconds for 1000 lines)

9. **Compatibility**:
   - [ ] Existing CSV upload functionality unchanged and working
   - [ ] Existing JSON upload functionality unchanged and working
   - [ ] No breaking changes to API contracts
   - [ ] Frontend remains compatible with backend responses

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `cd app/server && uv run pytest -v` - Run all server tests including new JSONL tests to validate feature works with zero regressions
- `cd app/server && uv run pytest tests/test_jsonl_processor.py -v` - Run JSONL-specific unit tests
- `cd app/server && uv run pytest tests/test_sql_injection.py -v` - Run security tests including new JSONL security tests
- `cd /Users/richardbodo/src/tac/tac-4/adws && uv run scripts/start.sh 300` - Start the development server with 5 minute timeout to manually test JSONL upload end-to-end

## Notes

### Implementation Considerations

1. **Two-Pass Processing**: The JSONL processor uses a two-pass approach:
   - **First pass**: Scan all records to infer complete schema (all possible fields)
   - **Second pass**: Parse records and ensure all fields are present (fill missing with NULL)
   - This ensures consistent schema even when records have varying structures

2. **Array Flattening Strategy**: Arrays are flattened by creating separate columns for each index:
   - `tags: ["python", "data"]` becomes `tags__0: "python"`, `tags__1: "data"`
   - This approach has limitations for variable-length arrays across records
   - Records with fewer array elements will have NULL values for higher indices
   - Consider documenting this limitation for users

3. **Memory Efficiency**: While we read line-by-line for parsing, we still load all data into a pandas DataFrame for SQLite insertion. For very large files (GB+), this could be a bottleneck. Consider streaming inserts in future iteration if needed.

4. **Column Name Collisions**: If a JSONL file has both `user_name` and `user.name`, the flattening will create `user_name` twice. The sanitization process handles this by using the same logic, but data might be overwritten. Document this edge case.

5. **Delimiter Configurability**: While we store delimiters in constants.py, changing them after data is uploaded would break existing queries. Consider this a "set once" configuration. Future enhancement could store delimiter metadata with each table.

6. **No Additional Libraries**: The implementation uses only standard library (`json`, `io`) and existing dependencies (`pandas`, `sqlite3`), as requested. No new libraries required.

7. **Performance Benchmarks**: For reference, expected performance:
   - 1,000 lines: < 2 seconds
   - 10,000 lines: < 10 seconds
   - 100,000 lines: < 60 seconds (highly dependent on nesting depth)

8. **Future Enhancements** (not in scope for this feature):
   - Streaming large files with progress bar
   - Configurable array handling (e.g., JSON stringify arrays instead of flattening)
   - Schema versioning for tables with evolving structures
   - Incremental JSONL uploads (append to existing table)
   - Support for compressed JSONL (.jsonl.gz)

### Testing Notes

- Test files should be small (< 100 lines) to keep tests fast
- Include at least one malformed line in mixed test file to validate error handling
- Use realistic field names and values in test files
- Test with both simple and complex nesting (2-4 levels)

### Documentation for Users

Consider adding a help section in the UI explaining:
- What JSONL format is (one JSON object per line)
- How nested objects are flattened (delimiter explanation)
- How arrays are handled (index notation)
- Example of JSONL → flattened table transformation
- Limitations (variable-length arrays, deep nesting)
