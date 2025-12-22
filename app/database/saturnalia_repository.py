"""Repository for Saturnalia Protocol data access

'All authority is a mask, not a face.' - Paulo Freire

The Saturnalia Protocol creates temporary inversions to prevent roles from
hardening into identities. Named after the Roman festival where masters
served slaves.
"""
import sqlite3
import json
from typing import List, Optional
from datetime import datetime, UTC
import uuid

from app.models.saturnalia import (
    SaturnaliaConfig,
    SaturnaliaEvent,
    SaturnaliaRoleSwap,
    SaturnaliaOptOut,
    SaturnaliaAnonymousPost,
    SaturnaliaReflection,
    SaturnaliaMode,
    EventStatus,
    TriggerType,
    SwapStatus,
)


class SaturnaliaRepository:
    """Database access for Saturnalia Protocol."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ===== Config =====

    def create_config(self, config: SaturnaliaConfig) -> SaturnaliaConfig:
        """Create a new Saturnalia configuration."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO saturnalia_config (
                id, cell_id, community_id,
                enabled, enabled_modes,
                frequency, duration_hours,
                exclude_safety_critical, allow_individual_opt_out,
                next_scheduled_start,
                created_at, updated_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            config.id,
            config.cell_id,
            config.community_id,
            1 if config.enabled else 0,
            json.dumps([mode.value for mode in config.enabled_modes]),
            config.frequency,
            config.duration_hours,
            1 if config.exclude_safety_critical else 0,
            1 if config.allow_individual_opt_out else 0,
            config.next_scheduled_start.isoformat() if config.next_scheduled_start else None,
            config.created_at.isoformat(),
            config.updated_at.isoformat(),
            config.created_by,
        ))

        conn.commit()
        conn.close()
        return config

    def get_config(self, config_id: str) -> Optional[SaturnaliaConfig]:
        """Get a configuration by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM saturnalia_config WHERE id = ?", (config_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_config(row)

    def get_config_for_cell(self, cell_id: str) -> Optional[SaturnaliaConfig]:
        """Get configuration for a specific cell."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM saturnalia_config WHERE cell_id = ? AND enabled = 1",
            (cell_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_config(row)

    def get_network_wide_config(self) -> Optional[SaturnaliaConfig]:
        """Get network-wide configuration."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM saturnalia_config WHERE cell_id IS NULL AND community_id IS NULL AND enabled = 1"
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_config(row)

    def update_config(self, config: SaturnaliaConfig) -> SaturnaliaConfig:
        """Update a configuration."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE saturnalia_config SET
                enabled = ?,
                enabled_modes = ?,
                frequency = ?,
                duration_hours = ?,
                exclude_safety_critical = ?,
                allow_individual_opt_out = ?,
                next_scheduled_start = ?,
                updated_at = ?
            WHERE id = ?
        """, (
            1 if config.enabled else 0,
            json.dumps([mode.value for mode in config.enabled_modes]),
            config.frequency,
            config.duration_hours,
            1 if config.exclude_safety_critical else 0,
            1 if config.allow_individual_opt_out else 0,
            config.next_scheduled_start.isoformat() if config.next_scheduled_start else None,
            datetime.now(UTC).isoformat(),
            config.id,
        ))

        conn.commit()
        conn.close()
        return config

    # ===== Events =====

    def create_event(self, event: SaturnaliaEvent) -> SaturnaliaEvent:
        """Create a new Saturnalia event."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO saturnalia_events (
                id, config_id,
                start_time, end_time,
                active_modes, status,
                trigger_type, triggered_by,
                created_at, activated_at, completed_at, cancelled_at, cancellation_reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event.id,
            event.config_id,
            event.start_time.isoformat(),
            event.end_time.isoformat(),
            json.dumps([mode.value for mode in event.active_modes]),
            event.status.value,
            event.trigger_type.value,
            event.triggered_by,
            event.created_at.isoformat(),
            event.activated_at.isoformat() if event.activated_at else None,
            event.completed_at.isoformat() if event.completed_at else None,
            event.cancelled_at.isoformat() if event.cancelled_at else None,
            event.cancellation_reason,
        ))

        conn.commit()
        conn.close()
        return event

    def get_event(self, event_id: str) -> Optional[SaturnaliaEvent]:
        """Get an event by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM saturnalia_events WHERE id = ?", (event_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_event(row)

    def get_active_events(self) -> List[SaturnaliaEvent]:
        """Get all currently active events."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM saturnalia_events WHERE status = ? ORDER BY start_time DESC",
            (EventStatus.ACTIVE.value,)
        )
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_event(row) for row in rows]

    def get_active_event_for_cell(self, cell_id: str) -> Optional[SaturnaliaEvent]:
        """Get active event for a specific cell."""
        # First get the config for this cell
        config = self.get_config_for_cell(cell_id)
        if not config:
            return None

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM saturnalia_events
            WHERE config_id = ? AND status = ?
            ORDER BY start_time DESC
            LIMIT 1
        """, (config.id, EventStatus.ACTIVE.value))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_event(row)

    def update_event(self, event: SaturnaliaEvent) -> SaturnaliaEvent:
        """Update an event."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE saturnalia_events SET
                status = ?,
                activated_at = ?,
                completed_at = ?,
                cancelled_at = ?,
                cancellation_reason = ?
            WHERE id = ?
        """, (
            event.status.value,
            event.activated_at.isoformat() if event.activated_at else None,
            event.completed_at.isoformat() if event.completed_at else None,
            event.cancelled_at.isoformat() if event.cancelled_at else None,
            event.cancellation_reason,
            event.id,
        ))

        conn.commit()
        conn.close()
        return event

    # ===== Role Swaps =====

    def create_role_swap(self, swap: SaturnaliaRoleSwap) -> SaturnaliaRoleSwap:
        """Create a new role swap."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO saturnalia_role_swaps (
                id, event_id,
                original_user_id, original_role,
                temporary_user_id,
                scope_type, scope_id,
                status, swapped_at, restored_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            swap.id,
            swap.event_id,
            swap.original_user_id,
            swap.original_role,
            swap.temporary_user_id,
            swap.scope_type,
            swap.scope_id,
            swap.status.value,
            swap.swapped_at.isoformat(),
            swap.restored_at.isoformat() if swap.restored_at else None,
        ))

        conn.commit()
        conn.close()
        return swap

    def get_active_swaps_for_event(self, event_id: str) -> List[SaturnaliaRoleSwap]:
        """Get all active role swaps for an event."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM saturnalia_role_swaps WHERE event_id = ? AND status = ?",
            (event_id, SwapStatus.ACTIVE.value)
        )
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_role_swap(row) for row in rows]

    def restore_role_swap(self, swap_id: str) -> None:
        """Restore a role swap (mark as restored)."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE saturnalia_role_swaps SET
                status = ?,
                restored_at = ?
            WHERE id = ?
        """, (SwapStatus.RESTORED.value, datetime.now(UTC).isoformat(), swap_id))

        conn.commit()
        conn.close()

    # ===== Opt-Outs =====

    def create_opt_out(self, opt_out: SaturnaliaOptOut) -> SaturnaliaOptOut:
        """Create a new opt-out."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO saturnalia_opt_outs (
                id, user_id,
                mode, scope_type, scope_id,
                reason, is_permanent, expires_at,
                opted_out_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            opt_out.id,
            opt_out.user_id,
            opt_out.mode.value,
            opt_out.scope_type,
            opt_out.scope_id,
            opt_out.reason,
            1 if opt_out.is_permanent else 0,
            opt_out.expires_at.isoformat() if opt_out.expires_at else None,
            opt_out.opted_out_at.isoformat(),
        ))

        conn.commit()
        conn.close()
        return opt_out

    def get_user_opt_outs(self, user_id: str, mode: SaturnaliaMode) -> List[SaturnaliaOptOut]:
        """Get all active opt-outs for a user and mode."""
        conn = self._get_connection()
        cursor = conn.cursor()

        now = datetime.now(UTC).isoformat()
        cursor.execute("""
            SELECT * FROM saturnalia_opt_outs
            WHERE user_id = ? AND mode = ?
            AND (is_permanent = 1 OR expires_at > ?)
        """, (user_id, mode.value, now))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_opt_out(row) for row in rows]

    def is_user_opted_out(self, user_id: str, mode: SaturnaliaMode, scope_id: Optional[str] = None) -> bool:
        """Check if user has opted out of a mode."""
        opt_outs = self.get_user_opt_outs(user_id, mode)

        for opt_out in opt_outs:
            # Check if opt-out applies to this scope
            if opt_out.scope_type == 'all':
                return True
            if scope_id and opt_out.scope_id == scope_id:
                return True

        return False

    # ===== Anonymous Posts =====

    def create_anonymous_post(self, post: SaturnaliaAnonymousPost) -> SaturnaliaAnonymousPost:
        """Create a new anonymous post record."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO saturnalia_anonymous_posts (
                id, event_id,
                post_type, post_id, actual_author_id,
                created_at, revealed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            post.id,
            post.event_id,
            post.post_type,
            post.post_id,
            post.actual_author_id,
            post.created_at.isoformat(),
            post.revealed_at.isoformat() if post.revealed_at else None,
        ))

        conn.commit()
        conn.close()
        return post

    def reveal_anonymous_posts_for_event(self, event_id: str) -> None:
        """Reveal all anonymous posts for an event."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE saturnalia_anonymous_posts SET
                revealed_at = ?
            WHERE event_id = ? AND revealed_at IS NULL
        """, (datetime.now(UTC).isoformat(), event_id))

        conn.commit()
        conn.close()

    def get_actual_author(self, post_id: str) -> Optional[str]:
        """Get the actual author of an anonymous post."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT actual_author_id FROM saturnalia_anonymous_posts WHERE post_id = ?",
            (post_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return row['actual_author_id']

    # ===== Reflections =====

    def create_reflection(self, reflection: SaturnaliaReflection) -> SaturnaliaReflection:
        """Create a new reflection."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO saturnalia_reflections (
                id, event_id, user_id,
                what_learned, what_surprised, what_changed,
                suggestions, overall_rating, would_do_again,
                submitted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            reflection.id,
            reflection.event_id,
            reflection.user_id,
            reflection.what_learned,
            reflection.what_surprised,
            reflection.what_changed,
            reflection.suggestions,
            reflection.overall_rating,
            1 if reflection.would_do_again else 0,
            reflection.submitted_at.isoformat(),
        ))

        conn.commit()
        conn.close()
        return reflection

    def get_reflections_for_event(self, event_id: str) -> List[SaturnaliaReflection]:
        """Get all reflections for an event."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM saturnalia_reflections WHERE event_id = ? ORDER BY submitted_at DESC",
            (event_id,)
        )
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_reflection(row) for row in rows]

    # ===== Helper Methods =====

    def _row_to_config(self, row: sqlite3.Row) -> SaturnaliaConfig:
        """Convert database row to SaturnaliaConfig."""
        return SaturnaliaConfig(
            id=row['id'],
            cell_id=row['cell_id'],
            community_id=row['community_id'],
            enabled=bool(row['enabled']),
            enabled_modes=[SaturnaliaMode(mode) for mode in json.loads(row['enabled_modes'])],
            frequency=row['frequency'],
            duration_hours=row['duration_hours'],
            exclude_safety_critical=bool(row['exclude_safety_critical']),
            allow_individual_opt_out=bool(row['allow_individual_opt_out']),
            next_scheduled_start=datetime.fromisoformat(row['next_scheduled_start']) if row['next_scheduled_start'] else None,
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at']),
            created_by=row['created_by'],
        )

    def _row_to_event(self, row: sqlite3.Row) -> SaturnaliaEvent:
        """Convert database row to SaturnaliaEvent."""
        return SaturnaliaEvent(
            id=row['id'],
            config_id=row['config_id'],
            start_time=datetime.fromisoformat(row['start_time']),
            end_time=datetime.fromisoformat(row['end_time']),
            active_modes=[SaturnaliaMode(mode) for mode in json.loads(row['active_modes'])],
            status=EventStatus(row['status']),
            trigger_type=TriggerType(row['trigger_type']),
            triggered_by=row['triggered_by'],
            created_at=datetime.fromisoformat(row['created_at']),
            activated_at=datetime.fromisoformat(row['activated_at']) if row['activated_at'] else None,
            completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None,
            cancelled_at=datetime.fromisoformat(row['cancelled_at']) if row['cancelled_at'] else None,
            cancellation_reason=row['cancellation_reason'],
        )

    def _row_to_role_swap(self, row: sqlite3.Row) -> SaturnaliaRoleSwap:
        """Convert database row to SaturnaliaRoleSwap."""
        return SaturnaliaRoleSwap(
            id=row['id'],
            event_id=row['event_id'],
            original_user_id=row['original_user_id'],
            original_role=row['original_role'],
            temporary_user_id=row['temporary_user_id'],
            scope_type=row['scope_type'],
            scope_id=row['scope_id'],
            status=SwapStatus(row['status']),
            swapped_at=datetime.fromisoformat(row['swapped_at']),
            restored_at=datetime.fromisoformat(row['restored_at']) if row['restored_at'] else None,
        )

    def _row_to_opt_out(self, row: sqlite3.Row) -> SaturnaliaOptOut:
        """Convert database row to SaturnaliaOptOut."""
        return SaturnaliaOptOut(
            id=row['id'],
            user_id=row['user_id'],
            mode=SaturnaliaMode(row['mode']),
            scope_type=row['scope_type'],
            scope_id=row['scope_id'],
            reason=row['reason'],
            is_permanent=bool(row['is_permanent']),
            expires_at=datetime.fromisoformat(row['expires_at']) if row['expires_at'] else None,
            opted_out_at=datetime.fromisoformat(row['opted_out_at']),
        )

    def _row_to_reflection(self, row: sqlite3.Row) -> SaturnaliaReflection:
        """Convert database row to SaturnaliaReflection."""
        return SaturnaliaReflection(
            id=row['id'],
            event_id=row['event_id'],
            user_id=row['user_id'],
            what_learned=row['what_learned'],
            what_surprised=row['what_surprised'],
            what_changed=row['what_changed'],
            suggestions=row['suggestions'],
            overall_rating=row['overall_rating'],
            would_do_again=bool(row['would_do_again']),
            submitted_at=datetime.fromisoformat(row['submitted_at']),
        )
