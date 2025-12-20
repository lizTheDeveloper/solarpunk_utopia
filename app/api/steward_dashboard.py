"""
API endpoints for Steward Dashboard

Provides cell leaders with visibility into cell health and pending actions.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import json

from ..database import get_db
from .cells import get_current_user

router = APIRouter(prefix="/steward", tags=["steward"])


class CellMetrics(BaseModel):
    cell_id: str
    cell_name: str
    member_count: int
    active_offers: int
    active_needs: int
    matches_this_week: int
    exchanges_this_week: int
    value_kept_local: float
    new_members_this_week: int


class AttentionItem(BaseModel):
    type: str  # 'join_request', 'proposal', 'inactive_member', 'trust_issue'
    priority: str  # 'high', 'medium', 'low'
    message: str
    action_url: Optional[str] = None
    count: int = 1


class RecentActivity(BaseModel):
    type: str  # 'offer', 'need', 'match', 'exchange', 'join'
    message: str
    timestamp: str
    user_id: Optional[str] = None


class Celebration(BaseModel):
    type: str  # 'milestone', 'achievement'
    message: str
    user_id: Optional[str] = None


class DashboardData(BaseModel):
    metrics: CellMetrics
    attention_items: List[AttentionItem]
    recent_activity: List[RecentActivity]
    celebrations: List[Celebration]


@router.get("/dashboard/{cell_id}", response_model=DashboardData)
async def get_steward_dashboard(
    cell_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Get dashboard data for a cell steward.

    Shows metrics, items needing attention, recent activity, and celebrations.
    """
    db = await get_db()

    # Verify user is a steward of this cell
    cursor = await db.execute("""
        SELECT role FROM cell_memberships
        WHERE cell_id = ? AND user_id = ? AND is_active = 1
    """, (cell_id, user_id))

    membership = await cursor.fetchone()

    if not membership or membership[0] != 'steward':
        raise HTTPException(status_code=403, detail="Only stewards can access this dashboard")

    # Get cell info
    cursor = await db.execute("SELECT name FROM cells WHERE id = ?", (cell_id,))
    cell_row = await cursor.fetchone()

    if not cell_row:
        raise HTTPException(status_code=404, detail="Cell not found")

    cell_name = cell_row[0]

    # Calculate metrics
    metrics = await get_cell_metrics(db, cell_id, cell_name)

    # Get attention items
    attention_items = await get_attention_items(db, cell_id)

    # Get recent activity
    recent_activity = await get_recent_activity(db, cell_id)

    # Get celebrations
    celebrations = await get_celebrations(db, cell_id)

    return DashboardData(
        metrics=metrics,
        attention_items=attention_items,
        recent_activity=recent_activity,
        celebrations=celebrations
    )


async def get_cell_metrics(db, cell_id: str, cell_name: str) -> CellMetrics:
    """Calculate cell metrics for the dashboard"""

    # Get member count
    cursor = await db.execute("""
        SELECT COUNT(*) FROM cell_memberships
        WHERE cell_id = ? AND is_active = 1
    """, (cell_id,))
    member_count = (await cursor.fetchone())[0]

    # Get new members this week
    week_ago = (datetime.now() - timedelta(days=7)).isoformat()
    cursor = await db.execute("""
        SELECT COUNT(*) FROM cell_memberships
        WHERE cell_id = ? AND is_active = 1 AND joined_at >= ?
    """, (cell_id, week_ago))
    new_members_this_week = (await cursor.fetchone())[0]

    # TODO: Get active offers/needs from ValueFlows intents
    # For now, return placeholder values
    active_offers = 0
    active_needs = 0
    matches_this_week = 0
    exchanges_this_week = 0
    value_kept_local = 0.0

    return CellMetrics(
        cell_id=cell_id,
        cell_name=cell_name,
        member_count=member_count,
        active_offers=active_offers,
        active_needs=active_needs,
        matches_this_week=matches_this_week,
        exchanges_this_week=exchanges_this_week,
        value_kept_local=value_kept_local,
        new_members_this_week=new_members_this_week
    )


