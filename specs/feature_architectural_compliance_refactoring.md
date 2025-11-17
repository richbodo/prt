# Feature: Architectural Compliance Refactoring

## Feature Description
Eliminate code duplication and architectural violations by refactoring the TUI DataService to strictly follow the intended API-first architecture. Currently, the TUI DataService bypasses the PRTAPI layer and accesses core modules and database directly, creating maintenance burden and inconsistency. This refactoring will consolidate all data access through the PRTAPI layer, eliminate duplicate implementations, and ensure architectural consistency across CLI, TUI, and LLM interfaces.

## User Story
As a developer maintaining PRT
I want all interfaces (CLI, TUI, LLM) to use consistent data access patterns through the PRTAPI
So that I can maintain a single source of truth for business logic, reduce code duplication, and ensure consistent behavior across all interfaces.

## Problem Statement
Analysis revealed significant architectural violations in the TUI layer:

1. **TUI DataService Direct Database Access**: Lines like `self.api.db.get_all_relationships()` and `self.api.db.session.query(Note).filter()` bypass the API abstraction
2. **Direct Core Module Imports**: `from prt_src.core.search_unified import UnifiedSearchAPI` violates the API-first pattern
3. **Code Duplication**: DataService reimplements functionality that already exists in PRTAPI with different implementations
4. **Inconsistent Patterns**: Some operations use API methods while others bypass to database/core directly
5. **Maintenance Burden**: Changes require updates in multiple places instead of single API layer

Current compliance rating: **C+ (75%)** - mostly good but with significant violations in TUI layer.

## Solution Statement
Refactor the TUI DataService to be a pure wrapper around PRTAPI methods, eliminating all direct database and core module access. Enhance PRTAPI with missing methods needed by DataService. Create a migration strategy that maintains existing TUI functionality while ensuring all data flows through the API layer consistently.

## Relevant Files
Use these files to implement the feature:

- `prt_src/api.py` - Main API layer that needs enhancement with missing methods
- `prt_src/tui/services/data.py` - Primary target for refactoring to remove architectural violations
- `prt_src/tui/app.py` - TUIDatabase extension needs evaluation for API compliance
- `prt_src/db.py` - May need new methods to support enhanced API functionality
- `prt_src/core/relationships.py` - Core relationship operations that should only be accessed via API
- `prt_src/core/search_unified.py` - Unified search that should only be accessed via API

### New Files
- `tests/integration/test_architectural_compliance.py` - Comprehensive tests to validate API-only access patterns
- `docs/ARCHITECTURAL_COMPLIANCE.md` - Documentation of the enforced architectural patterns

## Implementation Plan

### Phase 1: Foundation
Analyze and enhance the PRTAPI with missing methods currently implemented in TUI DataService. Ensure API layer has complete functionality needed by all interfaces.

### Phase 2: Core Implementation
Refactor TUI DataService to remove all direct database and core module access, converting all operations to use PRTAPI methods exclusively.

### Phase 3: Integration
Validate that TUI functionality remains identical while using pure API access. Add architectural compliance tests to prevent future violations.

## Step by Step Tasks

### Step 1: API Layer Enhancement
- Audit PRTAPI for missing methods used by TUI DataService
- Add missing relationship management methods to PRTAPI
- Add missing note management by ID methods to PRTAPI
- Add unified search wrapper method to PRTAPI
- Add relationship analytics methods to PRTAPI
- Test all new API methods work correctly

### Step 2: Create Architectural Compliance Tests
- Create integration test file to validate API-only access
- Add tests that verify no direct database access from TUI layer
- Add tests that verify no direct core module imports from TUI layer
- Add tests that verify consistent behavior between CLI and TUI data access
- Run tests to establish baseline before refactoring

### Step 3: Refactor TUI DataService Relationship Operations
- Replace `self.api.db.get_all_relationships()` with new PRTAPI method
- Replace direct RelationshipOperations usage with PRTAPI methods
- Replace direct database relationship queries with PRTAPI methods
- Test relationship functionality works identically in TUI

### Step 4: Refactor TUI DataService Note Operations
- Replace direct SQLAlchemy session note operations with PRTAPI methods
- Replace note update/delete direct database calls with API calls
- Test note functionality works identically in TUI

### Step 5: Refactor TUI DataService Search Operations
- Replace direct UnifiedSearchAPI usage with new PRTAPI wrapper method
- Remove direct core module imports from DataService
- Test search functionality works identically in TUI

