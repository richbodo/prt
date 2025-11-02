# Bug: Fixture Data Overwrites Real User Data

## Bug Description
When users run `--setup` and choose to run on fixture data, the application overwrites all their real world data in the main database without warning, without giving an opportunity to cancel, and without telling the user how to restore a backup of their real world data. The setup process destructively clears the production database and loads fixture data into it, causing permanent data loss.

The issue occurs in both the CLI setup wizard (`python -m prt_src.cli setup`) and TUI setup screen when users select "Load Demo Data (Fixtures)". The `FixtureService.clear_and_load_fixtures()` method completely wipes the production database (`prt_data/prt.db`) before loading sample data.

## Problem Statement
The current fixture system violates the principle of data safety by:
1. Operating directly on the production database instead of using a separate fixture database
2. Destructively clearing all user data without creating backups
3. Providing no way to restore user data after fixture loading
4. Not properly isolating fixture data from real user data
5. Defaulting back to the corrupted production database on next app restart

## Solution Statement
Implement database isolation by creating a separate fixture database that doesn't touch the real user database. The solution follows the existing `--debug` mode pattern which correctly creates an isolated `debug.db` file.

When users choose fixture data during setup:
1. Create a separate `fixture.db` database file
2. Load fixture data into this isolated database
3. Configure the app to use the fixture database for this session
4. On next app restart, default back to the real production database
5. Never touch or modify the user's real data

This approach eliminates the need for backups since the real database is never modified.

## Steps to Reproduce
1. Set up PRT with real user data (contacts, tags, notes)
2. Run `python -m prt_src.cli setup` or `python -m prt_src` and trigger setup
3. Choose option "2" for "Load Demo Data (Fixtures)"
4. Observe that all real user data is permanently lost
5. Exit and restart the app - real data is still gone

## Root Cause Analysis
The bug exists because the setup system always operates on the production database path stored in `prt_config.json`. The `FixtureService` class:

1. **Receives the production database**: Gets the same database instance used for real data
2. **Destructively clears data**: `clear_database()` method deletes all tables in production DB
3. **No isolation mechanism**: No separate database file for fixtures
4. **Configuration persistence**: The app configuration still points to the same database file

The `--debug` mode works correctly by creating a separate `debug.db` file and returning isolated configuration, but the setup wizard doesn't follow this pattern.

## Relevant Files
Use these files to fix the bug:

- `prt_src/cli.py:setup_debug_mode()` - **Reference implementation** that correctly creates isolated debug database
- `prt_src/tui/screens/setup.py:_handle_load_fixtures()` - **Primary bug location** where fixtures are loaded into production DB
- `prt_src/tui/services/fixture.py:clear_and_load_fixtures()` - **Secondary bug location** that destructively clears production data
- `prt_src/config.py:load_config()/save_config()` - **Configuration system** for database path management
- `migrations/setup_database.py:setup_database()` - **Setup wizard** that creates database configuration
- `prt_src/tui/app.py` - **TUI app initialization** where database configuration is applied

### New Files
- `prt_src/fixture_manager.py` - New service to manage fixture database isolation (similar to debug mode)

## Step by Step Tasks

### Step 1: Create Fixture Database Manager
- Create `prt_src/fixture_manager.py` with `setup_fixture_mode()` function
- Follow the exact pattern from `setup_debug_mode()` in `cli.py`
- Function should create isolated `fixture.db` file in `prt_data/` directory
- Return configuration dict pointing to fixture database
- Include fixture data loading in the setup process

### Step 2: Update TUI Setup Screen
- Modify `prt_src/tui/screens/setup.py:_handle_load_fixtures()` method
- Replace direct `FixtureService.clear_and_load_fixtures()` call
- Use new fixture manager to create isolated database
- Update data service to use fixture configuration
- Ensure navigation continues to work with new database

### Step 3: Update CLI Setup Wizard
- Modify `migrations/setup_database.py:setup_database()` to support fixture mode
- Add fixture option to CLI setup wizard interface
- Use fixture manager when user chooses fixture data
- Ensure proper configuration handling for fixture mode

### Step 4: Update TUI App Initialization
- Modify `prt_src/tui/app.py` to handle fixture configuration
- Ensure app properly switches between real and fixture databases
- Maintain existing debug mode functionality
- Add proper logging for fixture vs real database usage

### Step 5: Add Configuration State Management
- Update configuration system to track database mode (real/fixture/debug)
- Add helper functions to determine current database mode
- Ensure clean transitions between modes
- Add safeguards to prevent accidental data loss

### Step 6: Create Comprehensive Tests
- Write tests for fixture database isolation in `tests/test_fixture_isolation.py`
- Test that real database is never modified during fixture loading
- Test proper database switching between real and fixture modes
- Test that app defaults back to real database on restart
- Add regression tests to prevent future data loss bugs

### Step 7: Update Documentation and User Interface
- Update setup screen text to clarify that fixture data is isolated
- Remove warning about "replacing existing data" since real data is safe
- Add clear indication when app is running in fixture mode
- Update help text and documentation to reflect safety improvements

### Step 8: Validation Testing
- Run validation commands to ensure bug is fixed with zero regressions
- Test both CLI and TUI setup workflows
- Verify real data safety across all scenarios
- Confirm proper database isolation and switching

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `source ./init.sh` - Activate development environment
- `./prt_env/bin/pytest tests/ -v` - Run full test suite to ensure no regressions
- `./prt_env/bin/pytest tests/test_fixture_isolation.py -v` - Run new fixture isolation tests
- `python -m prt_src.cli setup` - Test CLI setup wizard with fixture option (should create isolated DB)
- `python -m prt_src --setup` - Test TUI setup screen with fixture option (should create isolated DB)
- `ls prt_data/` - Verify separate fixture.db file is created alongside prt.db
- `sqlite3 prt_data/prt.db "SELECT COUNT(*) FROM contacts;"` - Verify real database is untouched
- `sqlite3 prt_data/fixture.db "SELECT COUNT(*) FROM contacts;"` - Verify fixture database has sample data
- `python -m prt_src` - Test that app properly starts with real database after fixture testing
- `./prt_env/bin/ruff check prt_src/ --fix` - Ensure code quality standards
- `./prt_env/bin/black prt_src/` - Ensure code formatting standards

## Notes
- This fix follows the existing `--debug` mode pattern which correctly isolates database files
- The solution eliminates the need for backup/restore functionality since real data is never touched
- Database isolation is simpler and safer than trying to backup/restore user data
- The fixture database should be temporary and automatically cleaned up or reused
- All existing debug mode functionality must remain unchanged
- This change makes fixture testing completely safe for users with existing data