# prt
Personal Relationship Toolkit is a privacy-first client-side encrypted database designed to support mental health through intentional relationship management.


Started ideating on this [here](http://richbodo.pbworks.com/w/page/160555728/Personal%20Social%20Network%20Health)

I synthesized an [MVP PRD](docs/PRD/prt_prd_mvp.md) for the consolidated requirements.

## Setup

Run all commands from the repository root (the directory containing this README).

Create a virtual environment and install dependencies:

```bash
source ./init.sh
```

The script creates a `.venv` directory and installs packages listed in
`requirements.txt`.

## Running the CLI

The main application is a Typer CLI located inside the `prt` package. Launch it
with:

```bash
python -m prt.cli
```

Because the project folder shares the same name as the package, ensure you are
in the repository root before executing this command.

The CLI leverages the [Rich](https://github.com/Textualize/rich) library to
display colorful tables and styled messages.

## Running the tests


```bash
pytest -q
```

## Exit the virtual environment

```bash
source ./uninit.sh
```

## Database Setup

PRT automatically handles database setup when you first run the CLI. The database is stored locally in SQLite format.

### Automatic Setup

Simply run the CLI and it will:
- Create the necessary directories
- Generate database credentials
- Set up the database schema
- Create a backup of any existing database if needed

```bash
python -m prt.cli
```

### Manual Setup (Advanced)

If you need to manually configure the database:

```bash
python setup_database.py setup
```

This will:
- Generate database credentials
- Create/update your configuration file
- Set up the database schema

### Using Alembic for Migrations (Advanced)

PRT uses a comprehensive migration system with both Alembic and manual migrations for managing database schema changes.

#### Migration Types

1. **Alembic Migrations** (Recommended for schema changes)
   - Location: `alembic/versions/`
   - Format: `{revision}_{description}.py`
   - Usage: `alembic revision --autogenerate -m "description"`

2. **Manual Migrations** (For complex data migrations)
   - Location: `migrations/`
   - Format: `{number}_{description}.py`
   - Usage: `python migrations/run_migrations.py --run-all`

#### Migration Management

```bash
# List available migrations
python migrations/run_migrations.py --list

# Check migration status
python migrations/run_migrations.py --status

# Run all pending migrations
python migrations/run_migrations.py --run-all

# Run specific migration
python migrations/run_migrations.py --run 001
```

**Note:** The CLI automatically handles database initialization for new users. You only need to use migrations if you want to version-control schema changes or are developing the application.

#### Working with Migrations

**View migration history:**
```bash
alembic history
```

**Check current database version:**
```bash
alembic current
```

**Apply all pending migrations:**
```bash
alembic upgrade head
```

**Roll back one migration:**
```bash
alembic downgrade -1
```

**Roll back to a specific migration:**
```bash
alembic downgrade <revision_id>
```

**Roll back all migrations:**
```bash
alembic downgrade base
```

#### Creating New Migrations

When you modify your database schema (e.g., add new tables, columns, or indexes):

1. **Generate a new migration:**
   ```bash
   alembic revision --autogenerate -m "Description of changes"
   ```

2. **Review the generated migration file** in `alembic/versions/` to ensure it captures your intended changes.

3. **Apply the migration:**
   ```bash
   alembic upgrade head
   ```

#### Testing Migrations

**Test rollback and reapply:**
```bash
# Roll back one migration
alembic downgrade -1

# Verify the rollback worked
alembic current

# Reapply the migration
alembic upgrade +1

# Verify you're back to the latest
alembic current
```

**Test from scratch:**
```bash
# Remove the database
rm prt_data/prt.db

# Apply all migrations from scratch
alembic upgrade head
```

### Schema Files

PRT uses schema files to define the structure of your data:

- **Google People Schema**: `docs/latest_google_people_schema.json` - Defines the structure for Google Contacts data
- **Schema Plan**: `docs/schema_plan.md` - Complete documentation of database schema and design decisions

### Database Configuration

The database configuration is stored in `prt_data/prt_config.json`. This file contains:
- Database connection settings
- API keys (for future use)
- Other application settings

**Note:** PRT currently uses SQLite for simplicity. The database file is stored in `prt_data/prt.db`.

### Schema Migration

If you have an existing database with the old schema, you can migrate to the new schema:

```bash
python migrate_schema.py
```

This will:
- Create a backup of your existing database
- Migrate existing relationship data to the new schema
- Preserve all your existing tags and notes

### Troubleshooting

**Migration conflicts:**
If you get conflicts between your current database state and migration history:
```bash
# Mark the current database as the latest migration
alembic stamp head

# Or reset to a known good state
alembic stamp <revision_id>
```

**Database locked (SQLite):**
If you get database locked errors with SQLite:
```bash
# Check for open connections
lsof prt_data/prt.db

# Or restart your application
```

**Invalid migration files:**
If a migration file is corrupted or incorrect:
```bash
# Remove the problematic migration file
rm alembic/versions/<problematic_migration>.py

# Regenerate from current state
alembic revision --autogenerate -m "Regenerated migration"
```


