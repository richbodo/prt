# Database Management Guide

This guide covers advanced database configuration, encryption setup, and management using PRT's CLI tools.

## Table of Contents

- [Database Configuration](#database-configuration)
- [Database Encryption](#database-encryption)
- [CLI Management Tools](#cli-management-tools)
- [Migration Procedures](#migration-procedures)
- [Troubleshooting](#troubleshooting)
- [Security Best Practices](#security-best-practices)

## Database Configuration

### Configuration File Location

PRT stores configuration in `prt_data/prt_config.json`. Key settings:

```json
{
  "db_path": "prt_data/prt.db",
  "db_encrypted": false,
  "db_username": "your_username",
  "db_password": "your_password",
  "db_type": "sqlite",
  "db_host": "localhost",
  "db_port": 5432,
  "db_name": "prt",
  "google_api_key": "your_google_api_key",
  "openai_api_key": "your_openai_api_key"
}
```

### Configuration Options

| Setting | Description | Default |
|---------|-------------|---------|
| `db_path` | Path to the database file | `prt_data/prt.db` |
| `db_encrypted` | Whether the database is encrypted | `false` |
| `db_username` | Database username (auto-generated) | Random string |
| `db_password` | Database password (auto-generated) | Random string |
| `db_type` | Database type (currently only SQLite) | `sqlite` |
| `google_api_key` | Google API key for contact import | Required |
| `openai_api_key` | OpenAI API key for LLM features | Required |

### Manual Configuration

You can manually edit the configuration file:

```bash
# Edit configuration
nano prt_data/prt_config.json

# Or use a text editor
code prt_data/prt_config.json
```

## Database Encryption

PRT supports encrypted databases using SQLCipher for enhanced security. All data is encrypted with 256-bit AES encryption.

### Setting up an Encrypted Database from Scratch

```bash
# Set up with encryption enabled
python -m prt_src.cli setup --encrypted
```

This will:
1. Generate a secure encryption key
2. Store the key in `secrets/db_encryption_key.txt`
3. Create an encrypted database
4. Update configuration to enable encryption

### Encrypting an Existing Database

If you already have an unencrypted database, you can encrypt it:

```bash
# Encrypt existing database (creates backup automatically)
python -m prt_src.cli encrypt-db

# Or with custom options
python -m prt_src.cli encrypt-db --db-path /path/to/database.db --no-backup
```

**⚠️ Important**: This process creates a backup of your original database before encryption.

### Encryption Key Management

Encryption keys are stored securely in `secrets/db_encryption_key.txt`.

#### Key Backup and Recovery

```bash
# Export your encryption key to a secure location
python -m prt_src.cli export-key --output ~/secure_location/backup_key.txt

# Verify your encryption key works
python -m prt_src.cli verify-key --key-file ~/secure_location/backup_key.txt
```

#### Key Rotation

To change your encryption key:

```bash
# Rekey the database (changes encryption key)
python -m prt_src.cli rekey --new-key "your_new_encryption_key"
```

**⚠️ Security Notes:**
- Keep your encryption key safe - losing it means losing access to your data
- The encryption key is automatically generated and stored locally
- Consider backing up your encryption key to a secure location
- Never commit encryption keys to version control
- Use strong, unique keys for production environments

## CLI Management Tools

PRT provides comprehensive CLI tools for database management. All commands are run using `python -m prt_src.cli <command>`.

### Database Status and Health

```bash
# Check encryption status and database health
python -m prt_src.cli db-status
```

This command shows:
- Database path and encryption status
- Contact and relationship counts
- Database integrity status
- Connection health

### Database Backup and Recovery

```bash
# Create a backup of your database
python -m prt_src.cli backup-db

# Create backup with custom suffix
python -m prt_src.cli backup-db --suffix .$(date +%Y%m%d)

# Restore from backup (manual process)
cp prt_data/prt.db.backup prt_data/prt.db
```

### Emergency Decryption

If you need to decrypt your database (emergency only):

```bash
# Decrypt database (creates backup first)
python -m prt_src.cli decrypt-db

# Decrypt with custom key
python -m prt_src.cli decrypt-db --key "your_encryption_key"

# Decrypt without backup (not recommended)
python -m prt_src.cli decrypt-db --no-backup
```

### Database Testing and Validation

```bash
# Test database connection and credentials
python -m prt_src.cli test

# Validate database integrity
python -m prt_src.cli validate-db
```

## Migration Procedures

### From Unencrypted to Encrypted

1. **Backup your data** (automatic with `encrypt-db` command):
   ```bash
   python -m prt_src.cli encrypt-db
   ```

2. **Verify the migration**:
   ```bash
   python -m prt_src.cli db-status
   ```

3. **Test functionality**:
   ```bash
   python -m prt_src.cli run
   # Try viewing contacts and other operations
   ```

### From Encrypted to Unencrypted (Emergency)

```bash
python -m prt_src.cli decrypt-db
```

**⚠️ Warning**: Decryption removes the security benefits of encryption. Only use this in emergency situations.

### Database Schema Migrations

PRT uses a simple, safe schema management system that automatically backs up your data before any changes:

```bash
# Check current schema version and apply any needed updates
python -m prt_src.cli migrate

# The system will automatically:
# 1. Create a timestamped backup of your database
# 2. Apply schema changes safely
# 3. Provide recovery instructions if anything goes wrong
```

#### How Schema Migration Works

- **Version Tracking**: Each database has a schema version number
- **Automatic Backups**: Before any migration, a timestamped backup is created
- **Safety First**: If migration fails, you get exact instructions to recover
- **User Control**: You can always restore from backup if needed

#### Migration Process Example

```
🔄 Upgrading database schema from v1 to v2...
📁 Backup created: prt.v1.20250820_234010.backup
Adding profile image support to contacts...
  ✓ Added profile_image column
  ✓ Added profile_image_filename column
  ✓ Added profile_image_mime_type column
✅ Database successfully upgraded to version 2!
```

#### Recovery from Failed Migration

If a migration fails, you'll see clear recovery instructions:

```
❌ Database migration failed!
Your data is safe! A backup was created before the migration.

🔧 To recover:
1. Restore your backup: cp "prt.v1.backup" "prt_data/prt.db"
2. Get the working version: Download PRT v1.x from GitHub releases
3. Continue using the older version until this issue is fixed
```

This approach prioritizes **data safety** over complex migration features, perfect for a privacy-focused local application.

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
python -m prt_src.cli db-status

# Reinitialize database if needed
python -m prt_src.cli setup --force
```

#### Encryption Key Issues

If you've lost your encryption key:

1. **Do not delete the database file** - it may be recoverable
2. **Check for backups** in the `prt_data/` directory
3. **Look for key backups** in your secure storage
4. **Contact support** if you have a recent backup

#### Corrupted Database

```bash
# Check database integrity
python -m prt_src.cli db-status

# Restore from backup
cp prt_data/prt.db.backup prt_data/prt.db

# Reinitialize if necessary
python -m prt_src.cli setup --force
```

### Performance Issues

- **Encrypted databases** may be slightly slower than unencrypted ones
- **Large databases** (>10,000 contacts) may benefit from periodic optimization
- **Backup operations** can take time for large databases

### Debug Mode

Enable debug mode for detailed error information:

```bash
# Run with debug output
python -m prt_src.cli run --debug

# Check logs
tail -f prt_data/prt.log
```

## Security Best Practices

### Encryption Key Management

1. **Store keys securely**: Use a password manager or secure key storage
2. **Backup keys**: Keep multiple secure backups of your encryption key
3. **Rotate keys**: Periodically change your encryption key
4. **Limit access**: Restrict access to encryption keys to authorized personnel only

### Database Security

1. **Use encryption**: Always enable database encryption for sensitive data
2. **Regular backups**: Maintain regular encrypted backups
3. **Secure storage**: Store database files in secure locations
4. **Access control**: Limit physical and network access to database files

### Operational Security

1. **Monitor access**: Log and monitor database access
2. **Update regularly**: Keep PRT and dependencies updated
3. **Test recovery**: Regularly test backup and recovery procedures
4. **Document procedures**: Maintain documentation of security procedures

### Compliance Considerations

- **Data retention**: Implement appropriate data retention policies
- **Audit trails**: Maintain audit logs for compliance requirements
- **Data classification**: Classify data according to sensitivity levels
- **Access reviews**: Regularly review and update access permissions

## Advanced Configuration

### Custom Database Paths

```bash
# Set up database in custom location
python -m prt_src.cli setup --db-path /custom/path/database.db

# Use encrypted database in custom location
python -m prt_src.cli setup --encrypted --db-path /secure/location/encrypted.db
```

### Multiple Database Instances

You can manage multiple PRT databases:

```bash
# Set up development database
python -m prt_src.cli setup --db-path prt_data/dev.db

# Set up production database
python -m prt_src.cli setup --encrypted --db-path /secure/prod.db
```

### Integration with External Tools

PRT databases are standard SQLite files that can be accessed with external tools:

```bash
# Use SQLite command line tool
sqlite3 prt_data/prt.db

# Use encrypted database with SQLCipher
sqlcipher prt_data/prt.db
PRAGMA key = 'your_encryption_key';
```

## Support and Resources

For additional help:

- Check the main [README.md](../README.md) for basic setup
- Review the test files for usage examples
- Open an issue on GitHub for bugs or feature requests
- Check the [ROADMAP.md](../ROADMAP.md) for planned features

---

**Note**: This guide covers advanced database management. For basic setup and usage, see the main [README.md](../README.md).
