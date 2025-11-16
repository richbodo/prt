# Bug: CLI Modularization Missing Imports and Flags

## Bug Description
After CLI modularization refactoring, several critical functions and flags are missing from the main CLI compatibility layer, causing test failures and breaking expected functionality:

1. **Missing Import Functions (3 test failures)**:
   - `export_search_results` function exists in `prt_src/cli_modules/services/export.py` but is not imported into the main CLI compatibility layer (`prt_src/cli.py`)
   - `_launch_tui_with_fallback` function exists in `prt_src/cli_modules/bootstrap/launcher.py` but is not exposed in the main CLI module

2. **Debug Info Command Parameter Issue**:
   - Tests expect `--prt-debug-info` flag but the command is actually `prt-debug-info` (subcommand, not flag)
   - The command itself works fine as `python -m prt_src prt-debug-info`, but tests are calling `python -m prt_src --prt-debug-info`

3. **CLI Router Flag Issue**:
   - One test expects `--classic` flag behavior, which doesn't exist in the new modular CLI structure
   - The test `test_cli_router_classic_flag` expects `--classic` flag but it's not defined in the main command

## Problem Statement
The CLI modularization refactoring moved functions to separate modules but failed to properly export them through the main CLI compatibility layer. Additionally, test expectations don't match the actual CLI interface after refactoring.

## Solution Statement
1. Add missing function imports to the main CLI compatibility layer (`prt_src/cli.py`)
2. Add the missing `--prt-debug-info` flag to the main command callback (it should be a flag, not just a subcommand)
3. Add the missing `--classic` flag to maintain backward compatibility
4. Update the CLI structure to ensure all expected functions and flags are properly exposed

## Steps to Reproduce
1. Run `./prt_env/bin/python -m pytest tests/test_cli.py::test_search_export_functionality -v`
   - Fails with: `ImportError: cannot import name 'export_search_results' from 'prt_src.cli'`
2. Run `./prt_env/bin/python -m pytest tests/test_cli.py::test_launch_tui_with_fallback_import_error -v`
   - Fails with: `ImportError: cannot import name '_launch_tui_with_fallback' from 'prt_src.cli'`
3. Run `./prt_env/bin/python -m pytest tests/test_cli.py::test_cli_router_classic_flag -v`
   - Fails with exit code 2 due to missing `--classic` flag
4. Run `./prt_env/bin/python -m pytest tests/integration/test_debug_info_command.py -v`
   - Fails because tests expect `--prt-debug-info` flag but it's a subcommand

## Root Cause Analysis
1. **Missing Exports**: The CLI modularization moved functions to specialized modules but the main compatibility layer (`prt_src/cli.py`) doesn't re-export them for backward compatibility
2. **Inconsistent Interface**: The `prt-debug-info` was implemented as a subcommand only, but tests and documentation suggest it should also be available as a flag
3. **Missing Flag**: The `--classic` flag was removed during modularization but tests still expect it
4. **Test Misalignment**: Tests were written expecting the old interface but weren't updated to match the new modular structure

## Relevant Files
Use these files to fix the bug:

- **`prt_src/cli.py`** - Main CLI compatibility layer that needs to import missing functions and expose them
- **`prt_src/cli_modules/services/export.py`** - Contains `export_search_results` function that needs to be re-exported
- **`prt_src/cli_modules/bootstrap/launcher.py`** - Contains `_launch_tui_with_fallback` function that needs to be re-exported
- **`prt_src/cli_modules/commands/main.py`** - Main command callback that needs `--prt-debug-info` and `--classic` flags added
- **`prt_src/cli_modules/commands/debug.py`** - Contains `prt_debug_info_command` that needs to be exposed as both flag and subcommand
- **`tests/test_cli.py`** - Contains the failing tests that depend on the missing imports

### New Files
None required - all fixes can be made to existing files.

## Step by Step Tasks

### Step 1: Add Missing Function Imports to Main CLI Compatibility Layer
- Add import for `export_search_results` from `prt_src.cli_modules.services.export`
- Add import for `_launch_tui_with_fallback` from `prt_src.cli_modules.bootstrap.launcher`
- Update `__all__` list to include these functions

### Step 2: Add Missing --prt-debug-info Flag to Main Command
- Modify `prt_src/cli_modules/commands/main.py` to add `--prt-debug-info` flag parameter
- Import and call `prt_debug_info_command` when the flag is used
- Ensure the command exits after displaying debug info (don't launch TUI/CLI)

### Step 3: Add Missing --classic Flag Support
- Add `--classic` flag parameter to the main command in `prt_src/cli_modules/commands/main.py`
- Implement logic to force CLI mode when `--classic` flag is used
- Ensure backward compatibility with existing test expectations

### Step 4: Update CLI Compatibility Layer Exports
- Ensure all newly added imports are properly exported in `prt_src/cli.py`
- Test that functions can be imported directly from the main CLI module
- Verify backward compatibility is maintained

### Step 5: Run Validation Tests
- Run all CLI tests to ensure no regressions
- Run debug info command tests to verify flag functionality
- Test both flag and subcommand interfaces for prt-debug-info
- Verify export and TUI fallback functionality works correctly

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `./prt_env/bin/python -m pytest tests/test_cli.py::test_search_export_functionality -v` - Test export function import works
- `./prt_env/bin/python -m pytest tests/test_cli.py::test_launch_tui_with_fallback_import_error -v` - Test TUI fallback function import works
- `./prt_env/bin/python -m pytest tests/test_cli.py::test_cli_router_classic_flag -v` - Test --classic flag functionality
- `./prt_env/bin/python -m pytest tests/integration/test_debug_info_command.py -v` - Test --prt-debug-info flag works
- `./prt_env/bin/python -m pytest tests/test_cli.py -v` - Run all CLI tests to ensure no regressions
- `./prt_env/bin/python -m prt_src --prt-debug-info` - Test debug info flag works directly
- `./prt_env/bin/python -m prt_src prt-debug-info` - Test debug info subcommand still works
- `./prt_env/bin/python -m prt_src --classic --help` - Test classic flag shows help without TUI
- `./prt_env/bin/python -c "from prt_src.cli import export_search_results, _launch_tui_with_fallback; print('Imports work')"` - Test direct imports work

## Notes
- Maintain backward compatibility - both flag and subcommand interfaces should work for prt-debug-info
- The `--classic` flag should force CLI mode (disable TUI attempt) for test compatibility
- All imports should be available directly from `prt_src.cli` module to maintain API compatibility
- This fix addresses the CLI modularization refactoring gaps without changing the overall architecture
- The solution preserves the modular structure while ensuring the compatibility layer works properly