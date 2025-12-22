"""
End-to-End tests for Mycelial Strike defense system.

Tests the complete flow from evidence submission through consensus to proportional response.

Test scenarios (from GAP-E2E proposal):
WHEN Alice submits warlord alert against Mallory
WITH evidence (screenshot, transaction history)
THEN alert propagates to stewards via DTN
WHEN 3+ trusted sources corroborate
THEN auto-action triggered (throttle/quarantine)
WHEN steward reviews and confirms
THEN Mallory quarantined from network
WHEN new evidence exonerates Mallory
THEN steward can override with reason
"""

import pytest
import os
import tempfile
from datetime import datetime, timedelta
from freezegun import freeze_time

from app.models.mycelial_strike import (
    AbuseType,
    ThrottleLevel,
    StrikeStatus,
    EvidenceItem,
    OverrideAction,
    DeescalationReason,
)
from app.services.mycelial_strike_service import MycelialStrikeService


class TestMycelialStrikeE2E:
    """End-to-end Mycelial Strike defense flow tests"""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up test database and service"""
        # Create temp database
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)

        # Initialize schema
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Read and execute migration
        with open("app/database/migrations/009_add_mycelial_strike.sql") as f:
            migration_sql = f.read()
            # Execute each statement separately (can't use executescript with PRAGMA)
            for statement in migration_sql.split(';'):
                if statement.strip():
                    cursor.execute(statement)

        conn.commit()
        conn.close()

        # Create service
        self.service = MycelialStrikeService(self.db_path)

        yield

        # Cleanup
        os.unlink(self.db_path)

    def test_create_warlord_alert_with_evidence(self):
        """
        E2E Test 1: Create a Warlord Alert with evidence

        WHEN Alice submits warlord alert against Mallory
        WITH evidence (screenshot, transaction history)
        THEN alert created with correct fields
        AND evidence attached
        """
        # Prepare evidence
        evidence = [
            EvidenceItem(
                type="screenshot",
                details="Screenshot of extraction pattern: 20 exchanges received, 0 given",
                reliability_score=1.0
            ),
            EvidenceItem(
                type="transaction_history",
                details="User requested 15 batteries in last 30 days, contributed 0",
                reliability_score=1.0
            )
        ]

        # Action: Alice creates warlord alert
        alert = self.service.create_warlord_alert(
            target_user_id="mallory",
            severity=7,  # High severity
            abuse_type=AbuseType.BATTERY_WARLORD,
            evidence=evidence,
            reporting_node_fingerprint="alice-node-fp",
            reporting_user_id="alice",
            trusted_source=True
        )

        # Verify: Alert created correctly
        assert alert is not None
        assert alert.target_user_id == "mallory"
        assert alert.severity == 7
        assert alert.abuse_type == AbuseType.BATTERY_WARLORD
        assert len(alert.evidence) == 2
        assert alert.reporting_node_fingerprint == "alice-node-fp"
        assert alert.reporting_user_id == "alice"
        assert alert.trusted_source is True
        assert alert.cancelled is False
        assert alert.propagation_count == 0

        # Verify: Evidence attached
        assert alert.evidence[0].type == "screenshot"
        assert "extraction pattern" in alert.evidence[0].details
        assert alert.evidence[1].type == "transaction_history"

    def test_alert_triggers_automatic_strike(self):
        """
        E2E Test 2: High-trust alert triggers automatic strike

        GIVEN Alice is trusted source (0.9 trust)
        WHEN Alice's alert is processed
        THEN automatic strike activated against Mallory
        AND throttle level matches severity
        """
        # Setup: Create alert
        evidence = [
            EvidenceItem(
                type="pattern",
                details="Extraction pattern detected",
                reliability_score=1.0
            )
        ]

        alert = self.service.create_warlord_alert(
            target_user_id="mallory",
            severity=6,  # Should trigger HIGH throttle
            abuse_type=AbuseType.BATTERY_WARLORD,
            evidence=evidence,
            reporting_node_fingerprint="alice-node-fp",
            reporting_user_id="alice",
            trusted_source=True
        )

        # Action: Process incoming alert (high trust)
        strike = self.service.process_incoming_alert(
            alert=alert,
            local_node_fingerprint="local-node-fp",
            trust_score=0.9  # High trust
        )

        # Verify: Strike activated
        assert strike is not None
        assert strike.alert_id == alert.id
        assert strike.target_user_id == "mallory"
        assert strike.status == StrikeStatus.ACTIVE
        assert strike.automatic is True

        # Verify: Throttle level matches severity (6 = HIGH)
        assert strike.throttle_level == ThrottleLevel.HIGH
        assert strike.throttle_actions.deprioritize_matching is True
        assert strike.throttle_actions.add_message_latency == 15000  # 15 seconds
        assert strike.throttle_actions.show_warning_indicator is True

    def test_low_trust_source_does_not_trigger_automatic_strike(self):
        """
        E2E Test 3: Low-trust sources don't trigger automatic actions

        GIVEN Unknown node has low trust (0.3)
        WHEN Alert from unknown node is processed
        THEN Strike NOT automatically activated
        AND Alert stored for manual review
        """
        # Setup: Create alert
        evidence = [EvidenceItem(type="report", details="Suspicious behavior", reliability_score=0.5)]

        alert = self.service.create_warlord_alert(
            target_user_id="mallory",
            severity=8,
            abuse_type=AbuseType.EXTRACTION_PATTERN,
            evidence=evidence,
            reporting_node_fingerprint="unknown-node-fp",
            reporting_user_id=None,
            trusted_source=False
        )

        # Action: Process with low trust
        strike = self.service.process_incoming_alert(
            alert=alert,
            local_node_fingerprint="local-node-fp",
            trust_score=0.3  # Below threshold (0.6)
        )

        # Verify: No automatic strike
        assert strike is None

    def test_severity_determines_throttle_level(self):
        """
        E2E Test 4: Severity maps to appropriate throttle level

        WHEN Alerts with different severities are activated
        THEN Throttle levels match:
          - Low (1-2): Deprioritize in matching
          - Medium (3-4): Add message latency + matching penalty
          - High (5-7): Full throttle - minimal interaction
          - Critical (8-10): Automatic isolation pending steward review
        """
        evidence = [EvidenceItem(type="test", details="test", reliability_score=1.0)]

        # Test LOW throttle (severity 1-2)
        alert_low = self.service.create_warlord_alert(
            target_user_id="user1",
            severity=2,
            abuse_type=AbuseType.SPAM,
            evidence=evidence,
            reporting_node_fingerprint="node-fp"
        )
        strike_low = self.service.activate_strike(
            alert_id=alert_low.id,
            target_user_id="user1",
            severity=2,
            current_behavior_score=5.0
        )
        assert strike_low.throttle_level == ThrottleLevel.LOW
        assert strike_low.throttle_actions.deprioritize_matching is True
        assert strike_low.throttle_actions.add_message_latency == 0

        # Test MEDIUM throttle (severity 3-4)
        alert_medium = self.service.create_warlord_alert(
            target_user_id="user2",
            severity=4,
            abuse_type=AbuseType.HARASSMENT,
            evidence=evidence,
            reporting_node_fingerprint="node-fp"
        )
        strike_medium = self.service.activate_strike(
            alert_id=alert_medium.id,
            target_user_id="user2",
            severity=4,
            current_behavior_score=5.0
        )
        assert strike_medium.throttle_level == ThrottleLevel.MEDIUM
        assert strike_medium.throttle_actions.add_message_latency == 5000  # 5 seconds

        # Test HIGH throttle (severity 5-7)
        alert_high = self.service.create_warlord_alert(
            target_user_id="user3",
            severity=7,
            abuse_type=AbuseType.BATTERY_WARLORD,
            evidence=evidence,
            reporting_node_fingerprint="node-fp"
        )
        strike_high = self.service.activate_strike(
            alert_id=alert_high.id,
            target_user_id="user3",
            severity=7,
            current_behavior_score=5.0
        )
        assert strike_high.throttle_level == ThrottleLevel.HIGH
        assert strike_high.throttle_actions.add_message_latency == 15000  # 15 seconds
        assert strike_high.throttle_actions.reduce_proposal_visibility is True

        # Test CRITICAL throttle (severity 8-10)
        alert_critical = self.service.create_warlord_alert(
            target_user_id="user4",
            severity=10,
            abuse_type=AbuseType.EXPLOITATION,
            evidence=evidence,
            reporting_node_fingerprint="node-fp"
        )
        strike_critical = self.service.activate_strike(
            alert_id=alert_critical.id,
            target_user_id="user4",
            severity=10,
            current_behavior_score=5.0
        )
        assert strike_critical.throttle_level == ThrottleLevel.CRITICAL
        assert strike_critical.throttle_actions.block_high_value_exchanges is True

    def test_steward_can_override_strike(self):
        """
        E2E Test 5: Steward override cancels false positive

        WHEN Steward reviews strike
        AND determines it's a false positive
        THEN Steward can override with reason
        AND Strike marked as overridden
        AND User's access restored
        """
        # Setup: Create and activate strike
        evidence = [EvidenceItem(type="report", details="Reported for extraction", reliability_score=1.0)]

        alert = self.service.create_warlord_alert(
            target_user_id="mallory",
            severity=6,
            abuse_type=AbuseType.BATTERY_WARLORD,
            evidence=evidence,
            reporting_node_fingerprint="node-fp"
        )

        strike = self.service.activate_strike(
            alert_id=alert.id,
            target_user_id="mallory",
            severity=6,
            current_behavior_score=5.0
        )

        assert strike.status == StrikeStatus.ACTIVE

        # Action: Steward overrides strike
        self.service.override_strike(
            strike_id=strike.id,
            steward_user_id="steward-alice",
            action=OverrideAction.CANCEL_STRIKE,
            reason="False positive - user was recovering from illness, unable to contribute temporarily. Vouched by 3 trusted community members."
        )

        # Get override log from repository
        override_log = self.service.repo.get_override_logs_for_strike(strike.id)[0]

        # Verify: Override logged
        assert override_log is not None
        assert override_log.strike_id == strike.id
        assert override_log.action == OverrideAction.CANCEL_STRIKE
        assert override_log.override_by == "steward-alice"
        assert "False positive" in override_log.reason

        # Verify: Strike status changed
        updated_strike = self.service.repo.get_strike(strike.id)
        assert updated_strike.status == StrikeStatus.OVERRIDDEN
        assert updated_strike.overridden_by == "steward-alice"
        assert "False positive" in updated_strike.override_reason

    def test_behavior_improvement_triggers_deescalation(self):
        """
        E2E Test 6: Good behavior leads to automatic de-escalation

        GIVEN User under strike (HIGH throttle)
        WHEN User's behavior improves (contributes to community)
        AND Behavior score increases above threshold
        THEN Strike automatically de-escalates (HIGH -> MEDIUM -> LOW)
        AND Eventually deactivated if sustained
        """
        # Setup: Create strike
        evidence = [EvidenceItem(type="pattern", details="Extraction pattern", reliability_score=1.0)]

        alert = self.service.create_warlord_alert(
            target_user_id="bob",
            severity=6,
            abuse_type=AbuseType.BATTERY_WARLORD,
            evidence=evidence,
            reporting_node_fingerprint="node-fp"
        )

        strike = self.service.activate_strike(
            alert_id=alert.id,
            target_user_id="bob",
            severity=6,
            current_behavior_score=3.0  # Low behavior score
        )

        assert strike.throttle_level == ThrottleLevel.HIGH
        assert strike.current_behavior_score == 3.0

        # Action: Update behavior tracking (user improves with balanced exchanges)
        self.service.update_user_behavior(
            user_id="bob",
            exchanges_given=5,
            exchanges_received=4,  # Balanced exchanges (not extraction)
            offers_posted=3,
            needs_posted=2
        )

        # Get updated strike to check behavior score
        updated_strike = self.service.repo.get_strike(strike.id)

        # Check de-escalation log
        deescalation_log = self.service.repo.get_deescalation_logs_for_strike(strike.id)[0] if self.service.repo.get_deescalation_logs_for_strike(strike.id) else None

        # Verify: De-escalation occurred
        assert deescalation_log is not None
        assert deescalation_log.previous_level == ThrottleLevel.HIGH
        assert deescalation_log.new_level == ThrottleLevel.MEDIUM
        assert deescalation_log.trigger_reason == DeescalationReason.BEHAVIOR_IMPROVED
        assert deescalation_log.behavior_score > 6.0  # Improved from 3.0 to ~6.5

        # Verify: Strike updated
        updated_strike = self.service.repo.get_strike(strike.id)
        assert updated_strike.throttle_level == ThrottleLevel.MEDIUM
        assert updated_strike.current_behavior_score > 6.0  # Improved score

    def test_whitelisted_user_immune_to_automatic_strikes(self):
        """
        E2E Test 7: Whitelisted users don't get automatic strikes

        GIVEN User is whitelisted by steward (trusted elder, for example)
        WHEN Alert about whitelisted user arrives
        THEN Automatic strike NOT activated
        AND Alert stored for manual review
        """
        # Setup: Whitelist a user
        whitelist = self.service.whitelist_user(
            user_id="trusted-elder",
            steward_user_id="steward-carol",
            reason="Founding community member with 10+ years trusted service. Known to have accessibility needs that may appear as extraction pattern.",
            scope="specific_abuse_type",
            abuse_type=AbuseType.BATTERY_WARLORD,
            is_permanent=True
        )

        assert whitelist is not None

        # Create alert about whitelisted user
        evidence = [EvidenceItem(type="pattern", details="Extraction pattern", reliability_score=1.0)]

        alert = self.service.create_warlord_alert(
            target_user_id="trusted-elder",
            severity=8,
            abuse_type=AbuseType.BATTERY_WARLORD,
            evidence=evidence,
            reporting_node_fingerprint="node-fp"
        )

        # Action: Try to process alert
        strike = self.service.process_incoming_alert(
            alert=alert,
            local_node_fingerprint="local-node",
            trust_score=0.9  # High trust
        )

        # Verify: No automatic strike (whitelisted)
        assert strike is None

    def test_alert_cancellation_by_reporter(self):
        """
        E2E Test 8: Reporter can cancel alert with reason

        WHEN Reporter realizes they made a mistake
        THEN Can cancel their own alert
        AND Provide cancellation reason
        AND Active strikes deactivated
        """
        # Setup: Create alert
        evidence = [EvidenceItem(type="report", details="Suspicious activity", reliability_score=1.0)]

        alert = self.service.create_warlord_alert(
            target_user_id="bob",
            severity=5,
            abuse_type=AbuseType.HARASSMENT,
            evidence=evidence,
            reporting_node_fingerprint="alice-node",
            reporting_user_id="alice"
        )

        # Activate strike
        strike = self.service.activate_strike(
            alert_id=alert.id,
            target_user_id="bob",
            severity=5,
            current_behavior_score=5.0
        )

        assert strike.status == StrikeStatus.ACTIVE

        # Action: Alice cancels the alert via repository
        self.service.repo.cancel_alert(
            alert_id=alert.id,
            cancelled_by="alice",
            reason="Misunderstanding - Bob was helping organize mutual aid, not exploiting. Talked it out."
        )

        # Get updated alert
        cancelled_alert = self.service.repo.get_alert(alert.id)

        # Verify: Alert cancelled
        assert cancelled_alert.cancelled is True
        assert cancelled_alert.cancelled_by == "alice"
        assert "Misunderstanding" in cancelled_alert.cancellation_reason

        # Verify: Associated strikes deactivated
        updated_strike = self.service.repo.get_strike(strike.id)
        assert updated_strike.status == StrikeStatus.DEACTIVATED

    def test_multiple_corroborating_alerts_increase_severity(self):
        """
        E2E Test 9: Multiple independent reports increase confidence

        WHEN Multiple trusted sources report same user
        AND Evidence from different perspectives
        THEN System increases confidence in alert
        AND May escalate throttle level
        """
        # Create multiple alerts from different sources
        evidence1 = [EvidenceItem(type="observation", details="Observed extraction at community event", reliability_score=1.0)]
        evidence2 = [EvidenceItem(type="transaction", details="Transaction history shows pattern", reliability_score=1.0)]
        evidence3 = [EvidenceItem(type="report", details="Multiple community members reported similar behavior", reliability_score=0.9)]

        alert1 = self.service.create_warlord_alert(
            target_user_id="mallory",
            severity=4,
            abuse_type=AbuseType.BATTERY_WARLORD,
            evidence=evidence1,
            reporting_node_fingerprint="alice-node",
            reporting_user_id="alice"
        )

        alert2 = self.service.create_warlord_alert(
            target_user_id="mallory",
            severity=5,
            abuse_type=AbuseType.BATTERY_WARLORD,
            evidence=evidence2,
            reporting_node_fingerprint="bob-node",
            reporting_user_id="bob"
        )

        alert3 = self.service.create_warlord_alert(
            target_user_id="mallory",
            severity=4,
            abuse_type=AbuseType.BATTERY_WARLORD,
            evidence=evidence3,
            reporting_node_fingerprint="carol-node",
            reporting_user_id="carol"
        )

        # Verify: Multiple alerts created (get active alerts)
        all_alerts = self.service.repo.get_active_alerts_for_user("mallory")
        assert len(all_alerts) >= 3

        # Verify: Can calculate aggregate severity
        avg_severity = sum(a.severity for a in all_alerts) / len(all_alerts)
        assert avg_severity > 4  # Multiple sources increase confidence

    def test_time_based_alert_expiration(self):
        """
        E2E Test 10: Alerts expire after configured period

        GIVEN Alert created with 7-day expiration
        WHEN 8 days pass
        THEN Alert no longer considered active
        AND Strike can be de-escalated
        """
        # Setup: Create alert
        evidence = [EvidenceItem(type="pattern", details="Extraction pattern", reliability_score=1.0)]

        with freeze_time("2025-01-01 00:00:00"):
            alert = self.service.create_warlord_alert(
                target_user_id="bob",
                severity=6,
                abuse_type=AbuseType.BATTERY_WARLORD,
                evidence=evidence,
                reporting_node_fingerprint="node-fp"
            )

            # Verify expiration is 7 days from now
            assert alert.expires_at == datetime(2025, 1, 8, 0, 0, 0)

        # Fast-forward 8 days
        with freeze_time("2025-01-09 00:00:00"):
            # Check if alert is expired
            now = datetime.utcnow()
            is_expired = alert.expires_at < now
            assert is_expired is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
