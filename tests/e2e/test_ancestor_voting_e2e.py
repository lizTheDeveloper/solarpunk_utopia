"""
End-to-End tests for Ancestor Voting / Memorial Funds.

Tests the complete flow from member departure through ghost reputation allocation.

'The only good authority is a dead one.' - Mikhail Bakunin

Test scenarios (from GAP-E2E proposal):
WHEN community member departs (natural/migration/injury)
THEN memorial fund created from reputation
WHEN new proposal matches departed member's values
THEN ghost reputation allocated (by threshold signature)
WHEN 3-of-5 stewards approve allocation
THEN proposal receives ghost votes
WHEN family requests removal
THEN memorial fund deleted, ghost votes removed
"""

import pytest
import os
import tempfile
from datetime import datetime, timedelta

from app.services.ancestor_voting_service import AncestorVotingService
from app.models.ancestor_voting import (
    DepartureType,
    AllocationStatus,
    ProposalStatus,
    AuditAction,
)


class TestAncestorVotingE2E:
    """End-to-end Ancestor Voting flow tests"""

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
        with open("app/database/migrations/008_add_ancestor_voting.sql") as f:
            migration_sql = f.read()
            # Execute each statement separately (can't use executescript with PRAGMA)
            for statement in migration_sql.split(';'):
                if statement.strip():
                    cursor.execute(statement)

        conn.commit()
        conn.close()

        # Create service
        self.service = AncestorVotingService(self.db_path)

        yield

        # Cleanup
        os.unlink(self.db_path)

    def test_create_memorial_fund_on_death(self):
        """
        E2E Test 1: Create Memorial Fund when member dies

        WHEN community member departs (death)
        THEN memorial fund created from reputation
        AND departure record created
        AND impact tracking initialized
        """
        # Action: Member departs (death)
        fund = self.service.create_memorial_fund_on_departure(
            user_id="user-alice",
            user_name="Alice Johnson",
            display_name="Alice",
            final_reputation=0.85,
            departure_type=DepartureType.DEATH,
            departure_reason="Passed away in hospice care, surrounded by community",
            recorded_by="steward-bob"
        )

        # Verify: Memorial fund created
        assert fund is not None
        assert fund.created_from_user_id == "user-alice"
        assert fund.departed_user_name == "Alice Johnson"
        assert fund.departed_user_display_name == "Alice"
        assert fund.initial_reputation == 0.85
        assert fund.current_balance == 0.85
        assert fund.family_requested_removal is False

        # Verify: Departure record exists
        departure = self.service.get_departure_record("user-alice")
        assert departure is not None
        assert departure.departure_type == DepartureType.DEATH
        assert departure.final_reputation == 0.85
        assert departure.memorial_fund_id == fund.id
        assert departure.recorded_by == "steward-bob"

        # Verify: Impact tracking initialized
        tracking = self.service.get_impact_tracking(fund.id)
        assert tracking is not None
        assert tracking.total_allocated == 0.0
        assert tracking.proposals_boosted == 0

    def test_allocate_ghost_reputation_to_proposal(self):
        """
        E2E Test 2: Allocate ghost reputation to boost a proposal

        WHEN new proposal matches departed member's values
        THEN steward can allocate ghost reputation
        AND proposal receives ghost votes
        AND allocation has veto window
        """
        # Setup: Create memorial fund
        fund = self.service.create_memorial_fund_on_departure(
            user_id="user-alice",
            user_name="Alice Johnson",
            display_name="Alice",
            final_reputation=0.85,
            departure_type=DepartureType.DEATH,
        )

        # Action: Steward allocates ghost reputation to proposal
        allocation = self.service.allocate_ghost_reputation(
            fund_id=fund.id,
            proposal_id="proposal-community-garden",
            amount=0.20,  # 20% of fund
            allocated_by="steward-bob",
            reason="Alice was passionate about urban agriculture and teaching permaculture to youth. This community garden proposal aligns perfectly with her values.",
            proposal_metadata={
                "title": "Community Garden at 5th & Main",
                "proposer_id": "user-carol",
                "is_new_member": True,
                "is_controversial": False,
            }
        )

        # Verify: Allocation created
        assert allocation is not None
        assert allocation.fund_id == fund.id
        assert allocation.proposal_id == "proposal-community-garden"
        assert allocation.amount == 0.20
        assert allocation.allocated_by == "steward-bob"
        assert allocation.status == AllocationStatus.ACTIVE
        assert allocation.vetoed is False

        # Verify: Veto deadline is 24 hours from now
        veto_window = (allocation.veto_deadline - allocation.allocated_at).total_seconds()
        assert abs(veto_window - 24 * 3600) < 60  # Within 1 minute

        # Verify: Fund balance decreased
        updated_fund = self.service.get_memorial_fund(fund.id)
        assert updated_fund.current_balance == 0.65  # 0.85 - 0.20

        # Verify: Impact tracking updated
        tracking = self.service.get_impact_tracking(fund.id)
        assert tracking.total_allocated == 0.20
        assert tracking.proposals_boosted == 1
        assert tracking.new_members_helped == 1

        # Verify: Audit log created
        logs = self.service.get_allocation_audit_logs(allocation.id)
        assert len(logs) == 1
        assert logs[0].action == AuditAction.ALLOCATED
        assert logs[0].actor_id == "steward-bob"

    def test_veto_allocation_within_window(self):
        """
        E2E Test 3: Veto allocation within 24-hour window

        WHEN other steward disagrees with allocation
        AND veto window still open
        THEN steward can veto allocation
        AND ghost reputation refunded to fund
        """
        # Setup: Create fund and allocation
        fund = self.service.create_memorial_fund_on_departure(
            user_id="user-alice",
            user_name="Alice Johnson",
            display_name="Alice",
            final_reputation=0.85,
            departure_type=DepartureType.DEATH,
        )
        allocation = self.service.allocate_ghost_reputation(
            fund_id=fund.id,
            proposal_id="proposal-xyz",
            amount=0.15,
            allocated_by="steward-bob",
            reason="Test allocation",
            proposal_metadata={"proposer_id": "user-carol"}
        )

        # Action: Another steward vetoes
        vetoed_allocation = self.service.veto_allocation(
            allocation_id=allocation.id,
            vetoed_by="steward-dave",
            reason="This doesn't align with Alice's values - she opposed corporate partnerships"
        )

        # Verify: Allocation vetoed
        assert vetoed_allocation is not None
        assert vetoed_allocation.vetoed is True
        assert vetoed_allocation.vetoed_by == "steward-dave"
        assert vetoed_allocation.veto_reason == "This doesn't align with Alice's values - she opposed corporate partnerships"
        assert vetoed_allocation.status == AllocationStatus.VETOED

        # Verify: Fund balance refunded
        updated_fund = self.service.get_memorial_fund(fund.id)
        assert updated_fund.current_balance == 0.85  # Full amount refunded

        # Verify: Audit log created
        logs = self.service.get_allocation_audit_logs(allocation.id)
        assert any(log.action == AuditAction.VETOED for log in logs)

    def test_complete_allocation_after_proposal_approved(self):
        """
        E2E Test 4: Complete allocation when proposal is approved

        WHEN proposal with ghost reputation is approved
        THEN allocation marked as completed
        AND impact metrics updated
        """
        # Setup: Create fund and allocation
        fund = self.service.create_memorial_fund_on_departure(
            user_id="user-alice",
            user_name="Alice Johnson",
            display_name="Alice",
            final_reputation=0.85,
            departure_type=DepartureType.DEATH,
        )
        allocation = self.service.allocate_ghost_reputation(
            fund_id=fund.id,
            proposal_id="proposal-approved",
            amount=0.10,
            allocated_by="steward-bob",
            reason="Test allocation for approved proposal",
            proposal_metadata={"proposer_id": "user-carol"}
        )

        # Action: Mark proposal as approved
        completed_allocation = self.service.complete_allocation(
            allocation_id=allocation.id,
            proposal_status=ProposalStatus.APPROVED
        )

        # Verify: Allocation completed
        assert completed_allocation is not None
        assert completed_allocation.status == AllocationStatus.COMPLETED
        assert completed_allocation.completed_at is not None

        # Verify: Impact tracking updated
        tracking = self.service.get_impact_tracking(fund.id)
        assert tracking.proposals_approved == 1

        # Verify: Audit log created
        logs = self.service.get_allocation_audit_logs(allocation.id)
        assert any(log.action == AuditAction.COMPLETED for log in logs)

    def test_family_requests_memorial_removal(self):
        """
        E2E Test 5: Family requests memorial fund removal

        WHEN family requests removal of memorial fund
        THEN fund marked for removal
        AND no new allocations allowed
        AND existing allocations refunded
        """
        # Setup: Create fund with allocation
        fund = self.service.create_memorial_fund_on_departure(
            user_id="user-alice",
            user_name="Alice Johnson",
            display_name="Alice",
            final_reputation=0.85,
            departure_type=DepartureType.DEATH,
        )
        allocation = self.service.allocate_ghost_reputation(
            fund_id=fund.id,
            proposal_id="proposal-test",
            amount=0.10,
            allocated_by="steward-bob",
            reason="Test allocation",
            proposal_metadata={"proposer_id": "user-carol"}
        )

        # Action: Family requests removal
        self.service.request_memorial_removal(fund_id=fund.id)

        # Verify: Fund marked for removal
        updated_fund = self.service.get_memorial_fund(fund.id)
        assert updated_fund.family_requested_removal is True
        assert updated_fund.removal_requested_at is not None

        # Verify: Active allocations refunded
        updated_allocation = self.service.get_allocation(allocation.id)
        assert updated_allocation.status == AllocationStatus.REFUNDED
        assert updated_allocation.refund_reason == "Family requested memorial removal"

        # Verify: No new allocations allowed
        with pytest.raises(ValueError, match="Memorial Fund removal requested"):
            self.service.allocate_ghost_reputation(
                fund_id=fund.id,
                proposal_id="proposal-new",
                amount=0.05,
                allocated_by="steward-bob",
                reason="This should fail",
                proposal_metadata={"proposer_id": "user-dave"}
            )

    def test_prioritize_marginalized_voices(self):
        """
        E2E Test 6: Ghost reputation prioritizes marginalized voices

        WHEN allocating to new member's proposal
        THEN allocation gets priority boost
        AND impact tracking reflects marginalized voice support
        """
        # Setup: Create fund
        fund = self.service.create_memorial_fund_on_departure(
            user_id="user-alice",
            user_name="Alice Johnson",
            display_name="Alice",
            final_reputation=0.85,
            departure_type=DepartureType.DEATH,
        )

        # Action: Allocate to new member's controversial proposal
        allocation = self.service.allocate_ghost_reputation(
            fund_id=fund.id,
            proposal_id="proposal-controversial",
            amount=0.15,
            allocated_by="steward-bob",
            reason="New member proposing police abolition - needs support",
            proposal_metadata={
                "proposer_id": "user-new",
                "is_new_member": True,  # <3 months
                "has_low_reputation": True,
                "is_controversial": True,
                "is_marginalized_identity": True,
            }
        )

        # Verify: Priority calculated
        priority = self.service.get_allocation_priority(allocation.id)
        assert priority is not None
        assert priority.is_new_member is True
        assert priority.has_low_reputation is True
        assert priority.is_controversial is True
        assert priority.is_marginalized_identity is True
        assert priority.priority_score > 0  # Higher score = higher priority

        # Verify: Impact tracking reflects marginalized support
        tracking = self.service.get_impact_tracking(fund.id)
        assert tracking.new_members_helped == 1
        assert tracking.controversial_proposals_boosted == 1

    def test_cannot_exceed_max_allocation_percentage(self):
        """
        E2E Test 7: Cannot allocate more than 20% to single proposal

        WHEN steward tries to allocate >20% of fund
        THEN allocation rejected
        AND fund balance unchanged
        """
        # Setup: Create fund
        fund = self.service.create_memorial_fund_on_departure(
            user_id="user-alice",
            user_name="Alice Johnson",
            display_name="Alice",
            final_reputation=0.85,
            departure_type=DepartureType.DEATH,
        )

        # Action: Try to allocate 25% (exceeds 20% limit)
        with pytest.raises(ValueError, match="Cannot allocate more than 20%"):
            self.service.allocate_ghost_reputation(
                fund_id=fund.id,
                proposal_id="proposal-greedy",
                amount=0.22,  # 26% of 0.85
                allocated_by="steward-bob",
                reason="This should fail",
                proposal_metadata={"proposer_id": "user-carol"}
            )

        # Verify: Fund balance unchanged
        unchanged_fund = self.service.get_memorial_fund(fund.id)
        assert unchanged_fund.current_balance == 0.85

    def test_voluntary_departure_creates_memorial(self):
        """
        E2E Test 8: Voluntary departure also creates memorial fund

        WHEN member voluntarily leaves network
        THEN memorial fund created from reputation
        AND marked as voluntary departure
        """
        # Action: Member voluntarily leaves
        fund = self.service.create_memorial_fund_on_departure(
            user_id="user-bob",
            user_name="Bob Smith",
            display_name="Bob",
            final_reputation=0.75,
            departure_type=DepartureType.VOLUNTARY,
            departure_reason="Moving to rural commune, no internet access",
            recorded_by="steward-alice"
        )

        # Verify: Fund created
        assert fund is not None
        assert fund.initial_reputation == 0.75

        # Verify: Departure type recorded
        departure = self.service.get_departure_record("user-bob")
        assert departure.departure_type == DepartureType.VOLUNTARY
        assert "rural commune" in departure.departure_reason

    def test_list_memorial_funds_excludes_removal_requested(self):
        """
        E2E Test 9: Listing funds excludes those with removal requests

        WHEN family has requested removal
        THEN fund not shown in public list
        AND still accessible by ID (for refund processing)
        """
        # Setup: Create two funds, one with removal request
        fund1 = self.service.create_memorial_fund_on_departure(
            user_id="user-alice",
            user_name="Alice",
            display_name="Alice",
            final_reputation=0.85,
            departure_type=DepartureType.DEATH,
        )
        fund2 = self.service.create_memorial_fund_on_departure(
            user_id="user-bob",
            user_name="Bob",
            display_name="Bob",
            final_reputation=0.75,
            departure_type=DepartureType.DEATH,
        )
        self.service.request_memorial_removal(fund1.id)

        # Action: List memorial funds
        funds = self.service.list_memorial_funds()

        # Verify: Only fund2 in list
        assert len(funds) == 1
        assert funds[0].id == fund2.id

        # Verify: fund1 still accessible by ID
        fund1_direct = self.service.get_memorial_fund(fund1.id)
        assert fund1_direct is not None
        assert fund1_direct.family_requested_removal is True

    def test_impact_tracking_aggregates_correctly(self):
        """
        E2E Test 10: Impact tracking aggregates allocation outcomes

        WHEN multiple allocations made with different outcomes
        THEN impact metrics correctly aggregated
        """
        # Setup: Create fund
        fund = self.service.create_memorial_fund_on_departure(
            user_id="user-alice",
            user_name="Alice",
            display_name="Alice",
            final_reputation=1.0,
            departure_type=DepartureType.DEATH,
        )

        # Action: Create multiple allocations with different outcomes
        alloc1 = self.service.allocate_ghost_reputation(
            fund_id=fund.id,
            proposal_id="proposal-1",
            amount=0.10,
            allocated_by="steward-bob",
            reason="Test 1",
            proposal_metadata={"proposer_id": "user-1", "is_new_member": True}
        )
        self.service.complete_allocation(alloc1.id, ProposalStatus.APPROVED)

        alloc2 = self.service.allocate_ghost_reputation(
            fund_id=fund.id,
            proposal_id="proposal-2",
            amount=0.10,
            allocated_by="steward-bob",
            reason="Test 2",
            proposal_metadata={"proposer_id": "user-2"}
        )
        self.service.complete_allocation(alloc2.id, ProposalStatus.IMPLEMENTED)

        alloc3 = self.service.allocate_ghost_reputation(
            fund_id=fund.id,
            proposal_id="proposal-3",
            amount=0.10,
            allocated_by="steward-bob",
            reason="Test 3",
            proposal_metadata={"proposer_id": "user-3", "is_controversial": True}
        )
        self.service.veto_allocation(alloc3.id, "steward-dave", "Doesn't fit")

        # Verify: Impact metrics correct
        tracking = self.service.get_impact_tracking(fund.id)
        assert tracking.total_allocated == 0.20  # alloc1 + alloc2
        assert tracking.total_refunded == 0.10  # alloc3
        assert tracking.proposals_boosted == 3
        assert tracking.proposals_approved == 1
        assert tracking.proposals_implemented == 1
        assert tracking.new_members_helped == 1
        assert tracking.controversial_proposals_boosted == 1

    def test_audit_log_tracks_all_actions(self):
        """
        E2E Test 11: Audit log tracks all allocation actions

        WHEN allocation created, vetoed, or completed
        THEN each action logged
        AND logs retrievable chronologically
        """
        # Setup: Create fund and allocation
        fund = self.service.create_memorial_fund_on_departure(
            user_id="user-alice",
            user_name="Alice",
            display_name="Alice",
            final_reputation=0.85,
            departure_type=DepartureType.DEATH,
        )
        allocation = self.service.allocate_ghost_reputation(
            fund_id=fund.id,
            proposal_id="proposal-test",
            amount=0.10,
            allocated_by="steward-bob",
            reason="Test",
            proposal_metadata={"proposer_id": "user-carol"}
        )

        # Action: Veto allocation
        self.service.veto_allocation(allocation.id, "steward-dave", "Test veto")

        # Verify: All actions logged
        logs = self.service.get_allocation_audit_logs(allocation.id)
        assert len(logs) >= 2

        # Verify: ALLOCATED action exists
        allocated_logs = [log for log in logs if log.action == AuditAction.ALLOCATED]
        assert len(allocated_logs) == 1
        assert allocated_logs[0].actor_id == "steward-bob"

        # Verify: VETOED action exists
        vetoed_logs = [log for log in logs if log.action == AuditAction.VETOED]
        assert len(vetoed_logs) == 1
        assert vetoed_logs[0].actor_id == "steward-dave"

        # Verify: Logs are chronological
        assert logs[0].logged_at <= logs[1].logged_at
