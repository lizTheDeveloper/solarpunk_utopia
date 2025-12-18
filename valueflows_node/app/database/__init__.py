"""
ValueFlows Node Database Module

Handles SQLite database initialization and connection management.
"""

import sqlite3
from pathlib import Path
from typing import Optional
import os


class VFDatabase:
    """ValueFlows database manager"""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file. If None, uses default.
        """
        if db_path is None:
            # Default to app/database/valueflows.db
            db_dir = Path(__file__).parent
            db_path = db_dir / "valueflows.db"

        self.db_path = str(db_path)
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self):
        """Open database connection"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Access columns by name
        # Enable foreign keys
        self.conn.execute("PRAGMA foreign_keys = ON")
        return self.conn

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def initialize_schema(self):
        """Create all tables from schema.sql"""
        schema_path = Path(__file__).parent / "vf_schema.sql"

        with open(schema_path, 'r') as f:
            schema_sql = f.read()

        if not self.conn:
            self.connect()

        self.conn.executescript(schema_sql)
        self.conn.commit()

    def get_cursor(self) -> sqlite3.Cursor:
        """Get a database cursor"""
        if not self.conn:
            self.connect()
        return self.conn.cursor()

    def commit(self):
        """Commit current transaction"""
        if self.conn:
            self.conn.commit()

    def rollback(self):
        """Rollback current transaction"""
        if self.conn:
            self.conn.rollback()

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        self.close()


# Global database instance (singleton pattern)
_db_instance: Optional[VFDatabase] = None


def get_database(db_path: Optional[str] = None) -> VFDatabase:
    """
    Get or create the global database instance.

    Args:
        db_path: Optional custom database path

    Returns:
        VFDatabase instance
    """
    global _db_instance

    if _db_instance is None:
        _db_instance = VFDatabase(db_path)

    return _db_instance


def initialize_database(db_path: Optional[str] = None):
    """
    Initialize the ValueFlows database.

    Creates tables and indexes if they don't exist.

    Args:
        db_path: Optional custom database path
    """
    db = get_database(db_path)
    db.connect()
    db.initialize_schema()
    print(f"✓ ValueFlows database initialized at: {db.db_path}")
    return db
