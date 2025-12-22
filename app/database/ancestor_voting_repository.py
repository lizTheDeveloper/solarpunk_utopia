"""Repository for Ancestor Voting data access

'The only good authority is a dead one.' - Mikhail Bakunin

When members leave, their reputation becomes a Memorial Fund that stewards
can use to amplify marginalized voices.
"""
import sqlite3
import json
from typing import List, Optional
from datetime import datetime, timedelta, UTC
import uuid

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


class AncestorVotingRepository:
    """Database access for Ancestor Voting."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ===== Memorial Funds =====

    def create_memorial_fund(self, fund: MemorialFund) -> MemorialFund:
        """Create a new Memorial Fund."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO memorial_funds (
                id, created_from_user_id, departed_user_name,
                departed_user_display_name, initial_reputation,
                current_balance, created_at, updated_at,
                family_requested_removal, removal_requested_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            fund.id,
            fund.created_from_user_id,
            fund.departed_user_name,
            fund.departed_user_display_name,
            fund.initial_reputation,
            fund.current_balance,
            fund.created_at.isoformat(),
            fund.updated_at.isoformat(),
            1 if fund.family_requested_removal else 0,
            fund.removal_requested_at.isoformat() if fund.removal_requested_at else None,
        ))

        conn.commit()
        conn.close()
        return fund

    def get_memorial_fund(self, fund_id: str) -> Optional[MemorialFund]:
        """Get a Memorial Fund by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM memorial_funds WHERE id = ?", (fund_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_memorial_fund(row)

    def get_memorial_fund_by_user(self, user_id: str) -> Optional[MemorialFund]:
        """Get Memorial Fund for a departed user."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM memorial_funds WHERE created_from_user_id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_memorial_fund(row)

    def list_memorial_funds(
        self,
        limit: int = 50,
        offset: int = 0,
        exclude_requested_removal: bool = True
    ) -> List[MemorialFund]:
        """List all Memorial Funds."""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM memorial_funds"
        params: List = []

        if exclude_requested_removal:
            query += " WHERE family_requested_removal = 0"

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_memorial_fund(row) for row in rows]

    def update_memorial_fund_balance(
        self,
        fund_id: str,
        new_balance: float
    ) -> None:
        """Update Memorial Fund balance."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE memorial_funds
            SET current_balance = ?, updated_at = ?
            WHERE id = ?
        """, (new_balance, datetime.now(UTC).isoformat(), fund_id))

        conn.commit()
        conn.close()

    def request_fund_removal(self, fund_id: str) -> None:
        """Mark Memorial Fund for removal (family request)."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE memorial_funds
            SET family_requested_removal = 1,
                removal_requested_at = ?,
                updated_at = ?
            WHERE id = ?
        """, (datetime.now(UTC).isoformat(), datetime.now(UTC).isoformat(), fund_id))

        conn.commit()
        conn.close()

    # ===== Ghost Reputation Allocations =====

    def create_allocation(
        self,
        allocation: GhostReputationAllocation
    ) -> GhostReputationAllocation:
        """Create a new Ghost Reputation allocation."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO ghost_reputation_allocations (
                id, fund_id, proposal_id, amount, allocated_by,
                reason, status, refunded, refund_reason,
                allocated_at, refunded_at, completed_at,
                veto_deadline, vetoed, vetoed_by, veto_reason, vetoed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            allocation.id,
            allocation.fund_id,
            allocation.proposal_id,
            allocation.amount,
            allocation.allocated_by,
            allocation.reason,
            allocation.status.value,
            1 if allocation.refunded else 0,
            allocation.refund_reason,
            allocation.allocated_at.isoformat(),
            allocation.refunded_at.isoformat() if allocation.refunded_at else None,
            allocation.completed_at.isoformat() if allocation.completed_at else None,
            allocation.veto_deadline.isoformat(),
            1 if allocation.vetoed else 0,
            allocation.vetoed_by,
            allocation.veto_reason,
            allocation.vetoed_at.isoformat() if allocation.vetoed_at else None,
        ))

        conn.commit()
        conn.close()
        return allocation

    def get_allocation(self, allocation_id: str) -> Optional[GhostReputationAllocation]:
        """Get an allocation by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM ghost_reputation_allocations WHERE id = ?",
            (allocation_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_allocation(row)

    def list_allocations_for_fund(
        self,
        fund_id: str,
        limit: int = 50
    ) -> List[GhostReputationAllocation]:
        """List allocations for a specific Memorial Fund."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM ghost_reputation_allocations
            WHERE fund_id = ?
            ORDER BY allocated_at DESC
            LIMIT ?
        """, (fund_id, limit))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_allocation(row) for row in rows]

    def list_allocations_for_proposal(
        self,
        proposal_id: str
    ) -> List[GhostReputationAllocation]:
        """List allocations for a specific proposal."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM ghost_reputation_allocations
            WHERE proposal_id = ?
            ORDER BY allocated_at DESC
        """, (proposal_id,))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_allocation(row) for row in rows]

    def get_allocations_pending_veto(self) -> List[GhostReputationAllocation]:
        """Get allocations still within veto window."""
        conn = self._get_connection()
        cursor = conn.cursor()

        now = datetime.now(UTC).isoformat()

        cursor.execute("""
            SELECT * FROM ghost_reputation_allocations
            WHERE status = 'active'
            AND vetoed = 0
            AND veto_deadline > ?
            ORDER BY veto_deadline ASC
        """, (now,))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_allocation(row) for row in rows]

    def veto_allocation(
        self,
        allocation_id: str,
        vetoed_by: str,
        veto_reason: str
    ) -> None:
        """Veto an allocation."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE ghost_reputation_allocations
            SET vetoed = 1,
                vetoed_by = ?,
                veto_reason = ?,
                vetoed_at = ?,
                status = 'vetoed'
            WHERE id = ?
        """, (vetoed_by, veto_reason, datetime.now(UTC).isoformat(), allocation_id))

        conn.commit()
        conn.close()

    def refund_allocation(
        self,
        allocation_id: str,
        refund_reason: str
    ) -> None:
        """Refund an allocation."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE ghost_reputation_allocations
            SET refunded = 1,
                refund_reason = ?,
                refunded_at = ?,
                status = 'refunded'
            WHERE id = ?
        """, (refund_reason, datetime.now(UTC).isoformat(), allocation_id))

        conn.commit()
        conn.close()

    def complete_allocation(self, allocation_id: str) -> None:
        """Mark allocation as completed."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE ghost_reputation_allocations
            SET status = 'completed',
                completed_at = ?
            WHERE id = ?
        """, (datetime.now(UTC).isoformat(), allocation_id))

        conn.commit()
        conn.close()

    # ===== Proposal Ancestor Attribution =====

    def create_attribution(
        self,
        attribution: ProposalAncestorAttribution
    ) -> ProposalAncestorAttribution:
        """Create a new proposal ancestor attribution."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO proposal_ancestor_attribution (
                id, proposal_id, allocation_id, fund_id,
                ancestor_name, reputation_amount,
                proposal_status, attributed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            attribution.id,
            attribution.proposal_id,
            attribution.allocation_id,
            attribution.fund_id,
            attribution.ancestor_name,
            attribution.reputation_amount,
            attribution.proposal_status.value,
            attribution.attributed_at.isoformat(),
        ))

        conn.commit()
        conn.close()
        return attribution

    def get_attributions_for_proposal(
        self,
        proposal_id: str
    ) -> List[ProposalAncestorAttribution]:
        """Get all attributions for a proposal."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM proposal_ancestor_attribution
            WHERE proposal_id = ?
            ORDER BY attributed_at DESC
        """, (proposal_id,))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_attribution(row) for row in rows]

    def get_attributions_for_fund(
        self,
        fund_id: str
    ) -> List[ProposalAncestorAttribution]:
        """Get all attributions for a Memorial Fund."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM proposal_ancestor_attribution
            WHERE fund_id = ?
            ORDER BY attributed_at DESC
        """, (fund_id,))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_attribution(row) for row in rows]

    def update_attribution_status(
        self,
        attribution_id: str,
        new_status: ProposalStatus
    ) -> None:
        """Update attribution proposal status."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE proposal_ancestor_attribution
            SET proposal_status = ?
            WHERE id = ?
        """, (new_status.value, attribution_id))

        conn.commit()
        conn.close()

    # ===== User Departure Records =====

    def create_departure_record(
        self,
        record: UserDepartureRecord
    ) -> UserDepartureRecord:
        """Create a new user departure record."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO user_departure_records (
                id, user_id, departure_type, departure_reason,
                final_reputation, memorial_fund_id,
                private_data_purged, purged_at, public_contributions_retained,
                departed_at, recorded_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.id,
            record.user_id,
            record.departure_type.value,
            record.departure_reason,
            record.final_reputation,
            record.memorial_fund_id,
            1 if record.private_data_purged else 0,
            record.purged_at.isoformat() if record.purged_at else None,
            1 if record.public_contributions_retained else 0,
            record.departed_at.isoformat(),
            record.recorded_by,
        ))

        conn.commit()
        conn.close()
        return record

    def get_departure_record(self, record_id: str) -> Optional[UserDepartureRecord]:
        """Get a departure record by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM user_departure_records WHERE id = ?", (record_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_departure_record(row)

    def get_departure_record_by_user(
        self,
        user_id: str
    ) -> Optional[UserDepartureRecord]:
        """Get departure record for a specific user."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM user_departure_records WHERE user_id = ? ORDER BY departed_at DESC LIMIT 1",
            (user_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_departure_record(row)

    # ===== Allocation Priorities =====

    def create_allocation_priority(
        self,
        priority: AllocationPriority
    ) -> AllocationPriority:
        """Create allocation priority record."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO allocation_priorities (
                id, allocation_id,
                is_new_member, has_low_reputation,
                is_controversial, is_marginalized_identity,
                priority_score, calculated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            priority.id,
            priority.allocation_id,
            1 if priority.is_new_member else 0,
            1 if priority.has_low_reputation else 0,
            1 if priority.is_controversial else 0,
            1 if priority.is_marginalized_identity else 0,
            priority.priority_score,
            priority.calculated_at.isoformat(),
        ))

        conn.commit()
        conn.close()
        return priority

    def get_allocation_priority(
        self,
        allocation_id: str
    ) -> Optional[AllocationPriority]:
        """Get priority for an allocation."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM allocation_priorities WHERE allocation_id = ?",
            (allocation_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_allocation_priority(row)

    # ===== Memorial Impact Tracking =====

    def create_or_update_impact_tracking(
        self,
        tracking: MemorialImpactTracking
    ) -> MemorialImpactTracking:
        """Create or update impact tracking for a fund."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Try to update first
        cursor.execute("""
            UPDATE memorial_impact_tracking
            SET total_allocated = ?,
                total_refunded = ?,
                proposals_boosted = ?,
                proposals_approved = ?,
                proposals_implemented = ?,
                new_members_helped = ?,
                controversial_proposals_boosted = ?,
                last_updated = ?
            WHERE fund_id = ?
        """, (
            tracking.total_allocated,
            tracking.total_refunded,
            tracking.proposals_boosted,
            tracking.proposals_approved,
            tracking.proposals_implemented,
            tracking.new_members_helped,
            tracking.controversial_proposals_boosted,
            tracking.last_updated.isoformat(),
            tracking.fund_id,
        ))

        # If no rows updated, insert
        if cursor.rowcount == 0:
            cursor.execute("""
                INSERT INTO memorial_impact_tracking (
                    id, fund_id,
                    total_allocated, total_refunded,
                    proposals_boosted, proposals_approved, proposals_implemented,
                    new_members_helped, controversial_proposals_boosted,
                    last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tracking.id,
                tracking.fund_id,
                tracking.total_allocated,
                tracking.total_refunded,
                tracking.proposals_boosted,
                tracking.proposals_approved,
                tracking.proposals_implemented,
                tracking.new_members_helped,
                tracking.controversial_proposals_boosted,
                tracking.last_updated.isoformat(),
            ))

        conn.commit()
        conn.close()
        return tracking

    def get_impact_tracking(self, fund_id: str) -> Optional[MemorialImpactTracking]:
        """Get impact tracking for a fund."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM memorial_impact_tracking WHERE fund_id = ?",
            (fund_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_impact_tracking(row)

    # ===== Allocation Audit Log =====

    def create_audit_log(self, log: AllocationAuditLog) -> AllocationAuditLog:
        """Create an audit log entry."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO allocation_audit_log (
                id, allocation_id, action, actor_id, actor_role,
                details, logged_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            log.id,
            log.allocation_id,
            log.action.value,
            log.actor_id,
            log.actor_role,
            log.details,
            log.logged_at.isoformat(),
        ))

        conn.commit()
        conn.close()
        return log

    def get_audit_logs_for_allocation(
        self,
        allocation_id: str
    ) -> List[AllocationAuditLog]:
        """Get all audit logs for an allocation."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM allocation_audit_log
            WHERE allocation_id = ?
            ORDER BY logged_at ASC
        """, (allocation_id,))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_audit_log(row) for row in rows]

    # ===== Private Helper Methods =====

    def _row_to_memorial_fund(self, row: sqlite3.Row) -> MemorialFund:
        """Convert database row to MemorialFund."""
        return MemorialFund(
            id=row['id'],
            created_from_user_id=row['created_from_user_id'],
            departed_user_name=row['departed_user_name'],
            departed_user_display_name=row['departed_user_display_name'],
            initial_reputation=row['initial_reputation'],
            current_balance=row['current_balance'],
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at']),
            family_requested_removal=bool(row['family_requested_removal']),
            removal_requested_at=datetime.fromisoformat(row['removal_requested_at']) if row['removal_requested_at'] else None,
        )

    def _row_to_allocation(self, row: sqlite3.Row) -> GhostReputationAllocation:
        """Convert database row to GhostReputationAllocation."""
        return GhostReputationAllocation(
            id=row['id'],
            fund_id=row['fund_id'],
            proposal_id=row['proposal_id'],
            amount=row['amount'],
            allocated_by=row['allocated_by'],
            reason=row['reason'],
            status=AllocationStatus(row['status']),
            refunded=bool(row['refunded']),
            refund_reason=row['refund_reason'],
            allocated_at=datetime.fromisoformat(row['allocated_at']),
            refunded_at=datetime.fromisoformat(row['refunded_at']) if row['refunded_at'] else None,
            completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None,
            veto_deadline=datetime.fromisoformat(row['veto_deadline']),
            vetoed=bool(row['vetoed']),
            vetoed_by=row['vetoed_by'],
            veto_reason=row['veto_reason'],
            vetoed_at=datetime.fromisoformat(row['vetoed_at']) if row['vetoed_at'] else None,
        )

    def _row_to_attribution(self, row: sqlite3.Row) -> ProposalAncestorAttribution:
        """Convert database row to ProposalAncestorAttribution."""
        return ProposalAncestorAttribution(
            id=row['id'],
            proposal_id=row['proposal_id'],
            allocation_id=row['allocation_id'],
            fund_id=row['fund_id'],
            ancestor_name=row['ancestor_name'],
            reputation_amount=row['reputation_amount'],
            proposal_status=ProposalStatus(row['proposal_status']),
            attributed_at=datetime.fromisoformat(row['attributed_at']),
        )

    def _row_to_departure_record(self, row: sqlite3.Row) -> UserDepartureRecord:
        """Convert database row to UserDepartureRecord."""
        return UserDepartureRecord(
            id=row['id'],
            user_id=row['user_id'],
            departure_type=DepartureType(row['departure_type']),
            departure_reason=row['departure_reason'],
            final_reputation=row['final_reputation'],
            memorial_fund_id=row['memorial_fund_id'],
            private_data_purged=bool(row['private_data_purged']),
            purged_at=datetime.fromisoformat(row['purged_at']) if row['purged_at'] else None,
            public_contributions_retained=bool(row['public_contributions_retained']),
            departed_at=datetime.fromisoformat(row['departed_at']),
            recorded_by=row['recorded_by'],
        )

    def _row_to_allocation_priority(self, row: sqlite3.Row) -> AllocationPriority:
        """Convert database row to AllocationPriority."""
        return AllocationPriority(
            id=row['id'],
            allocation_id=row['allocation_id'],
            is_new_member=bool(row['is_new_member']),
            has_low_reputation=bool(row['has_low_reputation']),
            is_controversial=bool(row['is_controversial']),
            is_marginalized_identity=bool(row['is_marginalized_identity']),
            priority_score=row['priority_score'],
            calculated_at=datetime.fromisoformat(row['calculated_at']),
        )

    def _row_to_impact_tracking(self, row: sqlite3.Row) -> MemorialImpactTracking:
        """Convert database row to MemorialImpactTracking."""
        return MemorialImpactTracking(
            id=row['id'],
            fund_id=row['fund_id'],
            total_allocated=row['total_allocated'],
            total_refunded=row['total_refunded'],
            proposals_boosted=row['proposals_boosted'],
            proposals_approved=row['proposals_approved'],
            proposals_implemented=row['proposals_implemented'],
            new_members_helped=row['new_members_helped'],
            controversial_proposals_boosted=row['controversial_proposals_boosted'],
            last_updated=datetime.fromisoformat(row['last_updated']),
        )

    def _row_to_audit_log(self, row: sqlite3.Row) -> AllocationAuditLog:
        """Convert database row to AllocationAuditLog."""
        return AllocationAuditLog(
            id=row['id'],
            allocation_id=row['allocation_id'],
            action=AuditAction(row['action']),
            actor_id=row['actor_id'],
            actor_role=row['actor_role'],
            details=row['details'],
            logged_at=datetime.fromisoformat(row['logged_at']),
        )
