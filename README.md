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

The basic workflow is below.  If you need a deeper walkthrough, Git reminders, or LLM-friendly tips? Head over to **[Developer Environment & Workflow Guide](docs/DEV_SETUP.md)**.

Note that this project uses a couple different llm models that we are developing with for the chat features.  You can find out which models are available by typing python -m prt_src --models.  You'll need to download those and get them working with the ollama app to prove them out, and then they should be available to the app.  Basically the only model that works with tool calling that we've tried is gpt-oss:20b - download details in the dev docs.

Note that this project is LICENSE.md GPLv3, and has the most basic CONTRIBUTING.md and pull request template I could find that just avoids patent and copyright violations.  There is also a CODE_OF_CONDUCT.md which is just the basic mozilla one.

There is a [github project](https://github.com/users/richbodo/projects/2) where I divide up the issues by feature-type-bucket.

## Quick start for LLMs/Agents/AIs

We have not merged these yet, so:

Agents please start by reading Claude.md.  Then read all of the .claude directories commands, and then run the /prime command.  That will give you a good overview and get you ready to start work.

## 🛠️ Basic Development Workflow

### Quick Setup
```bash
source ./init.sh    # One command setup - installs everything!
```

### Daily Development
```bash
# Quick development cycle
python -m prt_src                 # Launch TUI
python -m prt_src --debug         # TUI with debug data

# Testing & Debugging with CLI
python -m prt_src prt-debug-info  # System diagnostic information
python -m prt_src --cli --chat "count contacts"  # Test AI functionality
python -m prt_src list-models     # Check available AI models

# Test suite
python -m pytest tests/           # Run test suite
./prt_env/bin/ruff check --fix prt_src/ tests/   # Lint and auto-fix
./prt_env/bin/black prt_src/ tests/              # Format code
```

**Pre-commit hooks** automatically run `ruff` and `black` on staged files when you commit. The init script installs them for you.

## Documentation Map

Looking for something specific? Start with this map.

| Doc | Status | What you’ll find |
| --- | --- | --- |
| `CONTRIBUTING.md` | ✅ Current | The most basic one I could find that works|
| `CODE_OF_CONDUCT.md` | ✅ Current | Most conventional mozilla version |
| `docs/DEV_SETUP.md` | ✅ Current | Start/end-of-day workflow, Git tips, AI helper pointers. |
| `docs/TUI_Specification.md` | ✅ Current | Feature and UX expectations for the TUI. |
| `ROADMAP.md` | ✅ Current |  Milestone planning. |
| `CLAUDE.md` | ✅ Current | Instructions for Claude and other LLMs |

## Motivation/Purpose: 

I am solving a few personal pain points with this project:

1) Storing all my contacts and personal relationship info with US C Corps is not perfect.  Having a little bit of contact-indexed data kept private to me is preferrable to storing it all with the biggest corporations in the world.  So, prt will be that private db for me.
2) I can't put names to faces particularly well without some way of grouping them and viewing them that works for me to memorize them.  Visuals always help with that.  Prt will create them for me.
3) It is depressing to look at a list of thousands of contacts and try to find the people I need to find immediately with the tools I have - this is made worse by my unwillingness to share certain data about contacts with big corporations.  I therefore almost never find the people I need to find when I most need to find them, using any centralized contact db (google, apple, facebook, linkedin, etc.).  I need a better, multifaceted, LLM-enabled chat-UI for search, and I need it to be humane and privacy preserving.  Prt will be my UI for finding folks.
4) I want to nerd out with P2P privacy and ZKPs, the ultimate fun goal once I get those first three under control.  There is actually a lot to do in that space and improving privacy preserving community health is one of those things to do.  Prt will be that nerdfest for me.

   For more detail on the vision of the project, see the [ROADMAP](https://github.com/richbodo/prt/blob/main/ROADMAP.md)

## CLI, TUI, and Chat

Status: None of the three interfaces are working fully, but all are useful and do something.

The default UI is the TUI.  Run python -m prt_src and the tui opens up.

PRT provides both a modern TUI (Text User Interface) and a CLI interface. The main entry point launches the TUI by default:

```bash
python -m prt_src                     # Launch TUI (default)
```

The CLI interface provides direct access to commands and is especially useful for scripting, testing, and AI-powered chat features.

### Available Commands

```bash
# TUI Interface (default)
python -m prt_src                     # Launch modern TUI interface
python -m prt_src --tui               # Explicitly launch TUI

# CLI Interface
python -m prt_src --cli               # Use command-line interface instead of TUI
python -m prt_src --classic           # Force classic CLI mode (disable TUI attempt)

# Setup and Configuration
python -m prt_src --setup             # First-time setup: import contacts or demo data
python -m prt_src --debug             # Run with sample data (safe, isolated database)
python -m prt_src --regenerate-fixtures # Reset sample data (use with --debug)

# System Information
python -m prt_src prt-debug-info      # Display system diagnostic information
python -m prt_src list-models         # List available AI models
python -m prt_src db-status           # Check database status
python -m prt_src test-db             # Test database connection

# AI-Powered Chat (Great for Testing & Development)
python -m prt_src --model gpt-oss-20b --chat "find friends"
python -m prt_src --cli --chat "make a directory of all contacts with first name Rich"
python -m prt_src --chat="" --model mistral-7b-instruct  # Interactive chat mode
```

### User Interfaces

**TUI (Text User Interface)** - The modern, default interface with intuitive navigation:
- Clean menu-driven interface with keyboard shortcuts
- Integrated search and contact management
- Built-in AI chat functionality
- Real-time visual feedback and progress indicators

**CLI (Command Line Interface)** - Direct command access for automation and power users:
- Direct command execution for scripting
- AI chat mode with natural language queries
- Perfect for development, testing, and automation
- Bypass the TUI for headless operations

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

### Testing

PRT follows a **"headless-first"** testing philosophy using a 4-layer testing pyramid:

- **⚡ Unit Tests** (< 1s each): Pure functions, formatters, parsers
- **⚙️ Integration Tests** (< 5s total): Component interactions with mocked dependencies
- **🧪 Contract Tests** (1-5min): Real LLM behavior validation
- **🐢 E2E Tests** (manual): Full system integration for critical workflows

**Key Principles**:
- Always write automated, headless tests when possible
- Use mocks for fast, deterministic testing
- Manual testing only when headless testing is impossible
- Test fixtures provide realistic sample data (6 contacts, 8 tags, 6 notes)

### Running Tests

**Quick Commands** (ensure you've run `source ./init.sh` first):
```bash
# Fast CI tests (unit + integration) - run before committing
./scripts/run-ci-tests.sh

# Full local test suite (with LLM tests if available)
./scripts/run-local-tests.sh

# Specific test categories
./prt_env/bin/pytest -m unit          # Unit tests only (< 1 sec each)
./prt_env/bin/pytest -m integration   # Integration tests (< 5 sec total)
./prt_env/bin/pytest -m e2e           # End-to-end tests

# Specific test files
./prt_env/bin/pytest tests/test_api.py -v
./prt_env/bin/pytest tests/test_db.py -v

# Run tests with coverage
./prt_env/bin/pytest tests/ --cov=prt_src --cov-report=html
```

**Performance Targets**:
- Unit tests: < 1 second each
- Integration tests: < 5 seconds total
- CI pipeline: < 2 minutes (fast tests only)
- Coverage target: > 85% for testable components

**CI/CD Integration**:
- Fast CI runs on every PR (unit + integration tests with mocks)
- Comprehensive CI runs nightly (includes real LLM contract tests)
- Use `./scripts/run-ci-tests.sh` to run the same tests locally that CI runs

**Documentation**: For complete testing strategy, commands, and troubleshooting, see:
- **[RUNNING_TESTS.md](docs/RUNNING_TESTS.md)** - Test execution guide and daily workflow
- **[TESTING_STRATEGY.md](docs/TESTING_STRATEGY.md)** - Comprehensive testing strategy and patterns

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
from tests.fixtures import get_fixture_spec

# Example test using the test_db fixture
def test_search_functionality(test_db):
    """Test search with populated database."""
    db, fixtures = test_db
    spec = get_fixture_spec()  # Get fixture specification

    config = {"db_path": str(db.path), "db_encrypted": False}
    api = PRTAPI(config)

    # Search will find "John Doe" in the fixture data
    results = api.search_contacts("John")
    assert len(results) > 0
    assert len(results) <= spec["contacts"]["count"]  # Use spec for validation
    assert "John Doe" in [contact["name"] for contact in results]
```

#### Creating Standalone Test Database

For manual testing or debugging, you can create a test database with fixture data:

```bash
# Run with fixture data (recommended approach)
./prt_env/bin/python -m prt_src --debug --regenerate-fixtures

# This creates prt_data/debug.db with all fixture data loaded
# Use this for development and testing without affecting production data
```

**Note**: The `--debug` mode uses an isolated database and never touches your production data.

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
# First, ensure you have debug database with fixture data
./prt_env/bin/python -m prt_src --debug --regenerate-fixtures

# Navigate to data directory
cd prt_data

# Open the debug database (NOT production database)
sqlite3 debug.db

# Examine the fixture data
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

**Important**: Always use the debug database (`debug.db`) for exploration, never the production database (`prt.db`).

#### Available Fixtures

- **`test_db`**: Full database with sample data (contacts, tags, notes, relationships)
- **`test_db_empty`**: Empty database with tables initialized but no data
- **`get_fixture_spec()`**: Returns specification of fixture data (counts, expected values)
- **Debug mode**: `--debug` flag for isolated testing environment

**Best Practice**: Use `get_fixture_spec()` in tests instead of hardcoded values:
```python
# Good: Uses fixture spec
spec = get_fixture_spec()
assert len(contacts) == spec["contacts"]["count"]

# Bad: Hardcoded values
assert len(contacts) == 6  # Breaks if fixture data changes
```

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



