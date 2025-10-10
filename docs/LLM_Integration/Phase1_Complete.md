# Phase 1 Complete: Database Schema Migration

**Date:** October 10, 2025
**Branch:** restore_old_llm_code
**Status:** ✅ COMPLETE

## What We Fixed

### The Problem
Critical schema mismatch between models.py and the actual database:

- **models.py** expected: `is_you`, `first_name`, `last_name` columns
- **Database** had: None of these columns (schema v5, last updated months ago)
- **Impact**: ALL contact queries failed with `OperationalError: no such column: contacts.first_name`

**Everything was broken:**
- ❌ LLM integration (couldn't query contacts)
- ❌ TUI (couldn't display contacts)
- ❌ CLI (contact operations failed)
- ❌ API (search_contacts() crashed)

### Root Cause
In commit a95a519 (Aug 31), someone added the columns to models.py and created a PostgreSQL-syntax migration file (`prt_src/migrations/add_is_you_column.sql`), but:
1. The migration was never run
2. The migration used PostgreSQL syntax (POSITION, SUBSTRING) not SQLite syntax (INSTR, SUBSTR)
3. SchemaManager didn't have a v5→v6 migration path

## The Solution

### Created v5→v6 Migration
Added `apply_migration_v5_to_v6()` to SchemaManager:

**Columns added:**
- `is_you` (BOOLEAN DEFAULT 0) - Marks the "You" contact for TUI
- `first_name` (VARCHAR(100)) - First name extracted from name field
- `last_name` (VARCHAR(100)) - Last name extracted from name field

**Index created:**
- `idx_contacts_is_you` - Fast lookup for "You" contact (partial index WHERE is_you = 1)

**Data migration:**
- Automatically splits existing `name` field into `first_name` and `last_name`
- Example: "John Smith" → first_name="John", last_name="Smith"
- Single names: "Madonna" → first_name="Madonna", last_name=""

### Migration Runner Script
Created `run_migration.py` for safe execution:

**Features:**
- `--check` flag to preview without running
- Automatic backup before migration (prt.v5.TIMESTAMP.backup)
- User confirmation required
- Schema verification after migration
- Clear error recovery instructions

**Usage:**
```bash
# Check if migration needed
./prt_env/bin/python run_migration.py --check

# Run migration
./prt_env/bin/python run_migration.py
```

## Test Results

### Migration Execution
```
✅ Backup created: prt.v5.20251010_221941.backup
✅ Added is_you column
✅ Added first_name column
✅ Added last_name column
✅ Created index for is_you lookup
✅ Populated first_name and last_name from name field
✅ Database successfully upgraded to version 6!
```

### Verification
**Schema verification:**
```
id                INTEGER       NOT NULL
name              VARCHAR(255)  NOT NULL
email             VARCHAR(255)
phone             VARCHAR(50)
profile_image     BLOB
created_at        DATETIME
updated_at        DATETIME
is_you            BOOLEAN       DEFAULT=0  ✅ NEW
first_name        VARCHAR(100)             ✅ NEW
last_name         VARCHAR(100)             ✅ NEW
```

**API verification:**
```python
api = PRTAPI()
contacts = api.list_all_contacts()
# ✅ Success! Found 36 contacts
# ✅ No "no such column" errors
# ✅ first_name/last_name accessible via ORM
```

## Files Changed

### Modified
- `prt_src/schema_manager.py`
  - Bumped CURRENT_VERSION from 5 to 6
  - Added `apply_migration_v5_to_v6()` method
  - Added migration paths: (5,6), (4,6), (3,6), (2,6), (1,6)

### Created
- `run_migration.py` - Safe migration runner script

### Committed
- Commit: 9d90ee4
- Message: "Fix schema mismatch: Add v5→v6 migration for TUI contact columns"

## Next Steps

**Phase 2: LLM Integration Testing**

Now that the database schema matches models.py, we can test the LLM integration:

1. Test via TUI chat screen
2. Try basic queries:
   - "Show me all contacts"
   - "Find John"
   - "What's Alice's email?"
3. Document what works and what doesn't
4. Move to Phase 2 (reliability testing) if basic queries work

**Known Issues to Address Later:**
- Pre-commit ruff errors in old migration code (B904, SIM105) - cosmetic, not blocking
- Some contacts have unusual names (e.g., "(No name)") - data quality issue

## Lessons Learned

1. **Always run migrations immediately after creating them**
   - Don't let schema and code drift apart

2. **Database-specific SQL matters**
   - PostgreSQL syntax ≠ SQLite syntax
   - POSITION/SUBSTRING → INSTR/SUBSTR
   - BOOLEAN TRUE/FALSE → 1/0

3. **SchemaManager is well-designed**
   - Automatic backups before migrations
   - Clear recovery instructions
   - Version tracking in schema_version table
   - Safe, incremental migrations

4. **Test the whole stack**
   - Models updated? Run migration.
   - Migration created? Test it immediately.
   - Schema changed? Verify API still works.

---

**Status:** ✅ Phase 1 COMPLETE - Database schema fixed, ready for LLM testing
**Time spent:** ~50 minutes (analysis, migration creation, testing, documentation)
**Next:** Manual LLM testing via TUI
