"""Service for Mycelial Strike

'Mutual Aid includes Mutual Defense.' - Peter Kropotkin

Automated solidarity defense against extractive behavior.
No committee meeting required. Instant, collective response.
"""
import uuid
from datetime import datetime, timedelta, UTC
from typing import List, Optional, Dict, Any

from app.models.mycelial_strike import (
    WarlordAlert,
    LocalStrike,
    BehaviorTracking,
    StrikeDeescalationLog,
    StrikeOverrideLog,
    UserStrikeWhitelist,
    AbuseType,
    ThrottleLevel,
    StrikeStatus,
    ThrottleActions,
    EvidenceItem,
    OverrideAction,
    DeescalationReason,
)
from app.database.mycelial_strike_repository import MycelialStrikeRepository


class MycelialStrikeService:
    """Business logic for Mycelial Strike system."""

    def __init__(self, db_path: str):
        self.repo = MycelialStrikeRepository(db_path)

    # ===== Alert Creation and Propagation =====

    def create_warlord_alert(
        self,
        target_user_id: str,
        severity: int,
        abuse_type: AbuseType,
        evidence: List[EvidenceItem],
        reporting_node_fingerprint: str,
        reporting_user_id: Optional[str] = None,
        trusted_source: bool = True
    ) -> WarlordAlert:
        """
        Create a Warlord Alert about extractive behavior.

        This is called by the Counter-Power Agent when it detects abuse.
        """
        if not 1 <= severity <= 10:
            raise ValueError("Severity must be between 1 and 10")

        if len(evidence) == 0:
            raise ValueError("At least one piece of evidence is required")

        now = datetime.now(UTC)
        expires_at = now + timedelta(days=7)  # 7 day alert window

        alert = WarlordAlert(
            id=str(uuid.uuid4()),
            target_user_id=target_user_id,
            severity=severity,
            abuse_type=abuse_type,
            evidence=evidence,
            reporting_node_fingerprint=reporting_node_fingerprint,
            reporting_user_id=reporting_user_id,
            trusted_source=trusted_source,
            propagation_count=0,
            created_at=now,
            expires_at=expires_at,
            cancelled=False,
        )

        return self.repo.create_alert(alert)

    def process_incoming_alert(
        self,
        alert: WarlordAlert,
        local_node_fingerprint: str,
        trust_score: float
    ) -> Optional[LocalStrike]:
        """
        Process an incoming Warlord Alert from another node.

        If we trust the source, automatically activate a strike.
        """
        # Check if user is whitelisted
        if self.repo.is_user_whitelisted(alert.target_user_id, alert.abuse_type):
            return None

        # Check if we trust this source enough
        MIN_TRUST_SCORE = 0.6
        if trust_score < MIN_TRUST_SCORE:
            # Store alert but don't auto-activate
            return None

        # Get current behavior tracking
        behavior = self.repo.get_behavior_tracking(alert.target_user_id)
        current_behavior_score = behavior.behavior_score if behavior else 5.0

        # Activate local strike
        return self.activate_strike(
            alert_id=alert.id,
            target_user_id=alert.target_user_id,
            severity=alert.severity,
            current_behavior_score=current_behavior_score
        )

    # ===== Strike Activation and Management =====

    def activate_strike(
        self,
        alert_id: str,
        target_user_id: str,
        severity: int,
        current_behavior_score: float
    ) -> LocalStrike:
        """
        Activate a local strike against a user.

        Throttle level is determined by severity:
        - Low (1-2): Deprioritize in matching
        - Medium (3-4): Add message latency + matching penalty
        - High (5-7): Full throttle - minimal interaction
        - Critical (8-10): Automatic isolation pending steward review
        """
        # Determine throttle level
        if severity <= 2:
            throttle_level = ThrottleLevel.LOW
            throttle_actions = ThrottleActions(
                deprioritize_matching=True,
                show_warning_indicator=True,
            )
        elif severity <= 4:
            throttle_level = ThrottleLevel.MEDIUM
            throttle_actions = ThrottleActions(
                deprioritize_matching=True,
                add_message_latency=5000,  # 5 seconds
                show_warning_indicator=True,
            )
        elif severity <= 7:
            throttle_level = ThrottleLevel.HIGH
            throttle_actions = ThrottleActions(
                deprioritize_matching=True,
                add_message_latency=15000,  # 15 seconds
                reduce_proposal_visibility=True,
                show_warning_indicator=True,
            )
        else:  # 8-10
            throttle_level = ThrottleLevel.CRITICAL
            throttle_actions = ThrottleActions(
                deprioritize_matching=True,
                add_message_latency=30000,  # 30 seconds
                reduce_proposal_visibility=True,
                show_warning_indicator=True,
                block_high_value_exchanges=True,
            )

        strike = LocalStrike(
            id=str(uuid.uuid4()),
            alert_id=alert_id,
            target_user_id=target_user_id,
            throttle_level=throttle_level,
            throttle_actions=throttle_actions,
            status=StrikeStatus.ACTIVE,
            automatic=True,
            behavior_score_at_start=current_behavior_score,
            current_behavior_score=current_behavior_score,
            activated_at=datetime.now(UTC),
        )

        return self.repo.create_strike(strike)

    def get_active_strikes_for_user(self, user_id: str) -> List[LocalStrike]:
        """Get all active strikes against a user."""
        return self.repo.get_active_strikes_for_user(user_id)

    def get_strike_status_for_user(self, user_id: str) -> Dict[str, Any]:
        """
        Get strike status for a user (for transparency).

        Shows what behavior triggered the strike and how to improve.
        """
        strikes = self.repo.get_active_strikes_for_user(user_id)
        if not strikes:
            return {
                'under_strike': False,
                'strikes': [],
            }

        # Get alerts for context
        alerts = []
        for strike in strikes:
            alert = self.repo.get_alert(strike.alert_id)
            if alert:
                alerts.append({
                    'severity': alert.severity,
                    'abuse_type': alert.abuse_type.value,
                    'evidence': [
                        {'type': e.type, 'details': e.details}
                        for e in alert.evidence
                    ],
                })

        # Get behavior tracking
        behavior = self.repo.get_behavior_tracking(user_id)

        return {
            'under_strike': True,
            'strikes': [
                {
                    'throttle_level': strike.throttle_level.value,
                    'activated_at': strike.activated_at.isoformat(),
                    'current_behavior_score': strike.current_behavior_score,
                }
                for strike in strikes
            ],
            'alerts': alerts,
            'current_behavior': {
                'score': behavior.behavior_score if behavior else 0.0,
                'exchanges_given': behavior.exchanges_given if behavior else 0,
                'exchanges_received': behavior.exchanges_received if behavior else 0,
            } if behavior else None,
            'how_to_improve': self._get_improvement_guidance(strikes, behavior),
        }

    # ===== Behavior Tracking and De-escalation =====

    def update_user_behavior(
        self,
        user_id: str,
        exchanges_given: int = 0,
        exchanges_received: int = 0,
        offers_posted: int = 0,
        needs_posted: int = 0
    ) -> None:
        """
        Update behavior tracking for a user.

        Called when user completes exchanges, posts offers/needs.
        Automatically checks if behavior has improved enough for de-escalation.
        """
        now = datetime.now(UTC)
        period_start = now - timedelta(days=30)  # 30-day rolling window

        # Get existing tracking
        tracking = self.repo.get_behavior_tracking(user_id)

        if not tracking:
            # Create new tracking
            tracking = BehaviorTracking(
                id=str(uuid.uuid4()),
                user_id=user_id,
                strike_id=None,
                exchanges_given=exchanges_given,
                exchanges_received=exchanges_received,
                offers_posted=offers_posted,
                needs_posted=needs_posted,
                behavior_score=self._calculate_behavior_score(
                    exchanges_given, exchanges_received, offers_posted, needs_posted
                ),
                period_start=period_start,
                period_end=now,
                last_updated=now,
            )
        else:
            # Update existing tracking
            tracking.exchanges_given += exchanges_given
            tracking.exchanges_received += exchanges_received
            tracking.offers_posted += offers_posted
            tracking.needs_posted += needs_posted
            tracking.behavior_score = self._calculate_behavior_score(
                tracking.exchanges_given,
                tracking.exchanges_received,
                tracking.offers_posted,
                tracking.needs_posted
            )
            tracking.last_updated = now

        self.repo.create_or_update_behavior_tracking(tracking)

        # Check for de-escalation
        strikes = self.repo.get_active_strikes_for_user(user_id)
        for strike in strikes:
            self._check_deescalation(strike, tracking.behavior_score)

    def _check_deescalation(
        self,
        strike: LocalStrike,
        current_behavior_score: float
    ) -> None:
        """
        Check if strike should be de-escalated based on behavior improvement.

        De-escalation occurs when:
        - Behavior score increases significantly
        - User completes 3+ successful exchanges (giving AND receiving)
        """
        score_improvement = current_behavior_score - strike.behavior_score_at_start

        # Update strike's current behavior score
        self.repo.update_strike_behavior_score(strike.id, current_behavior_score)

        # Check for de-escalation
        DEESCALATION_THRESHOLD = 2.0  # Score must improve by 2 points

        if score_improvement >= DEESCALATION_THRESHOLD:
            # Determine new throttle level
            new_level = self._deescalate_throttle_level(strike.throttle_level)

            if new_level is None:
                # Fully de-escalate - deactivate strike
                self.repo.deactivate_strike(strike.id)
                log_level = ThrottleLevel.LOW  # For logging purposes
            else:
                # Partial de-escalation - reduce throttle level
                new_actions = self._get_throttle_actions_for_level(new_level)
                self.repo.update_strike_throttle_level(strike.id, new_level, new_actions)
                log_level = new_level

            # Log de-escalation
            log = StrikeDeescalationLog(
                id=str(uuid.uuid4()),
                strike_id=strike.id,
                previous_level=strike.throttle_level,
                new_level=log_level,
                trigger_reason=DeescalationReason.BEHAVIOR_IMPROVED,
                behavior_score=current_behavior_score,
                deescalated_at=datetime.now(UTC),
            )
            self.repo.create_deescalation_log(log)

    def _deescalate_throttle_level(
        self,
        current_level: ThrottleLevel
    ) -> Optional[ThrottleLevel]:
        """
        Determine next throttle level after de-escalation.

        Returns None if strike should be fully deactivated.
        """
        if current_level == ThrottleLevel.CRITICAL:
            return ThrottleLevel.HIGH
        elif current_level == ThrottleLevel.HIGH:
            return ThrottleLevel.MEDIUM
        elif current_level == ThrottleLevel.MEDIUM:
            return ThrottleLevel.LOW
        else:  # LOW
            return None  # Deactivate completely

    def _get_throttle_actions_for_level(self, level: ThrottleLevel) -> ThrottleActions:
        """
        Get appropriate throttle actions for a given throttle level.
        """
        if level == ThrottleLevel.LOW:
            return ThrottleActions(
                deprioritize_matching=True,
                show_warning_indicator=True,
            )
        elif level == ThrottleLevel.MEDIUM:
            return ThrottleActions(
                deprioritize_matching=True,
                add_message_latency=5000,  # 5 seconds
                show_warning_indicator=True,
            )
        elif level == ThrottleLevel.HIGH:
            return ThrottleActions(
                deprioritize_matching=True,
                add_message_latency=15000,  # 15 seconds
                reduce_proposal_visibility=True,
                show_warning_indicator=True,
            )
        else:  # CRITICAL
            return ThrottleActions(
                deprioritize_matching=True,
                add_message_latency=30000,  # 30 seconds
                reduce_proposal_visibility=True,
                show_warning_indicator=True,
                block_high_value_exchanges=True,
            )

    def _calculate_behavior_score(
        self,
        exchanges_given: int,
        exchanges_received: int,
        offers_posted: int,
        needs_posted: int
    ) -> float:
        """
        Calculate behavior score (0-10, higher is better).

        Factors:
        - Reciprocity: giving vs receiving
        - Activity: offers and needs posted
        - Balance: not just taking or just giving
        """
        # Reciprocity score
        total_exchanges = exchanges_given + exchanges_received
        if total_exchanges == 0:
            reciprocity_score = 5.0  # Neutral
        else:
            # Ideal is 1:1 ratio
            ratio = exchanges_given / total_exchanges
            # Score is highest at 0.5 (equal giving/receiving)
            reciprocity_score = 10.0 * (1.0 - abs(ratio - 0.5) * 2)

        # Activity score
        total_activity = offers_posted + needs_posted
        activity_score = min(10.0, total_activity / 5.0)  # Max at 50 posts

        # Overall score (weighted average)
        behavior_score = (reciprocity_score * 0.7) + (activity_score * 0.3)

        return max(0.0, min(10.0, behavior_score))

    # ===== Steward Oversight =====

    def override_strike(
        self,
        strike_id: str,
        steward_user_id: str,
        action: OverrideAction,
        reason: str
    ) -> None:
        """
        Steward override of a strike.

        Actions:
        - Cancel strike
        - Cancel alert
        - Adjust severity
        - Whitelist user
        """
        strike = self.repo.get_strike(strike_id)
        if not strike:
            raise ValueError(f"Strike {strike_id} not found")

        # Capture before state
        before_state = {
            'strike_id': strike.id,
            'status': strike.status.value,
            'throttle_level': strike.throttle_level.value,
        }

        # Execute override
        if action == OverrideAction.CANCEL_STRIKE:
            self.repo.override_strike(strike_id, steward_user_id, reason)
            after_state = {'status': 'overridden'}

        elif action == OverrideAction.CANCEL_ALERT:
            alert = self.repo.get_alert(strike.alert_id)
            if alert:
                self.repo.cancel_alert(alert.id, steward_user_id, reason)
            self.repo.override_strike(strike_id, steward_user_id, reason)
            after_state = {'alert_cancelled': True, 'strike_overridden': True}

        else:
            after_state = {}

        # Log override
        log = StrikeOverrideLog(
            id=str(uuid.uuid4()),
            strike_id=strike_id,
            alert_id=strike.alert_id,
            action=action,
            override_by=steward_user_id,
            reason=reason,
            before_state=before_state,
            after_state=after_state,
            overridden_at=datetime.now(UTC),
        )
        self.repo.create_override_log(log)

    def whitelist_user(
        self,
        user_id: str,
        steward_user_id: str,
        reason: str,
        scope: str = 'all',
        abuse_type: Optional[AbuseType] = None,
        is_permanent: bool = False,
        duration_days: Optional[int] = None
    ) -> UserStrikeWhitelist:
        """
        Whitelist a user from automatic strikes.

        Used for false positives or special cases.
        """
        now = datetime.now(UTC)
        expires_at = None if is_permanent else now + timedelta(days=duration_days or 30)

        entry = UserStrikeWhitelist(
            id=str(uuid.uuid4()),
            user_id=user_id,
            whitelisted_by=steward_user_id,
            reason=reason,
            scope=scope,
            abuse_type=abuse_type,
            is_permanent=is_permanent,
            expires_at=expires_at,
            whitelisted_at=now,
        )

        return self.repo.create_whitelist_entry(entry)

    # ===== Helper Methods =====

    def _get_improvement_guidance(
        self,
        strikes: List[LocalStrike],
        behavior: Optional[BehaviorTracking]
    ) -> List[str]:
        """
        Generate guidance for how to improve behavior and remove strike.
        """
        guidance = []

        if not behavior or behavior.exchanges_given == 0:
            guidance.append("Complete exchanges where you GIVE resources, not just receive")

        if not behavior or behavior.exchanges_received == 0:
            guidance.append("Complete exchanges where you RECEIVE resources, show reciprocity")

        if not behavior or (behavior.exchanges_given < 3 or behavior.exchanges_received < 3):
            guidance.append("Complete at least 3 successful exchanges (both giving and receiving)")

        if not behavior or behavior.offers_posted == 0:
            guidance.append("Post offers of what you can give to the community")

        guidance.append("Demonstrate reciprocity - this network is about mutual aid, not extraction")

        return guidance
