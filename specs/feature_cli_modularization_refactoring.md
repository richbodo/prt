# Feature: CLI Modularization and Architecture Refactoring

**Type**: Feature Enhancement / Refactoring
**Priority**: High
**Complexity**: High
**Estimated Time**: 2 weeks (10 working days)

## Summary

Refactor the monolithic 3,218-line `prt_src/cli.py` into a well-structured modular architecture that separates concerns, improves testability, and enables both humans and LLMs to reason about the codebase effectively. The current file mixes three independent concerns (bootstrapping, menu handlers, and services) into a single module that has become difficult to maintain and extend.

## Problem Statement

The current `prt_src/cli.py` has severe architectural issues that impact maintainability:

### Current State Issues

1. **Excessive Size**: 3,218 lines in a single module with 63 functions
2. **Mixed Concerns**: Three largely independent responsibilities tangled together:
   - **Bootstrapping/Setup** (10+ functions): `setup_debug_mode`, `check_setup_status`, `run_setup_wizard`, `run_interactive_cli`, `_launch_tui_with_fallback`
   - **Domain Handlers** (40+ functions): All contact/tag/note/relationship menu handlers and utilities
   - **Services** (13+ functions): Export, import, directory generation, image handling

3. **Poor Separation of Concerns**:
   - Entrypoint logic tangled with domain handlers
   - Reusable services (export, import) locked inside CLI-specific code
   - Menu loops, handlers, and domain helpers all in one file (~2,000 lines)

4. **Testability Issues**:
   - Cannot test services without importing entire CLI machinery
   - Mock setup becomes complex due to deep coupling
   - No clear boundaries for unit vs integration testing

5. **Context Window Problems**:
   - Too large for single LLM context window
   - Unrelated features share namespace
   - Difficult to understand impact of changes

6. **Help Text Duplication**:
   - Help text appears in 3 places: `print_custom_help()`, `typer.Typer()` help, and individual `typer.Option()` strings
   - Maintaining consistency is manual and error-prone

### Evidence from Analysis

```
Total Functions: 63
├── Bootstrap/Setup: 10 functions (~400 lines)
├── Menu Handlers: 40 functions (~2,000 lines)
│   ├── Contacts: 2 functions
│   ├── Tags: 5 functions
│   ├── Notes: 7 functions
│   ├── Relationships: 14 functions
│   ├── Database: 5 functions
│   └── Search: 1 function
├── Services: 13 functions (~600 lines)
│   ├── Export: 6 functions
│   ├── Import: 2 functions
│   └── Directory: 5 functions
└── UI Utilities: ~200 lines
```

## Solution Overview

Create a modular `prt_src/cli/` directory structure that:
1. Separates commands (thin Typer wrappers) from business logic
2. Extracts reusable services into standalone modules
3. Groups domain handlers by concern (contacts, tags, notes, relationships)
4. Provides backwards compatibility during migration
5. Externalizes help text to markdown

### Core Architecture Principles

- **Thin Commands**: Typer commands only parse arguments and delegate
- **Domain Handlers**: Menu systems grouped by business domain
- **Pure Services**: Business logic with zero UI dependencies
- **Reusable UI**: Display/prompt utilities shared across handlers
- **Clean Bootstrap**: Application initialization separate from domain logic

## Detailed Architecture

### Proposed Directory Structure

