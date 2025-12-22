"""Repository for Panic Features data access"""
import sqlite3
import json
from typing import List, Optional
from datetime import datetime, UTC
import uuid

from app.models.panic import (
    DuressPIN,
    QuickWipeConfig,
    DeadMansSwitchConfig,
    DecoyModeConfig,
    BurnNotice,
    BurnNoticeStatus,
    SeedPhraseRecovery,
    WipeLog,
)


class PanicRepository:
    """Database access for panic features."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_tables()

    def _init_tables(self):
        """Create panic feature tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Duress PIN table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS duress_pins (
                user_id TEXT PRIMARY KEY,
                duress_pin_hash TEXT NOT NULL,
                enabled INTEGER DEFAULT 1,
                last_used TEXT,
                burn_notice_sent INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)

        # Quick wipe config table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quick_wipe_configs (
                user_id TEXT PRIMARY KEY,
                enabled INTEGER DEFAULT 0,
                gesture_type TEXT DEFAULT 'five_tap_logo',
                confirmation_required INTEGER DEFAULT 1,
                last_triggered TEXT,
                created_at TEXT NOT NULL
            )
        """)

        # Dead man's switch table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dead_mans_switch_configs (
                user_id TEXT PRIMARY KEY,
                enabled INTEGER DEFAULT 0,
                timeout_hours INTEGER DEFAULT 72,
                last_checkin TEXT NOT NULL,
                trigger_time TEXT,
                triggered INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)

        # Decoy mode table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decoy_mode_configs (
                user_id TEXT PRIMARY KEY,
                enabled INTEGER DEFAULT 0,
                decoy_type TEXT DEFAULT 'calculator',
                secret_gesture TEXT DEFAULT '31337=',
                currently_in_decoy INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)

        # Burn notices table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS burn_notices (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                reason TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                propagated_at TEXT,
                resolved_at TEXT,
                vouch_chain_notified INTEGER DEFAULT 0
            )
        """)

        # Seed phrase recovery table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS seed_phrase_recoveries (
                user_id TEXT PRIMARY KEY,
                seed_phrase_encrypted TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_used TEXT
            )
        """)

        # Wipe log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wipe_logs (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                trigger TEXT NOT NULL,
                wiped_at TEXT NOT NULL,
                data_types_wiped_json TEXT NOT NULL,
                recovery_possible INTEGER DEFAULT 1
            )
        """)

        # Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_burn_notices_user ON burn_notices(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_burn_notices_status ON burn_notices(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_wipe_logs_user ON wipe_logs(user_id)")

        conn.commit()
        conn.close()

    # ===== Duress PIN Methods =====

    def set_duress_pin(self, user_id: str, pin_hash: str) -> DuressPIN:
        """Set or update duress PIN for a user."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        created_at = datetime.now(UTC).isoformat()

        cursor.execute("""
            INSERT OR REPLACE INTO duress_pins
            (user_id, duress_pin_hash, enabled, created_at)
            VALUES (?, ?, 1, ?)
        """, (user_id, pin_hash, created_at))

        conn.commit()
        conn.close()

        return DuressPIN(
            user_id=user_id,
            duress_pin_hash=pin_hash,
            enabled=True,
            created_at=datetime.fromisoformat(created_at),
        )

    def get_duress_pin(self, user_id: str) -> Optional[DuressPIN]:
        """Get duress PIN config for a user."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT user_id, duress_pin_hash, enabled, last_used, burn_notice_sent, created_at
            FROM duress_pins WHERE user_id = ?
        """, (user_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return DuressPIN(
            user_id=row[0],
            duress_pin_hash=row[1],
            enabled=bool(row[2]),
            last_used=datetime.fromisoformat(row[3]) if row[3] else None,
            burn_notice_sent=bool(row[4]),
            created_at=datetime.fromisoformat(row[5]),
        )

    def mark_duress_pin_used(self, user_id: str):
        """Mark that duress PIN was used (indicates compromise)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        last_used = datetime.now(UTC).isoformat()
        cursor.execute("""
            UPDATE duress_pins SET last_used = ? WHERE user_id = ?
        """, (last_used, user_id))

        conn.commit()
        conn.close()

    # ===== Quick Wipe Methods =====

    def set_quick_wipe_config(
        self,
        user_id: str,
        enabled: bool = True,
        gesture_type: str = "five_tap_logo",
        confirmation_required: bool = True
    ) -> QuickWipeConfig:
        """Set quick wipe configuration."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        created_at = datetime.now(UTC).isoformat()

        cursor.execute("""
            INSERT OR REPLACE INTO quick_wipe_configs
            (user_id, enabled, gesture_type, confirmation_required, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, int(enabled), gesture_type, int(confirmation_required), created_at))

        conn.commit()
        conn.close()

        return QuickWipeConfig(
            user_id=user_id,
            enabled=enabled,
            gesture_type=gesture_type,
            confirmation_required=confirmation_required,
            created_at=datetime.fromisoformat(created_at),
        )

    def get_quick_wipe_config(self, user_id: str) -> Optional[QuickWipeConfig]:
        """Get quick wipe configuration."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT user_id, enabled, gesture_type, confirmation_required, last_triggered, created_at
            FROM quick_wipe_configs WHERE user_id = ?
        """, (user_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return QuickWipeConfig(
            user_id=row[0],
            enabled=bool(row[1]),
            gesture_type=row[2],
            confirmation_required=bool(row[3]),
            last_triggered=datetime.fromisoformat(row[4]) if row[4] else None,
            created_at=datetime.fromisoformat(row[5]),
        )

    def mark_quick_wipe_triggered(self, user_id: str):
        """Mark that quick wipe was triggered."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        last_triggered = datetime.now(UTC).isoformat()
        cursor.execute("""
            UPDATE quick_wipe_configs SET last_triggered = ? WHERE user_id = ?
        """, (last_triggered, user_id))

        conn.commit()
        conn.close()

    # ===== Dead Man's Switch Methods =====

    def set_dead_mans_switch(
        self,
        user_id: str,
        enabled: bool = True,
        timeout_hours: int = 72
    ) -> DeadMansSwitchConfig:
        """Set dead man's switch configuration."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now(UTC)
        created_at = now.isoformat()
        last_checkin = now.isoformat()

        cursor.execute("""
            INSERT OR REPLACE INTO dead_mans_switch_configs
            (user_id, enabled, timeout_hours, last_checkin, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, int(enabled), timeout_hours, last_checkin, created_at))

        conn.commit()
        conn.close()

        config = DeadMansSwitchConfig(
            user_id=user_id,
            enabled=enabled,
            timeout_hours=timeout_hours,
            last_checkin=now,
            created_at=now,
        )
        config.trigger_time = config.calculate_trigger_time()
        return config

    def get_dead_mans_switch(self, user_id: str) -> Optional[DeadMansSwitchConfig]:
        """Get dead man's switch configuration."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT user_id, enabled, timeout_hours, last_checkin, trigger_time, triggered, created_at
            FROM dead_mans_switch_configs WHERE user_id = ?
        """, (user_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return DeadMansSwitchConfig(
            user_id=row[0],
            enabled=bool(row[1]),
            timeout_hours=row[2],
            last_checkin=datetime.fromisoformat(row[3]),
            trigger_time=datetime.fromisoformat(row[4]) if row[4] else None,
            triggered=bool(row[5]),
            created_at=datetime.fromisoformat(row[6]),
        )

    def checkin_dead_mans_switch(self, user_id: str):
        """User checks in, resets dead man's switch timer."""
        config = self.get_dead_mans_switch(user_id)
        if not config:
            return

        config.checkin()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE dead_mans_switch_configs
            SET last_checkin = ?, trigger_time = ?, triggered = 0
            WHERE user_id = ?
        """, (
            config.last_checkin.isoformat(),
            config.trigger_time.isoformat(),
            user_id
        ))

        conn.commit()
        conn.close()

    def get_overdue_dead_mans_switches(self) -> List[DeadMansSwitchConfig]:
        """Get all dead man's switches that are overdue to trigger."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now(UTC).isoformat()

        cursor.execute("""
            SELECT user_id, enabled, timeout_hours, last_checkin, trigger_time, triggered, created_at
            FROM dead_mans_switch_configs
            WHERE enabled = 1 AND triggered = 0 AND trigger_time <= ?
        """, (now,))

        rows = cursor.fetchall()
        conn.close()

        return [DeadMansSwitchConfig(
            user_id=row[0],
            enabled=bool(row[1]),
            timeout_hours=row[2],
            last_checkin=datetime.fromisoformat(row[3]),
            trigger_time=datetime.fromisoformat(row[4]) if row[4] else None,
            triggered=bool(row[5]),
            created_at=datetime.fromisoformat(row[6]),
        ) for row in rows]

    # ===== Decoy Mode Methods =====

    def set_decoy_mode(
        self,
        user_id: str,
        enabled: bool = True,
        decoy_type: str = "calculator",
        secret_gesture: str = "31337="
    ) -> DecoyModeConfig:
        """Set decoy mode configuration."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        created_at = datetime.now(UTC).isoformat()

        cursor.execute("""
            INSERT OR REPLACE INTO decoy_mode_configs
            (user_id, enabled, decoy_type, secret_gesture, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, int(enabled), decoy_type, secret_gesture, created_at))

        conn.commit()
        conn.close()

        return DecoyModeConfig(
            user_id=user_id,
            enabled=enabled,
            decoy_type=decoy_type,
            secret_gesture=secret_gesture,
            created_at=datetime.fromisoformat(created_at),
        )

    def get_decoy_mode(self, user_id: str) -> Optional[DecoyModeConfig]:
        """Get decoy mode configuration."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT user_id, enabled, decoy_type, secret_gesture, currently_in_decoy, created_at
            FROM decoy_mode_configs WHERE user_id = ?
        """, (user_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return DecoyModeConfig(
            user_id=row[0],
            enabled=bool(row[1]),
            decoy_type=row[2],
            secret_gesture=row[3],
            currently_in_decoy=bool(row[4]),
            created_at=datetime.fromisoformat(row[5]),
        )

    # ===== Burn Notice Methods =====

    def create_burn_notice(self, user_id: str, reason: str) -> BurnNotice:
        """Create a burn notice for a compromised user."""
        notice_id = f"burn-notice-{uuid.uuid4()}"
        created_at = datetime.now(UTC)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO burn_notices
            (id, user_id, reason, status, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (notice_id, user_id, reason, BurnNoticeStatus.PENDING.value, created_at.isoformat()))

        conn.commit()
        conn.close()

        return BurnNotice(
            id=notice_id,
            user_id=user_id,
            reason=reason,
            status=BurnNoticeStatus.PENDING,
            created_at=created_at,
        )

    def get_burn_notice(self, notice_id: str) -> Optional[BurnNotice]:
        """Get a burn notice by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, user_id, reason, status, created_at, propagated_at, resolved_at, vouch_chain_notified
            FROM burn_notices WHERE id = ?
        """, (notice_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return BurnNotice(
            id=row[0],
            user_id=row[1],
            reason=row[2],
            status=BurnNoticeStatus(row[3]),
            created_at=datetime.fromisoformat(row[4]),
            propagated_at=datetime.fromisoformat(row[5]) if row[5] else None,
            resolved_at=datetime.fromisoformat(row[6]) if row[6] else None,
            vouch_chain_notified=bool(row[7]),
        )

    def get_burn_notices_for_user(self, user_id: str) -> List[BurnNotice]:
        """Get all burn notices for a user."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, user_id, reason, status, created_at, propagated_at, resolved_at, vouch_chain_notified
            FROM burn_notices WHERE user_id = ? ORDER BY created_at DESC
        """, (user_id,))

        rows = cursor.fetchall()
        conn.close()

        return [BurnNotice(
            id=row[0],
            user_id=row[1],
            reason=row[2],
            status=BurnNoticeStatus(row[3]),
            created_at=datetime.fromisoformat(row[4]),
            propagated_at=datetime.fromisoformat(row[5]) if row[5] else None,
            resolved_at=datetime.fromisoformat(row[6]) if row[6] else None,
            vouch_chain_notified=bool(row[7]),
        ) for row in rows]

    def update_burn_notice_status(self, notice_id: str, status: BurnNoticeStatus):
        """Update burn notice status."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now(UTC).isoformat()
        if status == BurnNoticeStatus.SENT or status == BurnNoticeStatus.PROPAGATED:
            cursor.execute("""
                UPDATE burn_notices SET status = ?, propagated_at = ? WHERE id = ?
            """, (status.value, now, notice_id))
        elif status == BurnNoticeStatus.RESOLVED:
            cursor.execute("""
                UPDATE burn_notices SET status = ?, resolved_at = ? WHERE id = ?
            """, (status.value, now, notice_id))
        else:
            cursor.execute("""
                UPDATE burn_notices SET status = ? WHERE id = ?
            """, (status.value, notice_id))

        conn.commit()
        conn.close()

    # ===== Wipe Log Methods =====

    def log_wipe(
        self,
        user_id: str,
        trigger: str,
        data_types_wiped: List[str],
        recovery_possible: bool = True
    ) -> WipeLog:
        """Log a data wipe event."""
        log_id = f"wipe-log-{uuid.uuid4()}"
        wiped_at = datetime.now(UTC)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO wipe_logs
            (id, user_id, trigger, wiped_at, data_types_wiped_json, recovery_possible)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            log_id,
            user_id,
            trigger,
            wiped_at.isoformat(),
            json.dumps(data_types_wiped),
            int(recovery_possible)
        ))

        conn.commit()
        conn.close()

        return WipeLog(
            id=log_id,
            user_id=user_id,
            trigger=trigger,
            wiped_at=wiped_at,
            data_types_wiped=data_types_wiped,
            recovery_possible=recovery_possible,
        )

    def get_wipe_logs_for_user(self, user_id: str) -> List[WipeLog]:
        """Get all wipe logs for a user."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, user_id, trigger, wiped_at, data_types_wiped_json, recovery_possible
            FROM wipe_logs WHERE user_id = ? ORDER BY wiped_at DESC
        """, (user_id,))

        rows = cursor.fetchall()
        conn.close()

        return [WipeLog(
            id=row[0],
            user_id=row[1],
            trigger=row[2],
            wiped_at=datetime.fromisoformat(row[3]),
            data_types_wiped=json.loads(row[4]),
            recovery_possible=bool(row[5]),
        ) for row in rows]
