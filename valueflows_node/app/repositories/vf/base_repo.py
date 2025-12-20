"""
Base Repository for VF objects

Provides common CRUD operations.
"""

from typing import Optional, List, TypeVar, Generic, Type
from datetime import datetime
import sqlite3


T = TypeVar('T')


class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations"""

    def __init__(self, conn: sqlite3.Connection, table_name: str, model_class: Type[T]):
        """
        Initialize repository.

        Args:
            conn: SQLite connection
            table_name: Name of the database table
            model_class: Model class for deserialization
        """
        self.conn = conn
        self.table_name = table_name
        self.model_class = model_class

    def _row_to_dict(self, row: sqlite3.Row) -> dict:
        """Convert SQLite row to dictionary"""
        return dict(row) if row else None

    def _execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a query"""
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor

    def _fetch_one(self, query: str, params: tuple = ()) -> Optional[dict]:
        """Fetch single row as dictionary"""
        cursor = self._execute(query, params)
        row = cursor.fetchone()
        return self._row_to_dict(row)

    def _fetch_all(self, query: str, params: tuple = ()) -> List[dict]:
        """Fetch all rows as list of dictionaries"""
        cursor = self._execute(query, params)
        rows = cursor.fetchall()
        return [self._row_to_dict(row) for row in rows]

    def find_by_id(self, obj_id: str) -> Optional[T]:
        """
        Find object by ID.

        Args:
            obj_id: Object ID

        Returns:
            Object instance or None
        """
        query = f"SELECT * FROM {self.table_name} WHERE id = ?"
        row = self._fetch_one(query, (obj_id,))

        if row:
            return self.model_class.from_dict(row)
        return None

    def find_all(self, limit: Optional[int] = None, offset: int = 0) -> List[T]:
        """
        Find all objects.

        Args:
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of objects
        """
        query = f"SELECT * FROM {self.table_name} ORDER BY created_at DESC"

        if limit is not None:
            # GAP-57: Use parameterized query to prevent SQL injection
            query += " LIMIT ? OFFSET ?"
            rows = self._fetch_all(query, (limit, offset))
        else:
            rows = self._fetch_all(query)

        return [self.model_class.from_dict(row) for row in rows]

    def count(self) -> int:
        """Count total objects"""
        query = f"SELECT COUNT(*) as count FROM {self.table_name}"
        cursor = self._execute(query)
        row = cursor.fetchone()
        return row['count'] if row else 0

    def delete(self, obj_id: str) -> bool:
        """
        Delete object by ID.

        Args:
            obj_id: Object ID

        Returns:
            True if deleted, False if not found
        """
        query = f"DELETE FROM {self.table_name} WHERE id = ?"
        cursor = self._execute(query, (obj_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def exists(self, obj_id: str) -> bool:
        """Check if object exists"""
        query = f"SELECT 1 FROM {self.table_name} WHERE id = ? LIMIT 1"
        cursor = self._execute(query, (obj_id,))
        return cursor.fetchone() is not None