```
prt_src/
├── cli/
│   ├── __init__.py                 # Main Typer app, delegates to submodules
│   ├── help_text.md               # Main CLI help documentation
│   ├── help.py                    # Help text loading & formatting
│   │
│   ├── commands/                  # Typer commands (thin wrappers)
│   │   ├── __init__.py
│   │   ├── main.py               # main() entrypoint (~50 lines)
│   │   ├── setup.py              # test_db, db_status commands
│   │   ├── models.py             # list_models command
│   │   ├── debug.py              # prt_debug_info command
│   │   └── chat.py               # Chat mode coordination
│   │
│   ├── bootstrap/                 # Application initialization
│   │   ├── __init__.py
│   │   ├── launcher.py           # run_interactive_cli, _launch_tui_with_fallback
│   │   ├── setup.py              # setup_debug_mode, check_setup_status, run_setup_wizard
│   │   ├── health.py             # check_database_health, handle_database_error
│   │   └── guidance.py           # show_empty_database_guidance
│   │
│   ├── handlers/                  # Domain-specific menu handlers
│   │   ├── __init__.py
│   │   ├── menu.py               # show_main_menu (menu coordinator)
│   │   ├── contacts.py           # 2 functions: handle_contacts_view, handle_contact_search_results
│   │   ├── tags.py               # 5 functions: handle_tags_menu, handle_create_tag, etc.
│   │   ├── notes.py              # 7 functions: handle_notes_menu, handle_create_note, etc.
│   │   ├── relationships.py      # 14 functions: handle_relationships_menu, etc.
│   │   ├── database.py           # 5 functions: handle_database_menu, etc.
│   │   └── search.py             # 1 function: handle_search_menu
│   │
│   ├── services/                  # Reusable business logic
│   │   ├── __init__.py
│   │   ├── export.py             # export_search_results, clean_results_for_json
│   │   ├── images.py             # export_profile_images_from_results, export_contact_profile_images
│   │   ├── directory.py          # offer_directory_generation, create_export_readme
│   │   ├── import_google.py      # handle_import_google_takeout, handle_import_google_contacts
│   │   └── llm.py                # start_llm_chat (LLM integration logic)
│   │
│   └── ui/                        # UI utilities and helpers
│       ├── __init__.py
│       ├── pagination.py         # paginate_results
│       ├── prompts.py            # smart_continue_prompt, _get_valid_date
│       ├── selection.py          # _validate_contact_id, _display_contacts_paginated
│       └── formatting.py         # show_full_note, display helpers
│
└── cli.py                         # DEPRECATED: Backwards compatibility shim
```

## Implementation Plan

### Phase 1: Extract Help System (Day 1) - LOW RISK

**Goal**: Single source of truth for help text.

**Tasks**:
1. Create `prt_src/cli/` directory structure
2. Create `prt_src/cli/help.py` with `CLI_OPTIONS` dict
3. Create `prt_src/cli/help_text.md` with main help content
4. Modify `prt_src/cli.py` to import from `help.py`
5. Update `print_custom_help()` to use markdown file
6. Update typer.Option() calls to use `CLI_OPTIONS` dict

**Validation**:
```bash
python -m prt_src --help  # Should show same help text
python -m prt_src.cli.help  # Test help loading directly
```

### Phase 2: Extract Services (Days 2-3) - MEDIUM RISK

**Goal**: Pure business logic modules with zero UI dependencies.

**Tasks**:
1. Create `prt_src/cli/services/` directory
2. Extract export, images, directory, import, and LLM functions
3. Write unit tests for each service module
4. Update imports in `prt_src/cli.py`

**Validation**:
```bash
./prt_env/bin/pytest tests/unit/cli/test_services_*.py -v
python -m prt_src --debug  # Test export functionality
```

### Phase 3: Extract UI Utilities (Day 4) - LOW RISK

**Goal**: Reusable display and prompt utilities.

**Tasks**:
1. Create `prt_src/cli/ui/` directory
2. Extract pagination, prompts, selection, and formatting functions
3. Write tests for UI utilities
4. Update imports in `prt_src/cli.py`

**Validation**:
```bash
./prt_env/bin/pytest tests/unit/cli/test_ui_*.py -v
python -m prt_src --debug  # Test interactive menus
```

### Phase 4: Extract Bootstrap Layer (Days 5-6) - MEDIUM RISK

**Goal**: Separate application initialization from domain logic.

**Tasks**:
1. Create `prt_src/cli/bootstrap/` directory
2. Extract launcher, setup, health, and guidance functions
3. Write integration tests for bootstrap
4. Update imports in `prt_src/cli.py`

