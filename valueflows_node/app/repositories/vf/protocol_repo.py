"""Protocol Repository - CRUD operations for Protocols"""

import sqlite3
from datetime import datetime
import json
from ...models.vf.protocol import Protocol
from .base_repo import BaseRepository


class ProtocolRepository(BaseRepository[Protocol]):
    def __init__(self, conn: sqlite3.Connection):
        super().__init__(conn, "protocols", Protocol)

    def create(self, protocol: Protocol) -> Protocol:
        if protocol.created_at is None:
            protocol.created_at = datetime.now()

        query = """
            INSERT INTO protocols
            (id, name, category, description, instructions, expected_inputs, expected_outputs,
             estimated_duration, difficulty_level, lesson_ids, file_hashes, tags, created_at, updated_at, author, signature)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (protocol.id, protocol.name, protocol.category, protocol.description, protocol.instructions,
                 protocol.expected_inputs, protocol.expected_outputs, protocol.estimated_duration,
                 protocol.difficulty_level,
                 json.dumps(protocol.lesson_ids) if protocol.lesson_ids else "[]",
                 json.dumps(protocol.file_hashes) if protocol.file_hashes else "[]",
                 json.dumps(protocol.tags) if protocol.tags else "[]",
                 protocol.created_at.isoformat(),
                 protocol.updated_at.isoformat() if protocol.updated_at else None,
                 protocol.author, protocol.signature)

        self._execute(query, params)
        self.conn.commit()
        return protocol

    def update(self, protocol: Protocol) -> Protocol:
        protocol.updated_at = datetime.now()
        query = "UPDATE protocols SET description = ?, instructions = ?, updated_at = ? WHERE id = ?"
        params = (protocol.description, protocol.instructions, protocol.updated_at.isoformat(), protocol.id)
        self._execute(query, params)
        self.conn.commit()
        return protocol
