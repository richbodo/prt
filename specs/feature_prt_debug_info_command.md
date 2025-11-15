# Feature: PRT Debug Info Command

## Feature Description
Add a `--prt-debug-info` command line option that provides comprehensive system debug information and exits. This command will **reuse existing system information gathering capabilities** to collect and display critical diagnostic information including the default LLM configuration, LLM connectivity test, system prompt preview, and system environment details. This feature is essential for troubleshooting user issues, validating LLM integration, and providing support information.

## User Story
As a **PRT user or developer**
I want to **run a single command that shows me all critical system diagnostic information**
So that **I can troubleshoot issues, verify my LLM setup is working, and provide comprehensive debug information when seeking support**

## Problem Statement
Currently, PRT users experiencing issues have no single command to gather comprehensive diagnostic information about their system setup, LLM configuration, and connectivity status. Users must manually check multiple aspects of the system to troubleshoot problems, which is time-consuming and error-prone. Support requests often lack critical system information needed for effective debugging.

## Solution Statement
Implement a `--prt-debug-info` command line flag that **orchestrates existing system information gathering functions** to collect and display all essential diagnostic information in a structured format. The command will **reuse existing database status, LLM connectivity, and configuration functions** rather than duplicating code, ensuring consistency with other parts of the application.

## Relevant Files
**CRITICAL: Reuse existing functions rather than duplicating functionality**

### Existing System Info Functions to Reuse:

**Database Status** (reuse existing):
- **`prt_src/api.py`**:
  - `test_database_connection()` - ✅ REUSE for DB connectivity test
  - `get_data_directory()` - ✅ REUSE for data directory path
- **`prt_src/db.py`**:
  - `is_valid()` - ✅ REUSE for database integrity check
  - `count_contacts()`, `count_relationships()` - ✅ REUSE for DB statistics
- **`prt_src/cli.py`**:
  - `check_database_health()` - ✅ REUSE for comprehensive DB status
  - `db_status()` command logic - ✅ REUSE patterns

**LLM Status** (reuse existing):
- **`prt_src/llm_factory.py`**:
  - `check_model_availability()` - ✅ REUSE for model availability check
  - `resolve_model_alias()` - ✅ REUSE for default LLM determination
  - `get_registry()` - ✅ REUSE for accessing Ollama registry
- **`prt_src/llm_model_registry.py`**:
  - `is_available()` - ✅ REUSE for Ollama connectivity check
  - `list_models()` - ✅ REUSE for available models list
- **`prt_src/cli.py`**:
  - `list_models()` command logic - ✅ REUSE patterns for model display

**Configuration** (reuse existing):
- **`prt_src/config.py`**:
  - `LLMConfigManager` - ✅ REUSE for loading LLM configuration
  - `load_config()` - ✅ REUSE for main config loading
- **`prt_src/schema_manager.py`**:
  - `get_schema_version()` - ✅ REUSE for current schema version
  - `get_migration_info()` - ✅ REUSE for migration status
- **`prt_src/__init__.py`**:
  - `__version__` - ✅ REUSE for PRT version

**System Prompt Generation** (reuse existing):
- **`prt_src/llm_ollama.py`**:
  - `_create_system_prompt()` - ✅ REUSE for system prompt display

### Files to Modify:
- **`prt_src/cli.py`**: Add `--prt-debug-info` flag to main callback function
- **`prt_src/tui/screens/settings.py`**: Update `get_database_stats_stub()` to use real data from API

### New Files:
- **`prt_src/debug_info.py`**: Orchestration module that **calls existing functions**
  - **NO duplicate functionality** - only orchestrates existing functions
  - Handles formatting and display of information gathered from existing functions
  - Provides system environment detection (OS, Python version) - **only new functionality**

## Implementation Plan
**CRITICAL: Focus on orchestration and reuse, not duplication**

### Phase 1: Foundation (Orchestration Module)
Create `prt_src/debug_info.py` as a **thin orchestration layer** that calls existing functions:
- Import and call existing database status functions from `api.py`, `db.py`, `cli.py`
- Import and call existing LLM status functions from `llm_factory.py`, `llm_model_registry.py`
- Import and call existing configuration functions from `config.py`, `schema_manager.py`
- **Only new code**: System environment detection (OS, Python version, Ollama version)

### Phase 2: Core Implementation (Function Orchestration)
Implement orchestration functions that **delegate to existing code**:
- `collect_database_info()` → calls `api.test_database_connection()`, `db.count_contacts()`, etc.
- `collect_llm_info()` → calls `llm_factory.resolve_model_alias()`, `check_model_availability()`, etc.
- `collect_config_info()` → calls `config.load_config()`, `schema_manager.get_schema_version()`, etc.
- `collect_system_prompt()` → calls existing LLM instantiation and `_create_system_prompt()`
- **Only new**: `collect_system_environment()` for OS/Python/Ollama version detection

