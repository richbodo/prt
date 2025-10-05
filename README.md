# Personal Relationship Toolkit (PRT)

## Quick Start for Developers

Right now we work out of the repository root and keep the virtual environment active while iterating with Cursor, Codex, or Claude. Use the shell scripts init.sh and uninit.sh.

```bash
# First time / start of day
source ./init.sh

# Launch the modern TUI
python -m prt_src

# End of day
source ./uninit.sh
```

Need a deeper walkthrough, Git reminders, or LLM-friendly tips? Head over to **[Developer Environment & Workflow Guide](docs/DEV_SETUP.md)**.

## 🛠️ Development Workflow

### Quick Setup
```bash
source ./init.sh    # One command setup - installs everything!
```

### Daily Development
```bash
# Quick development cycle
python -m prt_src                 # Launch TUI
python -m prt_src --debug         # TUI with debug data
python -m pytest tests/           # Run test suite
./prt_env/bin/ruff check --fix prt_src/ tests/   # Lint and auto-fix
./prt_env/bin/black prt_src/ tests/              # Format code
```

**Pre-commit hooks** automatically run `ruff` and `black` on staged files when you commit. The init script installs them for you.

## Documentation Map

Looking for something specific? Start with this map.

| Doc | Status | What you’ll find |
| --- | --- | --- |
| `docs/DEV_SETUP.md` | ✅ Current | Start/end-of-day workflow, Git tips, AI helper pointers. |
| `docs/INSTALL.md` | 🕰️ Historical | Legacy SQLCipher installation notes (kept for reference). |
| `docs/DB_MANAGEMENT.md` | 🕰️ Historical | Older encryption/database flows superseded by app-level encryption. |
| `docs/TUI_Specification.md` | ✅ Current | Feature and UX expectations for the modern TUI. |
| `docs/TUI_Key_Bindings.md` | ✅ Current | Shortcut reference for manual testing. |
| `ROADMAP.md` | ✅ Current | Current milestone planning. |
| `CLAUDE.md`, `CLAUDE_TUI_MIGRATION.plan` | 🕰️ Historical | Narrative planning archives for context. |

> ℹ️ Sections below this point capture a detailed CLI reference and historical notes. They’re still useful, but check the timestamps and comments inside the documents for freshness.

## Motivation/Purpose: 

I am solving a few personal pain points with this project:

1) Storing all my contacts and personal relationship info with US C Corps is not perfect.  Having a little bit of contact-indexed data kept private to me is preferrable to storing it all with the biggest corporations in the world.  So, prt will be that private db for me.
2) I can't put names to faces particularly well without some way of grouping them and viewing them that works for me to memorize them.  Visuals always help with that.  Prt will create them for me.
3) It is depressing to look at a list of thousands of contacts and try to find the people I need to find immediately with the tools I have - this is made worse by my unwillingness to share certain data about contacts with big corporations.  I therefore almost never find the people I need to find when I most need to find them, using any centralized contact db (google, apple, facebook, linkedin, etc.).  I need a better, multifaceted, LLM-enabled chat-UI for search, and I need it to be humane and privacy preserving.  Prt will be my UI for finding folks.
4) I want to nerd out with P2P privacy and ZKPs, the ultimate fun goal once I get those first three under control.  There is actually a lot to do in that space and improving privacy preserving community health is one of those things to do.  Prt will be that nerdfest for me. 

## Version History

MVP Alpha achieved! - really basic CLI right now, but the basics needed to be done first!

Note: These docs suck.  I'm not going to make them awesome until I hit a milestone where I think this could be useful to someone else, and then I'll fix docs, and look for feedback.  This app is only suitable for developers right now, if that.

## CLI Overview

PRT provides a unified CLI interface that automatically handles setup and operations. The main entry point is:

```bash
python -m prt_src.cli
```

### Available Commands

```bash
# Main interactive interface (default)
python -m prt_src.cli                 # Auto-detects setup needs

# Quick access to LLM chat
python -m prt_src.cli chat            # Start LLM chat directly

# Setup and configuration
python -m prt_src.cli setup           # Manual setup wizard
python -m prt_src.cli db-status       # Check database status
python -m prt_src.cli test            # Test database connection

# Database operations moved to application-level encryption (Issue #41)
```

