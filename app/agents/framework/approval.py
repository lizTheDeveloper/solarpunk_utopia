"""
Approval tracking and management for agent proposals.

Handles storing proposals, tracking approvals, and executing approved proposals.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from .proposal import Proposal, ProposalStatus, ProposalFilter


logger = logging.getLogger(__name__)


class ApprovalTracker:
    """
    Tracks and manages proposal approvals.

    Uses SQLite database for persistence via ProposalRepository.
    """

    def __init__(self):
        # Repository is imported lazily to avoid circular imports
        self._repo = None

    def _get_repo(self):
        """Lazy load repository to avoid circular imports"""
        if self._repo is None:
            from app.database.proposal_repo import ProposalRepository
            self._repo = ProposalRepository
        return self._repo

    async def store_proposal(self, proposal: Proposal) -> str:
        """
        Store a new proposal.

        Args:
            proposal: Proposal to store

        Returns:
            Proposal ID
        """
        repo = self._get_repo()
        await repo.save(proposal)
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
        repo = self._get_repo()
        return await repo.get_by_id(proposal_id)

    async def list_proposals(self, filter: Optional[ProposalFilter] = None) -> List[Proposal]:
        """
        List proposals matching filter criteria.

        Args:
            filter: Optional filter criteria

        Returns:
            List of matching proposals
        """
        repo = self._get_repo()
        return await repo.list_all(filter)

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
        repo = self._get_repo()
        proposal = await repo.get_by_id(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal {proposal_id} not found")

        if proposal.status not in [ProposalStatus.PENDING]:
            raise ValueError(f"Proposal {proposal_id} is {proposal.status.value}, cannot approve")

        proposal.add_approval(user_id, approved, reason)
        logger.info(
            f"User {user_id} {'approved' if approved else 'rejected'} "
            f"proposal {proposal_id}"
        )

        # Save updated proposal to database
        await repo.save(proposal)

        return proposal

    async def expire_old_proposals(self) -> int:
        """
        Mark expired proposals as expired.

        Returns:
            Number of proposals expired
        """
        now = datetime.now(timezone.utc)
        expired_count = 0

        repo = self._get_repo()
        filter = ProposalFilter(status=ProposalStatus.PENDING)
        proposals = await repo.list_all(filter)

        for proposal in proposals:
            if proposal.expires_at and proposal.expires_at < now:
                proposal.status = ProposalStatus.EXPIRED
                await repo.save(proposal)
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
        repo = self._get_repo()
        filter = ProposalFilter(status=ProposalStatus.PENDING, user_id=user_id)
        proposals = await repo.list_all(filter)

        # Filter to only those where user hasn't approved yet
        return [
            proposal for proposal in proposals
            if user_id not in proposal.approvals
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
        repo = self._get_repo()
        filter = ProposalFilter(
            status=ProposalStatus.APPROVED,
            agent_name=agent_name
        )
        proposals = await repo.list_all(filter)

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
        repo = self._get_repo()
        proposal = await repo.get_by_id(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal {proposal_id} not found")

        proposal.mark_executed()
        await repo.save(proposal)
        logger.info(f"Marked proposal {proposal_id} as executed")

        return proposal

    async def get_stats(self) -> Dict[str, int]:
        """Get approval statistics"""
        repo = self._get_repo()
        proposals = await repo.list_all()
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
