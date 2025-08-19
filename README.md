# Personal Relationship Toolkit (PRT)

## QuickStart

The init.sh file installs sqlcipher and sets some environment variables so the python sqlcipher package will install and work.  It also sets up a virtual environment for development

source ./init.sh

python -m prt_src.cli run

## Motivation: 

I am solving a few personal pain points with this project:

1) Storing all my contacts and personal relationship info with US C Corps is not perfect.  Having a little bit of contact-indexed data kept private to me is preferrable to storing it all with the biggest corporations in the world.  So, prt will be that private db for me.
2) I can't put names to faces particularly well without some way of grouping them and viewing them that works for me to memorize them.  Visuals always help with that.  Prt will create them for me.
3) It is depressing to look at a list of thousands of contacts and try to find the people I need to find immediately with the tools I have - this is made worse by my unwillingness to share certain data about contacts with big corporations.  I therefore almost never find the people I need to find when I most need to find them, using any centralized contact db (google, apple, facebook, linkedin, etc.).  I need a better, multifaceted, LLM-enabled chat-UI for search, and I need it to be humane and privacy preserving.  Prt will be my UI for finding folks.
4) I want to nerd out with P2P privacy and ZKPs, the ultimate fun goal once I get those first three under control.  There is actually a lot to do in that space and improving privacy preserving community health is one of those things to do.  Prt will be that nerdfest for me.
   
## Version History

MVP Alpha achieved! - really basic CLI right now, but the basics needed to be done first!

Note: these docs suck.  I'm not going to make them awesome until I hit a milestone where I think this could be useful to someone else, and then I'll fix docs, and look for feedback. 

## Documentation

- **[Installation Guide](docs/INSTALLATION.md)**: Platform-specific installation instructions (only really tested on my macs at this point the rest are LLM-generated but not tested.)
- **[Database Management](docs/DB_MANAGEMENT.md)**: Advanced database configuration, encryption, and CLI management tools
- **[Encryption Implementation](docs/ENCRYPTION_IMPLEMENTATION.md)**: Technical details of the encryption implementation

## Database Management

For advanced database configuration, encryption setup, and management tools, see the comprehensive [Database Management Guide](docs/DB_MANAGEMENT.md).

### Quick Database Commands

```bash
# Set up database
python -m prt_src.cli setup [--encrypted]

# Check database status
python -m prt_src.cli db-status

# Encrypt existing database
python -m prt_src.cli encrypt-db

# Decrypt database (emergency)
python -m prt_src.cli decrypt-db

# Test database connection
python -m prt_src.cli test
```

## Configuration

PRT stores configuration in `prt_data/prt_config.json`. Key settings:

- `db_path`: Path to the database file
- `db_encrypted`: Whether the database is encrypted
- `db_username`/`db_password`: Database credentials

## Usage

### Interactive Mode
```bash
# Start interactive CLI
python -m prt_src.cli run
```

Available commands in interactive mode:
- View and search contacts
- Import contacts from Google
- Manage tags and notes
- Start LLM chat
- Database status and backup
- Encryption management

### Security Features

- **Database Encryption**: SQLCipher encryption for security at rest
- **Local Storage**: All data stored locally on your machine
- **No Cloud Sync**: Your data never leaves your control
- **Secure Key Management**: Automatic encryption key generation and storage

## Troubleshooting

### Common Issues

#### "pysqlcipher3 not found" Error or pip crashes installing pysqlcipher

**Platform-specific solutions:**
- **macOS**: Ensure SQLCipher is installed via Homebrew, the run "source init.sh" again.
- **Linux**: Install `libsqlcipher-dev` package
- **Windows**: TBD - Windows support not yet implemented

#### Database Connection Errors
```bash
# Check database status
python -m prt_src.cli db-status

# Reinitialize database if needed
python -m prt_src.cli setup --force
```

For detailed troubleshooting and advanced database management, see [DB_MANAGEMENT.md](docs/DB_MANAGEMENT.md).

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run encrypted database tests only
pytest tests/test_encrypted_db.py

# Run migration tests
pytest tests/test_migrations.py
```



