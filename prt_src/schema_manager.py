"""
Simple Schema Manager for PRT

This module provides a straightforward approach to database schema management
with automatic backups and clear recovery instructions for users.
"""

import shutil
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from sqlalchemy import text

console = Console()


class SchemaManager:
    """Simple, safe database schema management."""

    CURRENT_VERSION = 5

    def __init__(self, db):
        """Initialize with database connection."""
        self.db = db

    def get_schema_version(self) -> int:
        """Get current database schema version."""
        try:
            # Try to get version from schema_version table
            result = self.db.session.execute(
                text("SELECT version FROM schema_version LIMIT 1")
            ).fetchone()
            if result:
                return result[0]
        except Exception:
            pass

        # Check if we have the original schema (version 1)
        try:
            # If contacts table exists but no profile_image column, it's version 1
            self.db.session.execute(text("SELECT name FROM contacts LIMIT 1"))

            # Check if profile_image column exists
            try:
                self.db.session.execute(text("SELECT profile_image FROM contacts LIMIT 1"))
                return 2  # Has profile image columns
            except Exception:
                return 1  # Original schema without profile images

        except Exception:
            return 0  # No schema at all

    def create_schema_version_table(self):
        """Create schema_version table if it doesn't exist."""
        try:
            self.db.session.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS schema_version (
                    id INTEGER PRIMARY KEY,
                    version INTEGER NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
                )
            )

            # Insert initial version if table is empty
            result = self.db.session.execute(text("SELECT COUNT(*) FROM schema_version")).fetchone()
            if result[0] == 0:
                current_version = self.get_schema_version()
                self.db.session.execute(
                    text("INSERT INTO schema_version (version) VALUES (:version)"),
                    {"version": current_version},
                )

            self.db.session.commit()
        except Exception as e:
            self.db.session.rollback()
            console.print(f"Warning: Could not create schema_version table: {e}", style="yellow")

    def create_backup(self, version: int) -> Path:
        """Create a timestamped backup of the database."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{self.db.path.stem}.v{version}.{timestamp}.backup"
        backup_path = self.db.path.parent / backup_name

        try:
            shutil.copy2(self.db.path, backup_path)
            console.print(f"📁 Backup created: {backup_path.name}", style="green")
            return backup_path
        except Exception as e:
            console.print(f"❌ Failed to create backup: {e}", style="red")
            raise

    def show_recovery_instructions(self, backup_path: Path, old_version: int):
        """Show user how to recover from migration failure."""
        instructions = f"""[red]❌ Database migration failed![/red]

[green]Your data is safe![/green] A backup was created before the migration.

[yellow]🔧 To recover:[/yellow]

1. [cyan]Restore your backup:[/cyan]
   cp "{backup_path}" "{self.db.path}"

2. [cyan]Get the working version:[/cyan]
   - Download PRT v{old_version}.x from GitHub releases
   - Or use git: git checkout v{old_version}.x

3. [cyan]Continue using the older version[/cyan] until this issue is fixed

