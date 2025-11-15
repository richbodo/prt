# Bug: LLM Memory Chaining Test Reliability and Functional Validation

## Bug Description
The LLM memory chaining tests in `tests/test_llm_memory_chaining.py` are failing due to module import issues and lack proper functional validation of the Ollama interface capabilities. The tests have the following specific problems:

1. **Import Path Mismatch**: 3 out of 7 tests are failing with `ModuleNotFoundError: No module named 'make_directory'` because the MockDirectoryGeneratorPatcher is trying to patch the wrong module path
2. **Dynamic Import Pattern Issues**: The LLM Ollama code uses dynamic imports within functions (`sys.path.insert()` + `from make_directory import DirectoryGenerator`) which breaks the current mocking approach
3. **Missing Functional Validation**: Tests focus on implementation details rather than validating the actual LLM memory chaining behavior and Ollama interface capabilities
4. **Inadequate Error Scenario Testing**: Tests don't properly validate error conditions and recovery mechanisms that are critical for reliable LLM operations

## Problem Statement
The LLM memory chaining tests need to be both reliable (no import failures) and functionally relevant (validate actual Ollama interface behavior and memory chaining workflows). Currently, they fail to run due to mocking issues and don't adequately test the core functionality that ensures LLM tools can chain operations through memory persistence.

## Solution Statement
Fix the mocking infrastructure to handle dynamic imports correctly, and refactor tests to focus on functional validation of:
1. LLM tool chaining workflows (save contacts → list memory → generate directory)
2. Ollama interface robustness (timeout handling, error recovery, response validation)
3. Memory system reliability (isolation, cleanup, data integrity)
4. Integration between PRT API and LLM tools

## Steps to Reproduce
1. Run `./prt_env/bin/pytest tests/test_llm_memory_chaining.py -v`
2. Observe 3 tests failing with `ModuleNotFoundError: No module named 'make_directory'`
3. The failing tests are: `test_generate_directory_with_memory_id`, `test_generate_directory_error_handling`, `test_memory_chaining_workflow_complete`
4. Error occurs during fixture setup when MockDirectoryGeneratorPatcher tries to patch `tools.make_directory.DirectoryGenerator`

## Root Cause Analysis
1. **Incorrect Patch Target**: MockDirectoryGeneratorPatcher patches `tools.make_directory.DirectoryGenerator` but the actual import in `llm_ollama.py` is `from make_directory import DirectoryGenerator` after dynamically adding tools to sys.path
2. **Dynamic Import Complexity**: The LLM code uses `sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))` followed by `from make_directory import DirectoryGenerator`, making the module available as `make_directory.DirectoryGenerator`, not `tools.make_directory.DirectoryGenerator`
3. **Test Focus Misalignment**: Tests are validating mock behavior rather than actual LLM memory chaining functionality and Ollama interface robustness
4. **Missing Ollama Capability Validation**: Tests don't verify that the memory chaining system works with actual Ollama API constraints and capabilities

## Relevant Files
Use these files to fix the bug:

- `tests/mocks/mock_directory_generator.py` - Fix the patch target to match actual import path used by LLM code
- `tests/test_llm_memory_chaining.py` - Refactor tests to focus on functional validation of memory chaining workflows
- `prt_src/llm_ollama.py` - LLM implementation with tool methods that need proper functional testing coverage
- `tests/conftest.py` - Test fixtures that need improved directory generation mocking
- `prt_src/llm_memory.py` - Memory system that needs comprehensive reliability testing

### New Files
- `tests/unit/test_llm_memory_functional.py` - Focused functional tests for memory operations
- `tests/integration/test_ollama_memory_chaining.py` - Integration tests for Ollama-specific memory chaining behavior

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Fix Directory Generator Mocking Infrastructure
- Fix the patch target in `MockDirectoryGeneratorPatcher` to use `make_directory.DirectoryGenerator` instead of `tools.make_directory.DirectoryGenerator`
- Update the patcher to handle the dynamic import pattern used in `llm_ollama.py`
- Test the fix by running a single failing test to ensure the import error is resolved
- Ensure the mock properly simulates both successful and failed directory generation scenarios

### Step 2: Enhance Memory System Functional Testing
- Create `tests/unit/test_llm_memory_functional.py` to test memory operations independently
- Add comprehensive tests for memory data integrity, serialization/deserialization, and cleanup
- Test memory system behavior with large datasets and edge cases (empty data, corrupted files)
- Validate memory ID generation uniqueness and format consistency

### Step 3: Improve LLM Tool Chain Validation
- Refactor existing tests to focus on functional behavior rather than implementation details
- Add tests that validate the complete workflow: save contacts → list memory → generate directory
- Test error propagation and recovery mechanisms when individual tools fail
- Validate that tool parameters and return values match expected schemas

### Step 4: Add Ollama Interface Reliability Tests
- Create `tests/integration/test_ollama_memory_chaining.py` for Ollama-specific testing
- Test timeout handling and network error recovery in memory chaining operations
- Validate response size limits and content type validation work correctly with memory operations
- Test tool calling behavior with various memory data sizes and formats

### Step 5: Validate Memory System Performance and Reliability
- Add performance tests for memory operations with realistic data volumes
- Test memory system behavior under concurrent access scenarios
- Validate cleanup mechanisms work correctly and don't leave orphaned files
- Test memory system resilience to file system errors and permission issues

### Step 6: Improve Test Isolation and Cleanup
- Ensure all tests properly clean up after themselves without relying on global state
- Validate that test isolation prevents cross-test contamination
- Add comprehensive assertions for test environment state before and after each test
- Test that mock systems properly restore original behavior after test completion

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `./prt_env/bin/pytest tests/test_llm_memory_chaining.py::test_generate_directory_with_memory_id -v` - Verify single failing test now passes
- `./prt_env/bin/pytest tests/test_llm_memory_chaining.py -v` - Run all memory chaining tests to ensure no regressions
- `./prt_env/bin/pytest tests/unit/test_llm_memory_functional.py -v` - Run new functional memory tests
- `./prt_env/bin/pytest tests/integration/test_ollama_memory_chaining.py -v` - Run new Ollama integration tests
- `./prt_env/bin/pytest tests/ -k "memory" -v` - Run all memory-related tests across the codebase
- `./prt_env/bin/pytest tests/test_llm_memory_chaining.py -v --count=3` - Reliability test (run 3 times to ensure consistency)
- `find /tmp -name "*prt_llm_memory*" -exec rm -rf {} + 2>/dev/null; ./prt_env/bin/pytest tests/test_llm_memory_chaining.py -v; python -c "from pathlib import Path; import tempfile; print('Temp files:', list(Path(tempfile.gettempdir()).glob('*prt_llm_memory*')))"` - Verify cleanup works correctly
- `./prt_env/bin/pytest tests/ -m integration --durations=10` - Performance regression check for integration tests

## Notes
- The root issue is that the test mocking infrastructure doesn't account for the dynamic import pattern used in the LLM code
- Future LLM tool implementations should consider using dependency injection to make testing easier
- The memory chaining system is a critical component for LLM operations and needs robust testing that validates actual functionality, not just mock behavior
- Ollama-specific constraints (timeouts, response sizes, content types) need to be tested as part of the memory chaining workflow
- Test performance targets: individual memory operations < 50ms, full test suite < 5 seconds, no persistent temp files after completion