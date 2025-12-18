"""ResourceSpec Repository - CRUD operations for ResourceSpecs"""

from typing import List
import sqlite3
from datetime import datetime
from ...models.vf.resource_spec import ResourceSpec, ResourceCategory
from .base_repo import BaseRepository


class ResourceSpecRepository(BaseRepository[ResourceSpec]):
    def __init__(self, conn: sqlite3.Connection):
        super().__init__(conn, "resource_specs", ResourceSpec)

    def create(self, spec: ResourceSpec) -> ResourceSpec:
        if spec.created_at is None:
            spec.created_at = datetime.now()

        query = """
            INSERT INTO resource_specs (id, name, category, description, subcategory,
                                       image_url, default_unit, created_at, updated_at, author, signature)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (spec.id, spec.name, spec.category.value, spec.description, spec.subcategory,
                 spec.image_url, spec.default_unit, spec.created_at.isoformat(),
                 spec.updated_at.isoformat() if spec.updated_at else None, spec.author, spec.signature)

        self._execute(query, params)
        self.conn.commit()
        return spec

    def update(self, spec: ResourceSpec) -> ResourceSpec:
        spec.updated_at = datetime.now()
        query = """
            UPDATE resource_specs SET name = ?, description = ?, subcategory = ?,
                                     image_url = ?, default_unit = ?, updated_at = ? WHERE id = ?
        """
        params = (spec.name, spec.description, spec.subcategory, spec.image_url,
                 spec.default_unit, spec.updated_at.isoformat(), spec.id)
        self._execute(query, params)
        self.conn.commit()
        return spec

    def find_by_category(self, category: ResourceCategory) -> List[ResourceSpec]:
        query = "SELECT * FROM resource_specs WHERE category = ? ORDER BY name"
        rows = self._fetch_all(query, (category.value,))
        return [ResourceSpec.from_dict(row) for row in rows]
