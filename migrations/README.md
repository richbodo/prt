# PRT Database Migrations

This directory contains utilities for database setup and encryption management.

## Current Migration System

PRT uses a **SchemaManager**-based migration system that automatically handles database schema updates. The old numbered migration files have been replaced with a more robust, automatic system.

### How It Works

1. **Automatic Detection**: The system automatically detects your current database schema version
2. **Safe Migration**: Migrations are performed with automatic backups
3. **Recovery**: Clear recovery instructions are provided if anything goes wrong
4. **No Manual Steps**: No need to run individual migration scripts

### Available Utilities

#### Database Setup
- **`setup_database.py`** - Database configuration and initialization
  - `setup_database()` - Set up database configuration
  - `initialize_database()` - Initialize database schema
  - `get_db_credentials()` - Generate database credentials

#### Database Encryption
- **`encrypt_database.py`** - Database encryption utilities
  - `encrypt_database()` - Encrypt an existing database
  - `decrypt_database()` - Decrypt an encrypted database (emergency)
  - `is_database_encrypted()` - Check encryption status
  - `backup_database()` - Create database backups
  - `export_encryption_key()` - Export encryption key
  - `verify_encryption_key()` - Verify encryption key

### Usage

These utilities are automatically used by the PRT CLI:

```bash
# Setup (automatic)
python -m prt_src.cli setup

# Encryption (via CLI)
python -m prt_src.cli encrypt-db
python -m prt_src.cli decrypt-db

# Status check
python -m prt_src.cli db-status
```

### Schema Versions

- **Version 1**: Original schema (basic contacts and relationships)
- **Version 2**: Added profile image support to contacts table

### Migration Process

1. **Automatic Detection**: System detects current schema version
2. **Backup Creation**: Automatic backup before any changes
3. **Schema Update**: Apply necessary schema changes
4. **Verification**: Verify database integrity
5. **Recovery**: Provide recovery instructions if needed

### Recovery

If a migration fails:
1. Your data is automatically backed up
2. Clear recovery instructions are displayed
3. You can restore from backup and continue using the previous version

### Security

- All migrations create automatic backups
- Encryption keys are stored securely
- Recovery instructions are provided for all operations
- No data loss risk during migrations
