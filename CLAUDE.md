# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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
# Set up environment and dependencies
source ./init.sh

# Run the application
python -m prt_src.cli
```

### Virtual Environment
The project uses a Python virtual environment in `prt_env/` created by `init.sh`. The script handles platform-specific dependency installation (macOS via Homebrew, Linux via apt).

### Testing
```bash
# Run all tests
python -m pytest tests/

# Run specific test modules
python -m pytest tests/test_api.py -v
python -m pytest tests/test_db.py -v

# Run tests with minimal output
python -m pytest tests/ --tb=short -q

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

## Security and Privacy Features

- **Application-level encryption**: Moving away from database-level encryption (Issue #41)
- **Local storage**: No cloud sync, all data stays on device
- **Profile image support**: Binary data stored directly in database
- **Comprehensive export system**: JSON + images for data portability

## Git Commit Guidelines

When creating commit messages:
- Write clear, descriptive commit messages that explain the changes and their purpose
- **Do NOT include**: 
  - "🤖 Generated with [Claude Code]" lines
  - "Co-Authored-By: Claude" lines
  - Any AI authorship attribution
- Focus on the technical changes and business value
- Keep commits focused and atomic when possible