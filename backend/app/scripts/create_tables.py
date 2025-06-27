#!/usr/bin/env python3
"""
Script to create database tables using SQLModel metadata
"""

import sys
import os

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pathlib import Path
import subprocess
from sqlalchemy import text

from core.database import get_admin_engine
from core.database import test_rls
from scripts.apply_rls_only import apply_rls_policies_only


def read_sql_file() -> str:
    """Read the RLS setup SQL file and return its content as a string."""
    sql_file_path = Path(__file__).parent / "db_setup.sql"
    return sql_file_path.read_text()


def apply_rls_policies() -> None:
    """Execute the RLS SQL script using the SQLAlchemy engine."""
    sql_content = read_sql_file()
    # Using exec_driver_sql to allow execution of multiple SQL statements
    with get_admin_engine().begin() as connection:
        connection.exec_driver_sql(sql_content)
    print("Row-level security policies applied successfully.")


from core.database import create_db_and_tables


def main():
    """Create all database tables"""
    try:
        print("Creating database tables...")
        create_db_and_tables(admin=True)
        apply_rls_policies_only()
        print("Database tables created successfully!")
    except Exception as e:
        print(f"Error creating database tables: {e}")


if __name__ == "__main__":
    exit(main())
