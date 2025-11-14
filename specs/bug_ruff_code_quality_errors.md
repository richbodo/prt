# Bug: 29 Ruff Code Quality Errors in Codebase

## Bug Description
The codebase has 29 ruff linting errors that need to be resolved to maintain code quality standards. These errors include:
- **2 SIM105 errors**: Using inefficient `try`-`except`-`pass` patterns instead of `contextlib.suppress()`
- **22 SIM117 errors**: Using nested `with` statements instead of single `with` statements with multiple contexts
- **5 syntax errors**: Using Python 3.9+ syntax (`with` statement parentheses) in code that should be compatible with Python 3.8+

The errors are primarily in test files and some TUI service code, indicating code quality issues that should be addressed for better maintainability and Python version compatibility.

## Problem Statement
The ruff linter has identified 29 code quality issues that violate best practices and potentially cause compatibility problems. These include inefficient exception handling, unnecessary code nesting, and syntax that breaks Python 3.8 compatibility. These errors need to be systematically resolved while maintaining functionality and ensuring no regressions are introduced.

## Solution Statement
Fix all 29 ruff errors by:
1. Replacing `try`-`except`-`pass` patterns with `contextlib.suppress()` where appropriate
2. Combining nested `with` statements into single statements with multiple contexts
3. Removing Python 3.9+ syntax (parenthesized context managers) to maintain Python 3.8+ compatibility
4. Running comprehensive tests to ensure no functionality is broken by the changes

## Steps to Reproduce
```bash
# Activate virtual environment
source ./init.sh

# Run ruff check to see all errors
./prt_env/bin/ruff check prt_src/ tests/ --output-format=full

# Should show 29 errors:
# - 2 SIM105 errors in prt_src/tui/services/notification.py and prt_src/tui/widgets/contact_detail.py
# - 22 SIM117 errors in various test files
# - 5 syntax errors in tests/integration/test_llm_network_validation.py
```

## Root Cause Analysis
1. **SIM105 errors**: Code uses inefficient `try`-`except`-`pass` patterns where `contextlib.suppress()` would be more appropriate and readable
2. **SIM117 errors**: Test code uses unnecessarily nested `with` statements instead of the more readable single `with` statement with multiple contexts
3. **Syntax errors**: Code uses Python 3.9+ parenthesized context manager syntax (`with (...):`) which is not compatible with Python 3.8, but the project needs to maintain broader compatibility

The root cause is likely that these patterns accumulated over time as different contributors added code without consistent linting enforcement, and some newer Python syntax was used without considering the minimum Python version requirement.

## Relevant Files
Use these files to fix the bug:

- **prt_src/tui/services/notification.py:88** - SIM105 error in `_remove_toast_safe()` method
- **prt_src/tui/widgets/contact_detail.py:219** - SIM105 error in `_select_field()` method
- **tests/integration/test_llm_network_validation.py:170,187,205,222,239,256** - 5 syntax errors using Python 3.9+ `with` statement syntax
- **tests/test_cli.py:393** - SIM117 error with nested `with` statements
- **tests/test_fts5_migration.py:33** - SIM117 error with nested `with` statements
- **tests/test_relationship_cli.py** (multiple lines) - 20 SIM117 errors with nested `with` statements

### New Files
None needed - all fixes are in existing files.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Fix SIM105 Errors (Replace try-except-pass with contextlib.suppress)
- Import `contextlib` in notification.py and contact_detail.py
- Replace `try`-`except`-`pass` patterns with `contextlib.suppress(Exception)`
- Ensure the error handling behavior remains the same

### Step 2: Fix Python 3.8 Compatibility Syntax Errors
- Remove parentheses from `with` statements in test_llm_network_validation.py
- Convert `with (patch1, patch2):` to traditional nested `with` statements
- Ensure Python 3.8+ compatibility is maintained

### Step 3: Fix SIM117 Errors (Combine Nested With Statements)
- Convert nested `with` statements to single `with` statements with multiple contexts in test files
- Start with test_cli.py (1 error)
- Fix test_fts5_migration.py (1 error)
- Fix all 20 errors in test_relationship_cli.py
- Ensure test functionality remains unchanged

### Step 4: Run Code Quality Validation
- Run ruff check to verify all errors are resolved
- Run black formatter to ensure consistent code style
- Verify no new errors were introduced

### Step 5: Run Comprehensive Test Suite
- Run the full test suite to ensure no functionality was broken
- Run specific tests for files that were modified
- Verify all tests pass

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

```bash
# Activate environment
source ./init.sh

# Verify all ruff errors are fixed
./prt_env/bin/ruff check prt_src/ tests/ --output-format=full
# Should show 0 errors

# Run formatting to ensure consistency
./prt_env/bin/black prt_src/ tests/
# Should show no changes needed or apply minimal formatting

# Run comprehensive test suite
./prt_env/bin/pytest tests/ -v
# All tests should pass

# Run specific tests for modified files
./prt_env/bin/pytest tests/test_cli.py -v
./prt_env/bin/pytest tests/test_fts5_migration.py -v
./prt_env/bin/pytest tests/test_relationship_cli.py -v
./prt_env/bin/pytest tests/integration/test_llm_network_validation.py -v
# All specific tests should pass

# Verify TUI components still work (for modified TUI files)
python -c "from prt_src.tui.services.notification import NotificationService; from prt_src.tui.widgets.contact_detail import ContactDetail; print('✅ TUI imports successful')"

# Final validation - should show 0 errors
./prt_env/bin/ruff check prt_src/ tests/
```

## Notes
- The project uses Python 3.8+ compatibility, so avoid Python 3.9+ specific syntax
- The `contextlib.suppress()` approach is more Pythonic and readable than `try`-`except`-`pass`
- When combining `with` statements, maintain the same order and ensure all context managers are properly handled
- Test files contain the majority of the errors (27 out of 29), indicating this is primarily a test code quality issue
- The SIM105 and SIM117 rules are simplification rules that improve code readability without changing functionality
- Pre-commit hooks should catch these errors in the future, so this is a one-time cleanup