**Validation**:
```bash
./prt_env/bin/pytest tests/integration/cli/test_bootstrap_*.py -v
python -m prt_src --setup  # Test setup wizard
python -m prt_src --debug  # Test debug mode
```

### Phase 5: Extract Domain Handlers (Days 7-9) - HIGH RISK

**Goal**: Group menu handlers by business domain.

**Tasks**:
1. Create `prt_src/cli/handlers/` directory
2. Extract menu, contacts, tags, notes, relationships, database, and search handlers
3. Write integration tests for each handler module
4. Update imports in `prt_src/cli.py`

**Validation**:
```bash
./prt_env/bin/pytest tests/integration/cli/test_handlers_*.py -v
python -m prt_src --debug --cli  # Test all CLI menus
```

### Phase 6: Create Command Layer (Day 10) - MEDIUM RISK

**Goal**: Thin Typer command wrappers that delegate to handlers.

**Tasks**:
1. Create `prt_src/cli/commands/` directory
2. Create command modules for main, setup, models, debug, and chat
3. Update `prt_src/cli/__init__.py` to export app
4. Convert `prt_src/cli.py` to deprecation shim

**Validation**:
```bash
./prt_env/bin/pytest tests/unit/cli/test_commands_*.py -v
python -m prt_src --help
python -m prt_src test-db
python -m prt_src list-models
```

## Files to Modify

### New Files to Create (~31 new modules)

**Help System** (3 files):
- `prt_src/cli/__init__.py`
- `prt_src/cli/help.py`
- `prt_src/cli/help_text.md`

**Commands** (6 files):
- `prt_src/cli/commands/__init__.py`
- `prt_src/cli/commands/main.py`
- `prt_src/cli/commands/setup.py`
- `prt_src/cli/commands/models.py`
- `prt_src/cli/commands/debug.py`
- `prt_src/cli/commands/chat.py`

**Bootstrap** (5 files):
- `prt_src/cli/bootstrap/__init__.py`
- `prt_src/cli/bootstrap/launcher.py`
- `prt_src/cli/bootstrap/setup.py`
- `prt_src/cli/bootstrap/health.py`
- `prt_src/cli/bootstrap/guidance.py`

**Handlers** (8 files):
- `prt_src/cli/handlers/__init__.py`
- `prt_src/cli/handlers/menu.py`
- `prt_src/cli/handlers/contacts.py`
- `prt_src/cli/handlers/tags.py`
- `prt_src/cli/handlers/notes.py`
- `prt_src/cli/handlers/relationships.py`
- `prt_src/cli/handlers/database.py`
- `prt_src/cli/handlers/search.py`

**Services** (6 files):
- `prt_src/cli/services/__init__.py`
- `prt_src/cli/services/export.py`
- `prt_src/cli/services/images.py`
- `prt_src/cli/services/directory.py`
- `prt_src/cli/services/import_google.py`
- `prt_src/cli/services/llm.py`

**UI Utilities** (5 files):
- `prt_src/cli/ui/__init__.py`
- `prt_src/cli/ui/pagination.py`
- `prt_src/cli/ui/prompts.py`
- `prt_src/cli/ui/selection.py`
- `prt_src/cli/ui/formatting.py`

**Documentation** (1 file):
- `docs/CLI_ARCHITECTURE.md` (new)

### Existing Files to Modify

**Major Modifications**:
- `prt_src/cli.py` - Convert to deprecation shim (~3,200 → ~100 lines)

**Minor Modifications**:
- `prt_src/__main__.py` - Update imports to use new structure
- `docs/DEV_SETUP.md` - Update with new import examples

## Acceptance Criteria

### Functional Requirements

- [ ] All existing CLI functionality works identically
- [ ] All 63 functions from original `cli.py` are preserved and working
- [ ] All menu systems function correctly
- [ ] Export/import functionality works
- [ ] Setup wizard works
- [ ] Debug mode works
- [ ] TUI launcher works
- [ ] Chat mode works
- [ ] All Typer commands work (`test-db`, `list-models`, etc.)

### Architectural Requirements

