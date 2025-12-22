"""Service for Ancestor Voting

'The only good authority is a dead one.' - Mikhail Bakunin

When members leave, their reputation becomes a Memorial Fund that stewards
can use to amplify marginalized voices.
"""
import uuid
from datetime import datetime, timedelta, UTC
from typing import List, Optional, Dict, Any
import json

from app.models.ancestor_voting import (
    MemorialFund,
    GhostReputationAllocation,
    ProposalAncestorAttribution,
    UserDepartureRecord,
    AllocationPriority,
    MemorialImpactTracking,
    AllocationAuditLog,
    DepartureType,
    AllocationStatus,
    ProposalStatus,
    AuditAction,
)
from app.database.ancestor_voting_repository import AncestorVotingRepository


class AncestorVotingService:
    """Business logic for Ancestor Voting."""

    def __init__(self, db_path: str):
        self.repo = AncestorVotingRepository(db_path)

    # ===== Memorial Fund Management =====

    def create_memorial_fund_on_departure(
        self,
        user_id: str,
        user_name: str,
        display_name: Optional[str],
        final_reputation: float,
        departure_type: DepartureType,
        departure_reason: Optional[str] = None,
        recorded_by: Optional[str] = None
    ) -> MemorialFund:
        """
        Create a Memorial Fund when a user departs.

        This is called automatically when:
        - A user voluntarily leaves
        - A user is marked as deceased
        - A user is removed from the network
        - A user is inactive for extended period
        """
        now = datetime.now(UTC)

        # Create Memorial Fund
        fund = MemorialFund(
            id=str(uuid.uuid4()),
            created_from_user_id=user_id,
            departed_user_name=user_name,
            departed_user_display_name=display_name,
            initial_reputation=final_reputation,
            current_balance=final_reputation,
            created_at=now,
            updated_at=now,
            family_requested_removal=False,
            removal_requested_at=None,
        )
        fund = self.repo.create_memorial_fund(fund)

        # Create Departure Record
        departure = UserDepartureRecord(
            id=str(uuid.uuid4()),
            user_id=user_id,
            departure_type=departure_type,
            departure_reason=departure_reason,
            final_reputation=final_reputation,
            memorial_fund_id=fund.id,
            private_data_purged=False,  # Will be purged by separate process
            purged_at=None,
            public_contributions_retained=True,
            departed_at=now,
            recorded_by=recorded_by,
        )
        self.repo.create_departure_record(departure)

        # Initialize Impact Tracking
        tracking = MemorialImpactTracking(
            id=str(uuid.uuid4()),
            fund_id=fund.id,
            total_allocated=0.0,
            total_refunded=0.0,
            proposals_boosted=0,
            proposals_approved=0,
            proposals_implemented=0,
            new_members_helped=0,
            controversial_proposals_boosted=0,
            last_updated=now,
        )
        self.repo.create_or_update_impact_tracking(tracking)

        return fund

    def get_memorial_fund(self, fund_id: str) -> Optional[MemorialFund]:
        """Get a Memorial Fund by ID."""
        return self.repo.get_memorial_fund(fund_id)

    def list_memorial_funds(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> List[MemorialFund]:
        """List all Memorial Funds (excluding those with removal requests)."""
        return self.repo.list_memorial_funds(limit, offset, exclude_requested_removal=True)

    def request_memorial_removal(self, fund_id: str) -> None:
        """Request removal of a Memorial Fund (family request)."""
        # Mark fund for removal
        self.repo.request_fund_removal(fund_id)

        # Refund all active allocations
        allocations = self.repo.list_allocations_for_fund(fund_id)
        for allocation in allocations:
            if allocation.status == AllocationStatus.ACTIVE:
                self.refund_allocation(
                    allocation_id=allocation.id,
                    refund_reason="Family requested memorial removal"
                )

    # ===== Ghost Reputation Allocation =====

    def allocate_ghost_reputation(
        self,
        fund_id: str,
        proposal_id: str,
        amount: float,
        allocated_by: str,  # Steward user ID
        reason: str,
        proposal_metadata: Dict[str, Any]
    ) -> GhostReputationAllocation:
        """
        Allocate Ghost Reputation to a proposal.

        Anti-abuse checks:
        - Steward cannot allocate to their own proposals
        - Cannot allocate more than 20% of fund to single proposal
        - Must provide written justification
        - Other stewards can veto within 24 hours
        """
        # Get the Memorial Fund
        fund = self.repo.get_memorial_fund(fund_id)
        if not fund:
            raise ValueError(f"Memorial Fund {fund_id} not found")

        # Check if fund has been marked for removal
        if fund.family_requested_removal:
            raise ValueError("Memorial Fund removal requested - no new allocations allowed")

        # Check sufficient balance
        if fund.current_balance < amount:
            raise ValueError(f"Insufficient balance. Available: {fund.current_balance}, Requested: {amount}")

        # Check 20% cap
        max_allocation = fund.initial_reputation * 0.20
        if amount > max_allocation:
            raise ValueError(f"Cannot allocate more than 20% of fund ({max_allocation}) to a single proposal")

        # Check steward not allocating to own proposal
        proposal_author = proposal_metadata.get('author_id')
        if proposal_author == allocated_by:
            raise ValueError("Stewards cannot allocate Ghost Reputation to their own proposals")

        # Calculate priority score
        priority = self._calculate_priority(proposal_metadata)

        # Create allocation
        now = datetime.now(UTC)
        veto_deadline = now + timedelta(hours=24)

        allocation = GhostReputationAllocation(
            id=str(uuid.uuid4()),
            fund_id=fund_id,
            proposal_id=proposal_id,
            amount=amount,
            allocated_by=allocated_by,
            reason=reason,
            status=AllocationStatus.ACTIVE,
            refunded=False,
            refund_reason=None,
            allocated_at=now,
            refunded_at=None,
            completed_at=None,
            veto_deadline=veto_deadline,
            vetoed=False,
            vetoed_by=None,
            veto_reason=None,
            vetoed_at=None,
        )
        allocation = self.repo.create_allocation(allocation)

        # Store priority
        priority_obj = AllocationPriority(
            id=str(uuid.uuid4()),
            allocation_id=allocation.id,
            is_new_member=priority['is_new_member'],
            has_low_reputation=priority['has_low_reputation'],
            is_controversial=priority['is_controversial'],
            is_marginalized_identity=priority['is_marginalized_identity'],
            priority_score=priority['priority_score'],
            calculated_at=now,
        )
        self.repo.create_allocation_priority(priority_obj)

        # Update fund balance
        new_balance = fund.current_balance - amount
        self.repo.update_memorial_fund_balance(fund_id, new_balance)

        # Create attribution
        attribution = ProposalAncestorAttribution(
            id=str(uuid.uuid4()),
            proposal_id=proposal_id,
            allocation_id=allocation.id,
            fund_id=fund_id,
            ancestor_name=fund.departed_user_name,
            reputation_amount=amount,
            proposal_status=ProposalStatus.PENDING,
            attributed_at=now,
        )
        self.repo.create_attribution(attribution)

        # Create audit log
        self._log_audit(
            allocation_id=allocation.id,
            action=AuditAction.ALLOCATED,
            actor_id=allocated_by,
            actor_role='steward',
            details=json.dumps({
                'fund_id': fund_id,
                'proposal_id': proposal_id,
                'amount': amount,
                'reason': reason,
                'priority_score': priority['priority_score'],
            })
        )

        # Update impact tracking
        self._update_impact_tracking(fund_id, amount, priority)

        return allocation

    def veto_allocation(
        self,
        allocation_id: str,
        vetoed_by: str,  # Steward user ID
        veto_reason: str
    ) -> None:
        """
        Veto an allocation within the 24-hour window.
        """
        allocation = self.repo.get_allocation(allocation_id)
        if not allocation:
            raise ValueError(f"Allocation {allocation_id} not found")

        # Check veto window
        if datetime.now(UTC) > allocation.veto_deadline:
            raise ValueError("Veto window has expired")

        # Check not already vetoed
        if allocation.vetoed:
            raise ValueError("Allocation already vetoed")

        # Check not same steward who allocated
        if allocation.allocated_by == vetoed_by:
            raise ValueError("Cannot veto your own allocation")

        # Veto the allocation
        self.repo.veto_allocation(allocation_id, vetoed_by, veto_reason)

        # Refund to Memorial Fund
        fund = self.repo.get_memorial_fund(allocation.fund_id)
        if fund:
            new_balance = fund.current_balance + allocation.amount
            self.repo.update_memorial_fund_balance(allocation.fund_id, new_balance)

        # Update impact tracking - record refund
        self._update_impact_tracking_refund(allocation.fund_id, allocation.amount)

        # Log audit
        self._log_audit(
            allocation_id=allocation_id,
            action=AuditAction.VETOED,
            actor_id=vetoed_by,
            actor_role='steward',
            details=json.dumps({
                'veto_reason': veto_reason,
                'refunded_amount': allocation.amount,
            })
        )

        return self.repo.get_allocation(allocation_id)

    def refund_allocation(
        self,
        allocation_id: str,
        refund_reason: str
    ) -> None:
        """
        Refund an allocation (e.g., proposal rejected).
        """
        allocation = self.repo.get_allocation(allocation_id)
        if not allocation:
            raise ValueError(f"Allocation {allocation_id} not found")

        if allocation.status != AllocationStatus.ACTIVE:
            raise ValueError(f"Cannot refund allocation with status {allocation.status}")

        # Refund to Memorial Fund
        fund = self.repo.get_memorial_fund(allocation.fund_id)
        if fund:
            new_balance = fund.current_balance + allocation.amount
            self.repo.update_memorial_fund_balance(allocation.fund_id, new_balance)

        # Mark as refunded
        self.repo.refund_allocation(allocation_id, refund_reason)

        # Update impact tracking - record refund
        self._update_impact_tracking_refund(allocation.fund_id, allocation.amount)

        # Log audit
        self._log_audit(
            allocation_id=allocation_id,
            action=AuditAction.REFUNDED,
            actor_id='system',
            actor_role='system',
            details=json.dumps({
                'refund_reason': refund_reason,
                'refunded_amount': allocation.amount,
            })
        )

    def complete_allocation(
        self,
        allocation_id: str,
        proposal_status: ProposalStatus
    ) -> GhostReputationAllocation:
        """
        Mark allocation as completed (proposal implemented).
        """
        allocation = self.repo.get_allocation(allocation_id)
        if not allocation:
            raise ValueError(f"Allocation {allocation_id} not found")

        # Mark as completed
        self.repo.complete_allocation(allocation_id)

        # Update attribution status
        attributions = self.repo.get_attributions_for_proposal(allocation.proposal_id)
        for attr in attributions:
            if attr.allocation_id == allocation_id:
                self.repo.update_attribution_status(attr.id, proposal_status)

        # Update impact tracking
        tracking = self.repo.get_impact_tracking(allocation.fund_id)
        if tracking:
            if proposal_status == ProposalStatus.IMPLEMENTED:
                tracking.proposals_implemented += 1
            elif proposal_status == ProposalStatus.APPROVED:
                tracking.proposals_approved += 1

            tracking.last_updated = datetime.now(UTC)
            self.repo.create_or_update_impact_tracking(tracking)

        # Log audit
        self._log_audit(
            allocation_id=allocation_id,
            action=AuditAction.COMPLETED,
            actor_id='system',
            actor_role='system',
            details=json.dumps({
                'proposal_status': proposal_status.value,
            })
        )

        return self.repo.get_allocation(allocation_id)

    # ===== Queries and Reporting =====

    def get_fund_impact(self, fund_id: str) -> Optional[Dict[str, Any]]:
        """Get impact metrics for a Memorial Fund."""
        fund = self.repo.get_memorial_fund(fund_id)
        if not fund:
            return None

        tracking = self.repo.get_impact_tracking(fund_id)
        attributions = self.repo.get_attributions_for_fund(fund_id)
        allocations = self.repo.list_allocations_for_fund(fund_id)

        return {
            'fund': {
                'id': fund.id,
                'ancestor_name': fund.departed_user_name,
                'initial_reputation': fund.initial_reputation,
                'current_balance': fund.current_balance,
                'created_at': fund.created_at.isoformat(),
            },
            'impact': {
                'total_allocated': tracking.total_allocated if tracking else 0.0,
                'total_refunded': tracking.total_refunded if tracking else 0.0,
                'proposals_boosted': tracking.proposals_boosted if tracking else 0,
                'proposals_approved': tracking.proposals_approved if tracking else 0,
                'proposals_implemented': tracking.proposals_implemented if tracking else 0,
                'new_members_helped': tracking.new_members_helped if tracking else 0,
                'controversial_proposals_boosted': tracking.controversial_proposals_boosted if tracking else 0,
            },
            'attributions': [
                {
                    'proposal_id': attr.proposal_id,
                    'reputation_amount': attr.reputation_amount,
                    'proposal_status': attr.proposal_status.value,
                    'attributed_at': attr.attributed_at.isoformat(),
                }
                for attr in attributions
            ],
            'allocations': [
                {
                    'id': alloc.id,
                    'proposal_id': alloc.proposal_id,
                    'amount': alloc.amount,
                    'allocated_by': alloc.allocated_by,
                    'reason': alloc.reason,
                    'status': alloc.status.value,
                    'allocated_at': alloc.allocated_at.isoformat(),
                }
                for alloc in allocations
            ],
        }

    def get_proposal_ancestors(self, proposal_id: str) -> List[Dict[str, Any]]:
        """Get all ancestors who boosted a proposal."""
        attributions = self.repo.get_attributions_for_proposal(proposal_id)

        return [
            {
                'ancestor_name': attr.ancestor_name,
                'reputation_amount': attr.reputation_amount,
                'attributed_at': attr.attributed_at.isoformat(),
                'fund_id': attr.fund_id,
            }
            for attr in attributions
        ]

    def get_allocations_pending_veto(self) -> List[GhostReputationAllocation]:
        """Get allocations still within veto window."""
        return self.repo.get_allocations_pending_veto()

    def get_audit_logs(self, allocation_id: str) -> List[AllocationAuditLog]:
        """Get audit logs for an allocation (transparency)."""
        return self.repo.get_audit_logs_for_allocation(allocation_id)

    def get_departure_record(self, user_id: str) -> Optional[UserDepartureRecord]:
        """Get the departure record for a user."""
        return self.repo.get_departure_record_by_user(user_id)

    def get_impact_tracking(self, fund_id: str) -> Optional[MemorialImpactTracking]:
        """Get impact tracking for a memorial fund."""
        return self.repo.get_impact_tracking(fund_id)

    def get_allocation(self, allocation_id: str) -> Optional[GhostReputationAllocation]:
        """Get a specific allocation by ID."""
        return self.repo.get_allocation(allocation_id)

    def get_allocation_audit_logs(self, allocation_id: str) -> List[AllocationAuditLog]:
        """Get audit logs for an allocation (alias for get_audit_logs)."""
        return self.get_audit_logs(allocation_id)

    def get_allocation_priority(self, allocation_id: str) -> Optional[AllocationPriority]:
        """Get the priority information for an allocation."""
        return self.repo.get_allocation_priority(allocation_id)

    # ===== Private Helper Methods =====

    def _calculate_priority(self, proposal_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate priority score for an allocation.

        Priority goes to:
        - New members (<3 months)
        - Members with low reputation
        - Controversial proposals
        - Marginalized identity groups (self-disclosed)
        """
        score = 0

        # New member check (<3 months) - support both naming conventions
        is_new_member = (
            proposal_metadata.get('is_new_member', False) or
            proposal_metadata.get('author_tenure_months', 999) < 3
        )
        if is_new_member:
            score += 3

        # Low reputation check - support both naming conventions
        has_low_reputation = (
            proposal_metadata.get('has_low_reputation', False) or
            proposal_metadata.get('author_reputation', 999) < 50
        )
        if has_low_reputation:
            score += 2

        # Controversial flag - support both naming conventions
        is_controversial = (
            proposal_metadata.get('is_controversial', False) or
            proposal_metadata.get('flagged_controversial', False)
        )
        if is_controversial:
            score += 2

        # Marginalized identity (self-disclosed) - support both naming conventions
        is_marginalized_identity = (
            proposal_metadata.get('is_marginalized_identity', False) or
            proposal_metadata.get('author_marginalized_identity', False)
        )
        if is_marginalized_identity:
            score += 3

        return {
            'is_new_member': is_new_member,
            'has_low_reputation': has_low_reputation,
            'is_controversial': is_controversial,
            'is_marginalized_identity': is_marginalized_identity,
            'priority_score': score,
        }

    def _update_impact_tracking(
        self,
        fund_id: str,
        amount: float,
        priority: Dict[str, Any]
    ) -> None:
        """Update impact tracking after allocation."""
        tracking = self.repo.get_impact_tracking(fund_id)
        if not tracking:
            tracking = MemorialImpactTracking(
                id=str(uuid.uuid4()),
                fund_id=fund_id,
                total_allocated=0.0,
                total_refunded=0.0,
                proposals_boosted=0,
                proposals_approved=0,
                proposals_implemented=0,
                new_members_helped=0,
                controversial_proposals_boosted=0,
                last_updated=datetime.now(UTC),
            )

        tracking.total_allocated += amount
        tracking.proposals_boosted += 1

        if priority['is_new_member']:
            tracking.new_members_helped += 1

        if priority['is_controversial']:
            tracking.controversial_proposals_boosted += 1

        tracking.last_updated = datetime.now(UTC)

        self.repo.create_or_update_impact_tracking(tracking)

    def _update_impact_tracking_refund(
        self,
        fund_id: str,
        amount: float
    ) -> None:
        """Update impact tracking after refund (veto or family removal)."""
        tracking = self.repo.get_impact_tracking(fund_id)
        if tracking:
            tracking.total_allocated -= amount  # Subtract from allocated
            tracking.total_refunded += amount
            tracking.last_updated = datetime.now(UTC)
            self.repo.create_or_update_impact_tracking(tracking)

    def _log_audit(
        self,
        allocation_id: str,
        action: AuditAction,
        actor_id: str,
        actor_role: str,
        details: Optional[str] = None
    ) -> None:
        """Create an audit log entry."""
        log = AllocationAuditLog(
            id=str(uuid.uuid4()),
            allocation_id=allocation_id,
            action=action,
            actor_id=actor_id,
            actor_role=actor_role,
            details=details,
            logged_at=datetime.now(UTC),
        )
        self.repo.create_audit_log(log)