### Interactive Menu

The main menu:

- ** Start Chat** - AI-powered chat mode that does anything the cli and tools can do
- ** View Contacts** - Browse contact information
- ** Search ** - Search contacts by contact, tag, or note content - export any results list to a directory
- ** Manage Tags** - Browse and manage contact tags
- ** Manage Notes** - Browse and manage contact notes
- ** Manage Database** - Check database stats and backup
- ** Import Google Takeout** - Import contacts from Google Takeout zip file
- ** Exit** - Exit the application

## Standalone Tools

PRT includes standalone tools in the `tools/` directory that work with PRT exports:

### make_directory.py - Contact Directory Generator

Generate interactive single-page websites from PRT JSON exports showing contact relationships as navigable 2D graphs.

```bash
# Generate from any PRT export
python tools/make_directory.py generate exports/contacts_search_20250826_191055/

# Custom output directory
python tools/make_directory.py generate exports/tags_search_20250826_191055/ --output ./my_directory

# Get help
python tools/make_directory.py --help
```

**Output**: Self-contained HTML websites in `directories/` folder that work offline.

See `tools/README.md` for complete tool documentation and development guidelines.

## Documentation

- **[Installation Guide](docs/INSTALL.md)**: Platform-specific installation instructions
- **[Database Management](docs/DB_MANAGEMENT.md)**: Advanced database configuration, encryption, and CLI management tools
- **[Encryption Implementation](docs/ENCRYPTION_IMPLEMENTATION.md)**: Technical details of the encryption implementation
- **[Ollama Integration](docs/OLLAMA_INTEGRATION.md)**: LLM chat integration with Ollama

## Database Management

For advanced database configuration, encryption setup, and management tools, see the comprehensive [Database Management Guide](docs/DB_MANAGEMENT.md).

### Quick Database Commands

```bash
# Set up database
python -m prt_src.cli setup

# Check database status
python -m prt_src.cli db-status

# Test database connection
python -m prt_src.cli test
```

## Configuration

PRT stores configuration in `prt_data/prt_config.json`. Key settings:

- `db_path`: Path to the database file
- `db_encrypted`: Always false (using application-level encryption instead)
- `db_username`/`db_password`: Database credentials

## Where PRT stores secrets and your data

