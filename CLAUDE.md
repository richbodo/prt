# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.


# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.

## External Documentation Policy

**ALWAYS check `EXTERNAL_DOCS/` directory FIRST** before requesting documentation or library source code:

- When you need documentation for a library (e.g., Textual, FastAPI, etc.), check `EXTERNAL_DOCS/<library-name>/docs/` first
- When you need source code to understand implementation details, check `EXTERNAL_DOCS/<library-name>/src/` first
- If the documentation or source is not in `EXTERNAL_DOCS/`, ask the user to add it there before proceeding
- This approach enables:
  - Faster debugging by reading actual source code
  - Better understanding of library internals and limitations
  - Reduced need for web searches or API calls
  - Ability to verify behavior against authoritative sources

**Example**: The Textual TUI framework documentation and source code are in `EXTERNAL_DOCS/textual/`:
- Docs: `EXTERNAL_DOCS/textual/docs/guide/` (user guides), `EXTERNAL_DOCS/textual/docs/widgets/` (widget docs)
- Source: `EXTERNAL_DOCS/textual/src/textual/` (implementation code)

**When debugging complex issues**: Read the actual source code in `EXTERNAL_DOCS/` to understand how libraries work internally, rather than relying on assumptions or general documentation.

## Project Overview

PRT (Personal Relationship Toolkit) is a privacy-first personal contact management system that helps users manage relationships, contacts, and notes entirely locally. The project provides both a CLI (Typer-based) and a TUI (Textual-based) interface. Built with Python and SQLAlchemy, it includes AI-powered chat functionality via Ollama integration.  

### Vision

The short term vision for PRT is to be a safe space to discover and enhance relationships.

To do that, PRT will provide a safe space for importing contacts from other systems, finding, and adding sensitive relationship data locally, keeping data encrypted when not in use, chatting with a local, safer AI than is available online, and exporting useful directories or diagrams as quick references to find relationships of a certain type, either for quick contact lookup, or as a memory aid, or to share intentionally with others.

The long term vision for PRT is to be a tool that is used in a decentralized community to build stronger community relationships.  

To do that, PRT will be enhaced with a more complicated decentralized communications tool (CRT).

CRT uses zero knowledge tech to expose data in a granular way to workflows that can: notify other community members of important social network health issues.  One such workflow would be the "help" workflow, in which a user notifies their community that they are in need of help, without immediately revealing who they are.  When other community members who are willing to provide help chime in, then information will gradually be revealed based on their preferences, and a communications channel agreed upon so that help can be provided.

CRT could also accept message logs from a user, and export zk proofs of connectedness, so that social network health metrics can be analyzed and "alerts" can be triggered when the community as a whole or a single member moves to an likely unhealthy state.

## TUI Documentation