### Phase 3: Integration (CLI and TUI)
- Add `--prt-debug-info` flag to CLI main callback
- **TUI Integration**: Update `prt_src/tui/screens/settings.py` to use real database stats from API
- Ensure debug command works independently and exits cleanly

## Step by Step Tasks
**CRITICAL: Each step emphasizes reusing existing functions**

### Step 1: Create Debug Info Orchestration Module
- Create `prt_src/debug_info.py` with basic structure and imports for existing functions
- **REUSE**: Import existing functions from `api.py`, `db.py`, `llm_factory.py`, `config.py`, etc.
- **NEW ONLY**: Implement `collect_system_environment()` for OS/Python/Ollama version detection
- Create output formatting functions for structured display

### Step 2: Implement Database Info Orchestration
- **REUSE**: `collect_database_info()` calls existing `api.test_database_connection()`
- **REUSE**: Call existing `db.count_contacts()`, `db.count_relationships()`
- **REUSE**: Call existing `cli.check_database_health()` patterns
- **REUSE**: Call existing `schema_manager.get_schema_version()`, `get_migration_info()`
- Add error handling wrapper around existing functions

### Step 3: Implement LLM Info Orchestration
- **REUSE**: `collect_llm_info()` calls existing `llm_factory.resolve_model_alias()`
- **REUSE**: Call existing `llm_factory.check_model_availability()`
- **REUSE**: Call existing `registry.is_available()` and `registry.list_models()`
- **REUSE**: Use existing LLM instantiation patterns from CLI commands
- Add error handling wrapper around existing functions

### Step 4: Implement System Prompt Orchestration
- **REUSE**: `collect_system_prompt()` calls existing LLM instantiation
- **REUSE**: Call existing `llm_ollama._create_system_prompt()` method
- **REUSE**: Use existing API and configuration loading patterns
- Add truncation/formatting for display, ensure works when DB unavailable

### Step 5: Create Main Orchestration Function
- Implement `collect_debug_info()` that **calls all the orchestration functions**
- **NO duplication**: Each section delegates to existing functions
- Add structured output formatting with status indicators (✓, ✗, ⚠)
- Add summary section showing overall system health

### Step 6: Write Unit Tests
- Create `tests/unit/test_debug_info.py` with comprehensive test coverage
- **Test orchestration**: Mock the existing functions being called, not their implementation
- Test error handling scenarios (missing Ollama, network issues, etc.)
- Test output formatting and ensure no sensitive information is displayed

### Step 7: Integrate with CLI
- Add `--prt-debug-info` option to the main CLI callback function in `prt_src/cli.py`
- Implement early exit logic that calls debug info collection and exits
- Ensure the flag works independently of other CLI options
- Add help text explaining the purpose of the debug command

### Step 8: TUI Integration (Settings Screen Enhancement)
- **REUSE**: Update `prt_src/tui/screens/settings.py` to use real database stats
- Replace `get_database_stats_stub()` with calls to existing API functions
- **REUSE**: Call existing `api.test_database_connection()`, `db.count_contacts()`, etc.
- Ensure TUI settings screen shows actual system status, not stub data

### Step 9: Add Integration Tests
- Create `tests/integration/test_debug_info_command.py` for end-to-end testing
- Test the CLI integration using subprocess to verify actual command execution
- Test various system configurations (with/without Ollama, different models, etc.)
- Verify exit codes and output format consistency

### Step 10: Documentation and Error Handling
- Update help text and documentation to include the new debug command
- Add comprehensive error handling for all failure scenarios
- Ensure graceful degradation when parts of the system are unavailable
- Add logging for debug command usage for support purposes

### Step 11: Validation Testing
- Run all existing tests to ensure no regressions
- Test the debug command in various system configurations
- Verify output is helpful and not overwhelming
- Test edge cases like missing configuration files or corrupted setup

## Testing Strategy
**CRITICAL: Test orchestration, not reimplementation**

### Unit Tests
- **System Environment Detection**: Test `collect_system_environment()` with mocked system calls (only new functionality)
- **Database Orchestration**: Test `collect_database_info()` calls existing `api.test_database_connection()`, `db.count_contacts()` etc.
- **LLM Orchestration**: Test `collect_llm_info()` calls existing `llm_factory.resolve_model_alias()`, `check_model_availability()` etc.
- **Configuration Orchestration**: Test `collect_config_info()` calls existing `config.load_config()`, `schema_manager.get_schema_version()` etc.
- **Output Formatting**: Test formatting functions for structured output display
- **Error Handling**: Test graceful handling when existing functions return errors or exceptions
- **Mock Strategy**: Mock the existing functions being called, not their internal implementation