- [ ] No module exceeds 500 lines (except relationships.py at ~800)
- [ ] Services have zero UI dependencies
- [ ] Commands are thin wrappers (<100 lines each)
- [ ] Clear separation of concerns achieved
- [ ] Circular imports avoided
- [ ] Import graph is clean and understandable

### Testing Requirements

- [ ] Unit tests for all service modules (100% coverage target)
- [ ] Unit tests for all UI utilities
- [ ] Integration tests for all handlers
- [ ] Integration tests for bootstrap layer
- [ ] Unit tests for command layer
- [ ] All existing tests continue to pass

### Code Quality Requirements

- [ ] All modules pass ruff checks
- [ ] All modules pass black formatting
- [ ] All modules have proper docstrings
- [ ] All modules have clear type hints

### Backwards Compatibility Requirements

- [ ] Old imports continue to work with deprecation warning
- [ ] No breaking changes to public API
- [ ] Tests can gradually migrate to new imports
- [ ] Clear migration path documented

### Documentation Requirements

- [ ] `docs/CLI_ARCHITECTURE.md` created explaining new structure
- [ ] `docs/DEV_SETUP.md` updated with new import examples
- [ ] All modules have module-level docstrings
- [ ] Migration guide provided in deprecation shim

## Validation Commands

Execute every command to validate refactoring is successful with zero regressions:

**Phase 1 Validation (Help System)**:
```bash
python -m prt_src --help
python -c "from prt_src.cli.help import load_help_text; print(load_help_text())"
```

**Phase 2 Validation (Services)**:
```bash
./prt_env/bin/pytest tests/unit/cli/test_services_*.py -v
python -m prt_src --debug  # Test export still works
```

**Phase 3 Validation (UI)**:
```bash
./prt_env/bin/pytest tests/unit/cli/test_ui_*.py -v
python -m prt_src --debug --cli  # Test interactive prompts
```

**Phase 4 Validation (Bootstrap)**:
```bash
./prt_env/bin/pytest tests/integration/cli/test_bootstrap_*.py -v
python -m prt_src --setup
python -m prt_src --debug
python -m prt_src  # Test TUI launch
```

**Phase 5 Validation (Handlers)**:
```bash
./prt_env/bin/pytest tests/integration/cli/test_handlers_*.py -v
python -m prt_src --debug --cli  # Test all menus
```

**Phase 6 Validation (Commands)**:
```bash
./prt_env/bin/pytest tests/unit/cli/test_commands_*.py -v
python -m prt_src --help
python -m prt_src test-db
python -m prt_src list-models
python -m prt_src prt-debug-info
python -m prt_src db-status
python -m prt_src --model gpt-oss-20b --chat "hello"
```

**Final Validation (Full Suite)**:
```bash
# All tests
./prt_env/bin/pytest tests/ -v

# Code quality
./prt_env/bin/ruff check prt_src/cli/ tests/
./prt_env/bin/black prt_src/cli/ tests/ --check

# Manual smoke tests
python -m prt_src --help
python -m prt_src --setup
python -m prt_src --debug
python -m prt_src --debug --cli
python -m prt_src test-db
python -m prt_src list-models

# Backwards compatibility
python -c "from prt_src.cli import handle_contacts_view; print('OK')"
```

## Timeline

- **Day 1**: Phase 1 (Help System)
- **Days 2-3**: Phase 2 (Services)
- **Day 4**: Phase 3 (UI Utilities)
- **Days 5-6**: Phase 4 (Bootstrap)
- **Days 7-9**: Phase 5 (Handlers)
- **Day 10**: Phase 6 (Commands)

**Total**: 10 working days (~2 weeks)

## Notes

- This refactoring does NOT change functionality - it only reorganizes code
- All existing tests should continue to pass throughout migration
- Backwards compatibility is maintained until explicit deprecation
- Each phase can be completed independently
- Low risk phases (Help, UI) can be done first for quick wins
- High value phases (Services, Handlers) provide most maintainability benefit
- The modular structure follows patterns already established in `prt_src/tui/` and `prt_src/llm_prompts/`

