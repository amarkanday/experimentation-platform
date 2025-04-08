#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

def run_migrations():
    """Run database migrations using Alembic."""
    # Get the absolute path to the migrations directory
    backend_dir = Path(__file__).parent.parent
    migrations_dir = backend_dir / "app" / "db" / "migrations"

    if not migrations_dir.exists():
        print(f"Error: Migrations directory not found at {migrations_dir}")
        sys.exit(1)

    # Change to the migrations directory
    os.chdir(migrations_dir)

    try:
        # Run the migrations
        print("Running database migrations...")
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        print("Migrations completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error running migrations: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migrations()
