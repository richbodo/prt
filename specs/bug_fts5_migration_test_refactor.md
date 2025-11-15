# Bug: FTS5 Migration Test Refactor - Replace Failing Unit Tests with Integration Tests

## Bug Description
The test `test_migration_v4_to_v5_creates_fts_tables` in `tests/test_fts5_migration.py` is failing because it's based on outdated assumptions about how the migration system works. The test mocks `db.session.execute()` but the actual `apply_migration_v4_to_v5()` method uses `cursor.executescript()` directly for better handling of FTS5 triggers with internal semicolons. The test shows "Adding full-text search support..." output but then fails with `AssertionError: assert False` because the mocked session.execute was never called.

The migration system evolved from using SQLAlchemy session-based SQL execution to using raw SQLite connections for complex multi-statement SQL operations, but the tests weren't updated to match this architectural change.

## Problem Statement
The failing FTS5 migration tests represent technical debt from the evolution of the migration system. The tests were written for an older SQLAlchemy session-based approach and haven't been updated to match the current raw SQLite cursor implementation. These unit tests mock implementation details rather than testing actual migration behavior, making them brittle and providing little value.

## Solution Statement
Replace the failing unit tests that mock implementation details with integration tests that validate actual migration behavior. Create proper integration tests that use real databases to verify that:
1. FTS5 tables are actually created during migration
2. Schema version is properly updated
3. FTS5 search functionality works after migration
4. Migration is idempotent and handles edge cases

This follows the project's "headless-first" testing philosophy and 4-layer testing pyramid, moving from brittle unit test mocks to reliable integration tests.

## Steps to Reproduce
1. Run `source ./init.sh` to activate the virtual environment
2. Run the failing test: `./prt_env/bin/pytest tests/test_fts5_migration.py::TestFTS5Migration::test_migration_v4_to_v5_creates_fts_tables -v`
3. Observe that the test fails with `AssertionError: assert False` even though the migration appears to run successfully (you see the success messages)
4. The root cause is that `mock_db.session.execute.called` is False because the actual implementation uses `cursor.executescript()` instead of `session.execute()`

## Root Cause Analysis
The root cause is an **architectural mismatch between test assumptions and implementation reality**:

1. **Implementation Evolution**: The `apply_migration_v4_to_v5()` method in `prt_src/schema_manager.py:431-438` uses `cursor.executescript(sql_content)` for atomic execution of complex SQL
2. **Test Assumptions**: The test mocks `db.session.execute()` but this method is never called by the actual implementation
3. **Technical Debt**: The tests were written for an older approach that used SQLAlchemy session-based SQL execution, but the system evolved to use raw SQLite connections for FTS5 migration
4. **Mock Brittleness**: The tests focus on mocking implementation details (which database method gets called) rather than testing actual behavior (does the migration work correctly)

The deleted empty migration file `004_create_initial_migration.py` has no impact on system functionality since the current migration system is method-based, not file-based.

## Relevant Files

### Existing Files to Modify
- `tests/test_fts5_migration.py` - Contains the failing unit tests that need to be replaced with integration tests
  - Remove: `test_migration_v4_to_v5_creates_fts_tables`, `test_migration_handles_existing_tables`, `test_schema_version_tracking`
  - Keep: `test_fts5_sql_file_content`, `test_current_version_is_6`, `test_migration_file_not_found`
  - Add: New integration tests that use real databases

- `prt_src/schema_manager.py` - The migration implementation that actually works correctly
  - Reference for understanding how migrations actually work (uses `cursor.executescript()`)

- `tests/conftest.py` - Contains shared fixtures including `test_db`
  - May need to add migration-specific fixtures

- `tests/fixtures.py` - Contains test database setup and fixture specifications
  - Reference for creating proper test data

### Files to Reference (No Changes)
- `migrations/add_fts5_support.sql` - The actual FTS5 migration SQL that needs to be tested
- `docs/TESTING_STRATEGY.md` - Project testing philosophy and patterns to follow
- `pytest.ini` - Test configuration and markers

## Step by Step Tasks

### Step 1: Remove Failing Unit Tests
- Remove `test_migration_v4_to_v5_creates_fts_tables` method - tests implementation details incorrectly
- Remove `test_migration_handles_existing_tables` method - not relevant to current `executescript()` approach
- Remove `test_schema_version_tracking` method - mocks don't match actual implementation
- Keep valuable tests that don't depend on mocks: `test_fts5_sql_file_content`, `test_current_version_is_6`, `test_migration_file_not_found`

### Step 2: Create Integration Test Fixtures
- Add `migration_test_db` fixture that creates a database at schema version 4
- Add helper functions to set up pre-migration state and verify post-migration state
- Use real SQLite database with actual migration execution (no mocking)

### Step 3: Implement Migration Integration Tests
- Create `test_v4_to_v5_migration_integration` - tests actual FTS5 migration with real database
- Create `test_migration_creates_fts_tables` - verifies FTS5 virtual tables exist after migration
- Create `test_migration_updates_schema_version` - verifies version progression from 4 to 5
- Create `test_fts_search_functionality_after_migration` - validates that search actually works post-migration
- Create `test_migration_is_idempotent` - ensures running migration twice doesn't break anything

### Step 4: Add Test Markers and Documentation
- Mark new integration tests with `@pytest.mark.integration`
- Add docstrings explaining what each test validates
- Follow the project's testing patterns from `docs/TESTING_STRATEGY.md`
- Ensure tests complete within the < 5 second integration test target

### Step 5: Update Test Organization
- Move integration tests to appropriate section in the file
- Add comprehensive test documentation explaining the migration testing approach
- Ensure tests use `get_fixture_spec()` pattern for expected values instead of hardcoded numbers

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `source ./init.sh` - Activate the virtual environment
- `./prt_env/bin/pytest tests/test_fts5_migration.py -v` - Run all FTS5 migration tests to ensure they pass
- `./prt_env/bin/pytest tests/test_fts5_migration.py::TestFTS5Migration::test_v4_to_v5_migration_integration -v` - Run the new integration test specifically
- `./prt_env/bin/pytest -m integration tests/test_fts5_migration.py` - Run integration tests only to verify performance targets
- `./prt_env/bin/pytest tests/ -k "migration" -v` - Run all migration-related tests to ensure no regressions
- `./prt_env/bin/pytest -m "unit or integration" --maxfail=5` - Run the fast test suite to ensure no impact on other tests
- `./scripts/run-ci-tests.sh` - Run the same tests that CI runs to validate zero regressions

## Notes
- The deletion of the empty `004_create_initial_migration.py` file has zero impact on functionality since the migration system is method-based, not file-based
- The new integration tests should complete in < 5 seconds total to meet the project's integration test performance targets
- Tests should use real SQLite databases (not mocks) following the project's database testing philosophy: "SQLite is fast enough for tests (<< 1ms per query), and testing with real DB catches SQL bugs"
- The failing test actually shows that the migration system works correctly - the test framework was just checking the wrong thing
- This refactor aligns with the project's "headless-first" testing philosophy by creating tests that validate actual behavior rather than mocking implementation details