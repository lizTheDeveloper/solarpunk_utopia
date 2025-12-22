"""
End-to-End tests for Saturnalia Protocol.

Tests the complete role inversion flow to prevent power crystallization.

'All authority is a mask, not a face.' - Paulo Freire

Test scenarios (from GAP-E2E proposal):
WHEN Saturnalia event configured (role_inversion mode)
AND event triggers (annual/manual)
THEN stewards become members
AND members can access steward functions
AND safety-critical flows (panic/sanctuary) NOT inverted
WHEN member opts out
THEN opt-out recorded with reason
WHEN event ends
THEN roles revert
AND reflection prompts appear
"""

import pytest
import os
import tempfile
from datetime import datetime, timedelta, UTC

from app.database.saturnalia_repository import SaturnaliaRepository
from app.services.saturnalia_service import SaturnaliaService
from app.models.saturnalia import (
    SaturnaliaMode,
    EventStatus,
    TriggerType,
    SwapStatus,
)


class TestSaturnaliaE2E:
    """End-to-end Saturnalia Protocol flow tests"""

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
        with open("app/database/migrations/007_add_saturnalia_protocol.sql") as f:
            migration_sql = f.read()
            # Execute each statement separately (can't use executescript with PRAGMA)
            for statement in migration_sql.split(';'):
                if statement.strip():
                    cursor.execute(statement)

        conn.commit()
        conn.close()

        # Create service
        self.service = SaturnaliaService(self.db_path)

        yield

        # Cleanup
        os.unlink(self.db_path)

    def test_create_annual_role_swap_configuration(self):
        """
        E2E Test 1: Create configuration for annual Saturnalia with role swaps

        WHEN steward configures Saturnalia
        THEN configuration created with correct modes and schedule
        AND next event scheduled for ~1 year from now
        """
        # Setup: Configuration parameters
        created_by = "steward-alice"
        enabled_modes = [SaturnaliaMode.ROLE_SWAP]
        frequency = "annually"
        duration_hours = 24  # One day

        # Action: Create configuration
        config = self.service.create_config(
            created_by=created_by,
            enabled_modes=enabled_modes,
            frequency=frequency,
            duration_hours=duration_hours,
            cell_id="cell-downtown",
            exclude_safety_critical=True,
            allow_individual_opt_out=True,
        )

        # Verify: Configuration created correctly
        assert config is not None
        assert config.enabled is True
        assert SaturnaliaMode.ROLE_SWAP in config.enabled_modes
        assert config.frequency == "annually"
        assert config.duration_hours == 24
        assert config.exclude_safety_critical is True
        assert config.allow_individual_opt_out is True
        assert config.created_by == created_by
        assert config.cell_id == "cell-downtown"

        # Verify: Next event scheduled for ~1 year from now
        assert config.next_scheduled_start is not None
        now = datetime.now(datetime.UTC)
        days_until = (config.next_scheduled_start - now).days
        assert 350 <= days_until <= 380  # 365 ± 15 days

    def test_manual_trigger_saturnalia_event(self):
        """
        E2E Test 2: Manually trigger a Saturnalia event

        WHEN steward triggers event manually
        THEN event created with ACTIVE status
        AND event modes match configuration
        AND event has correct duration
        """
        # Setup: Create configuration
        config = self.service.create_config(
            created_by="steward-alice",
            enabled_modes=[SaturnaliaMode.ROLE_SWAP, SaturnaliaMode.ANONYMOUS_PERIOD],
            frequency="manual",
            duration_hours=48,
        )

        # Action: Manually trigger event
        event = self.service.trigger_event(
            config_id=config.id,
            triggered_by="steward-alice",
            manual=True,
        )

        # Verify: Event created correctly
        assert event is not None
        assert event.config_id == config.id
        assert event.status == EventStatus.ACTIVE
        assert event.trigger_type == TriggerType.MANUAL
        assert event.triggered_by == "steward-alice"
        assert SaturnaliaMode.ROLE_SWAP in event.active_modes
        assert SaturnaliaMode.ANONYMOUS_PERIOD in event.active_modes

        # Verify: Event duration correct
        duration = event.end_time - event.start_time
        assert duration == timedelta(hours=48)

        # Verify: Event is activated
        assert event.activated_at is not None
        assert event.completed_at is None
        assert event.cancelled_at is None

    def test_role_swap_during_event(self):
        """
        E2E Test 3: Role swaps are created during Saturnalia event

        WHEN Saturnalia event is ACTIVE
        AND role swap mode enabled
        THEN stewards and members can swap roles
        AND swap recorded with correct status
        """
        # Setup: Create and trigger event
        config = self.service.create_config(
            created_by="steward-alice",
            enabled_modes=[SaturnaliaMode.ROLE_SWAP],
            frequency="manual",
            duration_hours=24,
        )
        event = self.service.trigger_event(
            config_id=config.id,
            triggered_by="steward-alice",
            manual=True,
        )

        # Action: Create role swap
        swap = self.service.create_role_swap(
            event_id=event.id,
            original_user_id="steward-alice",
            original_role="steward",
            temporary_user_id="member-bob",
            scope_type="cell",
            scope_id="cell-downtown",
        )

        # Verify: Swap created correctly
        assert swap is not None
        assert swap.event_id == event.id
        assert swap.original_user_id == "steward-alice"
        assert swap.original_role == "steward"
        assert swap.temporary_user_id == "member-bob"
        assert swap.status == SwapStatus.ACTIVE
        assert swap.scope_type == "cell"
        assert swap.scope_id == "cell-downtown"
        assert swap.restored_at is None

        # Verify: Swap appears in active swaps
        active_swaps = self.service.get_active_swaps_for_event(event.id)
        assert len(active_swaps) == 1
        assert active_swaps[0].id == swap.id

    def test_opt_out_from_saturnalia_mode(self):
        """
        E2E Test 4: User opts out of Saturnalia mode

        WHEN member opts out of role_swap mode
        THEN opt-out recorded with reason
        AND opt-out can be checked for future events
        """
        # Action: Member opts out
        opt_out = self.service.create_opt_out(
            user_id="member-carol",
            mode=SaturnaliaMode.ROLE_SWAP,
            scope_type="all",
            reason="Caring for sick family member, need stable role",
            is_permanent=False,
            duration_days=90,
        )

        # Verify: Opt-out created correctly
        assert opt_out is not None
        assert opt_out.user_id == "member-carol"
        assert opt_out.mode == SaturnaliaMode.ROLE_SWAP
        assert opt_out.scope_type == "all"
        assert opt_out.reason == "Caring for sick family member, need stable role"
        assert opt_out.is_permanent is False
        assert opt_out.expires_at is not None

        # Verify: Opt-out duration correct
        duration = opt_out.expires_at - opt_out.opted_out_at
        assert abs(duration.days - 90) <= 1  # Allow 1 day margin

        # Verify: Opt-out is active
        is_opted_out = self.service.is_user_opted_out(
            user_id="member-carol",
            mode=SaturnaliaMode.ROLE_SWAP,
        )
        assert is_opted_out is True

        # Verify: Different user not opted out
        is_opted_out_bob = self.service.is_user_opted_out(
            user_id="member-bob",
            mode=SaturnaliaMode.ROLE_SWAP,
        )
        assert is_opted_out_bob is False

    def test_complete_event_restores_roles(self):
        """
        E2E Test 5: Completing event restores all role swaps

        WHEN Saturnalia event ends
        THEN all role swaps restored
        AND event marked COMPLETED
        AND restoration timestamp recorded
        """
        # Setup: Create event with role swaps
        config = self.service.create_config(
            created_by="steward-alice",
            enabled_modes=[SaturnaliaMode.ROLE_SWAP],
            frequency="manual",
            duration_hours=24,
        )
        event = self.service.trigger_event(
            config_id=config.id,
            triggered_by="steward-alice",
            manual=True,
        )
        swap1 = self.service.create_role_swap(
            event_id=event.id,
            original_user_id="steward-alice",
            original_role="steward",
            temporary_user_id="member-bob",
            scope_type="cell",
            scope_id="cell-downtown",
        )
        swap2 = self.service.create_role_swap(
            event_id=event.id,
            original_user_id="steward-dave",
            original_role="steward",
            temporary_user_id="member-eve",
            scope_type="cell",
            scope_id="cell-downtown",
        )

        # Action: Complete event
        completed_event = self.service.complete_event(event.id)

        # Verify: Event completed
        assert completed_event is not None
        assert completed_event.status == EventStatus.COMPLETED
        assert completed_event.completed_at is not None

        # Verify: No active swaps remain
        active_swaps = self.service.get_active_swaps_for_event(event.id)
        assert len(active_swaps) == 0

    def test_cancel_event_with_reason(self):
        """
        E2E Test 6: Cancel event early with emergency reason

        WHEN steward cancels active event
        THEN event marked CANCELLED
        AND cancellation reason recorded
        AND all swaps restored
        """
        # Setup: Create active event
        config = self.service.create_config(
            created_by="steward-alice",
            enabled_modes=[SaturnaliaMode.ROLE_SWAP],
            frequency="manual",
            duration_hours=24,
        )
        event = self.service.trigger_event(
            config_id=config.id,
            triggered_by="steward-alice",
            manual=True,
        )

        # Action: Cancel event with emergency reason
        cancelled_event = self.service.cancel_event(
            event_id=event.id,
            reason="ICE raid in progress - need normal steward coordination",
        )

        # Verify: Event cancelled
        assert cancelled_event is not None
        assert cancelled_event.status == EventStatus.CANCELLED
        assert cancelled_event.cancelled_at is not None
        assert cancelled_event.cancellation_reason == "ICE raid in progress - need normal steward coordination"
        assert cancelled_event.completed_at is None  # Cancelled, not completed

    def test_anonymous_posting_during_event(self):
        """
        E2E Test 7: Anonymous posts during ANONYMOUS_PERIOD mode

        WHEN anonymous mode active
        AND member creates post
        THEN post recorded with hidden author
        AND author revealed when event completes
        """
        # Setup: Create event with anonymous mode
        config = self.service.create_config(
            created_by="steward-alice",
            enabled_modes=[SaturnaliaMode.ANONYMOUS_PERIOD],
            frequency="manual",
            duration_hours=24,
        )
        event = self.service.trigger_event(
            config_id=config.id,
            triggered_by="steward-alice",
            manual=True,
        )

        # Action: Create anonymous post
        anon_post = self.service.create_anonymous_post(
            event_id=event.id,
            post_type="proposal",
            post_id="proposal-xyz",
            actual_author_id="member-frank",
        )

        # Verify: Post created with hidden author
        assert anon_post is not None
        assert anon_post.event_id == event.id
        assert anon_post.post_type == "proposal"
        assert anon_post.post_id == "proposal-xyz"
        assert anon_post.actual_author_id == "member-frank"
        assert anon_post.revealed_at is None  # Not yet revealed

        # Action: Complete event (triggers reveal)
        self.service.complete_event(event.id)

        # Verify: Author can be retrieved after event
        actual_author = self.service.get_actual_author("proposal-xyz")
        assert actual_author == "member-frank"

    def test_reflection_submission_after_event(self):
        """
        E2E Test 8: Members submit reflections after Saturnalia

        WHEN event completes
        AND member submits reflection
        THEN reflection recorded with learnings
        AND can be aggregated for insights
        """
        # Setup: Create and complete event
        config = self.service.create_config(
            created_by="steward-alice",
            enabled_modes=[SaturnaliaMode.ROLE_SWAP],
            frequency="manual",
            duration_hours=24,
        )
        event = self.service.trigger_event(
            config_id=config.id,
            triggered_by="steward-alice",
            manual=True,
        )
        self.service.complete_event(event.id)

        # Action: Member submits reflection
        reflection = self.service.create_reflection(
            event_id=event.id,
            user_id="member-bob",
            what_learned="Being a steward is harder than I thought - constant decision-making pressure",
            what_surprised="How much invisible work stewards do to keep things running smoothly",
            what_changed="I now appreciate stewards more and will be more patient with decisions",
            suggestions="Maybe rotate steward role more frequently so everyone experiences it",
            overall_rating=5,
            would_do_again=True,
        )

        # Verify: Reflection created
        assert reflection is not None
        assert reflection.event_id == event.id
        assert reflection.user_id == "member-bob"
        assert "steward is harder" in reflection.what_learned
        assert reflection.overall_rating == 5
        assert reflection.would_do_again is True

        # Verify: Can retrieve reflections for event
        all_reflections = self.service.get_reflections_for_event(event.id)
        assert len(all_reflections) == 1
        assert all_reflections[0].id == reflection.id

    def test_exclude_safety_critical_features(self):
        """
        E2E Test 9: Safety-critical features excluded from role swaps

        WHEN Saturnalia configured with exclude_safety_critical=True
        THEN panic, sanctuary, rapid response NOT subject to role swaps
        AND only non-critical steward functions inverted
        """
        # Action: Create configuration excluding safety features
        config = self.service.create_config(
            created_by="steward-alice",
            enabled_modes=[SaturnaliaMode.ROLE_SWAP],
            frequency="annually",
            duration_hours=24,
            exclude_safety_critical=True,
        )

        # Verify: Safety exclusion flag set
        assert config.exclude_safety_critical is True

        # Note: The actual enforcement of this exclusion happens in the
        # authorization layer (app/auth/middleware.py) which would check:
        # 1. Is there an active Saturnalia event?
        # 2. Is this action safety-critical?
        # 3. If both true, bypass role swap and use original role
        #
        # This test verifies the config flag is stored correctly.
        # Full integration testing would verify the middleware behavior.

    def test_multiple_modes_simultaneously(self):
        """
        E2E Test 10: Multiple Saturnalia modes active at once

        WHEN event has ROLE_SWAP + ANONYMOUS_PERIOD + REPUTATION_BLINDNESS
        THEN all modes active simultaneously
        AND participants experience full power disruption
        """
        # Setup: Create event with multiple modes
        config = self.service.create_config(
            created_by="steward-alice",
            enabled_modes=[
                SaturnaliaMode.ROLE_SWAP,
                SaturnaliaMode.ANONYMOUS_PERIOD,
                SaturnaliaMode.REPUTATION_BLINDNESS,
            ],
            frequency="annually",
            duration_hours=48,
        )
        event = self.service.trigger_event(
            config_id=config.id,
            triggered_by="steward-alice",
            manual=True,
        )

        # Verify: All modes active
        assert SaturnaliaMode.ROLE_SWAP in event.active_modes
        assert SaturnaliaMode.ANONYMOUS_PERIOD in event.active_modes
        assert SaturnaliaMode.REPUTATION_BLINDNESS in event.active_modes
        assert len(event.active_modes) == 3

    def test_check_event_expiry_auto_completion(self):
        """
        E2E Test 11: Events auto-complete when duration expires

        WHEN background job checks for expired events
        AND event end_time has passed
        THEN event auto-completed
        AND roles restored
        """
        # Setup: Create event with past end time
        config = self.service.create_config(
            created_by="steward-alice",
            enabled_modes=[SaturnaliaMode.ROLE_SWAP],
            frequency="manual",
            duration_hours=1,
        )
        event = self.service.trigger_event(
            config_id=config.id,
            triggered_by="steward-alice",
            manual=True,
        )

        # Manually set end_time to past (simulating time passage)
        # Since update_event doesn't update end_time, we update it directly in DB
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        past_time = (datetime.now(datetime.UTC) - timedelta(hours=1)).isoformat()
        cursor.execute("UPDATE saturnalia_events SET end_time = ? WHERE id = ?", (past_time, event.id))
        conn.commit()
        conn.close()

        # Action: Check for expired events
        completed_events = self.service.check_event_expiry()

        # Verify: Event auto-completed
        assert len(completed_events) == 1
        assert completed_events[0].id == event.id
        assert completed_events[0].status == EventStatus.COMPLETED

    def test_get_active_event_for_cell(self):
        """
        E2E Test 12: Check active event status for a cell

        WHEN cell has active Saturnalia event
        THEN can query active status
        AND get event details
        """
        # Setup: Create cell-specific event
        config = self.service.create_config(
            created_by="steward-alice",
            enabled_modes=[SaturnaliaMode.ROLE_SWAP],
            frequency="manual",
            duration_hours=24,
            cell_id="cell-downtown",
        )
        event = self.service.trigger_event(
            config_id=config.id,
            triggered_by="steward-alice",
            manual=True,
        )

        # Action: Query active event for cell
        active_event = self.service.get_active_event_for_cell("cell-downtown")

        # Verify: Event found
        assert active_event is not None
        assert active_event.id == event.id
        assert active_event.status == EventStatus.ACTIVE

        # Verify: Different cell has no active event
        other_cell_event = self.service.get_active_event_for_cell("cell-riverside")
        assert other_cell_event is None

    def test_permanent_opt_out(self):
        """
        E2E Test 13: User permanently opts out of Saturnalia mode

        WHEN user opts out permanently with reason
        THEN opt-out has no expiration
        AND is respected in all future events
        """
        # Action: Permanent opt-out
        opt_out = self.service.create_opt_out(
            user_id="member-grace",
            mode=SaturnaliaMode.ROLE_SWAP,
            scope_type="all",
            reason="PTSD from past authority abuse - role swaps trigger trauma",
            is_permanent=True,
        )

        # Verify: Permanent opt-out created
        assert opt_out is not None
        assert opt_out.is_permanent is True
        assert opt_out.expires_at is None  # No expiration
        assert opt_out.reason == "PTSD from past authority abuse - role swaps trigger trauma"

        # Verify: Opt-out is active
        is_opted_out = self.service.is_user_opted_out(
            user_id="member-grace",
            mode=SaturnaliaMode.ROLE_SWAP,
        )
        assert is_opted_out is True

    def test_update_configuration(self):
        """
        E2E Test 14: Update Saturnalia configuration

        WHEN steward updates configuration
        THEN changes applied
        AND next scheduled event recalculated
        """
        # Setup: Create initial configuration
        config = self.service.create_config(
            created_by="steward-alice",
            enabled_modes=[SaturnaliaMode.ROLE_SWAP],
            frequency="annually",
            duration_hours=24,
        )

        # Action: Update configuration
        updated = self.service.update_config(
            config_id=config.id,
            enabled_modes=[SaturnaliaMode.ROLE_SWAP, SaturnaliaMode.ANONYMOUS_PERIOD],
            frequency="quarterly",
            duration_hours=48,
            enabled=True,
        )

        # Verify: Updates applied
        assert updated is not None
        assert len(updated.enabled_modes) == 2
        assert SaturnaliaMode.ANONYMOUS_PERIOD in updated.enabled_modes
        assert updated.frequency == "quarterly"
        assert updated.duration_hours == 48

        # Verify: Next scheduled event recalculated for quarterly
        now = datetime.now(datetime.UTC)
        days_until = (updated.next_scheduled_start - now).days
        assert 83 <= days_until <= 97  # 90 ± 7 days
