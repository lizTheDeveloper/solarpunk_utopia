"""
Temporal Justice Repository

Database operations for temporal justice features.
"""

import json
import uuid
from datetime import datetime, timedelta, UTC
from typing import List, Optional, Dict, Any
import aiosqlite

from app.models.temporal_justice import (
    AvailabilityWindow,
    SlowExchange,
    TimeContribution,
    AsyncVotingRecord,
    ChunkOffer,
    TemporalJusticeMetrics,
    TemporalAvailabilityPreference,
    SlowExchangeStatus,
    ContributionType,
    RecurrenceType,
    ChunkOfferStatus,
)


class TemporalJusticeRepository:
    """Repository for temporal justice operations"""

    def __init__(self, db: Optional[aiosqlite.Connection] = None):
        self.db = db

    # Availability Windows

    async def create_availability_window(
        self,
        user_id: str,
        duration_minutes: int,
        recurrence_type: RecurrenceType,
        day_of_week: Optional[int] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        specific_date: Optional[str] = None,
        specific_start_time: Optional[str] = None,
        description: Optional[str] = None,
    ) -> AvailabilityWindow:
        """Create a new availability window"""
        window_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()

        await self.db.execute(
            """
            INSERT INTO availability_windows (
                id, user_id, day_of_week, start_time, end_time,
                duration_minutes, specific_date, specific_start_time,
                recurrence_type, description, is_active, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            """,
            (
                window_id,
                user_id,
                day_of_week,
                start_time,
                end_time,
                duration_minutes,
                specific_date,
                specific_start_time,
                recurrence_type.value,
                description,
                now,
            ),
        )
        await self.db.commit()

        return AvailabilityWindow(
            id=window_id,
            user_id=user_id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration_minutes,
            specific_date=specific_date,
            specific_start_time=specific_start_time,
            recurrence_type=recurrence_type,
            description=description,
            is_active=True,
            created_at=datetime.fromisoformat(now),
            updated_at=None,
        )

    async def get_user_availability_windows(
        self, user_id: str, active_only: bool = True
    ) -> List[AvailabilityWindow]:
        """Get all availability windows for a user"""
        query = """
            SELECT * FROM availability_windows
            WHERE user_id = ?
        """
        params = [user_id]

        if active_only:
            query += " AND is_active = 1"

        query += " ORDER BY day_of_week, start_time"

        cursor = await self.db.execute(query, params)
        rows = await cursor.fetchall()

        windows = []
        for row in rows:
            windows.append(
                AvailabilityWindow(
                    id=row[0],
                    user_id=row[1],
                    day_of_week=row[2],
                    start_time=row[3],
                    end_time=row[4],
                    duration_minutes=row[5],
                    specific_date=row[6],
                    specific_start_time=row[7],
                    recurrence_type=RecurrenceType(row[8]),
                    description=row[9],
                    is_active=bool(row[10]),
                    created_at=datetime.fromisoformat(row[11]),
                    updated_at=datetime.fromisoformat(row[12]) if row[12] else None,
                )
            )

        return windows

    # Slow Exchanges

    async def create_slow_exchange(
        self,
        offerer_id: str,
        requester_id: str,
        what: str,
        category: str,
        expected_duration_days: int,
        proposal_id: Optional[str] = None,
        deadline: Optional[datetime] = None,
    ) -> SlowExchange:
        """Create a new slow exchange"""
        exchange_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()

        await self.db.execute(
            """
            INSERT INTO slow_exchanges (
                id, proposal_id, offerer_id, requester_id, what, category,
                expected_duration_days, deadline, status, check_ins_count,
                coordination_notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'coordinating', 0, '[]', ?)
            """,
            (
                exchange_id,
                proposal_id,
                offerer_id,
                requester_id,
                what,
                category,
                expected_duration_days,
                deadline.isoformat() if deadline else None,
                now,
            ),
        )
        await self.db.commit()

        return SlowExchange(
            id=exchange_id,
            proposal_id=proposal_id,
            offerer_id=offerer_id,
            requester_id=requester_id,
            what=what,
            category=category,
            expected_duration_days=expected_duration_days,
            deadline=deadline,
            status=SlowExchangeStatus.COORDINATING,
            last_contact_at=None,
            next_proposed_contact=None,
            check_ins_count=0,
            coordination_notes=[],
            created_at=datetime.fromisoformat(now),
            started_at=None,
            completed_at=None,
        )

    async def update_slow_exchange_status(
        self,
        exchange_id: str,
        status: SlowExchangeStatus,
        note: Optional[str] = None,
    ) -> None:
        """Update slow exchange status and optionally add a note"""
        now = datetime.now(UTC).isoformat()

        # Get current notes
        cursor = await self.db.execute(
            "SELECT coordination_notes FROM slow_exchanges WHERE id = ?",
            (exchange_id,),
        )
        row = await cursor.fetchone()
        if not row:
            raise ValueError(f"Slow exchange {exchange_id} not found")

        notes = json.loads(row[0]) if row[0] else []

        # Add new note if provided
        if note:
            notes.append({"timestamp": now, "note": note, "status": status.value})

        # Update status
        update_fields = {
            "status": status.value,
            "coordination_notes": json.dumps(notes),
            "last_contact_at": now,
        }

        if status == SlowExchangeStatus.IN_PROGRESS and row:
            update_fields["started_at"] = now
        elif status == SlowExchangeStatus.COMPLETED:
            update_fields["completed_at"] = now

        # Build UPDATE query
        set_clause = ", ".join([f"{k} = ?" for k in update_fields.keys()])
        values = list(update_fields.values()) + [exchange_id]

        await self.db.execute(
            f"UPDATE slow_exchanges SET {set_clause} WHERE id = ?", values
        )
        await self.db.commit()

    async def get_user_slow_exchanges(
        self, user_id: str, status: Optional[SlowExchangeStatus] = None
    ) -> List[SlowExchange]:
        """Get slow exchanges for a user (as offerer or requester)"""
        query = """
            SELECT * FROM slow_exchanges
            WHERE offerer_id = ? OR requester_id = ?
        """
        params = [user_id, user_id]

        if status:
            query += " AND status = ?"
            params.append(status.value)

        query += " ORDER BY created_at DESC"

        cursor = await self.db.execute(query, params)
        rows = await cursor.fetchall()

        return [self._row_to_slow_exchange(row) for row in rows]

    def _row_to_slow_exchange(self, row) -> SlowExchange:
        """Convert database row to SlowExchange"""
        return SlowExchange(
            id=row[0],
            proposal_id=row[1],
            offerer_id=row[2],
            requester_id=row[3],
            what=row[4],
            category=row[5],
            expected_duration_days=row[6],
            deadline=datetime.fromisoformat(row[7]) if row[7] else None,
            status=SlowExchangeStatus(row[8]),
            last_contact_at=datetime.fromisoformat(row[9]) if row[9] else None,
            next_proposed_contact=datetime.fromisoformat(row[10]) if row[10] else None,
            check_ins_count=row[11],
            coordination_notes=json.loads(row[12]) if row[12] else [],
            created_at=datetime.fromisoformat(row[13]),
            started_at=datetime.fromisoformat(row[14]) if row[14] else None,
            completed_at=datetime.fromisoformat(row[15]) if row[15] else None,
        )

    # Time Contributions

    async def record_time_contribution(
        self,
        user_id: str,
        contribution_type: ContributionType,
        description: str,
        hours_contributed: float,
        category: Optional[str] = None,
        related_exchange_id: Optional[str] = None,
        related_cell_id: Optional[str] = None,
    ) -> TimeContribution:
        """Record a time contribution"""
        contrib_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()

        await self.db.execute(
            """
            INSERT INTO time_contributions (
                id, user_id, contribution_type, description, category,
                hours_contributed, contributed_at, acknowledgment_count,
                related_exchange_id, related_cell_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
            """,
            (
                contrib_id,
                user_id,
                contribution_type.value,
                description,
                category,
                hours_contributed,
                now,
                related_exchange_id,
                related_cell_id,
                now,
            ),
        )
        await self.db.commit()

        return TimeContribution(
            id=contrib_id,
            user_id=user_id,
            contribution_type=contribution_type,
            description=description,
            category=category,
            hours_contributed=hours_contributed,
            contributed_at=datetime.fromisoformat(now),
            acknowledged_by=[],
            acknowledgment_count=0,
            related_exchange_id=related_exchange_id,
            related_cell_id=related_cell_id,
            created_at=datetime.fromisoformat(now),
        )

    async def acknowledge_contribution(
        self, contribution_id: str, acknowledging_user_id: str
    ) -> None:
        """Acknowledge someone's time contribution"""
        # Get current acknowledgments
        cursor = await self.db.execute(
            "SELECT acknowledged_by FROM time_contributions WHERE id = ?",
            (contribution_id,),
        )
        row = await cursor.fetchone()
        if not row:
            raise ValueError(f"Contribution {contribution_id} not found")

        acknowledged = json.loads(row[0]) if row[0] else []

        # Add new acknowledgment if not already present
        if acknowledging_user_id not in acknowledged:
            acknowledged.append(acknowledging_user_id)

            await self.db.execute(
                """
                UPDATE time_contributions
                SET acknowledged_by = ?, acknowledgment_count = ?
                WHERE id = ?
                """,
                (json.dumps(acknowledged), len(acknowledged), contribution_id),
            )
            await self.db.commit()

    # Chunk Offers

    async def create_chunk_offer(
        self,
        proposal_id: str,
        user_id: str,
        availability_window_id: str,
        what_offered: str,
        category: str,
    ) -> ChunkOffer:
        """Create a chunk offer for a specific time window"""
        chunk_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()

        await self.db.execute(
            """
            INSERT INTO chunk_offers (
                id, proposal_id, user_id, availability_window_id,
                what_offered, category, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'available', ?)
            """,
            (
                chunk_id,
                proposal_id,
                user_id,
                availability_window_id,
                what_offered,
                category,
                now,
            ),
        )
        await self.db.commit()

        return ChunkOffer(
            id=chunk_id,
            proposal_id=proposal_id,
            user_id=user_id,
            availability_window_id=availability_window_id,
            what_offered=what_offered,
            category=category,
            status=ChunkOfferStatus.AVAILABLE,
            claimed_by_user_id=None,
            claimed_at=None,
            created_at=datetime.fromisoformat(now),
            completed_at=None,
        )

    async def claim_chunk_offer(
        self, chunk_id: str, claiming_user_id: str
    ) -> ChunkOffer:
        """Claim a chunk offer"""
        now = datetime.now(UTC).isoformat()

        await self.db.execute(
            """
            UPDATE chunk_offers
            SET status = 'claimed', claimed_by_user_id = ?, claimed_at = ?
            WHERE id = ? AND status = 'available'
            """,
            (claiming_user_id, now, chunk_id),
        )

        if self.db.total_changes == 0:
            raise ValueError(f"Chunk offer {chunk_id} not available for claiming")

        await self.db.commit()

        # Get updated chunk
        cursor = await self.db.execute(
            "SELECT * FROM chunk_offers WHERE id = ?", (chunk_id,)
        )
        row = await cursor.fetchone()

        return self._row_to_chunk_offer(row)

    async def get_available_chunk_offers(
        self, category: Optional[str] = None
    ) -> List[ChunkOffer]:
        """Get available chunk offers, optionally filtered by category"""
        query = "SELECT * FROM chunk_offers WHERE status = 'available'"
        params = []

        if category:
            query += " AND category = ?"
            params.append(category)

        query += " ORDER BY created_at DESC"

        cursor = await self.db.execute(query, params)
        rows = await cursor.fetchall()

        return [self._row_to_chunk_offer(row) for row in rows]

    def _row_to_chunk_offer(self, row) -> ChunkOffer:
        """Convert database row to ChunkOffer"""
        return ChunkOffer(
            id=row[0],
            proposal_id=row[1],
            user_id=row[2],
            availability_window_id=row[3],
            what_offered=row[4],
            category=row[5],
            status=ChunkOfferStatus(row[6]),
            claimed_by_user_id=row[7],
            claimed_at=datetime.fromisoformat(row[8]) if row[8] else None,
            created_at=datetime.fromisoformat(row[9]),
            completed_at=datetime.fromisoformat(row[10]) if row[10] else None,
        )

    # Async Voting

    async def record_async_vote(
        self,
        proposal_id: str,
        user_id: str,
        vote: str,
        voting_notes: Optional[str] = None,
        proposal_created_at: Optional[datetime] = None,
    ) -> AsyncVotingRecord:
        """Record an async vote on a proposal"""
        vote_id = str(uuid.uuid4())
        now = datetime.now(UTC)

        # Calculate time to vote if proposal creation time provided
        time_to_vote_hours = None
        if proposal_created_at:
            time_to_vote_hours = (now - proposal_created_at).total_seconds() / 3600

        await self.db.execute(
            """
            INSERT INTO async_voting_records (
                id, proposal_id, user_id, vote, voted_at,
                time_to_vote_hours, voting_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                vote_id,
                proposal_id,
                user_id,
                vote,
                now.isoformat(),
                time_to_vote_hours,
                voting_notes,
            ),
        )
        await self.db.commit()

        return AsyncVotingRecord(
            id=vote_id,
            proposal_id=proposal_id,
            user_id=user_id,
            vote=vote,
            voted_at=now,
            time_to_vote_hours=time_to_vote_hours,
            voting_notes=voting_notes,
        )

    # Metrics

    async def calculate_temporal_justice_metrics(
        self, period_start: datetime, period_end: datetime
    ) -> TemporalJusticeMetrics:
        """Calculate temporal justice metrics for a period"""
        metrics_id = str(uuid.uuid4())
        now = datetime.now(UTC)

        # Total active members (those with any activity in period)
        cursor = await self.db.execute(
            """
            SELECT COUNT(DISTINCT id) FROM users
            WHERE created_at <= ?
            """,
            (period_end.isoformat(),),
        )
        total_active = (await cursor.fetchone())[0]

        # Members with fragmented availability
        cursor = await self.db.execute(
            """
            SELECT COUNT(DISTINCT user_id) FROM availability_windows
            WHERE created_at BETWEEN ? AND ?
            """,
            (period_start.isoformat(), period_end.isoformat()),
        )
        fragmented = (await cursor.fetchone())[0]

        # Members with care responsibilities
        cursor = await self.db.execute(
            """
            SELECT COUNT(*) FROM users
            WHERE has_care_responsibilities = 1
            AND created_at <= ?
            """,
            (period_end.isoformat(),),
        )
        care_responsibilities = (await cursor.fetchone())[0]

        # Slow exchanges
        cursor = await self.db.execute(
            """
            SELECT COUNT(*) FROM slow_exchanges
            WHERE created_at BETWEEN ? AND ?
            """,
            (period_start.isoformat(), period_end.isoformat()),
        )
        slow_exchanges = (await cursor.fetchone())[0]

        cursor = await self.db.execute(
            """
            SELECT COUNT(*) FROM slow_exchanges
            WHERE status = 'completed'
            AND completed_at BETWEEN ? AND ?
            """,
            (period_start.isoformat(), period_end.isoformat()),
        )
        slow_exchanges_completed = (await cursor.fetchone())[0]

        cursor = await self.db.execute(
            """
            SELECT AVG(
                JULIANDAY(completed_at) - JULIANDAY(created_at)
            ) FROM slow_exchanges
            WHERE status = 'completed'
            AND completed_at BETWEEN ? AND ?
            """,
            (period_start.isoformat(), period_end.isoformat()),
        )
        avg_duration = (await cursor.fetchone())[0] or 0.0

        # Time contributions
        cursor = await self.db.execute(
            """
            SELECT SUM(hours_contributed) FROM time_contributions
            WHERE contributed_at BETWEEN ? AND ?
            """,
            (period_start.isoformat(), period_end.isoformat()),
        )
        total_hours = (await cursor.fetchone())[0] or 0.0

        cursor = await self.db.execute(
            """
            SELECT SUM(hours_contributed) FROM time_contributions
            WHERE contribution_type = 'care_work'
            AND contributed_at BETWEEN ? AND ?
            """,
            (period_start.isoformat(), period_end.isoformat()),
        )
        care_work_hours = (await cursor.fetchone())[0] or 0.0

        # Calculate success metric
        fragmented_percentage = (
            (fragmented / total_active * 100) if total_active > 0 else 0.0
        )

        # Store metrics
        await self.db.execute(
            """
            INSERT INTO temporal_justice_metrics (
                id, period_start, period_end, total_active_members,
                members_with_fragmented_availability, members_with_care_responsibilities,
                total_exchanges, slow_exchanges_count, slow_exchanges_completed,
                avg_slow_exchange_duration_days, total_time_contributions_hours,
                care_work_acknowledged_hours, fragmented_availability_percentage,
                calculated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                metrics_id,
                period_start.isoformat(),
                period_end.isoformat(),
                total_active,
                fragmented,
                care_responsibilities,
                0,  # total_exchanges - would need to query proposals/exchanges
                slow_exchanges,
                slow_exchanges_completed,
                avg_duration,
                total_hours,
                care_work_hours,
                fragmented_percentage,
                now.isoformat(),
            ),
        )
        await self.db.commit()

        return TemporalJusticeMetrics(
            id=metrics_id,
            period_start=period_start,
            period_end=period_end,
            total_active_members=total_active,
            members_with_fragmented_availability=fragmented,
            members_with_care_responsibilities=care_responsibilities,
            total_exchanges=0,
            slow_exchanges_count=slow_exchanges,
            slow_exchanges_completed=slow_exchanges_completed,
            avg_slow_exchange_duration_days=avg_duration,
            total_time_contributions_hours=total_hours,
            care_work_acknowledged_hours=care_work_hours,
            fragmented_availability_percentage=fragmented_percentage,
            calculated_at=now,
        )
