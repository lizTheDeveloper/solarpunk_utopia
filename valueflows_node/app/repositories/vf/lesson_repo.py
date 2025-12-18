"""Lesson Repository - CRUD operations for Lessons"""

import sqlite3
from datetime import datetime
import json
from ...models.vf.lesson import Lesson
from .base_repo import BaseRepository


class LessonRepository(BaseRepository[Lesson]):
    def __init__(self, conn: sqlite3.Connection):
        super().__init__(conn, "lessons", Lesson)

    def create(self, lesson: Lesson) -> Lesson:
        if lesson.created_at is None:
            lesson.created_at = datetime.now()

        query = """
            INSERT INTO lessons
            (id, title, lesson_type, description, content, file_hash, file_url, estimated_duration,
             difficulty_level, skill_tags, protocol_ids, resource_spec_ids, prerequisite_lesson_ids,
             created_at, updated_at, author, signature)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (lesson.id, lesson.title, lesson.lesson_type, lesson.description, lesson.content,
                 lesson.file_hash, lesson.file_url, lesson.estimated_duration, lesson.difficulty_level,
                 json.dumps(lesson.skill_tags) if lesson.skill_tags else "[]",
                 json.dumps(lesson.protocol_ids) if lesson.protocol_ids else "[]",
                 json.dumps(lesson.resource_spec_ids) if lesson.resource_spec_ids else "[]",
                 json.dumps(lesson.prerequisite_lesson_ids) if lesson.prerequisite_lesson_ids else "[]",
                 lesson.created_at.isoformat(),
                 lesson.updated_at.isoformat() if lesson.updated_at else None,
                 lesson.author, lesson.signature)

        self._execute(query, params)
        self.conn.commit()
        return lesson

    def update(self, lesson: Lesson) -> Lesson:
        lesson.updated_at = datetime.now()
        query = "UPDATE lessons SET content = ?, file_url = ?, updated_at = ? WHERE id = ?"
        params = (lesson.content, lesson.file_url, lesson.updated_at.isoformat(), lesson.id)
        self._execute(query, params)
        self.conn.commit()
        return lesson
