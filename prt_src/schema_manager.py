"""
Simple Schema Manager for PRT

This module provides a straightforward approach to database schema management
with automatic backups and clear recovery instructions for users.
"""

import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional
from rich.console import Console
from rich.panel import Panel
import sqlalchemy
from sqlalchemy import text

console = Console()


class SchemaManager:
    """Simple, safe database schema management."""
    
    CURRENT_VERSION = 2
    
    def __init__(self, db):
        """Initialize with database connection."""
        self.db = db
        
    def get_schema_version(self) -> int:
        """Get current database schema version."""
        try:
            # Try to get version from schema_version table
            result = self.db.session.execute(text("SELECT version FROM schema_version LIMIT 1")).fetchone()
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
            self.db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    id INTEGER PRIMARY KEY,
                    version INTEGER NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Insert initial version if table is empty
            result = self.db.session.execute(text("SELECT COUNT(*) FROM schema_version")).fetchone()
            if result[0] == 0:
                current_version = self.get_schema_version()
                self.db.session.execute(text("INSERT INTO schema_version (version) VALUES (?)"), (current_version,))
            
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
            padding=(1, 2)
        )
        console.print(panel)
    
    def apply_migration_v1_to_v2(self):
        """Add profile image support to contacts table."""
        console.print("Adding profile image support to contacts...", style="blue")
        
        try:
            # Add the new columns
            self.db.session.execute(text("ALTER TABLE contacts ADD COLUMN profile_image BLOB"))
            console.print("  ✓ Added profile_image column", style="green")
            
            self.db.session.execute(text("ALTER TABLE contacts ADD COLUMN profile_image_filename TEXT"))
            console.print("  ✓ Added profile_image_filename column", style="green")
            
            self.db.session.execute(text("ALTER TABLE contacts ADD COLUMN profile_image_mime_type TEXT"))
            console.print("  ✓ Added profile_image_mime_type column", style="green")
            
            # Update schema version
            self.db.session.execute(text("UPDATE schema_version SET version = 2, updated_at = CURRENT_TIMESTAMP"))
            
            self.db.session.commit()
            console.print("✅ Profile image support added successfully!", style="green bold")
            
        except Exception as e:
            self.db.session.rollback()
            raise RuntimeError(f"Failed to add profile image columns: {e}")
    
    def migrate_to_version(self, target_version: int, current_version: int):
        """Apply migrations to reach target version."""
        if current_version == 1 and target_version == 2:
            self.apply_migration_v1_to_v2()
        else:
            raise ValueError(f"No migration path from version {current_version} to {target_version}")
    
    def migrate_safely(self) -> bool:
        """Perform safe database migration with backup and recovery instructions."""
        current_version = self.get_schema_version()
        
        if current_version >= self.CURRENT_VERSION:
            console.print(f"✅ Database is up to date (version {current_version})", style="green")
            return True
        
        if current_version == 0:
            # No existing schema - this should be handled by initial setup
            console.print("No existing database schema found. Use 'setup' command first.", style="yellow")
            return False
        
        console.print(f"🔄 Upgrading database schema from v{current_version} to v{self.CURRENT_VERSION}...", style="blue")
        
        # Create schema version table if needed
        self.create_schema_version_table()
        
        # Create backup
        backup_path = self.create_backup(current_version)
        
        try:
            # Apply migration
            self.migrate_to_version(self.CURRENT_VERSION, current_version)
            
            console.print(f"✅ Database successfully upgraded to version {self.CURRENT_VERSION}!", style="green bold")
            
            # Show backup info
            recovery_panel = Panel(
                f"[green]✅ Migration completed successfully![/green]\n\n"
                f"[blue]💡 Backup available:[/blue] {backup_path.name}\n"
                f"[dim]Keep this backup until you're sure everything works correctly.[/dim]",
                title="Migration Complete",
                border_style="green"
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
            'current_version': current_version,
            'target_version': self.CURRENT_VERSION,
            'migration_needed': current_version < self.CURRENT_VERSION,
            'migration_available': current_version > 0 and current_version < self.CURRENT_VERSION
        }
