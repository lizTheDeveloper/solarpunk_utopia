"""
API endpoints for Local Cells (Molecules)

Cells are geographic communities of 5-50 people who can meet IRL.
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import json
import uuid

from ..database import get_db

router = APIRouter(prefix="/cells", tags=["cells"])


class Cell(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    location_lat: Optional[float] = None
    location_lon: Optional[float] = None
    radius_km: float = 5.0
    created_at: str
    member_count: int = 0
    max_members: int = 50
    is_accepting_members: bool = True
    settings: dict = {}


class CellMembership(BaseModel):
    id: str
    cell_id: str
    user_id: str
    role: str  # 'member' or 'steward'
    joined_at: str
    vouched_by: Optional[str] = None
    is_active: bool = True


class CreateCellRequest(BaseModel):
    name: str
    description: Optional[str] = None
    location_lat: Optional[float] = None
    location_lon: Optional[float] = None
    radius_km: float = 5.0
    max_members: int = 50


class InviteToCellRequest(BaseModel):
    invitee_id: str


# Helper to get current user from auth header
async def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    """Extract user ID from authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Simple bearer token extraction
    # In production, validate JWT token here
    token = authorization.replace("Bearer ", "")

    db = await get_db()
    cursor = await db.execute(
        "SELECT user_id FROM sessions WHERE token = ? AND expires_at > datetime('now')",
        (token,)
    )
    row = await cursor.fetchone()

    if not row:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return row[0]


