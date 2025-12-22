"""Repository for Mycelial Strike data access

'Mutual Aid includes Mutual Defense.' - Peter Kropotkin

Automated solidarity defense against extractive behavior.
"""
import sqlite3
import json
from typing import List, Optional
from datetime import datetime, UTC
import uuid

from app.models.mycelial_strike import (
    WarlordAlert,
    LocalStrike,
    StrikeEvidence,
    StrikePropagation,
    BehaviorTracking,
    StrikeDeescalationLog,
    StrikeOverrideLog,
    UserStrikeWhitelist,
    StrikeNetworkStats,
    AbuseType,
    ThrottleLevel,
    StrikeStatus,
    ThrottleActions,
    EvidenceItem,
    OverrideAction,
    DeescalationReason,
)


class MycelialStrikeRepository:
    """Database access for Mycelial Strike system."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ===== Warlord Alerts =====

    def create_alert(self, alert: WarlordAlert) -> WarlordAlert:
        """Create a new warlord alert."""
        conn = self._get_connection()
        cursor = conn.cursor()

        evidence_json = json.dumps([
            {'type': e.type, 'details': e.details, 'reliability_score': e.reliability_score}
            for e in alert.evidence
        ])

        cursor.execute("""
            INSERT INTO warlord_alerts (
                id, target_user_id, severity, abuse_type,
                evidence, reporting_node_fingerprint, reporting_user_id,
                trusted_source, propagation_count,
                created_at, expires_at,
                cancelled, cancelled_by, cancellation_reason, cancelled_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alert.id, alert.target_user_id, alert.severity, alert.abuse_type.value,
            evidence_json, alert.reporting_node_fingerprint, alert.reporting_user_id,
            1 if alert.trusted_source else 0, alert.propagation_count,
            alert.created_at.isoformat(), alert.expires_at.isoformat(),
            1 if alert.cancelled else 0, alert.cancelled_by, alert.cancellation_reason,
            alert.cancelled_at.isoformat() if alert.cancelled_at else None
        ))

        conn.commit()
        conn.close()
        return alert

    def get_alert(self, alert_id: str) -> Optional[WarlordAlert]:
        """Get an alert by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM warlord_alerts WHERE id = ?", (alert_id,))
        row = cursor.fetchone()
        conn.close()

        return self._row_to_alert(row) if row else None

    def get_active_alerts_for_user(self, user_id: str) -> List[WarlordAlert]:
        """Get all active alerts for a user."""
        conn = self._get_connection()
        cursor = conn.cursor()

        now = datetime.now(UTC).isoformat()
        cursor.execute("""
            SELECT * FROM warlord_alerts
            WHERE target_user_id = ?
            AND cancelled = 0
            AND expires_at > ?
            ORDER BY severity DESC, created_at DESC
        """, (user_id, now))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_alert(row) for row in rows]

    def cancel_alert(self, alert_id: str, cancelled_by: str, reason: str) -> None:
        """Cancel an alert and deactivate associated strikes."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Cancel the alert
        cursor.execute("""
            UPDATE warlord_alerts
            SET cancelled = 1, cancelled_by = ?, cancellation_reason = ?, cancelled_at = ?
            WHERE id = ?
        """, (cancelled_by, reason, datetime.now(UTC).isoformat(), alert_id))

        # Deactivate any strikes associated with this alert
        cursor.execute("""
            UPDATE local_strikes
            SET status = 'deactivated', deactivated_at = ?
            WHERE alert_id = ? AND status = 'active'
        """, (datetime.now(UTC).isoformat(), alert_id))

        conn.commit()
        conn.close()

    # ===== Local Strikes =====

    def create_strike(self, strike: LocalStrike) -> LocalStrike:
        """Create a new local strike."""
        conn = self._get_connection()
        cursor = conn.cursor()

        throttle_actions_json = json.dumps({
            'deprioritize_matching': strike.throttle_actions.deprioritize_matching,
            'add_message_latency': strike.throttle_actions.add_message_latency,
            'reduce_proposal_visibility': strike.throttle_actions.reduce_proposal_visibility,
            'show_warning_indicator': strike.throttle_actions.show_warning_indicator,
            'block_high_value_exchanges': strike.throttle_actions.block_high_value_exchanges,
        })

        cursor.execute("""
            INSERT INTO local_strikes (
                id, alert_id, target_user_id,
                throttle_level, throttle_actions,
                status, automatic,
                behavior_score_at_start, current_behavior_score,
                activated_at, deactivated_at,
                overridden_by, override_reason, overridden_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            strike.id, strike.alert_id, strike.target_user_id,
            strike.throttle_level.value, throttle_actions_json,
            strike.status.value, 1 if strike.automatic else 0,
            strike.behavior_score_at_start, strike.current_behavior_score,
            strike.activated_at.isoformat(),
            strike.deactivated_at.isoformat() if strike.deactivated_at else None,
            strike.overridden_by, strike.override_reason,
            strike.overridden_at.isoformat() if strike.overridden_at else None
        ))

        conn.commit()
        conn.close()
        return strike

    def get_strike(self, strike_id: str) -> Optional[LocalStrike]:
        """Get a strike by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM local_strikes WHERE id = ?", (strike_id,))
        row = cursor.fetchone()
        conn.close()

        return self._row_to_strike(row) if row else None

    def get_active_strikes_for_user(self, user_id: str) -> List[LocalStrike]:
        """Get all active strikes for a user."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM local_strikes
            WHERE target_user_id = ? AND status = 'active'
            ORDER BY activated_at DESC
        """, (user_id,))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_strike(row) for row in rows]

    def update_strike_behavior_score(self, strike_id: str, new_score: float) -> None:
        """Update behavior score for a strike."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE local_strikes
            SET current_behavior_score = ?
            WHERE id = ?
        """, (new_score, strike_id))

        conn.commit()
        conn.close()

    def update_strike_throttle_level(self, strike_id: str, new_level: ThrottleLevel, new_actions: ThrottleActions) -> None:
        """Update throttle level and actions for a strike."""
        conn = self._get_connection()
        cursor = conn.cursor()

        throttle_actions_json = json.dumps({
            'deprioritize_matching': new_actions.deprioritize_matching,
            'add_message_latency': new_actions.add_message_latency,
            'reduce_proposal_visibility': new_actions.reduce_proposal_visibility,
            'show_warning_indicator': new_actions.show_warning_indicator,
            'block_high_value_exchanges': new_actions.block_high_value_exchanges,
        })

        cursor.execute("""
            UPDATE local_strikes
            SET throttle_level = ?, throttle_actions = ?
            WHERE id = ?
        """, (new_level.value, throttle_actions_json, strike_id))

        conn.commit()
        conn.close()

    def deactivate_strike(self, strike_id: str) -> None:
        """Deactivate a strike."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE local_strikes
            SET status = 'deactivated', deactivated_at = ?
            WHERE id = ?
        """, (datetime.now(UTC).isoformat(), strike_id))

        conn.commit()
        conn.close()

    def override_strike(
        self,
        strike_id: str,
        overridden_by: str,
        reason: str
    ) -> None:
        """Override a strike (steward action)."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE local_strikes
            SET status = 'overridden', overridden_by = ?, override_reason = ?, overridden_at = ?
            WHERE id = ?
        """, (overridden_by, reason, datetime.now(UTC).isoformat(), strike_id))

        conn.commit()
        conn.close()

    # ===== Behavior Tracking =====

    def create_or_update_behavior_tracking(
        self,
        tracking: BehaviorTracking
    ) -> BehaviorTracking:
        """Create or update behavior tracking."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Try update first
        cursor.execute("""
            UPDATE behavior_tracking
            SET strike_id = ?,
                exchanges_given = ?, exchanges_received = ?,
                offers_posted = ?, needs_posted = ?,
                behavior_score = ?,
                period_start = ?, period_end = ?, last_updated = ?
            WHERE user_id = ?
        """, (
            tracking.strike_id,
            tracking.exchanges_given, tracking.exchanges_received,
            tracking.offers_posted, tracking.needs_posted,
            tracking.behavior_score,
            tracking.period_start.isoformat(), tracking.period_end.isoformat(),
            tracking.last_updated.isoformat(),
            tracking.user_id
        ))

        if cursor.rowcount == 0:
            cursor.execute("""
                INSERT INTO behavior_tracking (
                    id, user_id, strike_id,
                    exchanges_given, exchanges_received,
                    offers_posted, needs_posted,
                    behavior_score,
                    period_start, period_end, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tracking.id, tracking.user_id, tracking.strike_id,
                tracking.exchanges_given, tracking.exchanges_received,
                tracking.offers_posted, tracking.needs_posted,
                tracking.behavior_score,
                tracking.period_start.isoformat(), tracking.period_end.isoformat(),
                tracking.last_updated.isoformat()
            ))

        conn.commit()
        conn.close()
        return tracking

    def get_behavior_tracking(self, user_id: str) -> Optional[BehaviorTracking]:
        """Get behavior tracking for a user."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM behavior_tracking WHERE user_id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        conn.close()

        return self._row_to_behavior_tracking(row) if row else None

    # ===== De-escalation Logs =====

    def create_deescalation_log(
        self,
        log: StrikeDeescalationLog
    ) -> StrikeDeescalationLog:
        """Create a de-escalation log entry."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO strike_deescalation_log (
                id, strike_id,
                previous_level, new_level, trigger_reason,
                behavior_score, deescalated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            log.id, log.strike_id,
            log.previous_level.value, log.new_level.value, log.trigger_reason.value,
            log.behavior_score, log.deescalated_at.isoformat()
        ))

        conn.commit()
        conn.close()
        return log

    # ===== Override Logs =====

    def create_override_log(self, log: StrikeOverrideLog) -> StrikeOverrideLog:
        """Create an override log entry."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO strike_override_log (
                id, strike_id, alert_id,
                action, override_by, reason,
                before_state, after_state, overridden_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            log.id, log.strike_id, log.alert_id,
            log.action.value, log.override_by, log.reason,
            json.dumps(log.before_state) if log.before_state else None,
            json.dumps(log.after_state) if log.after_state else None,
            log.overridden_at.isoformat()
        ))

        conn.commit()
        conn.close()
        return log

    def get_override_logs_for_strike(self, strike_id: str) -> List[StrikeOverrideLog]:
        """Get all override logs for a strike."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM strike_override_log
            WHERE strike_id = ?
            ORDER BY overridden_at DESC
        """, (strike_id,))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_override_log(row) for row in rows]

    def get_deescalation_logs_for_strike(self, strike_id: str) -> List[StrikeDeescalationLog]:
        """Get all de-escalation logs for a strike."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM strike_deescalation_log
            WHERE strike_id = ?
            ORDER BY deescalated_at DESC
        """, (strike_id,))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_deescalation_log(row) for row in rows]

    # ===== Whitelist =====

    def create_whitelist_entry(
        self,
        entry: UserStrikeWhitelist
    ) -> UserStrikeWhitelist:
        """Create a whitelist entry."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO user_strike_whitelist (
                id, user_id, whitelisted_by, reason,
                scope, abuse_type,
                is_permanent, expires_at, whitelisted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry.id, entry.user_id, entry.whitelisted_by, entry.reason,
            entry.scope, entry.abuse_type.value if entry.abuse_type else None,
            1 if entry.is_permanent else 0,
            entry.expires_at.isoformat() if entry.expires_at else None,
            entry.whitelisted_at.isoformat()
        ))

        conn.commit()
        conn.close()
        return entry

    def is_user_whitelisted(self, user_id: str, abuse_type: Optional[AbuseType] = None) -> bool:
        """Check if user is whitelisted."""
        conn = self._get_connection()
        cursor = conn.cursor()

        now = datetime.now(UTC).isoformat()

        if abuse_type:
            cursor.execute("""
                SELECT COUNT(*) FROM user_strike_whitelist
                WHERE user_id = ?
                AND (scope = 'all' OR (scope = 'specific_abuse_type' AND abuse_type = ?))
                AND (is_permanent = 1 OR expires_at > ?)
            """, (user_id, abuse_type.value, now))
        else:
            cursor.execute("""
                SELECT COUNT(*) FROM user_strike_whitelist
                WHERE user_id = ? AND scope = 'all'
                AND (is_permanent = 1 OR expires_at > ?)
            """, (user_id, now))

        count = cursor.fetchone()[0]
        conn.close()

        return count > 0

    # ===== Helper Methods =====

    def _row_to_alert(self, row: sqlite3.Row) -> WarlordAlert:
        """Convert database row to WarlordAlert."""
        evidence_json = json.loads(row['evidence'])
        evidence = [EvidenceItem(**e) for e in evidence_json]

        return WarlordAlert(
            id=row['id'],
            target_user_id=row['target_user_id'],
            severity=row['severity'],
            abuse_type=AbuseType(row['abuse_type']),
            evidence=evidence,
            reporting_node_fingerprint=row['reporting_node_fingerprint'],
            reporting_user_id=row['reporting_user_id'],
            trusted_source=bool(row['trusted_source']),
            propagation_count=row['propagation_count'],
            created_at=datetime.fromisoformat(row['created_at']),
            expires_at=datetime.fromisoformat(row['expires_at']),
            cancelled=bool(row['cancelled']),
            cancelled_by=row['cancelled_by'],
            cancellation_reason=row['cancellation_reason'],
            cancelled_at=datetime.fromisoformat(row['cancelled_at']) if row['cancelled_at'] else None,
        )

    def _row_to_strike(self, row: sqlite3.Row) -> LocalStrike:
        """Convert database row to LocalStrike."""
        throttle_actions_json = json.loads(row['throttle_actions'])
        throttle_actions = ThrottleActions(**throttle_actions_json)

        return LocalStrike(
            id=row['id'],
            alert_id=row['alert_id'],
            target_user_id=row['target_user_id'],
            throttle_level=ThrottleLevel(row['throttle_level']),
            throttle_actions=throttle_actions,
            status=StrikeStatus(row['status']),
            automatic=bool(row['automatic']),
            behavior_score_at_start=row['behavior_score_at_start'],
            current_behavior_score=row['current_behavior_score'],
            activated_at=datetime.fromisoformat(row['activated_at']),
            deactivated_at=datetime.fromisoformat(row['deactivated_at']) if row['deactivated_at'] else None,
            overridden_by=row['overridden_by'],
            override_reason=row['override_reason'],
            overridden_at=datetime.fromisoformat(row['overridden_at']) if row['overridden_at'] else None,
        )

    def _row_to_behavior_tracking(self, row: sqlite3.Row) -> BehaviorTracking:
        """Convert database row to BehaviorTracking."""
        return BehaviorTracking(
            id=row['id'],
            user_id=row['user_id'],
            strike_id=row['strike_id'],
            exchanges_given=row['exchanges_given'],
            exchanges_received=row['exchanges_received'],
            offers_posted=row['offers_posted'],
            needs_posted=row['needs_posted'],
            behavior_score=row['behavior_score'],
            period_start=datetime.fromisoformat(row['period_start']),
            period_end=datetime.fromisoformat(row['period_end']),
            last_updated=datetime.fromisoformat(row['last_updated']),
        )

    def _row_to_override_log(self, row: sqlite3.Row) -> StrikeOverrideLog:
        """Convert database row to StrikeOverrideLog."""
        return StrikeOverrideLog(
            id=row['id'],
            strike_id=row['strike_id'],
            alert_id=row['alert_id'],
            action=OverrideAction(row['action']),
            override_by=row['override_by'],
            reason=row['reason'],
            before_state=json.loads(row['before_state']) if row['before_state'] else None,
            after_state=json.loads(row['after_state']) if row['after_state'] else None,
            overridden_at=datetime.fromisoformat(row['overridden_at']),
        )

    def _row_to_deescalation_log(self, row: sqlite3.Row) -> StrikeDeescalationLog:
        """Convert database row to StrikeDeescalationLog."""
        return StrikeDeescalationLog(
            id=row['id'],
            strike_id=row['strike_id'],
            previous_level=ThrottleLevel(row['previous_level']),
            new_level=ThrottleLevel(row['new_level']),
            trigger_reason=DeescalationReason(row['trigger_reason']),
            behavior_score=row['behavior_score'],
            deescalated_at=datetime.fromisoformat(row['deescalated_at']),
        )
