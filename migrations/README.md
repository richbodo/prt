# PRT Migration Management

This directory contains migration scripts and tools for managing database schema changes in PRT.

## Migration Types

### 1. Alembic Migrations (Recommended)
- **Location**: `../alembic/versions/`
- **Format**: `{revision}_{description}.py`
- **Usage**: Use Alembic commands for schema changes

### 2. Manual Migration Scripts
- **Location**: `migrations/` directory
- **Format**: `{number}_{description}.py`
- **Usage**: For complex data migrations or one-time fixes

## Migration History

### Alembic Migrations
1. `d0e5116eecf5_initial_schema_contacts_relationships_` - Initial schema with contacts, relationships, tags, notes tables

### Manual Migrations
1. `001_fix_contacts_schema.py` - Added missing columns to contacts table
2. `002_fix_relationships_schema.py` - Migrated relationships table to new schema
3. `003_migrate_old_schema.py` - Legacy migration from old relationship schema
4. `004_create_initial_migration.py` - Creates initial Alembic migration
5. `setup_database.py` - Database setup and initialization utilities

## Best Practices

### Creating New Migrations

#### For Schema Changes (Use Alembic)
```bash
# Generate migration from model changes
alembic revision --autogenerate -m "Description of changes"

# Apply migration
alembic upgrade head
```

#### For Data Migrations (Use Manual Scripts)
1. Create numbered script: `migrations/004_description.py`
2. Include backup creation
3. Include rollback functionality
4. Test thoroughly before running

### Migration Naming Convention

#### Alembic Migrations
- Use descriptive names: `add_user_preferences_table`
- Include scope: `add_contact_phone_validation`
- Be specific: `rename_contact_email_to_primary_email`

#### Manual Migrations
- Use numbers: `001_`, `002_`, etc.
- Include description: `001_fix_contacts_schema.py`
- Include date if needed: `001_2024_01_15_fix_contacts_schema.py`

### Testing Migrations
1. Always test on a copy of production data
2. Test both upgrade and downgrade paths
3. Verify data integrity after migration
4. Test application functionality

### Rollback Strategy
- Alembic: `alembic downgrade -1`
- Manual: Include rollback code in migration script
- Always keep backups before running migrations

## Current Migration Status

- ✅ Initial schema created
- ✅ Contacts table schema fixed
- ✅ Relationships table migrated to new schema
- ✅ All tables have proper timestamps and constraints

## Running Migrations

### Alembic Commands
```bash
# Check current status
alembic current

# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show migration history
alembic history
```

### Manual Migration Scripts
```bash
# Run specific migration
python migrations/001_fix_contacts_schema.py

# Run all migrations (if applicable)
python migrations/run_all_migrations.py
```

## Troubleshooting

### Common Issues
1. **Schema mismatch**: Run `alembic stamp head` to mark current state
2. **Migration conflicts**: Check for manual schema changes
3. **Data loss**: Always backup before migrations

### Recovery
1. Restore from backup
2. Check migration history: `alembic history`
3. Reset to known good state: `alembic stamp {revision}`
4. Re-run migrations from that point