### Step 6: Refactor TUI DataService Database Management
- Replace direct database statistics calls with PRTAPI methods
- Replace direct database session management with API methods
- Test database management operations work identically in TUI

### Step 7: Refactor TUIDatabase Extension
- Evaluate TUIDatabase class for API compliance
- Move TUI-specific database methods to PRTAPI if needed
- Ensure TUIDatabase only extends for TUI-specific functionality, not data access

### Step 8: Remove All Direct Imports
- Remove all `from prt_src.core.*` imports from TUI layer
- Remove all `from prt_src.db import` statements from TUI services
- Remove all direct session access patterns
- Verify TUI layer only imports from API and models for type hints

### Step 9: Comprehensive Testing
- Run full test suite to ensure no regressions
- Test CLI functionality remains identical
- Test TUI functionality remains identical
- Test LLM tools functionality remains identical
- Run architectural compliance tests

### Step 10: Validation and Documentation
- Run validation commands to confirm zero regressions
- Update architectural documentation
- Create enforcement guidelines for future development
- Document the API-first architectural pattern

## Testing Strategy

### Unit Tests
- Test each new PRTAPI method individually
- Test DataService methods delegate correctly to API
- Test error handling in refactored DataService methods
- Mock PRTAPI in DataService tests to verify delegation

### Integration Tests
- Test TUI operations end-to-end through refactored DataService
- Test CLI and TUI produce identical results for same operations
- Test LLM tools work correctly with enhanced API
- Test relationship operations work across all interfaces

### Edge Cases
- Test DataService error handling when PRTAPI methods fail
- Test large dataset operations through API layer
- Test concurrent access patterns through API layer
- Test database connection failures propagate correctly through API

## Acceptance Criteria
- [ ] Zero direct database access from TUI DataService
- [ ] Zero direct core module imports from TUI layer
- [ ] All TUI operations use PRTAPI methods exclusively
- [ ] CLI and TUI produce identical results for equivalent operations
- [ ] LLM tools continue working without changes
- [ ] Full test suite passes with zero regressions
- [ ] Architectural compliance tests pass
- [ ] TUI performance remains equivalent to current implementation
- [ ] Code duplication between API and DataService eliminated
- [ ] Consistent error handling across all interfaces

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `./prt_env/bin/pytest tests/integration/test_architectural_compliance.py -v` - Run new architectural compliance tests
- `./prt_env/bin/pytest tests/test_tui_*.py -v` - Run all TUI tests to validate no regressions
- `./prt_env/bin/pytest tests/test_api.py -v` - Run API tests to validate new methods work
- `./prt_env/bin/pytest tests/ -m "not integration" -v` - Run fast unit tests for quick validation
- `./scripts/run-ci-tests.sh` - Run full CI test suite to ensure zero regressions
- `python -m prt_src --debug` - Launch TUI in debug mode to validate functionality
- `python -m prt_src --cli --debug` - Launch CLI in debug mode to validate functionality
- `python -m prt_src --chat="list all contacts" --model gpt-oss-20b --debug` - Test LLM chat functionality
- `grep -r "from prt_src\.core\." prt_src/tui/` - Verify no direct core imports in TUI (should return empty)
- `grep -r "\.db\." prt_src/tui/services/data.py` - Verify no direct database access in DataService (should return empty)
- `grep -r "session\." prt_src/tui/services/data.py` - Verify no direct session access (should return empty)

## Notes

### Migration Strategy
This refactoring follows a safe migration approach:
1. Add new API methods before removing old implementations
2. Maintain existing interfaces during transition
3. Use comprehensive testing to prevent regressions
4. Implement in phases to isolate any issues

### Performance Considerations
The refactoring should maintain or improve performance by:
- Eliminating duplicate query implementations
- Leveraging existing API optimizations
- Reducing memory usage through consistent object patterns
- Maintaining connection pooling through API layer

### Future Prevention
After this refactoring:
- Add pre-commit hooks to check for architectural violations
- Document clear guidelines for data access patterns
- Create example code snippets for common operations
- Consider architectural tests in CI pipeline

### Estimated Impact
- **Reduced maintenance burden**: Single source of truth for business logic
- **Improved consistency**: All interfaces use same data access patterns
- **Better testability**: Easier to mock and test individual layers
- **Clearer separation of concerns**: API layer owns all data operations
- **Foundation for future features**: Clean architecture supports extensibility