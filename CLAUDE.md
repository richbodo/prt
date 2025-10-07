# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.


# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.

## Project Overview

PRT (Personal Relationship Toolkit) is a privacy-first personal contact management system that helps users manage relationships, contacts, and notes entirely locally. The project uses Python with SQLAlchemy, Typer for CLI, Textual for a TUI, and includes AI-powered chat functionality via Ollama integration.  

### Vision

The short term vision for PRT is to be a safe space to discover and enhance relationships.

To do that, PRT will provide a safe space for importing contacts from other systems, finding, and adding sensitive relationship data locally, keeping data encrypted when not in use, chatting with a local, safer AI than is available online, and exporting useful directories or diagrams as quick references to find relationships of a certain type, either for quick contact lookup, or as a memory aid, or to share intentionally with others.

The long term vision for PRT is to be a tool that is used in a decentralized community to build stronger community relationships.  

To do that, PRT will be enhaced with a more complicated decentralized communications tool (CRT).

CRT uses zero knowledge tech to expose data in a granular way to workflows that can: notify other community members of important social network health issues.  One such workflow would be the "help" workflow, in which a user notifies their community that they are in need of help, without immediately revealing who they are.  When other community members who are willing to provide help chime in, then information will gradually be revealed based on their preferences, and a communications channel agreed upon so that help can be provided.

CRT could also accept message logs from a user, and export zk proofs of connectedness, so that social network health metrics can be analyzed and "alerts" can be triggered when the community as a whole or a single member moves to an likely unhealthy state.  

## Development Environment Setup

### Initial Setup
```bash
# Set up environment and dependencies
source ./init.sh

# Run the application
python -m prt_src.cli
```

### Virtual Environment
The project uses a Python virtual environment in `prt_env/` created by `init.sh`. The script handles platform-specific dependency installation (macOS via Homebrew, Linux via apt).

### Testing and Code Quality
```bash
# IMPORTANT: Always activate virtual environment first
source ./init.sh  # This also installs dev dependencies

# Run all tests
./prt_env/bin/python -m pytest tests/ -v

# Run specific test modules
./prt_env/bin/python -m pytest tests/test_api.py -v
./prt_env/bin/python -m pytest tests/test_relationship_cli.py -v

# Testing Commands (use these exact paths)
./prt_env/bin/python -m pytest tests/test_*.py -v  # Run all test files
./prt_env/bin/python -m pytest tests/test_unified_search.py -v  # Run specific test

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

1. **CLI Interface (`prt_src/cli.py`)**: Main entry point with Typer-based command interface
2. **API Layer (`prt_src/api.py`)**: Clean API abstraction for all operations
3. **Database Layer (`prt_src/db.py`)**: SQLAlchemy-based database operations
4. **Models (`prt_src/models.py`)**: SQLAlchemy ORM models for contacts, tags, notes, relationships

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

### Main CLI Commands
```bash
# Interactive mode (default)
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
- `prt_src/cli.py`: Main CLI interface with all interactive menus
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

## Git Commit Guidelines

When creating commit messages:
- Write clear, descriptive commit messages that explain the changes and their purpose
- **Do NOT include**: 
  - "🤖 Generated with [Claude Code]" lines
  - "Co-Authored-By: Claude" lines
  - Any AI authorship attribution
- Focus on the technical changes and business value
- Keep commits focused and atomic when possible
