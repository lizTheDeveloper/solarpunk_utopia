"""Repository for Sharing Preference data access"""
import sqlite3
from typing import Optional
from datetime import datetime, UTC
from valueflows_node.app.models.sharing_preference import (
    SharingPreference,
    SharingPreferenceCreate,
    VisibilityLevel,
    LocationPrecision,
)


class SharingPreferenceRepository:
    """Database access for sharing preferences."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def get_preference(self, user_id: str) -> Optional[SharingPreference]:
        """Get sharing preference for a user.

        Returns default preference if user hasn't set one.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT user_id, visibility, location_precision, local_radius_km, updated_at
            FROM sharing_preferences
            WHERE user_id = ?
        """, (user_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            # Return default preference
            return SharingPreference(
                user_id=user_id,
                visibility=VisibilityLevel.TRUSTED_NETWORK,
                location_precision=LocationPrecision.NEIGHBORHOOD,
                local_radius_km=25.0,
                updated_at=None,
            )

        return SharingPreference(
            user_id=row[0],
            visibility=row[1],
            location_precision=row[2],
            local_radius_km=row[3],
            updated_at=datetime.fromisoformat(row[4]) if row[4] else None,
        )

    def set_preference(self, user_id: str, preference: SharingPreferenceCreate) -> SharingPreference:
        """Create or update sharing preference."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        updated_at = datetime.now(UTC).isoformat()

        cursor.execute("""
            INSERT OR REPLACE INTO sharing_preferences
            (user_id, visibility, location_precision, local_radius_km, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            user_id,
            preference.visibility,
            preference.location_precision,
            preference.local_radius_km,
            updated_at,
        ))

        conn.commit()
        conn.close()

        return SharingPreference(
            user_id=user_id,
            visibility=preference.visibility,
            location_precision=preference.location_precision,
            local_radius_km=preference.local_radius_km,
            updated_at=datetime.fromisoformat(updated_at)
        )

    def delete_preference(self, user_id: str) -> bool:
        """Delete sharing preference (revert to default)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM sharing_preferences WHERE user_id = ?", (user_id,))
        deleted = cursor.rowcount > 0

        conn.commit()
        conn.close()

        return deleted
