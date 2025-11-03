# Bug: Fixture data not isolated when using --setup option 2

## Bug Description
When real world data is in prt.db, and the user runs `python -m prt_src --setup`, and chooses to load fixtures (option 2), after the fixtures load, and the user presses a key to return to the main menu, and then returns to chat to do some testing, the user will see that the database they are using is filled with their real-world data. At that point, the user should see fixture data.

The symptom is that fixture mode setup appears to succeed, but subsequent operations (like database queries, contact counts, and chat interactions) operate on the real user database instead of the isolated fixture database. This breaks the promise of safe demo/testing mode and could lead to users accidentally modifying their real data.

## Problem Statement
The specific problem is in the `--setup` command line option workflow where choosing option 2 (load fixtures/demo data) does not properly persist the fixture configuration. The fixture configuration is created but not saved to the persistent config file, causing the application to revert to the real database configuration when subsequent operations are performed.

## Solution Statement
Modify the setup wizard flow in the CLI to properly save the fixture configuration when option 2 is selected, ensuring complete database iso2lation for demo/testing mode. The solution should ensure that all subsequent operations in the session and future sessions use the fixture database until the user explicitly switches back to real mode.

## Steps to Reproduce
1. Ensure you have real data in `prt_data/prt.db`
2. Run `python -m prt_src --setup`
3. When prompted, select option "2" (Try with demo data / load fixtures)
4. Wait for the setup completion message and press any key to return to main menu
5. Navigate to chat mode or use database status/counting functionality
6. Observe that the system shows real database data instead of fixture demo data
7. Expected: Should see fixture/demo data (6 contacts: John Doe, Jane Smith, Bob Wilson, etc.)
8. Actual: Shows real user data from the original prt.db

## Root Cause Analysis
The root cause is in the `run_setup_wizard()` function in `prt_src/cli.py`. When option 2 is selected:

1. **For option 1 (real setup):** The `setup_database()` function is called, which properly saves the configuration via `save_config()`
2. **For option 2 (fixture setup):** The `setup_fixture_mode()` function is called, which returns a fixture configuration but does NOT save it to the persistent config file
3. The fixture config exists only as a local variable in the setup wizard
4. After setup completes, when subsequent operations call `load_config()`, they load the old/real database configuration
5. The fixture configuration is lost, and all operations revert to using the real database

This is a critical data safety issue because users believe they are in safe demo mode but are actually operating on their real data.

## Relevant Files
Use these files to fix the bug:

- `prt_src/cli.py` - Contains the setup wizard logic in `run_setup_wizard()` function that needs to save fixture config when option 2 is selected
- `prt_src/fixture_manager.py` - Contains `setup_fixture_mode()` function that creates fixture config but doesn't save it
- `prt_src/config.py` - Contains `save_config()` and `load_config()` functions; save_config() needs to be called for fixture mode
- `prt_src/api.py` - The PRTAPI class that loads config and should use fixture database when in fixture mode
- `prt_src/db.py` - Database operations that should work on fixture database when in fixture mode

### New Files
- `tests/test_setup_wizard_fixture_isolation.py` - New focused test to verify the specific --setup option 2 workflow

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Analyze current setup wizard implementation
- Read `prt_src/cli.py` to understand the current `run_setup_wizard()` implementation
- Identify exactly where option 2 (fixture mode) is handled
- Confirm that fixture config is created but not saved

### Step 2: Fix setup wizard to save fixture configuration
- Modify `run_setup_wizard()` in `prt_src/cli.py` to call `save_config()` when option 2 is selected
- Ensure the fixture configuration is properly persisted to disk
- Add appropriate success messaging to confirm fixture mode is active

### Step 3: Add database mode indicators
- Enhance status and info functions to clearly show when the system is in fixture mode
- Modify database status display to indicate current mode (real vs fixture)
- Add visual indicators in relevant CLI/TUI contexts

### Step 4: Create focused test for the specific bug scenario
- Write comprehensive test in `tests/test_setup_wizard_fixture_isolation.py`
- Test should reproduce the exact command line workflow: `--setup` → option 2 → subsequent operations
- Verify that after choosing option 2, all database operations use fixture data
- Verify that real database remains completely untouched

### Step 5: Run comprehensive validation
- Execute new test to verify bug is fixed
- Run existing test suite to ensure no regressions
- Perform manual testing of the exact reproduction steps
- Verify code quality with linting and formatting

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `source ./init.sh` - Set up development environment
- `./prt_env/bin/pytest tests/test_setup_wizard_fixture_isolation.py -v` - Run new focused test
- `./prt_env/bin/pytest tests/test_fixture_database_isolation.py -v` - Run existing isolation test
- `./prt_env/bin/pytest tests/ -x` - Run all tests to check for regressions
- `python -m prt_src --setup` (select option 2) → test isolation manually - Manual reproduction test
- `./prt_env/bin/ruff check prt_src/ --fix` - Lint and auto-fix code
- `./prt_env/bin/black prt_src/` - Format code to standards

## Notes
This is a critical data safety bug that affects user trust and could lead to accidental modification of real data. The fix should be minimal and surgical - simply ensuring that when option 2 is selected in the setup wizard, the fixture configuration is properly saved using the existing `save_config()` function.

The existing fixture infrastructure is already correct - the issue is solely in the setup wizard workflow not persisting the fixture configuration. This fix should maintain backward compatibility with existing functionality while ensuring complete data isolation for demo/testing mode.

The test should specifically focus on the `--setup` command line option workflow rather than just the fixture system in general, as this reproduces the exact user experience described in the bug report.