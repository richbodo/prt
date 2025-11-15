# Bug: LLM Memory Chaining Test Reliability and Isolation Issues

## Bug Description
The test `test_llm_memory_chaining.py::test_save_contacts_with_images_tool` is experiencing reliability issues due to poor test isolation and schema migration pollution. While the test currently passes, it suffers from multiple architectural problems that make it unreliable and potentially flaky:

1. **Schema Migration Pollution**: Each test run triggers database schema migrations from v2 to v6, creating noise and slowing down tests
2. **Memory File Persistence**: Tests share a global temp directory for LLM memory files, causing cross-test contamination (65 leftover memory files found)
3. **Poor Test Isolation**: Tests don't properly clean up after themselves and depend on external state
4. **Inadequate Tool Chaining Validation**: Tests don't thoroughly validate the correctness of the tool chaining logic itself

## Problem Statement
The LLM memory chaining tests lack proper isolation and reliability, leading to:
- Slow test execution due to unnecessary database migrations
- Cross-test pollution from shared memory directories
- Potential intermittent failures due to external state dependencies
- Insufficient validation of tool chaining correctness
- Poor developer experience with noisy test output

## Solution Statement
Implement proper test isolation by:
1. Preventing schema migrations in test environments
2. Using isolated memory directories per test
3. Creating focused unit tests for tool chaining logic
4. Adding comprehensive validation of memory chaining workflows
5. Ensuring complete test cleanup

## Steps to Reproduce
1. Run `./prt_env/bin/pytest tests/test_llm_memory_chaining.py -v`
2. Observe database migration output on every test
3. Check temp directory: `find /tmp -name "*prt_llm_memory*"` - shows persistent files
4. Run tests multiple times - observe accumulating memory files
5. Notice "Listed 65 memory results" instead of clean test state

## Root Cause Analysis
1. **PRTAPI Auto-Migration**: The `PRTAPI.__init__()` method automatically checks and performs schema migrations, even in test environments
2. **Global Memory Directory**: `LLMMemory` class uses a global temp directory without test isolation
3. **Outdated Test Fixtures**: Test fixtures create v2 schema databases that trigger migrations instead of creating v6 directly
4. **No Memory Cleanup**: Tests don't clean up memory files after execution
5. **Insufficient Mocking**: Tests use real implementations instead of focused unit testing

## Relevant Files
Use these files to fix the bug:

- `tests/test_llm_memory_chaining.py` - Main test file that needs reliability improvements and better isolation
- `prt_src/llm_memory.py` - LLM memory system that needs test-aware directory isolation
- `prt_src/api.py` - PRTAPI class that triggers unwanted migrations in tests (lines 50-64)
- `tests/conftest.py` - Test fixtures that need to prevent migrations and provide isolated memory
- `tests/fixtures.py` - Database fixtures that should create v6 schema directly
- `prt_src/llm_ollama.py` - OllamaLLM class with tool methods that need better test coverage

### New Files
- `tests/mocks/mock_llm_memory.py` - Isolated memory system for tests
- `tests/unit/test_llm_tool_chaining_logic.py` - Focused unit tests for tool chaining logic

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Create Isolated Memory System for Tests
- Create `tests/mocks/mock_llm_memory.py` with test-isolated memory implementation
- Mock memory system should use test-specific temp directories
- Implement automatic cleanup on test completion
- Ensure memory files don't persist across test runs

### Step 2: Prevent Schema Migrations in Tests
- Modify `prt_src/api.py` to detect test environment and skip auto-migrations
- Add test environment detection (check for pytest or test database paths)
- Update test fixtures to create v6 schema directly without triggering migrations
- Ensure `setup_test_database()` creates current schema version

### Step 3: Update Test Fixtures for Better Isolation
- Modify `tests/conftest.py` to provide isolated memory system fixture
- Update test database fixtures to use current schema version (v6)
- Add cleanup hooks to ensure complete test isolation
- Provide mock LLM memory instance for each test

### Step 4: Refactor Memory Chaining Tests
- Update `test_llm_memory_chaining.py` to use isolated memory fixtures
- Add comprehensive validation of tool chaining logic
- Test error conditions and edge cases
- Add tests for memory file cleanup and lifecycle management

### Step 5: Create Focused Unit Tests for Tool Chaining Logic
- Create `tests/unit/test_llm_tool_chaining_logic.py` for isolated testing
- Test individual tool methods without full system integration
- Mock database and memory dependencies
- Validate tool parameter passing and result handling
- Test tool chaining workflows step-by-step

### Step 6: Add Memory System Integration Tests
- Test memory system persistence and retrieval accuracy
- Validate JSON serialization/deserialization of contact data with images
- Test memory cleanup and automatic expiration
- Verify memory system statistics and listing functionality

### Step 7: Improve Test Coverage and Validation
- Add assertions for tool chaining result consistency
- Test memory ID generation uniqueness and format
- Validate contact data integrity through save/load cycles
- Test directory generation with memory IDs vs search queries

### Step 8: Performance and Reliability Testing
- Add performance benchmarks for memory operations
- Test memory system under concurrent access
- Validate cleanup of large memory files
- Test system behavior with corrupted memory files

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `./prt_env/bin/pytest tests/test_llm_memory_chaining.py -v` - Run original tests with clean output (no migrations)
- `./prt_env/bin/pytest tests/unit/test_llm_tool_chaining_logic.py -v` - Run new focused unit tests
- `./prt_env/bin/pytest tests/ -k "memory" -v` - Run all memory-related tests
- `find /tmp -name "*prt_llm_memory*" -exec rm -rf {} +` - Clean temp before test
- `./prt_env/bin/pytest tests/test_llm_memory_chaining.py -v --tb=short` - Verify no temp files persist
- `python -c "import tempfile; from pathlib import Path; print(list((Path(tempfile.gettempdir()) / 'prt_llm_memory').glob('*.json')))"` - Confirm cleanup
- `./prt_env/bin/pytest tests/ -m integration --durations=10` - Performance regression check
- `./prt_env/bin/pytest tests/test_llm_memory_chaining.py::test_save_contacts_with_images_tool -v --count=5` - Reliability check (run 5 times)

## Notes
- The test isolation issues affect all LLM-related tests, not just memory chaining
- Memory system should use dependency injection for better testability
- Consider adding memory system configuration options for test vs production behavior
- Schema migration detection should be more intelligent about test environments
- Future memory system enhancements should include transaction support for atomic operations
- Test performance targets: memory operations < 50ms, full test suite < 2 seconds