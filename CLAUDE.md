# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🚨 CRITICAL REMINDERS - READ FIRST!

1. **ALWAYS activate virtual environment before Python commands:**
   ```bash
   source prt_env/bin/activate
   ```
   
2. **Run tests before and after changes:**
   ```bash
   python -m pytest tests/ -q
   ```

3. **NO AI attribution in commits** - Never add "Generated with Claude" or similar

4. **SQLAlchemy uses named parameters**, not positional:
   ```python
   # Use {"param": value}, not (value,)
   ```

[byterover-mcp]

# important 
always use byterover-retrieve-knowledge tool to get the related context before any tasks 
always use byterover-store-knowledge to store all the critical informations after sucessful tasks
# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.

## Project Overview

PRT (Personal Relationship Toolkit) is a privacy-first personal contact management system that helps users manage relationships, contacts, and notes entirely locally. The project uses Python with SQLAlchemy, Typer for CLI, and includes AI-powered chat functionality via Ollama integration.

## Development Environment Setup

### Initial Setup
```bash
# CRITICAL: Run init.sh first to create virtual environment
source ./init.sh

# This creates and activates prt_env virtual environment
# The script handles platform-specific dependency installation (macOS via Homebrew, Linux via apt)
```

### Virtual Environment Activation (REQUIRED for all Python commands)
```bash
# ALWAYS activate the virtual environment before running Python commands
source prt_env/bin/activate

# Now you can run the application
python -m prt_src.cli
```

**⚠️ IMPORTANT**: If you see errors like "No module named pytest" or similar, you forgot to activate the virtual environment!

### Testing
```bash
# FIRST activate virtual environment
source prt_env/bin/activate

# Run all tests
python -m pytest tests/

# Run specific test modules with verbose output
python -m pytest tests/test_api.py -v
python -m pytest tests/test_relationships.py -v

# Run tests with minimal output
python -m pytest tests/ --tb=short -q

# Quick test summary (shows pass/fail count)
python -m pytest tests/ -q

# Create standalone test database with fixture data
cd tests && python fixtures.py
```

### Linting and Code Quality
```bash
# The project uses automated linting - run before commits
# Linter will automatically fix minor issues
# Always run tests after linting to ensure nothing broke

# Typical pre-commit workflow:
source prt_env/bin/activate
python -m pytest tests/ -q  # Verify tests pass
# (User runs linter here)
python -m pytest tests/ -q  # Verify tests still pass after linting
git add -A && git commit -m "Your commit message"
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

### Database Schema (Version 3)

**Core Tables:**
- **contacts**: Contact info with embedded profile images (binary data)
- **contact_metadata** (renamed from 'relationships'): Links contacts to tags and notes
- **tags**: Categorical labels for contacts  
- **notes**: Free-form text notes with titles
- **relationship_types**: Defines relationship types (parent_of, friend_of, etc.)
- **contact_relationships**: Links two contacts with a relationship type

**Join Tables:**
- **metadata_tags** (renamed from 'relationship_tags'): Links contact_metadata to tags
- **metadata_notes** (renamed from 'relationship_notes'): Links contact_metadata to notes

**Schema Versions:**
- Version 1: Original schema
- Version 2: Added profile_image support
- Version 3: Added relationship types and contact-to-contact relationships

## GitHub Integration

### Working with Issues and PRs
```bash
# View open issues
gh issue list

# View specific issue
gh issue view 38

# Create feature branch for an issue
git checkout -b feature/issue-38-description

# Create pull request
gh pr create --title "Implement Issue #38: Description" --body "..."

# Check PR status
gh pr status
gh pr view 63
```

### PR Best Practices
- Create feature branches for each issue
- Include issue number in branch name and PR title
- Run full test suite before creating PR
- Keep PRs focused on single issues when possible
- For large features, mention follow-up work needed

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

### Error Handling
The CLI includes comprehensive error handling with user-friendly messages for:
- Database connection issues
- Missing tables/setup
- Empty databases
- File permission problems

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
- `.cursor/rules/byterover-rules.mdc`: ByteRover MCP integration rules

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
- Handles both fresh installations and upgrades from older versions

**Migration Process:**
1. SchemaManager detects current database version
2. Creates timestamped backup (e.g., `prt.v2.20250829_005300.backup`)
3. Applies migrations sequentially (v1→v2→v3)
4. On failure, shows recovery instructions with backup restore commands

**Important Migration Notes:**
- Test databases may have different schemas than production
- Migrations must handle both old table names and new ones
- Always test migrations with `python -m pytest tests/` after changes

## Security and Privacy Features

- **Application-level encryption**: Moving away from database-level encryption (Issue #41)
- **Local storage**: No cloud sync, all data stays on device
- **Profile image support**: Binary data stored directly in database
- **Comprehensive export system**: JSON + images for data portability

## Common Development Pitfalls and Solutions

### SQLAlchemy Gotchas
```python
# ❌ WRONG: Positional parameters with SQLAlchemy
db.session.execute(text("INSERT INTO table VALUES (?)"), (value,))

# ✅ CORRECT: Named parameters with SQLAlchemy
db.session.execute(text("INSERT INTO table VALUES (:value)"), {"value": value})
```

### Python Environment Issues
```bash
# ❌ WRONG: Running Python without virtual environment
python -m pytest tests/
# Error: No module named pytest

# ✅ CORRECT: Always activate virtual environment first
source prt_env/bin/activate
python -m pytest tests/
```

### Testing After Schema Changes
```bash
# After modifying models.py or schema_manager.py:
source prt_env/bin/activate
python -m pytest tests/test_relationships.py -v  # Test new functionality
python -m pytest tests/ -q  # Ensure no regressions
```

### Backward Compatibility
When renaming database tables or columns:
- Always create aliases in models.py for backward compatibility
- Test that old code still works with new schema
- Example: `Relationship = ContactMetadata` alias after renaming

## Typical Development Workflow

1. **Start Work Session:**
```bash
cd /Users/richardbodo/src/prt
source prt_env/bin/activate
git pull
python -m pytest tests/ -q  # Verify clean state
```

2. **Make Changes:**
```bash
# Edit files as needed
# Run targeted tests frequently:
python -m pytest tests/test_api.py -v
```

3. **Before Committing:**
```bash
python -m pytest tests/ -q  # Full test suite
# User runs linter here
python -m pytest tests/ -q  # Verify tests pass after linting
git add -A
git commit -m "Clear description of changes"
```

4. **For Feature Branches:**
```bash
git checkout -b feature/issue-XX-description
# Make changes
git push -u origin feature/issue-XX-description
gh pr create --title "Title" --body "Description"
```

## Git Commit Guidelines

When creating commit messages:
- Write clear, descriptive commit messages that explain the changes and their purpose
- **Do NOT include**: 
  - "🤖 Generated with [Claude Code]" lines
  - "Co-Authored-By: Claude" lines
  - Any AI authorship attribution
- Focus on the technical changes and business value
- Keep commits focused and atomic when possible
- Run tests before committing to ensure nothing is broken