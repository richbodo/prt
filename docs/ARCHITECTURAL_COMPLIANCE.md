# Architectural Compliance Guide

This document defines the architectural rules and patterns that all PRT code must follow to maintain consistency, maintainability, and proper separation of concerns.

## Architectural Rules

PRT enforces a strict **API-first architecture** with the following mandatory rules:

### Rule 1: API Layer Ownership
- **All business logic** must be implemented in the PRTAPI layer (`prt_src/api.py`)
- **All data access** must go through the PRTAPI layer
- **No interface layer** (CLI, TUI, LLM tools) may bypass the API layer

### Rule 2: Database Access Restriction
- **Only the API layer** may access the database layer (`prt_src/db.py`)
- **Interface layers** must never use `self.api.db.*` patterns
- **Session access** from interface layers is prohibited

### Rule 3: Core Module Isolation
- **Core modules** (`prt_src/core/`) may only be imported by the API layer
- **Interface layers** must never import core modules directly
- **All core functionality** must be exposed through API layer methods

### Rule 4: Consistent Error Handling
- **All API methods** must return consistent error response formats
- **Interface layers** must handle errors consistently
- **Database errors** must be caught and transformed by the API layer

## Architectural Layers

### 1. API Layer (`prt_src/api.py`)
- **Single source of truth** for all business logic
- Handles database operations through `prt_src/db.py`
- Provides consistent interface for all consumers
- Contains comprehensive error handling and logging

### 2. Interface Layers
- **CLI** (`prt_src/cli.py`): Command-line interface
- **TUI** (`prt_src/tui/`): Text user interface
- **LLM Tools** (`prt_src/llm_tools.py`): AI-powered chat functionality

### 3. Data Layer (`prt_src/db.py`)
- Database connection and low-level operations
- Only accessed through API layer
- Never accessed directly by interface layers

### 4. Core Modules (`prt_src/core/`)
- Business logic and specialized operations
- Only accessed through API layer
- Never imported directly by interface layers

## Enforcement Rules

### ✅ ALLOWED Patterns

```python
# TUI DataService - API access only
from prt_src.api import PRTAPI

class DataService:
    def __init__(self, api: PRTAPI = None):
        self.api = api or PRTAPI()

    async def get_contacts(self):
        return self.api.list_all_contacts()  # ✅ Uses API method
```

```python
# CLI - Direct API usage
from prt_src.api import PRTAPI

def handle_search(query: str):
    api = PRTAPI()
    return api.search_contacts(query)  # ✅ Uses API method
```

### ❌ PROHIBITED Patterns

```python
# ❌ Direct database access from TUI
self.api.db.get_all_relationships()  # VIOLATION

# ❌ Direct core module imports from TUI
from prt_src.core.search_unified import UnifiedSearchAPI  # VIOLATION

# ❌ Direct session access from TUI
self.api.db.session.query(Note).filter(...)  # VIOLATION
```

## Required Methods in PRTAPI

The API layer must provide complete functionality for all interface needs:

### Contact Operations
- `list_all_contacts()`, `search_contacts()`, `get_contact()`
- `add_contact()`, `update_contact()`, `delete_contact()`
- `tag_contact()`, `remove_tag_from_contact()`

### Relationship Operations
- `get_all_relationships()`, `search_relationships()`
- `add_relationship()`, `list_all_relationship_types()`
- `create_relationship_type()`, `delete_relationship_type()`

### Note Operations
- `get_all_notes()`, `search_notes()`, `add_note()`
- `update_note_by_id()`, `delete_note_by_id()`, `get_note_by_id()`

### Search Operations
- `unified_search()` - Wraps core search functionality
- Individual search methods for each entity type

### Database Management
- `vacuum_database()`, `export_relationships_data()`
- `get_database_stats()`, `backup_database()`

## Testing and Validation

### Architectural Compliance Tests

Location: `tests/integration/test_architectural_compliance.py`

The compliance test suite validates:

1. **No Direct Database Access**: Scans TUI code for `self.api.db.` patterns
2. **No Direct Core Imports**: Scans TUI code for `from prt_src.core.` imports
3. **API Method Coverage**: Ensures PRTAPI has all required methods
4. **Behavior Consistency**: CLI and TUI produce identical results
5. **Performance Equivalence**: DataService performs comparably to direct API
6. **Error Handling**: Consistent error behavior across interfaces

### Validation Commands

```bash
# Run architectural compliance tests
./prt_env/bin/pytest tests/integration/test_architectural_compliance.py -v

# Verify no architectural violations
grep -r "from prt_src\.core\." prt_src/tui/          # Should return empty
grep -r "\.db\." prt_src/tui/services/data.py       # Should return empty
grep -r "session\." prt_src/tui/services/data.py    # Should return empty

# Test functionality
python -m prt_src --debug                           # Launch TUI
./prt_env/bin/pytest tests/test_api.py -v          # Validate API methods
./prt_env/bin/pytest tests/test_tui_*.py -v        # Validate TUI functionality
```

