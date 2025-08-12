# prt
Personal Relationship Toolkit is a privacy-first client-side encrypted database designed to support mental health through intentional relationship management.

Started ideating on this here: http://richbodo.pbworks.com/w/page/160555728/Personal%20Social%20Network%20Health

I had a few AIs convert those notes to PRDs, then synthesized an MVP PRD: [PRD/prt_prd_mvp.md](PRD/prt_prd_mvp.md) for the consolidated requirements.

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

## Database Setup and Migrations

PRT uses Alembic for database migrations, allowing you to version-control your database schema and easily roll forward and backward through changes.

### Initial Database Setup

1. **Set up database configuration:**
   ```bash
   python setup_database.py setup
   ```
   This will:
   - Generate database credentials
   - Create/update your configuration file
   - Show you the Alembic connection string

2. **Configure Alembic:**
   Edit `alembic.ini` line 87 with the connection string shown by the setup script:
   ```ini
   sqlalchemy.url = sqlite:///prt_data/prt.db
   ```

### Using Alembic for Migrations

#### Creating Your First Migration

1. **Generate the initial migration from your current schema:**
   ```bash
   alembic revision --autogenerate -m "Initial schema"
   ```
   This creates a migration file in `alembic/versions/` based on your current database schema.

2. **Apply the migration:**
   ```bash
   alembic upgrade head
   ```

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
- **Proposed Schema**: `docs/proposed_schema.json` - Your custom schema extensions
- **Schema Plan**: `docs/schema_plan.md` - Documentation of schema decisions

### Switching Database Types

**From SQLite to PostgreSQL:**

1. **Update database configuration:**
   ```bash
   python setup_database.py setup --db-type postgresql --host localhost --port 5432 --name prt
   ```

2. **Create PostgreSQL database:**
   ```bash
   createdb prt
   ```

3. **Update alembic.ini** with the new connection string:
   ```ini
   sqlalchemy.url = postgresql://username:password@localhost:5432/prt
   ```

4. **Apply migrations:**
   ```bash
   alembic upgrade head
   ```

**From PostgreSQL to SQLite:**
```bash
python setup_database.py setup --db-type sqlite
```

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


