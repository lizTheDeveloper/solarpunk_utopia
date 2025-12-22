"""Sanctuary Network Service

Coordinates underground railroad infrastructure:
- Safe houses, transport, legal resources
- Auto-purge after 24 hours (CRITICAL)
- High trust requirements (>0.8)
- Steward verification mandatory
"""
import uuid
from datetime import datetime, timedelta, UTC
from typing import List, Optional

from app.models.sanctuary import (
    SanctuaryResource,
    SanctuaryRequest,
    SanctuaryMatch,
    RapidAlert,
    SensitivityLevel,
    SanctuaryResourceType,
    VerificationStatus,
    VerificationMethod,
    VerificationRecord,
    SanctuaryVerification,
    SanctuaryUse,
    SANCTUARY_MIN_TRUST,
    SANCTUARY_MEDIUM_TRUST,
    MIN_SANCTUARY_VERIFICATIONS,
    VERIFICATION_VALIDITY_DAYS,
)
from app.database.sanctuary_repository import SanctuaryRepository


class SanctuaryService:
    """Service for sanctuary network operations."""

    def __init__(self, db_path: str):
        self.repo = SanctuaryRepository(db_path)

    # ===== Resource Management =====

    def offer_resource(
        self,
        user_id: str,
        cell_id: str,
        resource_type: SanctuaryResourceType,
        description: str,
        capacity: Optional[int] = None,
        duration_days: Optional[int] = None
    ) -> SanctuaryResource:
        """Offer a sanctuary resource.

        NOTE: High-sensitivity resources require steward verification.
        """
        # Determine sensitivity based on resource type
        sensitivity = SensitivityLevel.HIGH if resource_type in [
            SanctuaryResourceType.SAFE_SPACE,
            SanctuaryResourceType.TRANSPORT,
            SanctuaryResourceType.INTEL
        ] else SensitivityLevel.MEDIUM

        resource = SanctuaryResource(
            id=f"sanctuary-res-{uuid.uuid4()}",
            resource_type=resource_type,
            sensitivity=sensitivity,
            offered_by=user_id,
            cell_id=cell_id,
            description=description,
            capacity=capacity,
            duration_days=duration_days,
            verification_status=VerificationStatus.PENDING,
            available=True,
            available_from=datetime.now(UTC)
        )

        return self.repo.create_resource(resource)

    def verify_resource(
        self,
        resource_id: str,
        steward_id: str,
        notes: str
    ):
        """Steward verifies a sanctuary resource."""
        self.repo.verify_resource(resource_id, steward_id, notes)

    def get_available_resources(
        self,
        cell_id: str,
        user_trust_score: float,
        resource_type: Optional[SanctuaryResourceType] = None
    ) -> List[SanctuaryResource]:
        """Get available sanctuary resources for a cell.

        Filters by trust level:
        - HIGH sensitivity requires trust >0.8
        - MEDIUM sensitivity requires trust >0.6
        """
        # Get all resources for cell
        resources = self.repo.get_resources_by_cell(cell_id, verified_only=True)

        # Filter by trust level
        filtered = []
        for resource in resources:
            if resource.sensitivity == SensitivityLevel.HIGH:
                if user_trust_score >= SANCTUARY_MIN_TRUST:
                    filtered.append(resource)
            elif resource.sensitivity == SensitivityLevel.MEDIUM:
                if user_trust_score >= SANCTUARY_MEDIUM_TRUST:
                    filtered.append(resource)
            else:
                filtered.append(resource)

        # Filter by resource type if specified
        if resource_type:
            filtered = [r for r in filtered if r.resource_type == resource_type]

        return filtered

    # ===== Request Management =====

    def create_request(
        self,
        user_id: str,
        cell_id: str,
        steward_id: str,
        request_type: SanctuaryResourceType,
        urgency: str,
        description: str,
        people_count: int = 1,
        duration_needed_days: Optional[int] = None,
        location_hint: Optional[str] = None
    ) -> SanctuaryRequest:
        """Create a sanctuary request (steward-verified only)."""
        # Calculate expiration based on urgency
        if urgency == "critical":
            expires_in_hours = 6
        elif urgency == "urgent":
            expires_in_hours = 24
        else:
            expires_in_hours = 72

        request = SanctuaryRequest(
            id=f"sanctuary-req-{uuid.uuid4()}",
            request_type=request_type,
            urgency=urgency,
            requested_by=user_id,
            cell_id=cell_id,
            verified_by=steward_id,
            description=description,
            people_count=people_count,
            duration_needed_days=duration_needed_days,
            location_hint=location_hint,
            status="pending",
            purge_at=datetime.now(UTC) + timedelta(days=1),
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(hours=expires_in_hours)
        )

        return self.repo.create_request(request)

    def match_request_to_resource(
        self,
        request_id: str,
        resource_id: str,
        cell_id: str,
        steward_id: str
    ) -> SanctuaryMatch:
        """Match a sanctuary request to a resource."""
        match = SanctuaryMatch(
            id=f"sanctuary-match-{uuid.uuid4()}",
            request_id=request_id,
            resource_id=resource_id,
            cell_id=cell_id,
            coordinated_by=steward_id,
            status="active",
            purge_at=datetime.now(UTC) + timedelta(days=1),
            created_at=datetime.now(UTC)
        )

        return self.repo.create_match(match)

    def complete_match(self, match_id: str):
        """Mark a sanctuary match as completed.

        This triggers 24-hour purge timer.
        """
        self.repo.mark_match_completed(match_id)

    # ===== Rapid Alerts =====

    def create_rapid_alert(
        self,
        user_id: str,
        cell_id: str,
        alert_type: str,
        severity: str,
        location_hint: str,
        description: str,
        people_affected: Optional[int] = None
    ) -> RapidAlert:
        """Create a rapid alert (ICE raid, etc)."""
        alert = RapidAlert(
            id=f"alert-{uuid.uuid4()}",
            alert_type=alert_type,
            severity=severity,
            reported_by=user_id,
            cell_id=cell_id,
            location_hint=location_hint,
            description=description,
            people_affected=people_affected,
            purge_at=datetime.now(UTC) + timedelta(days=7),
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(hours=24)
        )

        return self.repo.create_alert(alert)

    def get_active_alerts(self, cell_id: str) -> List[RapidAlert]:
        """Get active rapid alerts for a cell."""
        return self.repo.get_active_alerts(cell_id)

    # ===== Auto-Purge =====

    def run_auto_purge(self) -> dict:
        """Run auto-purge of old sanctuary records.

        Should be called by background worker every hour.
        """
        return self.repo.purge_old_records()

    # ===== Multi-Steward Verification (GAP-109) =====

    def add_verification(
        self,
        resource_id: str,
        steward_id: str,
        verification_method: VerificationMethod,
        notes: Optional[str] = None,
        escape_routes_verified: bool = False,
        capacity_verified: bool = False,
        buddy_protocol_available: bool = False
    ) -> dict:
        """Add a steward verification to a sanctuary resource.

        Requires 2 independent steward verifications before resource becomes available.

        Returns:
            {
                'verification_id': str,
                'verification_count': int,
                'status': 'pending' or 'verified',
                'needs_second_verification': bool,
                'message': str
            }
        """
        # Get current verification status
        verification_agg = self.repo.get_verification_aggregate(resource_id)

        if verification_agg is None:
            # No verifications yet, create aggregate
            verification_agg = SanctuaryVerification(
                resource_id=resource_id,
                verifications=[],
                successful_uses=0
            )

        # Check if steward can add verification (hasn't already verified)
        if not verification_agg.can_add_verification(steward_id):
            raise ValueError(f"Different steward required. Steward {steward_id} has already verified this resource.")

        # Create verification record
        verification = VerificationRecord(
            id=f"ver-{uuid.uuid4()}",
            resource_id=resource_id,
            steward_id=steward_id,
            verified_at=datetime.now(UTC),
            verification_method=verification_method,
            notes=notes,
            escape_routes_verified=escape_routes_verified,
            capacity_verified=capacity_verified,
            buddy_protocol_available=buddy_protocol_available
        )

        # Save verification record
        self.repo.create_verification(verification)

        # Add to aggregate
        verification_agg.add_verification(verification)

        # Update resource metadata
        self.repo.update_resource_verification_metadata(
            resource_id=resource_id,
            first_verified_at=verification_agg.first_verified_at,
            last_check=verification_agg.last_check,
            expires_at=verification_agg.expires_at
        )

        # Update verification status if we have enough verifications
        if verification_agg.verification_count >= MIN_SANCTUARY_VERIFICATIONS:
            self.repo.update_verification_status(resource_id, VerificationStatus.VERIFIED)
            status = 'verified'
            message = "Resource verified and available for matching."
        else:
            # Still pending
            status = 'pending'
            message = f"Verification added. Needs {MIN_SANCTUARY_VERIFICATIONS - verification_agg.verification_count} more steward(s) to approve."

        return {
            'verification_id': verification.id,
            'verification_count': verification_agg.verification_count,
            'status': status,
            'needs_second_verification': verification_agg.needs_second_verification,
            'message': message
        }

    def get_verification_status(self, resource_id: str) -> Optional[SanctuaryVerification]:
        """Get verification status for a sanctuary resource."""
        return self.repo.get_verification_aggregate(resource_id)

    def get_resources_needing_verification(
        self,
        cell_id: str,
        steward_id: Optional[str] = None
    ) -> dict:
        """Get sanctuary resources that need verification or re-verification.

        Returns:
            {
                'pending_verification': [resources with only 1 verification],
                'expiring_soon': [resources expiring in next 14 days]
            }
        """
        result = self.repo.get_resources_needing_verification(
            cell_id=cell_id,
            exclude_steward_id=steward_id  # Exclude resources this steward already verified
        )

        return {
            'pending_verification': result['pending'],
            'expiring_soon': result['expiring']
        }

    def record_sanctuary_use(
        self,
        resource_id: str,
        request_id: str,
        outcome: str = "success"
    ) -> SanctuaryUse:
        """Record a sanctuary use (for quality tracking).

        Args:
            resource_id: Sanctuary resource used
            request_id: Request fulfilled
            outcome: 'success', 'failed', or 'compromised'
        """
        use = SanctuaryUse(
            id=f"use-{uuid.uuid4()}",
            resource_id=resource_id,
            request_id=request_id,
            completed_at=datetime.now(UTC),
            outcome=outcome,
            purge_at=datetime.now(UTC) + timedelta(days=30)
        )

        self.repo.create_sanctuary_use(use)

        # If successful, increment the successful_uses counter
        if outcome == "success":
            self.repo.increment_successful_uses(resource_id)

        return use

    def get_high_trust_resources(
        self,
        cell_id: str,
        resource_type: SanctuaryResourceType
    ) -> List[SanctuaryResource]:
        """Get sanctuary resources suitable for CRITICAL severity needs.

        Filters to:
        - Resources with 3+ successful prior uses
        - Resources verified by 2+ stewards
        - Resources not expired
        """
        # Get all verified resources
        resources = self.repo.get_resources_by_cell(cell_id, verified_only=True)

        # Filter by type
        if resource_type:
            resources = [r for r in resources if r.resource_type == resource_type]

        # Filter to high-trust resources
        high_trust = []
        for resource in resources:
            verification = self.repo.get_verification_aggregate(resource.id)
            if verification and verification.is_high_trust:
                high_trust.append(resource)

        return high_trust