The TUI is being refactored for simplicity, testability, and debuggability (Issue #120). Key documentation:

- **[TUI_Specification.md](docs/TUI/TUI_Specification.md)** - Complete specification of screens, navigation, and behavior
- **[TUI_Style_Guide.md](docs/TUI/TUI_Style_Guide.md)** - Design principles and style guidelines
- **[TUI_REFACTOR_PLAN.md](docs/TUI/TUI_REFACTOR_PLAN.md)** - Comprehensive refactoring plan and implementation strategy
- **[TUI_Dev_Tips.md](docs/TUI/TUI_Dev_Tips.md)** - Common issues, solutions, and best practices
- **[TUI_Key_Bindings.md](docs/TUI/TUI_Key_Bindings.md)** - Complete key binding reference

**IMPORTANT**: Always review the TUI specification and style guide before implementing TUI features. The refactoring prioritizes simplicity over features - follow the spec exactly.

## TUI Debugging Guidelines

**CRITICAL**: TUIs are event-driven systems that are notoriously difficult to debug. When working on TUI code, ALWAYS add comprehensive logging FIRST before attempting fixes.

### Standard Logging Configuration

The project uses a centralized logging system (`prt_src/logging_config.py`):

- **Log file location**: `prt_data/prt.log` (auto-created)
- **Default log level**: INFO (shows INFO, WARNING, ERROR)
- **Logger access**: `from prt_src.logging_config import get_logger; logger = get_logger(__name__)`
- **Log format**: `YYYY-MM-DD HH:MM:SS - module.name - LEVEL - message`

### When to Add Debug Logging

Add comprehensive logging whenever:

1. **Implementing or modifying TUI event handlers** (on_key, on_mount, on_button_pressed, etc.)
2. **Working with screen navigation** (push_screen, pop_screen, navigate_to)
3. **Debugging user-reported TUI issues** where behavior is inconsistent or unexpected
4. **Adding new interactive widgets** or modifying existing ones
5. **Working with stateful UI components** (dropdowns, forms, multi-screen workflows)

### Essential Logging Pattern for Event-Driven Code

When debugging TUI issues, add logs at these critical points:

```python
# Event handlers - log entry, state, and exit
def on_key(self, event) -> None:
    key = event.key.lower()
    logger.info(f"[COMPONENT] on_key: key='{key}', state={self.some_state}")

    # Log decision points
    if some_condition:
        logger.info(f"[COMPONENT] Taking path A because {reason}")
        action()
        logger.info(f"[COMPONENT] Path A completed")

    event.prevent_default()

# Navigation - log screen stack changes
def navigate_to(self, screen_name: str) -> None:
    logger.info(f"[APP] navigate_to('{screen_name}') STARTED")
    logger.info(f"[APP] Screen stack before: {[type(s).__name__ for s in self.screen_stack]}")

    self.push_screen(new_screen)

    logger.info(f"[APP] Screen stack after: {[type(s).__name__ for s in self.screen_stack]}")
    logger.info(f"[APP] navigate_to('{screen_name}') COMPLETED")

# Action methods - log execution and state changes
def action_do_something(self) -> None:
    logger.info("[SCREEN] action_do_something STARTED")
    logger.info(f"[SCREEN] State before: dropdown={self.dropdown.display}, menu={self.menu_open}")

    # Perform action
    self.dropdown.hide()
    self.menu_open = False

    logger.info(f"[SCREEN] State after: dropdown={self.dropdown.display}, menu={self.menu_open}")
    logger.info("[SCREEN] action_do_something COMPLETED")
```

### Logging Tag Convention

Use bracketed tags to identify log source:

- `[APP]` - Application-level events (PRTApp)
- `[SCREEN]` - Screen-specific events (HomeScreen, HelpScreen, etc.)
- `[WIDGET]` - Widget-specific events (DropdownMenu, TopNav, etc.)
- `[SERVICE]` - Service-level events (NavigationService, DataService, etc.)

### Viewing TUI Logs

```bash
# Run TUI normally (logs go to prt_data/prt.log)
python -m prt_src.tui

# In another terminal, tail the logs
tail -f prt_data/prt.log

# Filter logs by component
tail -f prt_data/prt.log | grep '\[APP\]'
tail -f prt_data/prt.log | grep '\[HELP\]'

# Get recent event flow
tail -200 prt_data/prt.log | grep -E '\[HELP\]|\[APP\]|\[DROPDOWN\]'
```

### Critical Debugging Lessons

**Lesson from Issue #120 (Double-push bug)**:

When a user reported "pressing n,b on help screen requires two attempts to navigate back," the logs revealed:

```
Screen stack before pop: ['Screen', 'HomeScreen', 'HelpScreen', 'HelpScreen']
```

The help screen was being pushed **twice** due to duplicate event handlers. Without the screen stack logging, this would have taken hours to debug through code inspection alone.

**Key Takeaway**: Log the screen stack at every navigation point. Screen stack corruption is a common TUI bug that's invisible without logging.

### Temporary vs Permanent Logging

- **Temporary**: Use `logger.info()` with tags like `[DEBUG]` or `[TRACE]` for investigation
- **Permanent**: Keep navigation, error, and state-change logging at INFO level
- **Remove**: Delete overly verbose logs (e.g., logging every render) after debugging

### Setting Log Level for Deep Debugging

When standard INFO logging isn't enough:

```python
# Temporarily set DEBUG level in the module you're debugging
from prt_src.logging_config import setup_logging
setup_logging(log_level="DEBUG")  # Shows DEBUG, INFO, WARNING, ERROR
```

Or use conditional debug logging:

```python
DEBUG_MODE = True  # Set to False before committing

if DEBUG_MODE:
    logger.debug(f"Detailed state: {expensive_operation()}")
```

### Before You Start Debugging

1. **Add logging first** - Don't start fixing until you have visibility
2. **Log the event flow** - Trace the complete path from user action to final state
3. **Log state changes** - Before/after for all mutations
4. **Log screen stack** - Every push/pop operation
5. **Log decision points** - Why each code path was taken

Remember: **"If you can't see it, you can't debug it."** TUIs hide their internal state behind terminal rendering. Logging is your window into what's actually happening.

## Development Environment Setup

### Initial Setup
```bash
# Set up environment and dependencies
source ./init.sh

# Run the CLI application
python -m prt_src.cli

# Run the TUI application
python -m prt_src.tui
```

### Virtual Environment
The project uses a Python virtual environment in `prt_env/` created by `init.sh`. The script handles platform-specific dependency installation (macOS via Homebrew, Linux via apt).

### Testing and Code Quality
```bash
# IMPORTANT: Always activate virtual environment first
source ./init.sh  # This also installs dev dependencies

# Run all tests
./prt_env/bin/python -m pytest tests/ -v

# Run specific test files or modules
./prt_env/bin/python -m pytest tests/test_api.py -v
./prt_env/bin/python -m pytest tests/test_relationship_cli.py -v
./prt_env/bin/python -m pytest tests/test_home_screen.py -v

# Run linting and formatting (MUST use venv binaries)
./prt_env/bin/ruff check prt_src/ --fix
./prt_env/bin/black prt_src/

# Run both linter and formatter on specific files
./prt_env/bin/ruff check prt_src/cli.py prt_src/db.py --fix
./prt_env/bin/black prt_src/cli.py prt_src/db.py

# Create standalone test database with fixture data
cd tests && python fixtures.py
```

## High-Level Architecture

### Core Components

1. **CLI Interface (`prt_src/cli.py`)**: Typer-based command-line interface
2. **TUI Interface (`prt_src/tui/`)**: Textual-based text user interface
3. **API Layer (`prt_src/api.py`)**: Clean API abstraction for all operations
4. **Database Layer (`prt_src/db.py`)**: SQLAlchemy-based database operations
5. **Models (`prt_src/models.py`)**: SQLAlchemy ORM models for contacts, tags, notes, relationships

### Key Features
- **Local-first**: All data stored locally, no cloud sync
- **Contact Management**: Import from Google Takeout, search, tag, and annotate contacts
- **Relationship Modeling**: Complex many-to-many relationships between contacts, tags, and notes
- **Export System**: JSON exports with profile images for external tools
- **Interactive Directories**: Web-based visualization tool (`tools/make_directory.py`)
- **AI Integration**: Ollama-powered chat interface for natural language queries
- **Fixture System**: Comprehensive test fixtures with realistic sample data

### Database Schema
- **contacts**: Contact info with embedded profile images (binary data)
- **tags**: Categorical labels for contacts
- **notes**: Free-form text notes with titles
- **relationships**: Links contacts to tags and notes (many-to-many)
- **relationship_tags** / **relationship_notes**: Join tables

## Commands Reference

### TUI Application
```bash
# Launch TUI (Text User Interface)
python -m prt_src.tui

# Run with Textual development tools
textual run --dev python -m prt_src.tui

# Debug console (separate terminal)
textual console --port 7342 -v
```

### CLI Commands
```bash
# Interactive CLI mode (legacy)
python -m prt_src.cli

# Direct chat mode
python -m prt_src.cli chat

# Setup wizard
python -m prt_src.cli setup

# Database status
python -m prt_src.cli db-status

# Test connection
python -m prt_src.cli test

# Debug mode with fixture data
python -m prt_src.cli --debug
```

### Standalone Tools
```bash
# Generate interactive contact directory from exports
python tools/make_directory.py generate exports/contacts_search_20250826_191055/

# With custom output
python tools/make_directory.py generate exports/tags_search_20250826_191055/ --output ./my_directory
```

## Configuration and Data Storage

### Configuration File
- Location: `prt_data/prt_config.json`
- Contains database credentials, paths, and API keys

### Data Directories
- `prt_data/`: Main data directory (databases, config, imports)
- `prt_data/secrets/`: Encryption keys and sensitive data
- `exports/`: Search result exports with JSON and profile images
- `directories/`: Generated interactive web directories
- `prt_env/`: Python virtual environment

## Development Patterns

### API Usage
Always use the `PRTAPI` class for database operations rather than direct database access:
```python
from prt_src.api import PRTAPI

api = PRTAPI()  # Loads config automatically
contacts = api.search_contacts("john")
```

### Error Handling Pattern
Always use the logger and provide fallbacks for robust error handling:
```python
from prt_src.logging_config import get_logger
logger = get_logger(__name__)

try:
    result = operation()
except Exception as e:
    logger.warning(f"Operation failed: {e}", exc_info=True)
    return safe_default  # Always provide a fallback
```

The CLI includes comprehensive error handling with user-friendly messages for:
- Database connection issues
- Missing tables/setup
- Empty databases
- File permission problems

### Memory Management
For long-running operations with in-memory collections:
```python
# Bound all in-memory collections
MAX_CACHE_SIZE = 1000  # Define reasonable limits
MAX_HISTORY_SIZE = 100

# Implement cleanup when limits exceeded
if len(cache) > MAX_CACHE_SIZE:
    # Remove least recently used/least important items
    sorted_items = sorted(cache.items(), key=lambda x: x[1], reverse=True)
    cache = dict(sorted_items[:int(MAX_CACHE_SIZE * 0.75)])
```

Target: The system must handle 5000+ contacts efficiently without memory issues.

### Test Fixtures
Use the fixture system for testing:
```python
def test_functionality(test_db):
    db, fixtures = test_db
    # fixtures contains 6 contacts, 8 tags, 6 notes with relationships
```

## Important File Paths

### Core Source Files
- `prt_src/cli.py`: CLI interface (Typer-based)
- `prt_src/tui/`: TUI interface (Textual-based)
  - `prt_src/tui/app.py`: Main TUI application
  - `prt_src/tui/screens/`: Screen implementations
  - `prt_src/tui/widgets/`: Reusable widgets
  - `prt_src/tui/services/`: Services (data, navigation, notification, LLM status)
- `prt_src/api.py`: Clean API layer for all operations
- `prt_src/models.py`: SQLAlchemy ORM models
- `prt_src/db.py`: Database connection and operations
- `prt_src/google_takeout.py`: Google Takeout import logic
- `prt_src/llm_ollama.py`: AI chat integration

### Configuration Files
- `requirements.txt`: Python dependencies
- `init.sh`: Environment setup script
- `prt_data/prt_config.json`: Runtime configuration

### Tools and Utilities
- `tools/make_directory.py`: Interactive directory generator
- `migrations/setup_database.py`: Database initialization
- `tests/fixtures.py`: Comprehensive test fixture system
- `utils/`: Various utility scripts for profile images and data processing

## Migration and Schema Management

The project uses a simple schema management system in `prt_src/schema_manager.py` that:
- Creates automatic backups before migrations
- Provides clear recovery instructions on failure
- Prioritizes data safety over complex migration features

## Security and Privacy Features

- **Application-level encryption**: Moving away from database-level encryption (Issue #41)
- **Local storage**: No cloud sync, all data stays on device
- **Profile image support**: Binary data stored directly in database
- **Comprehensive export system**: JSON + images for data portability

## Relationship Management System

### Architecture
The relationship management system is split across three layers:
- **Database Layer (`prt_src/db.py`)**: Core relationship operations and analytics
- **API Layer (`prt_src/api.py`)**: Business logic and data transformation
- **CLI Layer (`prt_src/cli.py`)**: User interaction and display

### Key Database Methods for Relationships
```python
# Basic operations
db.create_contact_relationship(from_id, to_id, type_key, start_date=None)
db.delete_contact_relationship(from_id, to_id, type_key)
db.get_contact_relationships(contact_id)
db.list_relationship_types()

# Advanced analytics (Part 3 of Issue #64)
db.get_relationship_analytics()  # Returns network statistics
db.find_mutual_connections(contact1_id, contact2_id)  # Common connections
db.find_relationship_path(from_id, to_id, max_depth=6)  # BFS pathfinding
db.get_network_degrees(contact_id, degrees=2)  # Network exploration
db.bulk_create_relationships(relationships)  # Batch operations
db.export_relationships(format="json")  # Export to JSON/CSV
```

### CLI Helper Functions
```python
# Validation and UI helpers
_get_valid_date(prompt_text)  # Date input with retry logic
_validate_contact_id(contact_id, contacts)  # ID verification
_display_contacts_paginated(contacts, title)  # Large list handling
_select_contact_with_search(contacts, prompt_text)  # Search + selection
```

## SQLAlchemy Import Patterns

### Essential Imports for Complex Queries
```python
# Always include these when working with advanced database operations
from sqlalchemy import and_, case, func, or_, text
from sqlalchemy.orm import aliased

# Required model imports for relationship operations
from prt_src.models import Contact, ContactRelationship, RelationshipType
```

### Common Query Patterns
```python
# Using aliased for self-joins
ContactAlias = aliased(Contact)

# Case statements for conditional logic
case([(condition, value)], else_=default_value)

# Aggregate functions
func.count(), func.max(), func.min()

# Complex filters
.filter(or_(condition1, condition2))
.filter(and_(condition1, condition2))

# Null checks (use .is_ not ==)
.filter(ContactRelationship.end_date.is_(None))  # Correct
# NOT: .filter(ContactRelationship.end_date == None)  # Wrong
```

## TUI Development Guidelines

### Testing with Textual
- **Textual Testing Guide**: See `EXTERNAL_DOCS/textual/docs/guide/testing.md` for comprehensive Textual testing patterns and best practices
- The guide covers async testing with pytest, UI interaction testing, and Textual's dedicated test features
- **Future Task**: Refactor all TUI tests to use Textual's recommended testing patterns, which will enable Claude Code to perform more automated testing
- Current tests use basic pytest patterns; Textual's approach provides better UI interaction testing capabilities

### Parallel Development
- When working on multiple parallel features, expect merge conflicts in `__init__.py` and `styles.tcss`
- Resolve conflicts by **combining** imports/styles, not choosing one over the other
- Merge PRs one at a time to minimize conflict complexity

### Common Issues and Solutions
- **Lambda closure bug**: Use default parameters to capture loop variables
  ```python
  # Bug: All validators reference the last field_name
  lambda v: validate(v, field_name)
  
  # Fix: Capture current field_name with default parameter
  lambda v, fn=field_name: validate(v, fn)
  ```
- **Reserved properties**: Avoid using `name` on Textual widgets (it's reserved)
  - Use alternatives like `category_name`, `item_name`, etc.
- **Event handlers**: Place `@on` decorators outside `compose()` method
  ```python
  def compose(self) -> ComposeResult:
      yield Button("Save", id="save-btn")
  
  # Correct placement - outside compose()
  @on(Button.Pressed, "#save-btn")
  def handle_save(self) -> None:
      ...
  ```

### Testing Approach
- Use lightweight TDD: Write 2-3 failing tests → implement → expand tests
- Run tests with: `./prt_env/bin/python -m pytest tests/test_*.py -v`
- Always lint before committing: 
  ```bash
  ./prt_env/bin/ruff check prt_src/tui/ --fix && ./prt_env/bin/black prt_src/tui/
  ```

### Widget Organization
- Base classes in `prt_src/tui/widgets/base.py`
- Specific widgets in their own files under `prt_src/tui/widgets/`
- All widgets must be exported in `__init__.py`

### Data Schema Consistency
- Use consistent field names across components (e.g., `from_contact`/`to_contact` not `from`/`to`)
- Validate data structures match between widgets that communicate

### TUI Debugging
When debugging TUI issues:
- Use **2-terminal setup**: Debug console in Terminal 1, TUI in Terminal 2
- The TUI blocks the terminal while running - use separate terminal for commands
- Use Textual devtools: `textual run --dev python -m prt_src.tui`
- Enable visual debugging with `textual console` for real-time logging
- Refer to TUI_Dev_Tips.md for common issues and solutions

## Git Commit Guidelines

When creating commit messages:
- Write clear, descriptive commit messages that explain the changes and their purpose
- **Do NOT include**: 
  - "🤖 Generated with [Claude Code]" lines
  - "Co-Authored-By: Claude" lines
  - Any AI authorship attribution
- Focus on the technical changes and business value
- Keep commits focused and atomic when possible
