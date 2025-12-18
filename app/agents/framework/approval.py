"""
Approval tracking and management for agent proposals.

Handles storing proposals, tracking approvals, and executing approved proposals.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from .proposal import Proposal, ProposalStatus, ProposalFilter


logger = logging.getLogger(__name__)


class ApprovalTracker:
    """
    Tracks and manages proposal approvals.

    In-memory implementation; production would use database.
    """

    def __init__(self):
        self._proposals: Dict[str, Proposal] = {}

    async def store_proposal(self, proposal: Proposal) -> str:
        """
        Store a new proposal.

        Args:
            proposal: Proposal to store

        Returns:
            Proposal ID
        """
        self._proposals[proposal.proposal_id] = proposal
        logger.info(f"Stored proposal {proposal.proposal_id} from {proposal.agent_name}")
        return proposal.proposal_id

    async def get_proposal(self, proposal_id: str) -> Optional[Proposal]:
        """
        Get a proposal by ID.

        Args:
            proposal_id: Proposal ID

        Returns:
            Proposal or None if not found
        """
        return self._proposals.get(proposal_id)

    async def list_proposals(self, filter: Optional[ProposalFilter] = None) -> List[Proposal]:
        """
        List proposals matching filter criteria.

        Args:
            filter: Optional filter criteria

        Returns:
            List of matching proposals
        """
        proposals = list(self._proposals.values())

        if not filter:
            return proposals

        # Apply filters
        if filter.agent_name:
            proposals = [p for p in proposals if p.agent_name == filter.agent_name]

        if filter.proposal_type:
            proposals = [p for p in proposals if p.proposal_type == filter.proposal_type]

        if filter.status:
            proposals = [p for p in proposals if p.status == filter.status]

        if filter.user_id:
            proposals = [
                p for p in proposals
                if filter.user_id in p.requires_approval
            ]

        if filter.created_after:
            proposals = [p for p in proposals if p.created_at >= filter.created_after]

        if filter.created_before:
            proposals = [p for p in proposals if p.created_at <= filter.created_before]

        return proposals

    async def approve_proposal(
        self,
        proposal_id: str,
        user_id: str,
        approved: bool,
        reason: Optional[str] = None
    ) -> Proposal:
        """
        Record approval or rejection from a user.

        Args:
            proposal_id: Proposal ID
            user_id: User making the decision
            approved: True if approved, False if rejected
            reason: Optional reason for decision

        Returns:
            Updated proposal

        Raises:
            ValueError: If proposal not found or user not required approver
        """
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal {proposal_id} not found")

        if proposal.status not in [ProposalStatus.PENDING]:
            raise ValueError(f"Proposal {proposal_id} is {proposal.status.value}, cannot approve")

        proposal.add_approval(user_id, approved, reason)
        logger.info(
            f"User {user_id} {'approved' if approved else 'rejected'} "
            f"proposal {proposal_id}"
        )

        return proposal

    async def expire_old_proposals(self) -> int:
        """
        Mark expired proposals as expired.

        Returns:
            Number of proposals expired
        """
        now = datetime.utcnow()
        expired_count = 0

        for proposal in self._proposals.values():
            if (
                proposal.status == ProposalStatus.PENDING
                and proposal.expires_at
                and proposal.expires_at < now
            ):
                proposal.status = ProposalStatus.EXPIRED
                expired_count += 1
                logger.info(f"Expired proposal {proposal.proposal_id}")

        return expired_count

    async def get_pending_approvals(self, user_id: str) -> List[Proposal]:
        """
        Get proposals pending approval from a specific user.

        Args:
            user_id: User ID

        Returns:
            List of proposals awaiting this user's approval
        """
        return [
            proposal for proposal in self._proposals.values()
            if (
                proposal.status == ProposalStatus.PENDING
                and user_id in proposal.requires_approval
                and user_id not in proposal.approvals
            )
        ]

    async def get_approved_proposals(
        self,
        agent_name: Optional[str] = None,
        unexecuted_only: bool = True
    ) -> List[Proposal]:
        """
        Get approved proposals, optionally filtered by agent and execution status.

        Args:
            agent_name: Optional filter by agent name
            unexecuted_only: If True, only return proposals not yet executed

        Returns:
            List of approved proposals
        """
        proposals = [
            proposal for proposal in self._proposals.values()
            if proposal.status == ProposalStatus.APPROVED
        ]

        if agent_name:
            proposals = [p for p in proposals if p.agent_name == agent_name]

        if unexecuted_only:
            proposals = [p for p in proposals if not p.executed_at]

        return proposals

    async def mark_executed(self, proposal_id: str) -> Proposal:
        """
        Mark a proposal as executed.

        Args:
            proposal_id: Proposal ID

        Returns:
            Updated proposal

        Raises:
            ValueError: If proposal not found or not approved
        """
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal {proposal_id} not found")

        proposal.mark_executed()
        logger.info(f"Marked proposal {proposal_id} as executed")

        return proposal

    def get_stats(self) -> Dict[str, int]:
        """Get approval statistics"""
        proposals = list(self._proposals.values())
        return {
            "total": len(proposals),
            "pending": len([p for p in proposals if p.status == ProposalStatus.PENDING]),
            "approved": len([p for p in proposals if p.status == ProposalStatus.APPROVED]),
            "rejected": len([p for p in proposals if p.status == ProposalStatus.REJECTED]),
            "expired": len([p for p in proposals if p.status == ProposalStatus.EXPIRED]),
            "executed": len([p for p in proposals if p.status == ProposalStatus.EXECUTED]),
        }


# Global singleton (in production, use dependency injection)
approval_tracker = ApprovalTracker()