The app will create three directories to store secret stuff in (all are .gitignore'd):

/prt_env
- this is created by pyenv - not a lot of secrets, but we handle it as secret - it just stores your local environment config

/prt_data
- databases
- config
- sensitive user data to import
  
/prt_data/secrets
- encryption keys for the db and other things that need to be encrypted

/exports
- any exported data from your database is stored in this directory

/directories
- directories created with the make_directory.py tool as single-page web pages


### Google Takeout Import Files

PRT automatically searches for Google Takeout files in these locations:
- **~/Downloads** - Most common location where takeout files are downloaded
- **Current directory** - Where you run PRT from
- **prt_data/** - PRT's data directory

To get your Google Takeout:
1. Go to [https://takeout.google.com](https://takeout.google.com)
2. Select **"Contacts"** only (deselect everything else)
3. Choose **"Export once"** and download the zip file
4. The file will typically be named like `takeout-YYYYMMDD-HHMMSS.zip`
5. Use PRT's **Import Google Takeout** option (option 3) to import

## Usage

### Interactive Mode
```bash
# Start interactive CLI
python -m prt_src.cli run
```

Available commands in interactive mode:
- View and search contacts
- Import contacts from Google Takeout
- Manage tags and notes
- Start LLM chat
- Database status and backup

### Security Features

- **Application-Level Encryption**: Coming in Issue #42 - cryptography library + OS keyrings
- **Local Storage**: All data stored locally on your machine
- **No Cloud Sync**: Your data never leaves your control
- **Secure Key Management**: OS keyring integration for secure key storage

## Troubleshooting

### Common Issues

#### Virtual Environment Issues

**If packages fail to install:**
- Ensure you have Python 3.9+ installed
- Run `source init.sh` to set up the virtual environment
- **Windows**: Windows is not fully supported yet

#### Database Connection Errors
```bash
# Check database status
python -m prt_src.cli db-status

# Reinitialize database if needed
python -m prt_src.cli setup --force
```

For detailed troubleshooting and advanced database management, see [DB_MANAGEMENT.md](docs/DB_MANAGEMENT.md).

## Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/richbodo/prt.git
cd prt

# Set up virtual environment and dependencies
source ./init.sh

# Activate the environment (if not already active)
source prt_env/bin/activate
```

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test modules
python -m pytest tests/test_api.py -v
python -m pytest tests/test_db.py -v

# Run tests with coverage
python -m pytest tests/ --tb=short -q
```

### Working with Test Fixtures

PRT includes a comprehensive test fixture system for consistent testing with realistic data.

#### Creating Test Data

The fixture system provides a pre-populated database with:
- **6 sample contacts** (John Doe, Jane Smith, Bob Wilson, etc.)
- **8 tags** (family, friend, colleague, client, etc.)
- **6 notes** (meeting notes, birthday reminders, etc.)
- **Realistic profile images** (256x256 JPEG images, 1.8-4.5 KB each)
- **Relationships** connecting contacts to tags and notes

#### Using Fixtures in Tests

```python
# Example test using the test_db fixture
def test_search_functionality(test_db):
    """Test search with populated database."""
    db, fixtures = test_db
    config = {"db_path": str(db.path), "db_encrypted": False}
    api = PRTAPI(config)
    
    # Search will find "John Doe" in the fixture data
    results = api.search_contacts("John")
    assert len(results) > 0
    assert "John Doe" in [contact["name"] for contact in results]
```

#### Creating Standalone Test Database

You can create a test database for manual testing or debugging:

```bash
cd tests
python fixtures.py
```

This creates a database at `tests/prt_data/test_fixtures.db` with all sample data loaded.

#### Viewing Profile Images

To extract and view the profile images from the test database:

```bash
cd utils
python extract_profile_images.py
# Images saved to utils/extracted_images/
```

#### Examining Test Data with SQLite

Use the SQLite command line to examine test data:

```bash
# Navigate to test data directory
cd tests/prt_data

# Open the test database
sqlite3 test_fixtures.db

# Examine the data
.tables                          # List all tables
SELECT * FROM contacts LIMIT 5;  # View sample contacts
SELECT * FROM tags;               # View all tags
SELECT * FROM notes;              # View all notes

# View relationships
SELECT c.name, t.name as tag 
FROM contacts c 
JOIN relationships r ON c.id = r.contact_id
JOIN relationship_tags rt ON r.id = rt.relationship_id
JOIN tags t ON rt.tag_id = t.id;

# Exit SQLite
.quit
```

#### Available Fixtures

- **`test_db`**: Full database with sample data (contacts, tags, notes, relationships)
- **`test_db_empty`**: Empty database with tables initialized but no data
- **`sample_config`**: Sample configuration for testing

#### Adding New Fixtures

To add new test data, edit `tests/fixtures.py`:

```python
# Add to SAMPLE_CONTACTS list
SAMPLE_CONTACTS.append({
    "name": "New Contact",
    "email": "new@example.com",
    "phone": "+1-555-0107",
    "image_key": None
})

# Add to SAMPLE_RELATIONSHIPS to connect with tags/notes
SAMPLE_RELATIONSHIPS.append({
    "contact_name": "New Contact",
    "tags": ["friend"],
    "notes": ["First Meeting"]
})
```

### Database Schema

PRT uses SQLAlchemy with these main tables:
- **contacts**: Contact information and profile images
- **tags**: Categorical labels for contacts
- **notes**: Text notes about contacts
- **relationships**: Links contacts to tags and notes
- **relationship_tags**: Many-to-many relationship table
- **relationship_notes**: Many-to-many relationship table

### Code Architecture

- **`prt_src/models.py`**: SQLAlchemy models and database schema
- **`prt_src/db.py`**: Database connection and operations
- **`prt_src/api.py`**: Main API class for contact management
- **`prt_src/cli.py`**: Command-line interface using Typer
- **`tests/fixtures.py`**: Test fixture system and sample data