async def get_attention_items(db, cell_id: str) -> List[AttentionItem]:
    """Get items needing steward attention"""
    items = []

    # Check for pending join requests (invitations)
    cursor = await db.execute("""
        SELECT COUNT(*) FROM cell_invitations
        WHERE cell_id = ? AND status = 'pending'
        AND expires_at > datetime('now')
    """, (cell_id,))
    pending_requests = (await cursor.fetchone())[0]

    if pending_requests > 0:
        items.append(AttentionItem(
            type='join_request',
            priority='high',
            message=f'{pending_requests} join request{"s" if pending_requests != 1 else ""} pending',
            count=pending_requests
        ))

    # Check for inactive members (no activity in 14 days)
    two_weeks_ago = (datetime.now() - timedelta(days=14)).isoformat()
    cursor = await db.execute("""
        SELECT COUNT(*) FROM cell_memberships cm
        WHERE cm.cell_id = ? AND cm.is_active = 1
        AND cm.user_id NOT IN (
            SELECT DISTINCT user_id FROM user_sessions
            WHERE last_activity >= ?
        )
    """, (cell_id, two_weeks_ago))

    try:
        inactive_members = (await cursor.fetchone())[0]
        if inactive_members > 0:
            items.append(AttentionItem(
                type='inactive_member',
                priority='low',
                message=f'{inactive_members} member{"s" if inactive_members != 1 else ""} haven\'t been active in 2 weeks',
                count=inactive_members
            ))
    except aiosqlite.OperationalError as e:
        # Table might not exist yet during initial setup
        logger.debug(f"Could not query inactive members (table may not exist): {e}")
    except Exception as e:
        logger.error(f"Unexpected error querying inactive members: {e}", exc_info=True)
        # Don't fail the whole dashboard for one metric

    # All clear if no items
    if not items:
        items.append(AttentionItem(
            type='all_clear',
            priority='low',
            message='All clear - no pending actions'
        ))

    return items


async def get_recent_activity(db, cell_id: str) -> List[RecentActivity]:
    """Get recent activity in the cell"""
    activity = []

    # Get recent member joins
    cursor = await db.execute("""
        SELECT user_id, joined_at FROM cell_memberships
        WHERE cell_id = ? AND is_active = 1
        ORDER BY joined_at DESC
        LIMIT 10
    """, (cell_id,))

    rows = await cursor.fetchall()

    for row in rows:
        user_id_short = row[0][:8] if row[0] else 'Unknown'
        joined_at = row[1]

        activity.append(RecentActivity(
            type='join',
            message=f'New member: User {user_id_short}',
            timestamp=joined_at,
            user_id=row[0]
        ))

    # Sort by timestamp
    activity.sort(key=lambda x: x.timestamp, reverse=True)

    return activity[:10]  # Return top 10


async def get_celebrations(db, cell_id: str) -> List[Celebration]:
    """Get celebrations for the cell"""
    celebrations = []

    # Check if cell reached member milestone
    cursor = await db.execute("""
        SELECT COUNT(*) FROM cell_memberships
        WHERE cell_id = ? AND is_active = 1
    """, (cell_id,))
    member_count = (await cursor.fetchone())[0]

    if member_count >= 10 and member_count % 10 == 0:
        celebrations.append(Celebration(
            type='milestone',
            message=f'Cell reached {member_count} members!'
        ))

    # TODO: Add more celebration logic
    # - Member exchange milestones
    # - Total value circulated milestones
    # - Consecutive active days

    return celebrations


@router.get("/cells/managed", response_model=List[dict])
async def get_managed_cells(user_id: str = Depends(get_current_user)):
    """Get all cells where the user is a steward"""
    db = await get_db()

    cursor = await db.execute("""
        SELECT c.id, c.name, c.member_count, cm.role
        FROM cells c
        INNER JOIN cell_memberships cm ON c.id = cm.cell_id
        WHERE cm.user_id = ? AND cm.role = 'steward' AND cm.is_active = 1
        ORDER BY c.name
    """, (user_id,))

    rows = await cursor.fetchall()

    cells = []
    for row in rows:
        cells.append({
            'id': row[0],
            'name': row[1],
            'member_count': row[2],
            'role': row[3]
        })

    return cells
