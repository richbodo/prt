# Bug: Contacts with Images Performance Optimization Failure

## Bug Description
The performance test `test_contacts_with_images_vs_full_scan_performance` is failing because the "optimized" query in `get_contacts_with_images()` is actually 1.8x slower than the naive approach. The test shows:
- **Optimized query**: 6.1ms
- **Naive full scan**: 3.3ms
- **Expected**: Optimized should be ≤ 1.5x slower than naive (≤ 5.0ms), but it's actually 1.8x slower

The assertion fails: `AssertionError: Optimized query shouldn't be significantly slower than naive approach`

## Problem Statement
The `get_contacts_with_images()` method, despite being labeled as "optimized" and having database indexing, performs worse than a simple `list_all_contacts()` followed by Python filtering. This undermines the performance benefits expected from database-level optimization.

## Solution Statement
Optimize the `get_contacts_with_images()` method by:
1. **Removing unnecessary overhead** - eliminate excessive image validation and logging during query execution
2. **Optimizing database queries** - use bulk operations with joins instead of N+1 queries for relationship data
3. **Improving database indexing** - create composite index covering both filtering and sorting requirements
4. **Deferring expensive operations** - move image validation to a separate method when needed for specific use cases

## Steps to Reproduce
```bash
source ./init.sh
./prt_env/bin/pytest tests/test_contacts_with_images_performance.py::test_contacts_with_images_vs_full_scan_performance -v
```
Expected: Test should pass with optimized query being faster or at most 1.5x slower than naive approach
Actual: Test fails with optimized query being 1.8x slower (6.1ms vs 3.3ms)

## Root Cause Analysis
**Primary Performance Issues in `get_contacts_with_images()`:**

1. **Excessive Processing Overhead** (Major Impact):
   - Image size calculation: `len(contact.profile_image)` for each contact
   - Image validation: size checks (< 100 bytes, > 5MB), MIME type validation
   - Complex logging: multiple logger calls per contact with string formatting
   - Data analysis: `total_size` and `corrupted_count` calculations

2. **N+1 Query Problem** (Major Impact):
   - Both methods call `get_relationship_info(contact.id)` for each contact
   - This executes separate SQL queries for relationship data instead of using joins
   - In a dataset with N contacts, this results in N+1 total database queries

3. **Suboptimal Database Index** (Moderate Impact):
   - Current index: `idx_contacts_profile_image_not_null ON contacts(id) WHERE profile_image IS NOT NULL`
   - Query pattern: `WHERE profile_image IS NOT NULL ORDER BY name`
   - Index doesn't cover the `ORDER BY name` clause, requiring additional sorting

4. **False Optimization Assumption**:
   - The "naive" approach benefits from bulk list comprehension in Python
   - The "optimized" approach does more work per contact than the filtering operation

## Relevant Files
Use these files to fix the bug:

- **`prt_src/api.py`** - Contains the `get_contacts_with_images()` method that needs optimization and the `list_all_contacts()` method for comparison
- **`tests/test_contacts_with_images_performance.py`** - Contains the failing test that needs to pass after optimization
- **`migrations/005_add_performance_indexes.sql`** - Contains current index definition that may need improvement
- **`prt_src/db.py`** - Contains `get_relationship_info()` method that causes N+1 query problem

### New Files
- **`migrations/006_optimize_image_queries.sql`** - New migration to add composite index for optimal query performance

## Step by Step Tasks

### Step 1: Create Optimized Database Index
- Create new migration `migrations/006_optimize_image_queries.sql`
- Add composite index: `CREATE INDEX IF NOT EXISTS idx_contacts_profile_image_name ON contacts(name) WHERE profile_image IS NOT NULL`
- This covers both the WHERE clause and ORDER BY clause in a single index

### Step 2: Optimize the API Query Method
- Refactor `get_contacts_with_images()` in `prt_src/api.py` to remove performance overhead:
  - Remove per-contact image validation and size calculations during query
  - Minimize logging to essential information only
  - Remove `total_size` and `corrupted_count` tracking from query path
  - Keep the core database query but make it lean and fast

### Step 3: Add Efficient Bulk Relationship Loading
- Create optimized version of relationship loading in `prt_src/api.py`:
  - Add `_get_bulk_relationship_info()` method that fetches all relationship data in one or two queries
  - Use this in `get_contacts_with_images()` instead of calling `get_relationship_info()` per contact
  - Maintain the same output format for API compatibility

### Step 4: Create Separate Image Validation Method
- Add `validate_contact_images()` method in `prt_src/api.py` for when detailed image analysis is needed
- Move image validation logic (size checks, MIME type validation, corruption detection) to this separate method
- This keeps the query fast while preserving validation functionality for specific use cases

### Step 5: Run Database Migration
- Execute the new migration to create the optimized index
- Verify the index exists and is being used by the query

### Step 6: Update and Run Performance Tests
- Run the failing test to verify the optimization fixes the performance issue
- Run all performance tests to ensure no regressions
- Verify the optimized query is now faster than or comparable to the naive approach

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

```bash
# Setup environment
source ./init.sh

# Run the database migration to add optimized index
./prt_env/bin/python -c "
from prt_src.schema_manager import SchemaManager
from prt_src.db import Database
from pathlib import Path
import tempfile

# Create test database and apply migration
with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
    db = Database(Path(tmp.name))
    db.connect()
    manager = SchemaManager(db)
    success = manager.migrate_safely()
    print(f'Migration successful: {success}')
    db.disconnect()
"

# Run the specific failing test to verify fix
./prt_env/bin/pytest tests/test_contacts_with_images_performance.py::test_contacts_with_images_vs_full_scan_performance -v

# Run all performance tests to check for regressions
./prt_env/bin/pytest tests/test_contacts_with_images_performance.py -v

# Run index verification test
./prt_env/bin/pytest tests/test_contacts_with_images_performance.py::test_index_usage_verification -v

# Run broader contact-related tests to ensure no functional regressions
./prt_env/bin/pytest tests/test_api.py -v -k "contact"

# Run database performance tests
./prt_env/bin/pytest tests/test_database_performance_indexes.py -v

# Verify overall test suite still passes
./prt_env/bin/pytest tests/ --tb=short -q
```

## Notes
- The fix maintains API compatibility - `get_contacts_with_images()` returns the same data structure
- Image validation functionality is preserved but moved to a separate method for optional use
- The solution addresses the root cause (excessive overhead) rather than just adjusting test thresholds
- Database indexing optimization may benefit other queries that filter by profile_image presence
- Consider making image validation configurable in future iterations if performance vs. data quality trade-offs are needed
- The N+1 query optimization will benefit all contact listing operations, not just image queries