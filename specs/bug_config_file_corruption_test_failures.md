# Bug: Config file corruption causing test failures

## Bug Description
A large number of tests are failing with `ValueError: Config file is corrupt`. The error occurs when tests try to initialize LLM components that internally call `load_config()` to read from the file system, but encounter a corrupted or missing configuration file. This affects 46 tests across multiple test files, primarily related to LLM functionality including contacts-with-images workflows, memory chaining, query optimization, and Ollama integration.

## Problem Statement
Tests are not properly isolated from the global config file system. When tests initialize `OllamaLLM` without providing a `config_manager` parameter, it creates a new `LLMConfigManager()` which calls `load_config()` to read from the file system. If the `prt_data/prt_config.json` file is missing, corrupted, or contains invalid JSON, this causes all tests to fail with the "Config file is corrupt" error, making the test suite unreliable and environment-dependent.

## Solution Statement
Create test isolation by providing a proper test fixture that ensures LLM tests always have access to a valid configuration. This will involve creating a test configuration fixture and modifying tests to use it consistently, ensuring they don't depend on the global config file state. The fix will be minimal and surgical, focusing on test configuration isolation without changing production code behavior.

## Steps to Reproduce
1. Corrupt the config file: `echo '{ "corrupted": json syntax' > prt_data/prt_config.json`
2. Run any of the failing tests: `./prt_env/bin/pytest tests/test_llm_contacts_with_images_workflow.py::test_get_contacts_with_images_tool -v`
3. Observe the `ValueError: Config file is corrupt` error
4. Restore config file: `mv prt_data/prt_config.json.backup prt_data/prt_config.json`
5. Test passes again

## Root Cause Analysis
The root cause is in the test design pattern for LLM tests:

1. **Test Pattern**: Tests create local config for database: `config = {"db_path": str(db.path), "db_encrypted": False}`
2. **API Initialization**: Tests pass config to API: `api = PRTAPI(config)`
3. **LLM Initialization**: Tests call `llm = OllamaLLM(api=api)` without `config_manager` parameter
4. **Config Manager Creation**: `OllamaLLM.__init__` creates `LLMConfigManager()` with no arguments
5. **File System Read**: `LLMConfigManager.__init__` calls `load_config()` which reads from file system
6. **JSON Parsing**: If config file is missing or corrupt, `json.load()` fails with `JSONDecodeError`
7. **Error Wrapping**: `load_config()` wraps this as `ValueError("Config file is corrupt")`

The issue is that tests intended to be isolated are inadvertently depending on global file system state.

## Relevant Files
Use these files to fix the bug:

- `tests/conftest.py` - Add LLM test configuration fixture to provide valid config for all LLM tests
- `prt_src/config.py` - Contains `load_config()` function that raises the error when JSON parsing fails
- `prt_src/llm_ollama.py` - `OllamaLLM.__init__` calls `LLMConfigManager()` without parameters, causing file system read
- `tests/test_llm_contacts_with_images_workflow.py` - Example failing test file that needs to use the config fixture
- `tests/test_llm_memory_chaining.py` - Another failing test file
- `tests/test_llm_query_optimization_prompts.py` - Another failing test file
- `tests/test_ollama_integration.py` - Another failing test file

### New Files
- `prt_data/prt_config_test.json` - Valid test configuration file to ensure tests have a reliable config baseline

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Create valid test configuration file
- Create `prt_data/prt_config_test.json` with minimal valid configuration for tests
- Ensure it contains all required fields to prevent JSON parsing errors
- Use safe default values that won't affect test isolation

### Step 2: Add LLM configuration fixture to conftest.py
- Add `llm_config` fixture that provides a complete `LLMConfigManager` instance for tests
- Add `llm_config_dict` fixture that provides config dictionary for tests that need to pass config directly
- Ensure fixtures use test-specific configuration that doesn't depend on file system state

### Step 3: Update failing test files to use config fixtures
- Modify `tests/test_llm_contacts_with_images_workflow.py` to use `llm_config` fixture when creating `OllamaLLM`
- Modify `tests/test_llm_memory_chaining.py` to use the fixture
- Modify `tests/test_llm_query_optimization_prompts.py` to use the fixture
- Modify `tests/test_ollama_integration.py` to use the fixture
- Apply the same pattern to any other failing test files

### Step 4: Ensure config file robustness
- Verify that `load_config()` handles missing config files gracefully by providing defaults
- Check if we need to add any additional error handling for test environments

### Step 5: Run validation tests to confirm fix
- Run all previously failing tests to ensure they pass consistently
- Test with missing config file to ensure tests are isolated
- Test with corrupted config file to ensure tests are isolated
- Run full test suite to check for regressions

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `./prt_env/bin/pytest tests/test_llm_contacts_with_images_workflow.py -v` - Run LLM contacts workflow tests
- `./prt_env/bin/pytest tests/test_llm_memory_chaining.py -v` - Run LLM memory chaining tests
- `./prt_env/bin/pytest tests/test_llm_query_optimization_prompts.py -v` - Run LLM query optimization tests
- `./prt_env/bin/pytest tests/test_ollama_integration.py -v` - Run Ollama integration tests
- `./prt_env/bin/pytest tests/test_contacts_with_images_performance.py -v` - Run performance tests
- `cp prt_data/prt_config.json prt_data/prt_config.json.backup && echo '{ "corrupted": json' > prt_data/prt_config.json` - Corrupt config file
- `./prt_env/bin/pytest tests/test_llm_contacts_with_images_workflow.py::test_get_contacts_with_images_tool -v` - Test should pass even with corrupted config
- `mv prt_data/prt_config.json.backup prt_data/prt_config.json` - Restore config file
- `rm -f prt_data/prt_config.json` - Remove config file entirely
- `./prt_env/bin/pytest tests/test_llm_contacts_with_images_workflow.py::test_get_contacts_with_images_tool -v` - Test should pass even with missing config
- `./prt_env/bin/pytest tests/ -k "not (integration and ollama)" --maxfail=5` - Run all non-integration tests to check for regressions

## Notes
- The fix is surgical and focused only on test isolation without changing production behavior
- The bug likely appears intermittently based on test environment state and timing
- Once fixed, tests will be more reliable and won't fail due to external file system state
- The solution preserves the existing test patterns while adding proper configuration isolation