"""Community service for managing communities and memberships"""

import uuid
import json
from datetime import datetime, timezone
from typing import List, Optional

from ..models.community import (
    Community,
    CommunityCreate,
    CommunityUpdate,
    CommunityMembership,
    CommunityMembershipCreate,
    CommunityStats,
)
from app.database.db import get_db


class CommunityService:
    """Service for community operations"""

    async def create_community(
        self, community_data: CommunityCreate, creator_user_id: str
    ) -> Community:
        """Create a new community and add creator as first member"""
        db = await get_db()

        # Check if community with this name exists
        cursor = await db.execute(
            "SELECT id FROM communities WHERE name = ?", (community_data.name,)
        )
        existing = await cursor.fetchone()
        if existing:
            raise ValueError(f"Community with name '{community_data.name}' already exists")

        # Create community
        community_id = f"community:{uuid.uuid4()}"
        now = datetime.now(timezone.utc).isoformat()

        await db.execute(
            """
            INSERT INTO communities (id, name, description, created_at, settings, is_public)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                community_id,
                community_data.name,
                community_data.description,
                now,
                "{}",
                community_data.is_public,
            ),
        )

        # Add creator as first member with creator role
        membership_id = f"membership:{uuid.uuid4()}"
        await db.execute(
            """
            INSERT INTO community_memberships (id, user_id, community_id, role, joined_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (membership_id, creator_user_id, community_id, "creator", now),
        )

        await db.commit()

        return Community(
            id=community_id,
            name=community_data.name,
            description=community_data.description,
            created_at=datetime.fromisoformat(now),
            settings={},
            is_public=community_data.is_public,
        )

    async def get_community(self, community_id: str) -> Optional[Community]:
        """Get community by ID"""
        db = await get_db()

        cursor = await db.execute(
            "SELECT * FROM communities WHERE id = ?", (community_id,)
        )
        row = await cursor.fetchone()

        if not row:
            return None

        return Community(
            id=row[0],
            name=row[1],
            description=row[2],
            created_at=datetime.fromisoformat(row[3]),
            settings=json.loads(row[4]) if row[4] else {},
            is_public=bool(row[5]),
        )

    async def get_user_communities(self, user_id: str) -> List[Community]:
        """Get all communities a user is a member of"""
        db = await get_db()

        cursor = await db.execute(
            """
            SELECT c.*
            FROM communities c
            JOIN community_memberships m ON c.id = m.community_id
            WHERE m.user_id = ?
            ORDER BY m.joined_at DESC
            """,
            (user_id,),
        )
        rows = await cursor.fetchall()

        communities = []
        for row in rows:
            communities.append(
                Community(
                    id=row[0],
                    name=row[1],
                    description=row[2],
                    created_at=datetime.fromisoformat(row[3]),
                    settings=json.loads(row[4]) if row[4] else {},
                    is_public=bool(row[5]),
                )
            )

        return communities

    async def update_community(
        self, community_id: str, updates: CommunityUpdate
    ) -> Optional[Community]:
        """Update community settings"""
        db = await get_db()

        # Build update query dynamically
        update_fields = []
        params = []

        if updates.name is not None:
            update_fields.append("name = ?")
            params.append(updates.name)
        if updates.description is not None:
            update_fields.append("description = ?")
            params.append(updates.description)
        if updates.settings is not None:
            update_fields.append("settings = ?")
            params.append(json.dumps(updates.settings))
        if updates.is_public is not None:
            update_fields.append("is_public = ?")
            params.append(updates.is_public)

        if not update_fields:
            return await self.get_community(community_id)

        params.append(community_id)

        await db.execute(
            f"UPDATE communities SET {', '.join(update_fields)} WHERE id = ?",
            tuple(params),
        )
        await db.commit()

        return await self.get_community(community_id)

    async def delete_community(self, community_id: str) -> bool:
        """Delete a community (and all memberships via CASCADE)"""
        db = await get_db()

        await db.execute("DELETE FROM communities WHERE id = ?", (community_id,))
        await db.commit()

        return True

    async def add_member(
        self, community_id: str, membership_data: CommunityMembershipCreate
    ) -> CommunityMembership:
        """Add a member to a community"""
        db = await get_db()

        # Check if already a member
        cursor = await db.execute(
            """
            SELECT id FROM community_memberships
            WHERE user_id = ? AND community_id = ?
            """,
            (membership_data.user_id, community_id),
        )
        existing = await cursor.fetchone()
        if existing:
            raise ValueError("User is already a member of this community")

        # Add membership
        membership_id = f"membership:{uuid.uuid4()}"
        now = datetime.now(timezone.utc).isoformat()

        await db.execute(
            """
            INSERT INTO community_memberships (id, user_id, community_id, role, joined_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                membership_id,
                membership_data.user_id,
                community_id,
                membership_data.role,
                now,
            ),
        )
        await db.commit()

        return CommunityMembership(
            id=membership_id,
            user_id=membership_data.user_id,
            community_id=community_id,
            role=membership_data.role,
            joined_at=datetime.fromisoformat(now),
        )

    async def get_members(self, community_id: str) -> List[CommunityMembership]:
        """Get all members of a community"""
        db = await get_db()

        cursor = await db.execute(
            """
            SELECT * FROM community_memberships
            WHERE community_id = ?
            ORDER BY joined_at ASC
            """,
            (community_id,),
        )
        rows = await cursor.fetchall()

        memberships = []
        for row in rows:
            memberships.append(
                CommunityMembership(
                    id=row[0],
                    user_id=row[1],
                    community_id=row[2],
                    role=row[3],
                    joined_at=datetime.fromisoformat(row[4]),
                )
            )

        return memberships

    async def remove_member(self, community_id: str, user_id: str) -> bool:
        """Remove a member from a community"""
        db = await get_db()

        await db.execute(
            """
            DELETE FROM community_memberships
            WHERE community_id = ? AND user_id = ?
            """,
            (community_id, user_id),
        )
        await db.commit()

        return True

    async def is_member(self, community_id: str, user_id: str) -> bool:
        """Check if user is a member of a community"""
        db = await get_db()

        cursor = await db.execute(
            """
            SELECT id FROM community_memberships
            WHERE community_id = ? AND user_id = ?
            """,
            (community_id, user_id),
        )
        row = await cursor.fetchone()

        return row is not None

    async def get_member_role(self, community_id: str, user_id: str) -> Optional[str]:
        """Get user's role in a community"""
        db = await get_db()

        cursor = await db.execute(
            """
            SELECT role FROM community_memberships
            WHERE community_id = ? AND user_id = ?
            """,
            (community_id, user_id),
        )
        row = await cursor.fetchone()

        return row[0] if row else None

    async def get_stats(self, community_id: str) -> CommunityStats:
        """Get statistics for a community"""
        db = await get_db()

        # Count members
        cursor = await db.execute(
            "SELECT COUNT(*) FROM community_memberships WHERE community_id = ?",
            (community_id,),
        )
        member_count = (await cursor.fetchone())[0]

        # Count listings
        cursor = await db.execute(
            "SELECT COUNT(*) FROM listings WHERE community_id = ?", (community_id,)
        )
        listing_count = (await cursor.fetchone())[0]

        # Count exchanges
        cursor = await db.execute(
            "SELECT COUNT(*) FROM vf_exchanges WHERE community_id = ?", (community_id,)
        )
        exchange_count = (await cursor.fetchone())[0]

        # Count proposals
        cursor = await db.execute(
            "SELECT COUNT(*) FROM proposals WHERE community_id = ?", (community_id,)
        )
        proposal_count = (await cursor.fetchone())[0]

        return CommunityStats(
            member_count=member_count,
            listing_count=listing_count,
            exchange_count=exchange_count,
            proposal_count=proposal_count,
        )


# Global instance
_community_service: Optional[CommunityService] = None


def get_community_service() -> CommunityService:
    """Get global community service instance"""
    global _community_service
    if _community_service is None:
        _community_service = CommunityService()
    return _community_service