## Development Guidelines

### For TUI Development

1. **Always use DataService** - Never access API directly from TUI components
2. **DataService uses API only** - Never add database access to DataService
3. **Import restrictions** - Only import from:
   - `prt_src.api` (through DataService)
   - `prt_src.models` (for type hints only)
   - `prt_src.logging_config`
   - `prt_src.tui.*` (internal TUI modules)
   - Standard library and Textual framework

### For API Development

1. **Single responsibility** - API layer owns all business logic
2. **Comprehensive coverage** - Provide methods for all interface needs
3. **Consistent error handling** - Return predictable error responses
4. **Performance optimization** - Cache and optimize for common operations

### For Core Module Development

1. **API integration** - Ensure new core functionality is accessible via API
2. **No direct usage** - Core modules should only be imported by API layer
3. **Documentation** - Document API methods when adding core functionality

## Migration Strategy

When adding new functionality:

1. **Add to API first** - Implement business logic in PRTAPI
2. **Update DataService** - Add wrapper methods in TUI DataService
3. **Add compliance tests** - Ensure new functionality follows patterns
4. **Update CLI if needed** - Maintain feature parity across interfaces

When refactoring existing code:

1. **Identify violations** - Use grep commands to find direct access patterns
2. **Add missing API methods** - Enhance PRTAPI with needed functionality
3. **Refactor layer by layer** - Fix TUI, then CLI, then test
4. **Validate thoroughly** - Run compliance tests after each change

## Benefits

This architectural approach provides:

- **Single source of truth**: All business logic centralized in API layer
- **Consistent behavior**: All interfaces use identical data access patterns
- **Better testability**: Clear separation enables effective mocking and testing
- **Maintainability**: Changes to business logic only require API layer updates
- **Extensibility**: New interfaces can be added without duplicating logic

## Enforcement

### Automated Validation

Architectural compliance is enforced through:

- **Pre-commit hooks**: Scan for prohibited patterns before commits
- **CI pipeline**: Run compliance tests on all pull requests
- **Integration tests**: Validate architectural rules in `tests/integration/test_architectural_compliance.py`

### Code Review Requirements

All code changes must:

1. Follow API-first patterns
2. Avoid direct database or core module access from interfaces
3. Add necessary API methods when adding new functionality
4. Include compliance tests for new architectural components

## Adding New Functionality

### Step 1: API Layer First
```python
# prt_src/api.py
def new_feature_method(self, param: str) -> Dict[str, Any]:
    """New feature implementation."""
    try:
        result = self.db.new_feature_operation(param)
        return {"success": True, "data": result}
    except Exception as e:
        self.logger.error(f"Error in new feature: {e}")
        return {"success": False, "error": str(e)}
```

### Step 2: Interface Layer Integration
```python
# prt_src/tui/services/data.py
async def new_feature(self, param: str) -> Any:
    """TUI wrapper for new feature."""
    result = self.api.new_feature_method(param)
    return result.get("data") if result.get("success") else None
```

### Step 3: Compliance Validation
- Add tests in `test_architectural_compliance.py`
- Verify no architectural rule violations
- Run full compliance test suite

## Extending Architecture

### Adding New Interface Types
1. Create new interface module (e.g., `prt_src/web/`)
2. Interface must only import from `prt_src.api`
3. Add compliance tests for new interface
4. Document interface-specific patterns

### Adding New Core Modules
1. Implement core functionality
2. Add API layer methods to expose functionality
3. Update required API method documentation
4. Add compliance tests

### Adding New Rules
1. Define rule clearly in this document
2. Add automated validation in compliance tests
3. Update enforcement tooling
4. Document rule exceptions (if any)

## Rule Exceptions

### Intentional API Layer Core Imports
The API layer may import core modules when:
- The import provides business logic needed by the API
- The import is documented as intentional architecture
- Alternative API-only implementation would be impractical

### Model Imports for Type Hints
Interface layers may import models when:
- Imports are only used for type annotations
- No model instances are created or manipulated
- Import uses `from __future__ import annotations` pattern

## Validation Commands

```bash
# Check for architectural violations
grep -r "from prt_src\.core\." prt_src/tui/
grep -r "\.db\." prt_src/tui/services/data.py
grep -r "session\." prt_src/tui/services/data.py

# Run compliance test suite
./prt_env/bin/pytest tests/integration/test_architectural_compliance.py -v

# Validate API completeness
./prt_env/bin/pytest tests/test_api.py -v
```