"""Steward Authentication and Authorization

Helpers for verifying steward role on cells.
Stewards are high-trust community leaders with special permissions.
"""
from fastapi import HTTPException, Depends
from functools import wraps
from typing import Optional

from app.database import get_db


async def verify_steward(user_id: str, cell_id: Optional[str] = None) -> bool:
    """Verify user is a steward of the specified cell.

    Args:
        user_id: User ID to check
        cell_id: Cell ID (if None, checks if user is steward of ANY cell)

    Returns:
        True if user is steward, False otherwise
    """
    db = await get_db()

    if cell_id:
        # Check if steward of specific cell
        cursor = await db.execute(
            """SELECT role FROM cell_memberships
               WHERE user_id = ? AND cell_id = ? AND is_active = 1""",
            (user_id, cell_id)
        )
        row = await cursor.fetchone()
        return row is not None and row[0] == 'steward'
    else:
        # Check if steward of any cell
        cursor = await db.execute(
            """SELECT COUNT(*) FROM cell_memberships
               WHERE user_id = ? AND role = 'steward' AND is_active = 1""",
            (user_id,)
        )
        row = await cursor.fetchone()
        return row is not None and row[0] > 0


async def require_steward_of_cell(user_id: str, cell_id: str):
    """Require user to be steward of specific cell.

    Raises HTTPException if not steward.

    Args:
        user_id: User ID
        cell_id: Cell ID

    Raises:
        HTTPException: 403 if user is not steward of cell
    """
    if not await verify_steward(user_id, cell_id):
        raise HTTPException(
            status_code=403,
            detail=f"Steward role required for cell {cell_id}"
        )


async def require_steward(user_id: str):
    """Require user to be a steward of any cell.

    Raises HTTPException if not steward.

    Args:
        user_id: User ID

    Raises:
        HTTPException: 403 if user is not a steward
    """
    if not await verify_steward(user_id):
        raise HTTPException(
            status_code=403,
            detail="Steward role required for this action"
        )
