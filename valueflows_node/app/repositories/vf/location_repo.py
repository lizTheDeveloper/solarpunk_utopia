"""Location Repository - CRUD operations for Locations"""

from typing import List
import sqlite3
from datetime import datetime
from ...models.vf.location import Location
from .base_repo import BaseRepository


class LocationRepository(BaseRepository[Location]):
    def __init__(self, conn: sqlite3.Connection):
        super().__init__(conn, "locations", Location)

    def create(self, location: Location) -> Location:
        if location.created_at is None:
            location.created_at = datetime.now()

        query = """
            INSERT INTO locations (id, name, description, address, latitude, longitude,
                                 parent_location_id, created_at, updated_at, author, signature)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (location.id, location.name, location.description, location.address,
                 location.latitude, location.longitude, location.parent_location_id,
                 location.created_at.isoformat(), location.updated_at.isoformat() if location.updated_at else None,
                 location.author, location.signature)

        self._execute(query, params)
        self.conn.commit()
        return location

    def update(self, location: Location) -> Location:
        location.updated_at = datetime.now()
        query = """
            UPDATE locations SET name = ?, description = ?, address = ?, latitude = ?,
                               longitude = ?, updated_at = ? WHERE id = ?
        """
        params = (location.name, location.description, location.address, location.latitude,
                 location.longitude, location.updated_at.isoformat(), location.id)
        self._execute(query, params)
        self.conn.commit()
        return location
