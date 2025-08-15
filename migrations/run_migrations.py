#!/usr/bin/env python3
"""
PRT Migration Runner

This script manages and runs database migrations in the correct order.
It tracks which migrations have been applied and ensures they run only once.

Usage:
    python migrations/run_migrations.py [--list] [--run-all] [--run 001] [--status]
"""

import sys
import argparse
import sqlite3
from pathlib import Path
from typing import List, Dict, Any
from rich.console import Console
from rich.table import Table
import importlib.util

console = Console()


class MigrationTracker:
    """Track migration status in the database."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._ensure_migration_table()
    
    def _ensure_migration_table(self):
        """Create migration tracking table if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS migration_history (
                id INTEGER PRIMARY KEY,
                migration_name TEXT NOT NULL UNIQUE,
                applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN DEFAULT TRUE,
                error_message TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migration names."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT migration_name FROM migration_history WHERE success = TRUE ORDER BY id")
        migrations = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return migrations
    
    def mark_migration_applied(self, migration_name: str, success: bool = True, error_message: str = None):
        """Mark a migration as applied."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO migration_history (migration_name, success, error_message)
            VALUES (?, ?, ?)
        """, (migration_name, success, error_message))
        
        conn.commit()
        conn.close()
    
    def is_migration_applied(self, migration_name: str) -> bool:
        """Check if a migration has been applied."""
        return migration_name in self.get_applied_migrations()


class MigrationRunner:
    """Run migrations in order."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.tracker = MigrationTracker(db_path)
        self.migrations_dir = Path(__file__).parent
        # Change to main directory for relative imports
        sys.path.insert(0, str(Path(__file__).parent.parent))
    
    def get_available_migrations(self) -> List[Path]:
        """Get list of available migration files."""
        migration_files = []
        
        for file_path in self.migrations_dir.glob("*.py"):
            if file_path.name.startswith(("0", "1", "2", "3", "4", "5", "6", "7", "8", "9")) and file_path.name != "run_migrations.py":
                migration_files.append(file_path)
        
        # Sort by migration number
        migration_files.sort(key=lambda x: x.name)
        return migration_files
    
    def run_migration(self, migration_path: Path) -> bool:
        """Run a single migration."""
        migration_name = migration_path.stem
        
        if self.tracker.is_migration_applied(migration_name):
            console.print(f"Migration {migration_name} already applied, skipping.", style="yellow")
            return True
        
        console.print(f"Running migration: {migration_name}", style="bold blue")
        
        try:
            # Import and run the migration
            spec = importlib.util.spec_from_file_location(migration_name, migration_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Run the main function
            success = module.main()
            
            if success:
                self.tracker.mark_migration_applied(migration_name, success=True)
                console.print(f"Migration {migration_name} completed successfully.", style="green")
                return True
            else:
                self.tracker.mark_migration_applied(migration_name, success=False, error_message="Migration failed")
                console.print(f"Migration {migration_name} failed.", style="red")
                return False
                
        except Exception as e:
            error_msg = str(e)
            self.tracker.mark_migration_applied(migration_name, success=False, error_message=error_msg)
            console.print(f"Migration {migration_name} failed with error: {error_msg}", style="red")
            return False
    
    def run_all_migrations(self) -> bool:
        """Run all pending migrations."""
        migration_files = self.get_available_migrations()
        
        if not migration_files:
            console.print("No migration files found.", style="yellow")
            return True
        
        console.print(f"Found {len(migration_files)} migration files.", style="blue")
        
        success_count = 0
        for migration_path in migration_files:
            if self.run_migration(migration_path):
                success_count += 1
            else:
                console.print(f"Stopping migration process due to failure in {migration_path.name}", style="red")
                break
        
        console.print(f"Completed {success_count}/{len(migration_files)} migrations.", style="blue")
        return success_count == len(migration_files)
    
    def run_specific_migration(self, migration_number: str) -> bool:
        """Run a specific migration by number."""
        migration_files = self.get_available_migrations()
        
        target_migration = None
        for migration_path in migration_files:
            if migration_path.name.startswith(f"{migration_number}_"):
                target_migration = migration_path
                break
        
        if not target_migration:
            console.print(f"Migration {migration_number} not found.", style="red")
            return False
        
        return self.run_migration(target_migration)
    
    def show_status(self):
        """Show migration status."""
        available_migrations = self.get_available_migrations()
        applied_migrations = self.tracker.get_applied_migrations()
        
        table = Table(title="Migration Status")
        table.add_column("Migration", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Applied At", style="yellow")
        
        for migration_path in available_migrations:
            migration_name = migration_path.stem
            if migration_name in applied_migrations:
                status = "✅ Applied"
                applied_at = "N/A"  # Could fetch from database if needed
            else:
                status = "⏳ Pending"
                applied_at = "N/A"
            
            table.add_row(migration_name, status, applied_at)
        
        console.print(table)
    
    def list_migrations(self):
        """List all available migrations."""
        migration_files = self.get_available_migrations()
        
        if not migration_files:
            console.print("No migration files found.", style="yellow")
            return
        
        table = Table(title="Available Migrations")
        table.add_column("Number", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Description", style="yellow")
        
        for migration_path in migration_files:
            # Extract migration number and description
            name_parts = migration_path.stem.split("_", 1)
            if len(name_parts) >= 2:
                number = name_parts[0]
                description = name_parts[1].replace("_", " ")
            else:
                number = "???"
                description = migration_path.stem
            
            table.add_row(number, migration_path.name, description)
        
        console.print(table)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="PRT Migration Runner")
    parser.add_argument("--list", action="store_true", help="List available migrations")
    parser.add_argument("--run-all", action="store_true", help="Run all pending migrations")
    parser.add_argument("--run", type=str, help="Run specific migration by number (e.g., 001)")
    parser.add_argument("--status", action="store_true", help="Show migration status")
    
    args = parser.parse_args()
    
    # Find database file
    db_path = Path("prt_data/prt.db")
    if not db_path.exists():
        console.print("Database not found. Please run the CLI first to create it.", style="red")
        return 1
    
    runner = MigrationRunner(db_path)
    
    if args.list:
        runner.list_migrations()
    elif args.status:
        runner.show_status()
    elif args.run_all:
        success = runner.run_all_migrations()
        return 0 if success else 1
    elif args.run:
        success = runner.run_specific_migration(args.run)
        return 0 if success else 1
    else:
        # Default: show status
        runner.show_status()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
