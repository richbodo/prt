# Personal Relationship Toolkit (PRT)

## Features

- **Contact Management**: Import and manage contacts from Google Contacts
- **Relationship Tracking**: Add tags and notes to track relationship details
- **Encrypted Database**: Secure your data with SQLCipher encryption
- **LLM Integration**: AI-powered insights and conversation assistance
- **CLI Interface**: Easy-to-use command-line interface

## Documentation

- **[Installation Guide](docs/INSTALLATION.md)**: Detailed platform-specific installation instructions
- **[Database Management](docs/DB_MANAGEMENT.md)**: Advanced database configuration, encryption, and CLI management tools
- **[Encryption Implementation](docs/ENCRYPTION_IMPLEMENTATION.md)**: Technical details of the encryption implementation

## Installation

### Prerequisites

- Python 3.8 or higher
- SQLCipher development libraries (for encrypted database support)

### Platform-Specific Installation

For detailed installation instructions for each platform, see the [Installation Guide](docs/INSTALLATION.md).

#### macOS

**Required Dependencies:**
- Homebrew (for package management)
- SQLCipher development libraries

**Installation Steps:**

1. **Install Homebrew** (if not already installed):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install SQLCipher**:
   ```bash
   brew install sqlcipher
   ```

3. **Clone and setup PRT**:
   ```bash
   git clone https://github.com/richbodo/prt.git
   cd prt
   ```

4. **Create virtual environment and install dependencies**:
   ```bash
   source ./init.sh
   ```

5. **Install pysqlcipher3** (may require environment variables):
   ```bash
   export CFLAGS="-I/opt/homebrew/Cellar/sqlcipher/4.6.1/include"
   export LDFLAGS="-L/opt/homebrew/Cellar/sqlcipher/4.6.1/lib"
   pip install pysqlcipher3
   ```

6. **Set up the database**:
   ```bash
   python -m prt.cli setup
   ```

**Troubleshooting macOS:**
- If you get "command not found: brew", install Homebrew first
- If pysqlcipher3 installation fails, ensure SQLCipher is installed via Homebrew
- The exact path for CFLAGS/LDFLAGS may vary depending on your SQLCipher version

#### Linux (Ubuntu/Debian)

**Required Dependencies:**
- SQLCipher development libraries
- Python development headers

**Installation Steps:**

1. **Install system dependencies**:
   ```bash
   sudo apt-get update
   sudo apt-get install libsqlcipher-dev python3-dev python3-pip python3-venv
   ```

2. **Clone and setup PRT**:
   ```bash
   git clone https://github.com/richbodo/prt.git
   cd prt
   ```

3. **Create virtual environment and install dependencies**:
   ```bash
   source ./init.sh
   ```

4. **Install pysqlcipher3**:
   ```bash
   pip install pysqlcipher3
   ```

5. **Set up the database**:
   ```bash
   python -m prt.cli setup
   ```

**Troubleshooting Linux:**
- If you get "libsqlcipher-dev not found", try `sudo apt-get install sqlcipher-dev`
- For other distributions, use the appropriate package manager:
  - **CentOS/RHEL/Fedora**: `sudo yum install sqlcipher-devel` or `sudo dnf install sqlcipher-devel`
  - **Arch Linux**: `sudo pacman -S sqlcipher`

#### Windows

**Status**: TBD - Windows installation instructions will be added when Windows support is implemented.

**Planned Requirements:**
- Windows 10/11
- Python 3.8+
- SQLCipher Windows binaries
- Visual Studio Build Tools (for compiling pysqlcipher3)

**Note**: Windows support is planned but not yet implemented. The encrypted database functionality may require additional work for Windows compatibility.

### Install PRT

1. **Clone the repository**:
   ```bash
   git clone https://github.com/richbodo/prt.git
   cd prt
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up the database**:
   ```bash
   python -m prt.cli setup
   ```

## Quick Start

### Basic Setup

1. **Initial Setup**: Run the setup command to configure your database:
   ```bash
   python -m prt.cli setup
   ```

2. **Start the CLI**: Launch the interactive interface:
   ```bash
   python -m prt.cli run
   ```

3. **Import Contacts**: Use the `fetch` command to import contacts from Google:
   ```bash
   python -m prt.cli run
   # Then type: fetch
   ```

## Database Management

For advanced database configuration, encryption setup, and management tools, see the comprehensive [Database Management Guide](docs/DB_MANAGEMENT.md).

### Quick Database Commands

```bash
# Set up database
python -m prt.cli setup [--encrypted]

# Check database status
python -m prt.cli db-status

# Encrypt existing database
python -m prt.cli encrypt-db

# Decrypt database (emergency)
python -m prt.cli decrypt-db

# Test database connection
python -m prt.cli test
```

## Configuration

PRT stores configuration in `prt_data/prt_config.json`. Key settings:

- `db_path`: Path to the database file
- `db_encrypted`: Whether the database is encrypted
- `db_username`/`db_password`: Database credentials
- `google_api_key`: Google API key for contact import
- `openai_api_key`: OpenAI API key for LLM features

## Usage

### Interactive Mode
```bash
# Start interactive CLI
python -m prt.cli run
```

Available commands in interactive mode:
- View and search contacts
- Import contacts from Google
- Manage tags and notes
- Start LLM chat
- Database status and backup
- Encryption management

### Security Features

- **Database Encryption**: Optional SQLCipher encryption for enhanced security
- **Local Storage**: All data stored locally on your machine
- **No Cloud Sync**: Your data never leaves your control
- **Secure Key Management**: Automatic encryption key generation and storage

## Troubleshooting

### Common Issues

#### "pysqlcipher3 not found" Error
```bash
# Install SQLCipher dependencies first, then:
pip install pysqlcipher3
```

**Platform-specific solutions:**
- **macOS**: Ensure SQLCipher is installed via Homebrew
- **Linux**: Install `libsqlcipher-dev` package
- **Windows**: TBD - Windows support not yet implemented

#### Database Connection Errors
```bash
# Check database status
python -m prt.cli db-status

# Reinitialize database if needed
python -m prt.cli setup --force
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

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues and questions:
- Check the troubleshooting section above
- Review the test files for usage examples
- Open an issue on GitHub

## Roadmap

See [ROADMAP.md](ROADMAP.md) for planned features and improvements.