### Integration Tests
- **CLI Integration**: Test `--prt-debug-info` flag execution using subprocess to verify real command behavior
- **End-to-End Flow**: Test complete debug info collection in a controlled environment with known configuration
- **Cross-Platform**: Test on different operating systems to verify system information detection
- **Multiple LLM Configurations**: Test with different LLM setups (Ollama, llamacpp, missing models)

### Edge Cases
- **Missing Ollama**: Verify graceful handling when Ollama is not installed or not running
- **Corrupted Configuration**: Test behavior when configuration files are missing or malformed
- **Network Issues**: Test LLM connectivity testing with network timeouts or connection failures
- **Insufficient Permissions**: Test behavior when the system can't access certain system information
- **Large System Prompts**: Test output formatting with very long system prompts
- **Missing Dependencies**: Test when optional dependencies are not installed

## Acceptance Criteria
- [ ] `--prt-debug-info` command line flag is available and properly documented in help text
- [ ] Command displays operating system, Python version, and Ollama version (if available)
- [ ] Command shows the currently configured default LLM model with clear status indication
- [ ] Command tests LLM connectivity and displays response status (success/failure with details)
- [ ] Command generates and displays the complete system prompt that would be sent to the LLM
- [ ] Command provides clear visual indicators (✓/✗/⚠) for each system component status
- [ ] Command exits immediately after displaying information without launching TUI or CLI
- [ ] Command works even when PRT is not fully configured or when components are unavailable
- [ ] All error conditions are handled gracefully with helpful error messages
- [ ] Output is formatted in a clear, structured manner suitable for troubleshooting and support
- [ ] Command execution completes within 30 seconds even with slow network connections
- [ ] No sensitive information (passwords, API keys, personal data) is displayed in output

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `source ./init.sh` - Ensure development environment is properly set up
- `./prt_env/bin/python -m prt_src --help` - Verify new flag appears in help output
- `./prt_env/bin/python -m prt_src --prt-debug-info` - Test the debug command execution with default configuration
- `OLLAMA_HOST=invalid ./prt_env/bin/python -m prt_src --prt-debug-info` - Test behavior with invalid Ollama configuration
- `./prt_env/bin/python -m prt_src --prt-debug-info --model gpt-oss:20b` - Test debug command with specific model override
- `./prt_env/bin/pytest tests/unit/test_debug_info.py -v` - Run unit tests for debug info module
- `./prt_env/bin/pytest tests/integration/test_debug_info_command.py -v` - Run integration tests for CLI command
- `./prt_env/bin/pytest tests/ -k "not llm" --tb=short` - Run non-LLM tests to verify no regressions
- `./prt_env/bin/python -m prt_src --prt-debug-info | head -20` - Verify output format and ensure it doesn't hang
- `timeout 30s ./prt_env/bin/python -m prt_src --prt-debug-info` - Verify command completes within timeout
- `echo $?` - Verify command exits with appropriate exit code

## Code Reuse Benefits

### Consistency and Reliability
- **Same Logic Everywhere**: By reusing existing functions, the debug command shows exactly the same status as other parts of the application
- **Single Source of Truth**: Database status, LLM connectivity, and configuration are checked using the same code that the CLI and TUI use
- **Maintained Automatically**: When existing functions are updated or fixed, the debug command automatically gets those improvements

### TUI Integration Strategy
- **Settings Screen Enhancement**: Update `prt_src/tui/screens/settings.py` to use real data from the debug info orchestration functions
- **Shared Status Display**: The same database statistics shown in `--prt-debug-info` will be displayed in the TUI settings screen
- **Consistent Experience**: Users see identical system status information whether using CLI `--prt-debug-info`, CLI `db-status`, or TUI settings screen
- **Future Integration**: The orchestration functions can easily be used to add system status panels to other TUI screens

### Technical Benefits
- **Reduced Code Duplication**: Zero duplication of database checks, LLM connectivity tests, or configuration loading
- **Easier Testing**: Tests focus on orchestration logic, not reimplementing existing functionality
- **Simpler Maintenance**: Changes to core system info gathering happen in one place and propagate everywhere
- **Lower Bug Risk**: Reusing well-tested existing functions reduces chances of introducing new bugs

## Notes
- The debug command should be designed to work in environments where Ollama might not be available or configured
- System information collection should be cross-platform compatible (macOS, Linux, Windows)
- **Code Reuse**: Only implement new functionality for system environment detection (OS, Python, Ollama versions)
- The system prompt display should be truncated or paginated if extremely long to avoid overwhelming output
- This feature will be valuable for GitHub issue templates and support requests
- Error messages should guide users toward solutions (e.g., "Ollama not found - install from https://ollama.ai")
- Consider adding machine-readable output format (JSON) in future iterations for automated debugging
- **TUI Integration**: The same orchestration functions will enhance the Settings screen with real data