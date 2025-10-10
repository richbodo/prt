#!/usr/bin/env python3
"""
Database Migration Runner for PRT

This script safely runs the database migration from v5 to v6,
adding is_you, first_name, and last_name columns to the contacts table.

Usage:
    python run_migration.py          # Run migration
    python run_migration.py --check  # Check if migration is needed
"""

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

# Add prt_src to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text

from prt_src.db import create_database
from prt_src.schema_manager import SchemaManager

console = Console()


def check_migration():
    """Check if migration is needed without running it."""
    console.print("\n[bold blue]Checking database migration status...[/bold blue]\n")

    db_path = Path("prt_data/prt.db")
    if not db_path.exists():
        console.print("[red]Error: Database not found at prt_data/prt.db[/red]")
        return False

    db = create_database(db_path)
    mgr = SchemaManager(db)
    info = mgr.get_migration_info()

    console.print(f"[cyan]Current schema version:[/cyan] {info['current_version']}")
    console.print(f"[cyan]Target schema version:[/cyan] {info['target_version']}")

    if info["migration_needed"]:
        console.print(
            f"\n[yellow]⚠ Migration needed: v{info['current_version']} → v{info['target_version']}[/yellow]"
        )
        console.print("\n[blue]This migration will add:[/blue]")
        console.print("  - is_you column (BOOLEAN) for marking the 'You' contact")
        console.print("  - first_name column (VARCHAR(100)) split from name")
        console.print("  - last_name column (VARCHAR(100)) split from name")
        console.print("  - Index for fast 'You' contact lookup")
        console.print("\n[green]Run without --check to apply migration[/green]")
        return True
    else:
        console.print(f"\n[green]✅ Database is up to date (v{info['current_version']})[/green]")
        return False


def run_migration():
    """Run the database migration."""
    console.print("\n[bold blue]🔄 Running Database Migration[/bold blue]\n")

    db_path = Path("prt_data/prt.db")
    if not db_path.exists():
        console.print("[red]Error: Database not found at prt_data/prt.db[/red]")
        return False

    # Check current schema
    db = create_database(db_path)
    mgr = SchemaManager(db)
    info = mgr.get_migration_info()

    if not info["migration_needed"]:
        console.print(f"[green]✅ Database already up to date (v{info['current_version']})[/green]")
        return True

    # Show what will happen
    panel = Panel(
        f"""[yellow]About to migrate database:[/yellow]

[cyan]From:[/cyan] Schema version {info['current_version']}
[cyan]To:[/cyan] Schema version {info['target_version']}

[blue]Changes:[/blue]
• Add is_you column to contacts table
• Add first_name column to contacts table
• Add last_name column to contacts table
• Create index for 'You' contact lookup
• Populate first_name/last_name from existing name field

[green]Backup will be created automatically before migration.[/green]
""",
        title="Migration Plan",
        border_style="blue",
    )
    console.print(panel)

    # Ask for confirmation
    response = console.input("\n[yellow]Proceed with migration? (yes/no):[/yellow] ")
    if response.lower() not in ["yes", "y"]:
        console.print("[red]Migration cancelled.[/red]")
        return False

    # Run migration
    console.print("\n[blue]Starting migration...[/blue]\n")
    success = mgr.migrate_safely()

    if success:
        console.print("\n[bold green]✅ Migration completed successfully![/bold green]\n")

        # Verify the schema
        console.print("[blue]Verifying schema...[/blue]")
        db.session.execute(text("SELECT is_you, first_name, last_name FROM contacts LIMIT 1"))
        console.print("[green]✓ New columns accessible[/green]")

        return True
    else:
        console.print("\n[bold red]❌ Migration failed![/bold red]\n")
        console.print(
            "[yellow]Please check the error messages above and recovery instructions.[/yellow]"
        )
        return False


def main():
    parser = argparse.ArgumentParser(description="Run database migration for PRT (v5 → v6)")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if migration is needed without running it",
    )

    args = parser.parse_args()

    try:
        if args.check:
            check_migration()
        else:
            run_migration()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Migration cancelled by user.[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
