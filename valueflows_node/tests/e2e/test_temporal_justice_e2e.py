"""
End-to-End tests for Temporal Justice system.

Tests the complete flow of slow exchanges with multi-session tracking.

Silvia Federici: "The clock of the wage has replaced the clock of the stars."

This system resists the tyranny of synchronous availability - recognizing that
caregivers, workers with fragmented schedules, and those with care responsibilities
deserve full participation in the gift economy.
"""

import pytest
import pytest_asyncio
import os
import tempfile
from datetime import datetime, timedelta, UTC
from freezegun import freeze_time

from app.models.temporal_justice import (
    SlowExchangeStatus,
    ContributionType,
    RecurrenceType,
)
from app.database.temporal_justice_repository import TemporalJusticeRepository
from app.services.temporal_justice_service import TemporalJusticeService


class TestTemporalJusticeE2E:
    """End-to-end temporal justice flow tests"""

    @pytest_asyncio.fixture(autouse=True)
    async def setup_and_teardown(self):
        """Set up test database and service"""
        # Setup
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")

        # Run migrations
        import aiosqlite
        import os
        # Find project root (where both valueflows_node and app directories exist)
        test_file_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(test_file_dir)))

        # Open database connection and run migrations
        self.db = await aiosqlite.connect(self.db_path)

        # Load base schema first (has users, proposals, cells tables)
        vf_schema_path = os.path.join(project_root, "valueflows_node", "app", "database", "vf_schema.sql")
        with open(vf_schema_path) as f:
            base_schema = f.read()
        await self.db.executescript(base_schema)
        await self.db.commit()

        # Load temporal justice migration
        temporal_migration_path = os.path.join(project_root, "app", "database", "migrations", "012_add_temporal_justice.sql")
        with open(temporal_migration_path) as f:
            migration_sql = f.read()
        await self.db.executescript(migration_sql)
        await self.db.commit()

        # Create repository and service with open connection
        self.repo = TemporalJusticeRepository(self.db)
        self.service = TemporalJusticeService(self.repo)

        yield  # Run the test

        # Teardown
        await self.db.close()
        os.close(self.db_fd)
        os.unlink(self.db_path)

    @pytest.mark.asyncio
    async def test_slow_exchange_multi_session_flow(self):
        """
        E2E test: Create slow exchange → track sessions → complete

        Scenario from proposal:
        - Alice offers "teach bike repair" (slow exchange)
        - Expected duration = 3 sessions over 2 weeks
        - Exchange created with timeline
        - Check-in prompts at session boundaries
        - Alice marks sessions complete
        - Both parties mark complete
        """

        # Step 1: Create slow exchange for bike repair teaching
        exchange = await self.service.create_slow_exchange(
            offerer_id="alice",
            requester_id="bob",
            what="teach bike repair",
            category="skill_share",
            expected_duration_days=14,  # 2 weeks
            deadline_days=21,  # 3 weeks deadline
        )

        assert exchange.id is not None
        assert exchange.offerer_id == "alice"
        assert exchange.requester_id == "bob"
        assert exchange.what == "teach bike repair"
        assert exchange.status == SlowExchangeStatus.COORDINATING
        assert exchange.expected_duration_days == 14
        assert exchange.check_ins_count == 0

        # Step 2: Start the exchange
        await self.service.update_slow_exchange(
            exchange_id=exchange.id,
            status="in_progress",
            note="Session 1 scheduled for this Saturday at 10am",
        )

        updated = await self.repo.get_slow_exchange(exchange.id)
        assert updated.status == SlowExchangeStatus.IN_PROGRESS
        assert updated.started_at is not None
        assert len(updated.coordination_notes) == 1

        # Step 3: Complete session 1 (day 3)
        with freeze_time(exchange.created_at + timedelta(days=3)):
            await self.service.update_slow_exchange(
                exchange_id=exchange.id,
                status="in_progress",
                note="Session 1 complete: Covered basic maintenance and tire changing",
            )

            updated = await self.repo.get_slow_exchange(exchange.id)
            assert updated.check_ins_count == 1
            assert len(updated.coordination_notes) == 2

        # Step 4: Check-in after 7 days
        with freeze_time(exchange.created_at + timedelta(days=7)):
            await self.service.update_slow_exchange(
                exchange_id=exchange.id,
                status="in_progress",
                note="Session 2 complete: Learned brake adjustment and chain maintenance",
            )

            updated = await self.repo.get_slow_exchange(exchange.id)
            assert updated.check_ins_count == 2

        # Step 5: Session 3 delayed, but within deadline
        with freeze_time(exchange.created_at + timedelta(days=16)):
            await self.service.update_slow_exchange(
                exchange_id=exchange.id,
                status="in_progress",
                note="Session 3 complete: Advanced repairs and spoke replacement",
            )

            updated = await self.repo.get_slow_exchange(exchange.id)
            assert updated.check_ins_count == 3

        # Step 6: Both parties mark complete
        with freeze_time(exchange.created_at + timedelta(days=17)):
            await self.service.update_slow_exchange(
                exchange_id=exchange.id,
                status="completed",
                note="Exchange complete! Bob can now maintain his own bike.",
            )

            final = await self.repo.get_slow_exchange(exchange.id)
            assert final.status == SlowExchangeStatus.COMPLETED
            assert final.completed_at is not None
            assert len(final.coordination_notes) == 4

    @pytest.mark.asyncio
    async def test_slow_exchange_paused_and_resumed(self):
        """
        Exchange can be paused (life happens) and resumed.

        Scenario:
        - Exchange starts
        - Gets paused (childcare emergency)
        - Resumes after 2 weeks
        - Completes successfully
        """

        exchange = await self.service.create_slow_exchange(
            offerer_id="carol",
            requester_id="dave",
            what="teach woodworking",
            category="skill_share",
            expected_duration_days=10,
        )

        # Start
        await self.service.update_slow_exchange(
            exchange_id=exchange.id,
            status="in_progress",
            note="First session went well",
        )

        # Pause (day 3)
        with freeze_time(exchange.created_at + timedelta(days=3)):
            await self.service.update_slow_exchange(
                exchange_id=exchange.id,
                status="paused",
                note="Need to pause - eldercare emergency",
            )

            paused = await self.repo.get_slow_exchange(exchange.id)
            assert paused.status == SlowExchangeStatus.PAUSED

        # Resume (day 17)
        with freeze_time(exchange.created_at + timedelta(days=17)):
            await self.service.update_slow_exchange(
                exchange_id=exchange.id,
                status="in_progress",
                note="Resuming - ready to continue!",
            )

            resumed = await self.repo.get_slow_exchange(exchange.id)
            assert resumed.status == SlowExchangeStatus.IN_PROGRESS

        # Complete (day 25)
        with freeze_time(exchange.created_at + timedelta(days=25)):
            await self.service.update_slow_exchange(
                exchange_id=exchange.id,
                status="completed",
                note="Completed all sessions",
            )

            final = await self.repo.get_slow_exchange(exchange.id)
            assert final.status == SlowExchangeStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_timeline_exceeded_not_auto_cancelled(self):
        """
        CRITICAL: When timeline exceeded, coordinator notified (not auto-cancelled).

        From proposal: "WHEN timeline exceeded THEN coordinator notified (not auto-cancelled)"
        """

        exchange = await self.service.create_slow_exchange(
            offerer_id="eve",
            requester_id="frank",
            what="teach sewing",
            category="skill_share",
            expected_duration_days=7,  # 1 week expected
            deadline_days=10,  # 10 day deadline
        )

        await self.service.update_slow_exchange(
            exchange_id=exchange.id,
            status="in_progress",
            note="Started",
        )

        # Exceed expected duration but not deadline
        with freeze_time(exchange.created_at + timedelta(days=8)):
            # Check if exchange still active
            current = await self.repo.get_slow_exchange(exchange.id)

            # CRITICAL: Should still be IN_PROGRESS, not auto-cancelled
            assert current.status == SlowExchangeStatus.IN_PROGRESS

            # Coordinator can add note but exchange continues
            await self.service.update_slow_exchange(
                exchange_id=exchange.id,
                status="in_progress",
                note="Taking longer than expected, checking in",
            )

        # Complete after expected duration
        with freeze_time(exchange.created_at + timedelta(days=9)):
            await self.service.update_slow_exchange(
                exchange_id=exchange.id,
                status="completed",
                note="Done!",
            )

            final = await self.repo.get_slow_exchange(exchange.id)
            assert final.status == SlowExchangeStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_fragmented_availability_windows(self):
        """
        User with fragmented availability can share when they're available.

        Scenario:
        - Caregiver has 3 windows: Tue morning, Thu afternoon, Sat morning
        - Can offer services in those specific chunks
        - Others can claim chunks that work for them
        """

        # Add fragmented availability windows
        tue_morning = await self.service.add_availability_window(
            user_id="grace",
            duration_minutes=120,  # 2 hours
            recurrence_type="weekly",
            day_of_week=2,  # Tuesday
            start_time="09:00",
            end_time="11:00",
            description="After kids go to school",
        )

        thu_afternoon = await self.service.add_availability_window(
            user_id="grace",
            duration_minutes=90,  # 1.5 hours
            recurrence_type="weekly",
            day_of_week=4,  # Thursday
            start_time="13:00",
            end_time="14:30",
            description="Lunch break",
        )

        sat_morning = await self.service.add_availability_window(
            user_id="grace",
            duration_minutes=180,  # 3 hours
            recurrence_type="weekly",
            day_of_week=6,  # Saturday
            start_time="08:00",
            end_time="11:00",
            description="Weekend morning",
        )

        # Verify windows created
        windows = await self.service.get_user_availability(user_id="grace")
        assert len(windows) == 3

        # Create chunk offers for these windows
        chunk1 = await self.service.create_chunk_offer(
            proposal_id="offer-123",
            user_id="grace",
            availability_window_id=tue_morning.id,
            what_offered="Help with gardening",
            category="community_labor",
        )

        chunk2 = await self.service.create_chunk_offer(
            proposal_id="offer-123",
            user_id="grace",
            availability_window_id=sat_morning.id,
            what_offered="Help with gardening",
            category="community_labor",
        )

        # Someone claims Saturday chunk
        claimed = await self.service.claim_chunk_offer(
            chunk_id=chunk2.id,
            claiming_user_id="hank",
        )

        assert claimed.claimed_by_user_id == "hank"
        assert claimed.claimed_at is not None

        # Tuesday chunk still available
        available = await self.service.get_available_chunk_offers(category="community_labor")
        assert len(available) == 1
        assert available[0].id == chunk1.id

    @pytest.mark.asyncio
    async def test_care_work_time_contribution_acknowledged(self):
        """
        Care work is recorded and acknowledged by community.

        Scenario:
        - Alice records 10 hours of childcare for community event
        - Others acknowledge her contribution
        - Contribution visible in temporal justice metrics
        """

        # Record care work contribution
        contribution = await self.service.record_contribution(
            user_id="alice",
            contribution_type="care_work",
            description="Provided childcare during community planning meeting",
            hours_contributed=10.0,
            category="childcare",
            related_cell_id="sunrise-collective",
        )

        assert contribution.user_id == "alice"
        assert contribution.contribution_type == ContributionType.CARE_WORK
        assert contribution.hours_contributed == 10.0
        assert contribution.acknowledgment_count == 0

        # Three people acknowledge
        await self.service.acknowledge_contribution(contribution.id, "bob")
        await self.service.acknowledge_contribution(contribution.id, "carol")
        await self.service.acknowledge_contribution(contribution.id, "dave")

        # Verify acknowledgments
        updated = await self.repo.get_time_contribution(contribution.id)
        assert updated.acknowledgment_count == 3
        assert "bob" in updated.acknowledged_by
        assert "carol" in updated.acknowledged_by
        assert "dave" in updated.acknowledged_by

    @pytest.mark.asyncio
    async def test_temporal_justice_metrics(self):
        """
        Metrics track success of temporal justice features.

        Success metric: >30% of active members have fragmented availability
        """

        # Add availability windows for multiple users
        for i, user_id in enumerate(["user1", "user2", "user3", "user4"]):
            await self.service.add_availability_window(
                user_id=user_id,
                duration_minutes=90,
                recurrence_type="weekly",
                day_of_week=i % 7,
                start_time="10:00",
                end_time="11:30",
            )

        # Create slow exchanges
        exchange1 = await self.service.create_slow_exchange(
            offerer_id="user1",
            requester_id="user2",
            what="skill share",
            category="skills",
            expected_duration_days=7,
        )

        exchange2 = await self.service.create_slow_exchange(
            offerer_id="user3",
            requester_id="user4",
            what="repair assistance",
            category="repairs",
            expected_duration_days=14,
        )

        # Complete one exchange
        await self.service.update_slow_exchange(
            exchange_id=exchange1.id,
            status="completed",
            note="Done",
        )

        # Record time contributions
        await self.service.record_contribution(
            user_id="user1",
            contribution_type="care_work",
            description="Eldercare",
            hours_contributed=20.0,
        )

        # Get metrics
        metrics = await self.service.get_temporal_justice_metrics(days_back=30)

        # Should have data
        assert metrics.slow_exchanges_count >= 2
        assert metrics.slow_exchanges_completed >= 1
        assert metrics.total_time_contributions_hours >= 20.0

    @pytest.mark.asyncio
    async def test_async_voting_with_time_tracking(self):
        """
        Async voting records time-to-vote to show participation patterns.

        This complements the governance silence weight system.
        """

        proposal_created = datetime.now(datetime.UTC) - timedelta(days=2)

        # User votes 2 days after proposal
        vote = await self.service.record_vote(
            proposal_id="prop-123",
            user_id="iris",
            vote="approve",
            voting_notes="Looks good, needed time to think it over",
            proposal_created_at=proposal_created,
        )

        assert vote.user_id == "iris"
        assert vote.vote == "approve"
        assert vote.time_to_vote_hours is not None
        assert vote.time_to_vote_hours >= 48.0  # ~2 days

    @pytest.mark.asyncio
    async def test_coordinator_not_shamed_for_slow_progress(self):
        """
        CRITICAL: Slow exchanges don't generate shame/pressure.

        From Federici: The point is NOT to track productivity.
        The point is to ACCOMMODATE reality.
        """

        exchange = await self.service.create_slow_exchange(
            offerer_id="jack",
            requester_id="jane",
            what="repair laptop",
            category="repairs",
            expected_duration_days=3,
        )

        await self.service.update_slow_exchange(
            exchange_id=exchange.id,
            status="in_progress",
            note="Started",
        )

        # Takes 30 days instead of 3
        with freeze_time(exchange.created_at + timedelta(days=30)):
            # No automatic notifications
            # No "overdue" status
            # No pressure metrics

            current = await self.repo.get_slow_exchange(exchange.id)

            # Status is still just "in_progress"
            # NOT "overdue" or "late" or any shaming language
            assert current.status == SlowExchangeStatus.IN_PROGRESS

            # Can complete without penalty
            await self.service.update_slow_exchange(
                exchange_id=exchange.id,
                status="completed",
                note="Took longer than expected, but done well!",
            )

            final = await self.repo.get_slow_exchange(exchange.id)
            assert final.status == SlowExchangeStatus.COMPLETED


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
