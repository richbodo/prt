#!/usr/bin/env python3
"""
Create initial Alembic migration from SQLAlchemy models.

This script helps set up the initial migration for PRT using the
SQLAlchemy models defined in prt_src/models.py.
"""

import sys
from pathlib import Path
import subprocess

def main():
    print("PRT Initial Migration Setup")
    print("=" * 40)
    
    # Check if alembic is installed
    try:
        import alembic
    except ImportError:
        print("Alembic not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "alembic"])
    
    # Check if alembic.ini exists
    if not Path("alembic.ini").exists():
        print("Initializing Alembic...")
        subprocess.run(["alembic", "init", "alembic"])
        print("Alembic initialized.")
    
    # Update alembic.ini to use our models
    update_alembic_config()
    
    # Generate initial migration
    print("\nGenerating initial migration...")
    subprocess.run(["alembic", "revision", "--autogenerate", "-m", "Initial schema"])
    
    print("\nMigration created! Next steps:")
    print("1. Review the generated migration file in alembic/versions/")
    print("2. Apply the migration: alembic upgrade head")
    print("3. Verify the database was created correctly")

def update_alembic_config():
    """Update alembic.ini to use our SQLAlchemy models."""
    import configparser
    
    config = configparser.ConfigParser()
    config.read("alembic.ini")
    
    # Update the sqlalchemy.url to use our database
    config.set("alembic", "sqlalchemy.url", "sqlite:///prt_data/prt.db")
    
    # Update the script_location to point to our alembic directory
    config.set("alembic", "script_location", "alembic")
    
    # Update env.py to import our models
    update_env_py()
    
    # Save the updated config
    with open("alembic.ini", "w") as f:
        config.write(f)
    
    print("Updated alembic.ini configuration.")

def update_env_py():
    """Update alembic/env.py to import our models."""
    env_py_path = Path("alembic/env.py")
    if not env_py_path.exists():
        print("Warning: alembic/env.py not found. Please run 'alembic init alembic' first.")
        return
    
    # Read the current env.py
    with open(env_py_path, "r") as f:
        content = f.read()
    
    # Add our model imports
    if "from prt_src.models import Base" not in content:
        # Find the target line and add our imports
        lines = content.split("\n")
        new_lines = []
        
        for line in lines:
            new_lines.append(line)
            if "from alembic import context" in line:
                # Add our imports after the alembic import
                new_lines.append("")
                new_lines.append("# Import our models")
                new_lines.append("import sys")
                new_lines.append("from pathlib import Path")
                new_lines.append("sys.path.insert(0, str(Path(__file__).parent.parent))")
                new_lines.append("from prt_src.models import Base")
        
        # Update the target_metadata line
        for i, line in enumerate(new_lines):
            if "target_metadata = None" in line:
                new_lines[i] = "target_metadata = Base.metadata"
                break
        
        # Write the updated content
        with open(env_py_path, "w") as f:
            f.write("\n".join(new_lines))
        
        print("Updated alembic/env.py to import our models.")

if __name__ == "__main__":
    main()
