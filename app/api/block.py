"""
Block API - User blocking for harassment prevention (GAP-107)

Endpoints:
- POST /block/{user_id} - Block a user
- DELETE /block/{user_id} - Unblock a user
- GET /block/list - Get list of users you've blocked
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List
import sqlite3

from app.auth.middleware import require_auth
from app.auth.models import User
from app.database.block_repository import BlockRepository


router = APIRouter(prefix="/block", tags=["block"])


def get_block_repo() -> BlockRepository:
    """Get block repository with database connection"""
    # TODO: Use proper database connection from DI
    # For now, create local SQLite connection
    conn = sqlite3.connect("data/solarpunk.db", check_same_thread=False)
    return BlockRepository(conn)


@router.post("/{user_id}")
async def block_user(
    user_id: str,
    reason: str = None,
    current_user: User = Depends(require_auth),
    repo: BlockRepository = Depends(get_block_repo),
):
    """
    Block a user - they won't be able to match or message you.

    The block is silent - the blocked user won't know they've been blocked.
    They just won't see your offers/needs in their matches.

    Args:
        user_id: ID of user to block
        reason: Optional private reason (not shared with blocked user)
    """
    try:
        if user_id == current_user.id:
            raise HTTPException(status_code=400, detail="Cannot block yourself")

        block = repo.block_user(current_user.id, user_id, reason)

        return {
            "status": "blocked",
            "blocked_id": user_id,
            "created_at": block.created_at.isoformat(),
        }

    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="User already blocked")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{user_id}")
async def unblock_user(
    user_id: str,
    current_user: User = Depends(require_auth),
    repo: BlockRepository = Depends(get_block_repo),
):
    """
    Unblock a user.

    Args:
        user_id: ID of user to unblock
    """
    try:
        success = repo.unblock_user(current_user.id, user_id)

        if not success:
            raise HTTPException(status_code=404, detail="No block found")

        return {"status": "unblocked", "unblocked_id": user_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_blocked_users(
    current_user: User = Depends(require_auth),
    repo: BlockRepository = Depends(get_block_repo),
) -> List[str]:
    """
    Get list of users you've blocked.

    Returns:
        List[str]: List of blocked user IDs
    """
    try:
        blocked_ids = repo.get_blocked_by_user(current_user.id)
        return blocked_ids

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/check/{user_id}")
async def check_blocked(
    user_id: str,
    current_user: User = Depends(require_auth),
    repo: BlockRepository = Depends(get_block_repo),
) -> dict:
    """
    Check if you have blocked a specific user.

    Args:
        user_id: ID of user to check

    Returns:
        dict: {"blocked": bool}
    """
    try:
        blocked = repo.is_blocked(current_user.id, user_id)
        return {"blocked": blocked}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