@router.post("/", response_model=Cell)
async def create_cell(
    request: CreateCellRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Create a new local cell.

    The creator becomes the first steward of the cell.
    """
    db = await get_db()

    cell_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()

    # Create cell
    await db.execute("""
        INSERT INTO cells (
            id, name, description, location_lat, location_lon,
            radius_km, created_at, member_count, max_members, is_accepting_members
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, 1)
    """, (
        cell_id, request.name, request.description,
        request.location_lat, request.location_lon,
        request.radius_km, created_at, request.max_members
    ))

    # Create cell settings
    await db.execute("""
        INSERT INTO cell_settings (cell_id) VALUES (?)
    """, (cell_id,))

    # Add creator as first steward
    membership_id = str(uuid.uuid4())
    term_start = datetime.now().isoformat()
    term_end = (datetime.now() + timedelta(days=90)).isoformat()

    await db.execute("""
        INSERT INTO cell_memberships (
            id, cell_id, user_id, role, joined_at,
            term_start_date, term_end_date, is_active
        ) VALUES (?, ?, ?, 'steward', ?, ?, ?, 1)
    """, (membership_id, cell_id, user_id, created_at, term_start, term_end))

    await db.commit()

    return Cell(
        id=cell_id,
        name=request.name,
        description=request.description,
        location_lat=request.location_lat,
        location_lon=request.location_lon,
        radius_km=request.radius_km,
        created_at=created_at,
        member_count=1,
        max_members=request.max_members,
        is_accepting_members=True
    )


@router.get("/", response_model=List[Cell])
async def list_cells(
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    radius_km: float = 50.0,
    accepting_members_only: bool = False
):
    """
    List cells, optionally filtered by location.

    If lat/lon provided, returns cells within radius_km.
    """
    db = await get_db()

    # For now, simple query without geospatial calculations
    # In production, use proper distance calculations
    query = "SELECT * FROM cells WHERE 1=1"
    params = []

    if accepting_members_only:
        query += " AND is_accepting_members = 1"

    if lat is not None and lon is not None:
        # Simple bounding box filter
        # In production, use haversine formula
        lat_delta = radius_km / 111.0  # Rough km to degrees
        lon_delta = radius_km / (111.0 * abs(lat))

        query += """ AND location_lat BETWEEN ? AND ?
                     AND location_lon BETWEEN ? AND ?"""
        params.extend([
            lat - lat_delta, lat + lat_delta,
            lon - lon_delta, lon + lon_delta
        ])

    query += " ORDER BY created_at DESC LIMIT 100"

    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()

    cells = []
    for row in rows:
        cells.append(Cell(
            id=row[0],
            name=row[1],
            description=row[2],
            location_lat=row[3],
            location_lon=row[4],
            radius_km=row[5],
            created_at=row[6],
            member_count=row[7],
            max_members=row[8],
            is_accepting_members=bool(row[9]),
            settings=json.loads(row[10]) if row[10] else {}
        ))

    return cells


@router.get("/{cell_id}", response_model=Cell)
async def get_cell(cell_id: str):
    """Get details for a specific cell"""
    db = await get_db()

    cursor = await db.execute("SELECT * FROM cells WHERE id = ?", (cell_id,))
    row = await cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Cell not found")

    return Cell(
        id=row[0],
        name=row[1],
        description=row[2],
        location_lat=row[3],
        location_lon=row[4],
        radius_km=row[5],
        created_at=row[6],
        member_count=row[7],
        max_members=row[8],
        is_accepting_members=bool(row[9]),
        settings=json.loads(row[10]) if row[10] else {}
    )


@router.get("/{cell_id}/members", response_model=List[CellMembership])
async def get_cell_members(cell_id: str):
    """Get all members of a cell"""
    db = await get_db()

    cursor = await db.execute("""
        SELECT id, cell_id, user_id, role, joined_at, vouched_by, is_active
        FROM cell_memberships
        WHERE cell_id = ? AND is_active = 1
        ORDER BY role DESC, joined_at ASC
    """, (cell_id,))

    rows = await cursor.fetchall()

    members = []
    for row in rows:
        members.append(CellMembership(
            id=row[0],
            cell_id=row[1],
            user_id=row[2],
            role=row[3],
            joined_at=row[4],
            vouched_by=row[5],
            is_active=bool(row[6])
        ))

    return members


@router.post("/{cell_id}/invite")
async def invite_to_cell(
    cell_id: str,
    request: InviteToCellRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Invite a user to join the cell.

    Only cell members can invite others.
    """
    db = await get_db()

    # Check if inviter is a member
    cursor = await db.execute("""
        SELECT id FROM cell_memberships
        WHERE cell_id = ? AND user_id = ? AND is_active = 1
    """, (cell_id, user_id))

    if not await cursor.fetchone():
        raise HTTPException(status_code=403, detail="Only cell members can invite")

    # Check if cell is accepting members
    cursor = await db.execute(
        "SELECT is_accepting_members, member_count, max_members FROM cells WHERE id = ?",
        (cell_id,)
    )
    cell_row = await cursor.fetchone()

    if not cell_row:
        raise HTTPException(status_code=404, detail="Cell not found")

    if not cell_row[0]:
        raise HTTPException(status_code=400, detail="Cell not accepting new members")

    if cell_row[1] >= cell_row[2]:
        raise HTTPException(status_code=400, detail="Cell is full")

    # Create invitation
    invitation_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()
    expires_at = (datetime.now() + timedelta(days=7)).isoformat()

    await db.execute("""
        INSERT INTO cell_invitations (
            id, cell_id, inviter_id, invitee_id, status, created_at, expires_at
        ) VALUES (?, ?, ?, ?, 'pending', ?, ?)
    """, (invitation_id, cell_id, user_id, request.invitee_id, created_at, expires_at))

    await db.commit()

    return {"invitation_id": invitation_id, "status": "pending"}


@router.post("/{cell_id}/invitations/{invitation_id}/accept")
async def accept_cell_invitation(
    cell_id: str,
    invitation_id: str,
    user_id: str = Depends(get_current_user)
):
    """Accept an invitation to join a cell"""
    db = await get_db()

    # Get invitation
    cursor = await db.execute("""
        SELECT inviter_id, invitee_id, status, expires_at
        FROM cell_invitations
        WHERE id = ? AND cell_id = ?
    """, (invitation_id, cell_id))

    invite = await cursor.fetchone()

    if not invite:
        raise HTTPException(status_code=404, detail="Invitation not found")

    if invite[1] != user_id:
        raise HTTPException(status_code=403, detail="This invitation is for someone else")

    if invite[2] != 'pending':
        raise HTTPException(status_code=400, detail="Invitation already processed")

    if datetime.fromisoformat(invite[3]) < datetime.now():
        raise HTTPException(status_code=400, detail="Invitation expired")

    # Add user to cell
    membership_id = str(uuid.uuid4())
    joined_at = datetime.now().isoformat()

    await db.execute("""
        INSERT INTO cell_memberships (
            id, cell_id, user_id, role, joined_at, vouched_by, is_active
        ) VALUES (?, ?, ?, 'member', ?, ?, 1)
    """, (membership_id, cell_id, user_id, joined_at, invite[0]))

    # Update invitation status
    await db.execute("""
        UPDATE cell_invitations
        SET status = 'accepted', responded_at = datetime('now')
        WHERE id = ?
    """, (invitation_id,))

    # Increment member count
    await db.execute("""
        UPDATE cells SET member_count = member_count + 1 WHERE id = ?
    """, (cell_id,))

    await db.commit()

    return {"status": "accepted"}


@router.get("/my/cells", response_model=List[Cell])
async def get_my_cells(user_id: str = Depends(get_current_user)):
    """Get all cells the current user is a member of"""
    db = await get_db()

    cursor = await db.execute("""
        SELECT c.* FROM cells c
        INNER JOIN cell_memberships cm ON c.id = cm.cell_id
        WHERE cm.user_id = ? AND cm.is_active = 1
        ORDER BY cm.joined_at DESC
    """, (user_id,))

    rows = await cursor.fetchall()

    cells = []
    for row in rows:
        cells.append(Cell(
            id=row[0],
            name=row[1],
            description=row[2],
            location_lat=row[3],
            location_lon=row[4],
            radius_km=row[5],
            created_at=row[6],
            member_count=row[7],
            max_members=row[8],
            is_accepting_members=bool(row[9]),
            settings=json.loads(row[10]) if row[10] else {}
        ))

    return cells