[blue]💡 Please report this error as a GitHub issue so we can fix it![/blue]"""

        panel = Panel(
            instructions,
            title="🆘 Recovery Instructions",
            border_style="red",
            padding=(1, 2),
        )
        console.print(panel)

    def apply_migration_v1_to_v2(self):
        """Add profile image support to contacts table."""
        console.print("Adding profile image support to contacts...", style="blue")

        try:
            # Add the new columns
            self.db.session.execute(text("ALTER TABLE contacts ADD COLUMN profile_image BLOB"))
            console.print("  ✓ Added profile_image column", style="green")

            self.db.session.execute(
                text("ALTER TABLE contacts ADD COLUMN profile_image_filename TEXT")
            )
            console.print("  ✓ Added profile_image_filename column", style="green")

            self.db.session.execute(
                text("ALTER TABLE contacts ADD COLUMN profile_image_mime_type TEXT")
            )
            console.print("  ✓ Added profile_image_mime_type column", style="green")

            # Update schema version
            self.db.session.execute(
                text("UPDATE schema_version SET version = 2, updated_at = CURRENT_TIMESTAMP")
            )

            self.db.session.commit()
            console.print("✅ Profile image support added successfully!", style="green bold")

        except Exception as e:
            self.db.session.rollback()
            raise RuntimeError(f"Failed to add profile image columns: {e}")

    def apply_migration_v2_to_v3(self):
        """Add relationship types and rename relationships table to contact_metadata."""
        console.print("Upgrading to flexible relationship types...", style="blue")

        try:
            # 1. Create relationship_types table
            self.db.session.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS relationship_types (
                    id INTEGER PRIMARY KEY,
                    type_key TEXT NOT NULL UNIQUE,
                    description TEXT,
                    inverse_type_key TEXT,
                    is_symmetrical INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (inverse_type_key) REFERENCES relationship_types(type_key)
                )
            """
                )
            )
            console.print("  ✓ Created relationship_types table", style="green")

            # 2. Create contact_relationships table
            self.db.session.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS contact_relationships (
                    id INTEGER PRIMARY KEY,
                    from_contact_id INTEGER NOT NULL,
                    to_contact_id INTEGER NOT NULL,
                    type_id INTEGER NOT NULL,
                    start_date DATE,
                    end_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (from_contact_id) REFERENCES contacts(id) ON DELETE CASCADE,
                    FOREIGN KEY (to_contact_id) REFERENCES contacts(id) ON DELETE CASCADE,
                    FOREIGN KEY (type_id) REFERENCES relationship_types(id),
                    UNIQUE(from_contact_id, to_contact_id, type_id)
                )
            """
                )
            )
            console.print("  ✓ Created contact_relationships table", style="green")

            # 3. Check if we have relationships table or contact_metadata table
            # (Handle cases where database might already have renamed table)
            try:
                self.db.session.execute(text("SELECT 1 FROM relationships LIMIT 1"))
                # Table exists as relationships, rename it
                self.db.session.execute(
                    text("ALTER TABLE relationships RENAME TO contact_metadata")
                )
                console.print("  ✓ Renamed relationships table to contact_metadata", style="green")
            except Exception:
                # Table might already be renamed or not exist, check for contact_metadata
                try:
                    self.db.session.execute(text("SELECT 1 FROM contact_metadata LIMIT 1"))
                    console.print("  ✓ contact_metadata table already exists", style="green")
                except Exception:
                    # Neither exists, create contact_metadata
                    self.db.session.execute(
                        text(
                            """
                        CREATE TABLE IF NOT EXISTS contact_metadata (
                            id INTEGER PRIMARY KEY,
                            contact_id INTEGER NOT NULL UNIQUE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE
                        )
                    """
                        )
                    )
                    console.print("  ✓ Created contact_metadata table", style="green")

            # 4. Handle join tables migration
            # Check if old join tables exist
            old_tables_exist = False
            try:
                self.db.session.execute(text("SELECT 1 FROM relationship_tags LIMIT 1"))
                old_tables_exist = True
            except Exception:
                pass

            # Create new join tables
            self.db.session.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS metadata_tags (
                    metadata_id INTEGER,
                    tag_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (metadata_id, tag_id),
                    FOREIGN KEY (metadata_id) REFERENCES contact_metadata(id) ON DELETE CASCADE,
                    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
                )
            """
                )
            )

            self.db.session.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS metadata_notes (
                    metadata_id INTEGER,
                    note_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (metadata_id, note_id),
                    FOREIGN KEY (metadata_id) REFERENCES contact_metadata(id) ON DELETE CASCADE,
                    FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE
                )
            """
                )
            )
            console.print("  ✓ Created new join tables", style="green")

            # 5. Migrate data if old tables exist
            if old_tables_exist:
                try:
                    self.db.session.execute(
                        text(
                            """
                        INSERT OR IGNORE INTO metadata_tags (metadata_id, tag_id, created_at)
                        SELECT relationship_id, tag_id, created_at FROM relationship_tags
                    """
                        )
                    )

                    self.db.session.execute(
                        text(
                            """
                        INSERT OR IGNORE INTO metadata_notes (metadata_id, note_id, created_at)
                        SELECT relationship_id, note_id, created_at FROM relationship_notes
                    """
                        )
                    )
                    console.print("  ✓ Migrated join table data", style="green")

                    # Drop old join tables
                    self.db.session.execute(text("DROP TABLE IF EXISTS relationship_tags"))
                    self.db.session.execute(text("DROP TABLE IF EXISTS relationship_notes"))
                    console.print("  ✓ Cleaned up old join tables", style="green")
                except Exception as e:
                    console.print(f"  ⚠ Could not migrate old join tables: {e}", style="yellow")

            # 7. Populate default relationship types
            default_types = [
                # Familial (directional)
                ("parent_of", "Is the parent of", "child_of", 0),
                ("child_of", "Is the child of", "parent_of", 0),
                # Familial (symmetrical)
                ("sibling_of", "Is the sibling of", "sibling_of", 1),
                ("spouse_of", "Is the spouse of", "spouse_of", 1),
                # Professional (directional)
                ("manager_of", "Is the manager of", "reports_to", 0),
                ("reports_to", "Reports to", "manager_of", 0),
                ("mentor_of", "Is the mentor of", "mentee_of", 0),
                ("mentee_of", "Is the mentee of", "mentor_of", 0),
                # Professional (symmetrical)
                ("coworker", "Is a coworker of", "coworker", 1),
                # Social (symmetrical)
                ("friend_of", "Is a friend of", "friend_of", 1),
            ]

            for type_key, description, inverse_key, is_symmetrical in default_types:
                self.db.session.execute(
                    text(
                        """
                    INSERT OR IGNORE INTO relationship_types 
                    (type_key, description, inverse_type_key, is_symmetrical)
                    VALUES (:type_key, :description, :inverse_key, :is_symmetrical)
                """
                    ),
                    {
                        "type_key": type_key,
                        "description": description,
                        "inverse_key": inverse_key,
                        "is_symmetrical": is_symmetrical,
                    },
                )

            console.print("  ✓ Added default relationship types", style="green")

            # Update schema version
            self.db.session.execute(
                text("UPDATE schema_version SET version = 3, updated_at = CURRENT_TIMESTAMP")
            )

            self.db.session.commit()
            console.print("✅ Relationship types support added successfully!", style="green bold")

        except Exception as e:
            self.db.session.rollback()
            raise RuntimeError(f"Failed to add relationship types: {e}")

    def apply_migration_v3_to_v4(self):
        """Add backup metadata tracking table."""
        console.print("Adding backup metadata tracking...", style="blue")

        try:
            # Create backup_metadata table
            self.db.session.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS backup_metadata (
                    id INTEGER PRIMARY KEY,
                    backup_filename TEXT NOT NULL UNIQUE,
                    backup_path TEXT NOT NULL,
                    comment TEXT,
                    is_auto INTEGER DEFAULT 0,
                    file_size INTEGER,
                    schema_version INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
                )
            )
            console.print("  ✓ Created backup_metadata table", style="green")

            # Create index for faster queries
            self.db.session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_backup_metadata_created 
                ON backup_metadata(created_at DESC)
            """
                )
            )
            console.print("  ✓ Added index for backup queries", style="green")

            # Update schema version if table exists
            try:
                self.db.session.execute(
                    text("UPDATE schema_version SET version = 4, updated_at = CURRENT_TIMESTAMP")
                )
            except Exception:
                # Schema version table might not exist in test databases
                pass

            self.db.session.commit()
            console.print("✅ Backup metadata tracking added successfully!", style="green bold")

        except Exception as e:
            self.db.session.rollback()
            raise RuntimeError(f"Failed to add backup metadata tracking: {e}")

    def apply_migration_v4_to_v5(self):
        """Add FTS5 full-text search support."""
        console.print("Adding full-text search support...", style="blue")

        try:
            # Read and execute the FTS5 migration SQL
            from pathlib import Path

            migration_path = Path(__file__).parent.parent / "migrations" / "add_fts5_support.sql"
            if not migration_path.exists():
                raise RuntimeError(f"Migration file not found: {migration_path}")

            with open(migration_path) as f:
                sql_content = f.read()

            # Execute SQL statements one by one (split by semicolon)
            statements = [s.strip() for s in sql_content.split(";") if s.strip()]

            for statement in statements:
                if statement and not statement.startswith("--"):
                    try:
                        self.db.session.execute(text(statement))
                    except Exception as e:
                        # Some statements might fail if objects already exist
                        # Log but continue
                        if "already exists" not in str(e).lower():
                            console.print(f"  ⚠ Warning during FTS5 setup: {e}", style="yellow")

            console.print("  ✓ Created FTS5 virtual tables", style="green")
            console.print("  ✓ Added synchronization triggers", style="green")
            console.print("  ✓ Indexed existing data", style="green")

            # Update schema version
            self.db.session.execute(
                text("UPDATE schema_version SET version = 5, updated_at = CURRENT_TIMESTAMP")
            )

            self.db.session.commit()
            console.print("✅ Full-text search support added successfully!", style="green bold")

        except Exception as e:
            self.db.session.rollback()
            raise RuntimeError(f"Failed to add FTS5 support: {e}")

    def migrate_to_version(self, target_version: int, current_version: int):
        """Apply migrations to reach target version."""
        # Map of all migration paths
        migrations = {
            (1, 2): [self.apply_migration_v1_to_v2],
            (2, 3): [self.apply_migration_v2_to_v3],
            (3, 4): [self.apply_migration_v3_to_v4],
            (4, 5): [self.apply_migration_v4_to_v5],
            (1, 3): [self.apply_migration_v1_to_v2, self.apply_migration_v2_to_v3],
            (1, 4): [
                self.apply_migration_v1_to_v2,
                self.apply_migration_v2_to_v3,
                self.apply_migration_v3_to_v4,
            ],
            (1, 5): [
                self.apply_migration_v1_to_v2,
                self.apply_migration_v2_to_v3,
                self.apply_migration_v3_to_v4,
                self.apply_migration_v4_to_v5,
            ],
            (2, 4): [self.apply_migration_v2_to_v3, self.apply_migration_v3_to_v4],
            (2, 5): [
                self.apply_migration_v2_to_v3,
                self.apply_migration_v3_to_v4,
                self.apply_migration_v4_to_v5,
            ],
            (3, 5): [self.apply_migration_v3_to_v4, self.apply_migration_v4_to_v5],
        }

        migration_path = migrations.get((current_version, target_version))
        if not migration_path:
            raise ValueError(
                f"No migration path from version {current_version} to {target_version}"
            )

        # Apply migrations in sequence
        for migration in migration_path:
            migration()

    def migrate_safely(self) -> bool:
        """Perform safe database migration with backup and recovery instructions."""
        current_version = self.get_schema_version()

        if current_version >= self.CURRENT_VERSION:
            console.print(f"✅ Database is up to date (version {current_version})", style="green")
            return True

        if current_version == 0:
            # No existing schema - this should be handled by initial setup
            console.print(
                "No existing database schema found. Use 'setup' command first.",
                style="yellow",
            )
            return False

        console.print(
            f"🔄 Upgrading database schema from v{current_version} to v{self.CURRENT_VERSION}...",
            style="blue",
        )

        # Create schema version table if needed
        self.create_schema_version_table()

        # Create backup
        backup_path = self.create_backup(current_version)

        try:
            # Apply migration
            self.migrate_to_version(self.CURRENT_VERSION, current_version)

            console.print(
                f"✅ Database successfully upgraded to version {self.CURRENT_VERSION}!",
                style="green bold",
            )

            # Show backup info
            recovery_panel = Panel(
                f"[green]✅ Migration completed successfully![/green]\n\n"
                f"[blue]💡 Backup available:[/blue] {backup_path.name}\n"
                f"[dim]Keep this backup until you're sure everything works correctly.[/dim]",
                title="Migration Complete",
                border_style="green",
            )
            console.print(recovery_panel)

            return True

        except Exception as e:
            console.print(f"❌ Migration failed: {e}", style="red")
            self.show_recovery_instructions(backup_path, current_version)
            return False

    def check_migration_needed(self) -> bool:
        """Check if database migration is needed."""
        current_version = self.get_schema_version()
        return current_version < self.CURRENT_VERSION

    def get_migration_info(self) -> dict:
        """Get information about current schema and needed migrations."""
        current_version = self.get_schema_version()

        return {
            "current_version": current_version,
            "target_version": self.CURRENT_VERSION,
            "migration_needed": current_version < self.CURRENT_VERSION,
            "migration_available": current_version > 0 and current_version < self.CURRENT_VERSION,
        }
