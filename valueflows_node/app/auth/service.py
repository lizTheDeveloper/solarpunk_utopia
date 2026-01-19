"""
Simple local authentication service

No passwords, no magic links, no JWT complexity.
Just name-based registration with session tokens for demos.
"""

import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
import json

from .models import User, UserCreate, Session, LoginResponse
from app.database.db import get_db


class AuthService:
    """Simple local auth service"""

    SESSION_DURATION_DAYS = 7

    async def register(self, user_data: UserCreate) -> LoginResponse:
        """
        Register a new user (or login if exists).
        Simple name-based registration - perfect for demos.
        """
        db = await get_db()

        # Check if user with this name exists
        cursor = await db.execute(
            "SELECT * FROM users WHERE name = ?",
            (user_data.name,)
        )
        row = await cursor.fetchone()

        if row:
            # User exists, just log them in
            user = User(
                id=row[0],
                name=row[1],
                email=row[2],
                created_at=datetime.fromisoformat(row[3]),
                last_login=datetime.fromisoformat(row[4]) if row[4] else None,
                settings=json.loads(row[5]) if row[5] else {}
            )
        else:
            # Create new user
            user_id = f"user:{uuid.uuid4()}"
            now = datetime.now(timezone.utc).isoformat()

            await db.execute(
                """
                INSERT INTO users (id, name, email, created_at, last_login, settings)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, user_data.name, user_data.email, now, now, '{}')
            )
            await db.commit()

            user = User(
                id=user_id,
                name=user_data.name,
                email=user_data.email,
                created_at=datetime.fromisoformat(now),
                last_login=datetime.fromisoformat(now),
                settings={}
            )

        # Create session
        session = await self._create_session(user.id)

        return LoginResponse(
            user=user,
            token=session.token,
            expires_at=session.expires_at
        )

    async def login(self, name: str) -> Optional[LoginResponse]:
        """Login existing user by name"""
        db = await get_db()

        cursor = await db.execute(
            "SELECT * FROM users WHERE name = ?",
            (name,)
        )
        row = await cursor.fetchone()

        if not row:
            return None

        user = User(
            id=row[0],
            name=row[1],
            email=row[2],
            created_at=datetime.fromisoformat(row[3]),
            last_login=datetime.fromisoformat(row[4]) if row[4] else None,
            settings=json.loads(row[5]) if row[5] else {}
        )

        # Update last login
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "UPDATE users SET last_login = ? WHERE id = ?",
            (now, user.id)
        )
        await db.commit()

        # Create session
        session = await self._create_session(user.id)

        return LoginResponse(
            user=user,
            token=session.token,
            expires_at=session.expires_at
        )

    async def get_user_from_token(self, token: str) -> Optional[User]:
        """Get user from session token"""
        db = await get_db()

        # Find session
        cursor = await db.execute(
            """
            SELECT s.*, u.*
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.token = ?
            """,
            (token,)
        )
        row = await cursor.fetchone()

        if not row:
            return None

        # Check if session expired
        expires_at = datetime.fromisoformat(row[3])
        if expires_at < datetime.now(timezone.utc):
            # Session expired, delete it
            await db.execute("DELETE FROM sessions WHERE token = ?", (token,))
            await db.commit()
            return None

        # Return user (columns 5-10 are user fields)
        user = User(
            id=row[5],
            name=row[6],
            email=row[7],
            created_at=datetime.fromisoformat(row[8]),
            last_login=datetime.fromisoformat(row[9]) if row[9] else None,
            settings=json.loads(row[10]) if row[10] else {}
        )

        return user

    async def logout(self, token: str) -> bool:
        """Logout - delete session"""
        db = await get_db()

        await db.execute("DELETE FROM sessions WHERE token = ?", (token,))
        await db.commit()

        return True

    async def update_user_settings(self, user_id: str, settings: dict) -> bool:
        """Update user settings"""
        db = await get_db()

        await db.execute(
            "UPDATE users SET settings = ? WHERE id = ?",
            (json.dumps(settings), user_id)
        )
        await db.commit()

        return True

    async def get_user_settings(self, user_id: str) -> dict:
        """Get user settings"""
        db = await get_db()

        cursor = await db.execute(
            "SELECT settings FROM users WHERE id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()

        if not row or not row[0]:
            return {}

        return json.loads(row[0])

    async def _create_session(self, user_id: str) -> Session:
        """Create a new session for user"""
        db = await get_db()

        session_id = f"session:{uuid.uuid4()}"
        token = secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=self.SESSION_DURATION_DAYS)

        await db.execute(
            """
            INSERT INTO sessions (id, user_id, token, expires_at, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_id, user_id, token, expires_at.isoformat(), now.isoformat())
        )
        await db.commit()

        return Session(
            id=session_id,
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            created_at=now
        )


# Global instance
_auth_service: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    """Get global auth service instance"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service
