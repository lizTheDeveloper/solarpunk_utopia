"""
Temporal Justice Service

Business logic for temporal justice features.
"""

from datetime import datetime, timedelta, UTC
from typing import List, Optional, Dict, Any

from app.database.temporal_justice_repository import TemporalJusticeRepository
from app.models.temporal_justice import (
    AvailabilityWindow,
    SlowExchange,
    TimeContribution,
    ChunkOffer,
    TemporalJusticeMetrics,
    TemporalAvailabilityPreference,
    SlowExchangeStatus,
    ContributionType,
    RecurrenceType,
)


class TemporalJusticeService:
    """Service for temporal justice operations"""

    def __init__(self, repository: TemporalJusticeRepository):
        self.repo = repository

    # Availability Management

    async def add_availability_window(
        self,
        user_id: str,
        duration_minutes: int,
        recurrence_type: str,
        day_of_week: Optional[int] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        specific_date: Optional[str] = None,
        specific_start_time: Optional[str] = None,
        description: Optional[str] = None,
    ) -> AvailabilityWindow:
        """Add an availability window for a user"""
        return await self.repo.create_availability_window(
            user_id=user_id,
            duration_minutes=duration_minutes,
            recurrence_type=RecurrenceType(recurrence_type),
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            specific_date=specific_date,
            specific_start_time=specific_start_time,
            description=description,
        )

    async def get_user_availability(
        self, user_id: str, active_only: bool = True
    ) -> List[AvailabilityWindow]:
        """Get user's availability windows"""
        return await self.repo.get_user_availability_windows(user_id, active_only)

    # Slow Exchange Management

    async def create_slow_exchange(
        self,
        offerer_id: str,
        requester_id: str,
        what: str,
        category: str,
        expected_duration_days: int,
        proposal_id: Optional[str] = None,
        deadline_days: Optional[int] = None,
    ) -> SlowExchange:
        """Create a new slow exchange"""
        deadline = None
        if deadline_days:
            deadline = datetime.now(UTC) + timedelta(days=deadline_days)

        return await self.repo.create_slow_exchange(
            offerer_id=offerer_id,
            requester_id=requester_id,
            what=what,
            category=category,
            expected_duration_days=expected_duration_days,
            proposal_id=proposal_id,
            deadline=deadline,
        )

    async def update_slow_exchange(
        self,
        exchange_id: str,
        status: str,
        note: Optional[str] = None,
    ) -> None:
        """Update slow exchange status"""
        await self.repo.update_slow_exchange_status(
            exchange_id=exchange_id,
            status=SlowExchangeStatus(status),
            note=note,
        )

    async def get_user_slow_exchanges(
        self, user_id: str, status: Optional[str] = None
    ) -> List[SlowExchange]:
        """Get user's slow exchanges"""
        status_enum = SlowExchangeStatus(status) if status else None
        return await self.repo.get_user_slow_exchanges(user_id, status_enum)

    async def get_slow_exchanges_needing_check_in(
        self, days_since_contact: int = 7
    ) -> List[SlowExchange]:
        """Get slow exchanges that haven't had contact recently"""
        # This would need a custom query - for now return empty
        # In production, add to repository
        return []

    # Time Contribution Management

    async def record_contribution(
        self,
        user_id: str,
        contribution_type: str,
        description: str,
        hours_contributed: float,
        category: Optional[str] = None,
        related_exchange_id: Optional[str] = None,
        related_cell_id: Optional[str] = None,
    ) -> TimeContribution:
        """Record a time contribution"""
        return await self.repo.record_time_contribution(
            user_id=user_id,
            contribution_type=ContributionType(contribution_type),
            description=description,
            hours_contributed=hours_contributed,
            category=category,
            related_exchange_id=related_exchange_id,
            related_cell_id=related_cell_id,
        )

    async def acknowledge_contribution(
        self, contribution_id: str, acknowledging_user_id: str
    ) -> None:
        """Acknowledge someone's time contribution"""
        await self.repo.acknowledge_contribution(contribution_id, acknowledging_user_id)

    # Chunk Offer Management

    async def create_chunk_offer(
        self,
        proposal_id: str,
        user_id: str,
        availability_window_id: str,
        what_offered: str,
        category: str,
    ) -> ChunkOffer:
        """Create a chunk offer"""
        return await self.repo.create_chunk_offer(
            proposal_id=proposal_id,
            user_id=user_id,
            availability_window_id=availability_window_id,
            what_offered=what_offered,
            category=category,
        )

    async def claim_chunk_offer(
        self, chunk_id: str, claiming_user_id: str
    ) -> ChunkOffer:
        """Claim a chunk offer"""
        return await self.repo.claim_chunk_offer(chunk_id, claiming_user_id)

    async def get_available_chunk_offers(
        self, category: Optional[str] = None
    ) -> List[ChunkOffer]:
        """Get available chunk offers"""
        return await self.repo.get_available_chunk_offers(category)

    async def match_chunk_offers_with_needs(
        self, category: str, day_of_week: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Match chunk offers with needs based on category and timing.

        This is where the matchmaker would integrate temporal justice.
        For now, just return available chunks.
        """
        chunks = await self.repo.get_available_chunk_offers(category)

        # Would need to cross-reference with needs/requests
        # and check availability window compatibility
        return [
            {
                "chunk_id": chunk.id,
                "what_offered": chunk.what_offered,
                "category": chunk.category,
                "availability_window_id": chunk.availability_window_id,
            }
            for chunk in chunks
        ]

    # Metrics

    async def get_temporal_justice_metrics(
        self, days_back: int = 30
    ) -> TemporalJusticeMetrics:
        """Get temporal justice metrics"""
        period_end = datetime.now(UTC)
        period_start = period_end - timedelta(days=days_back)

        return await self.repo.calculate_temporal_justice_metrics(
            period_start, period_end
        )

    # Async Voting

    async def record_vote(
        self,
        proposal_id: str,
        user_id: str,
        vote: str,
        voting_notes: Optional[str] = None,
        proposal_created_at: Optional[datetime] = None,
    ):
        """Record an async vote"""
        return await self.repo.record_async_vote(
            proposal_id=proposal_id,
            user_id=user_id,
            vote=vote,
            voting_notes=voting_notes,
            proposal_created_at=proposal_created_at,
        )

    # Helper Methods

    async def suggest_slow_exchange(
        self, user_id: str, what: str, category: str
    ) -> bool:
        """
        Check if a slow exchange mode would be better for this user.

        Returns True if user has fragmented availability or care responsibilities.
        """
        windows = await self.repo.get_user_availability_windows(user_id)

        # If user has defined availability windows, they likely have fragmented time
        if len(windows) > 0:
            return True

        # Could also check user preferences
        # (would need to query users table for temporal_availability_preference)

        return False

    async def get_coordination_suggestions(
        self, exchange_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get suggestions for coordinating a slow exchange based on
        both parties' availability windows.
        """
        # Would need to:
        # 1. Get exchange details
        # 2. Get both users' availability windows
        # 3. Find overlapping or sequential windows
        # 4. Suggest coordination times

        # For now, return empty
        return []
