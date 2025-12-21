"""
End-to-End tests for Rapid Response system.

Tests the complete flow from alert creation through to resolution and after-action review.

CRITICAL: These tests verify life-safety systems. Failure = people get detained.

Test scenario (from proposal):
WHEN Alice taps emergency button twice
AND enters alert type "ice_raid" with location hint "downtown area"
THEN alert bundle created with EMERGENCY priority
AND propagates to all responders within 30 seconds
AND responders can mark "available" or "en_route"
AND coordinator can escalate/de-escalate
AND after-action review captures lessons
"""

import pytest
import pytest_asyncio
import os
import tempfile
from datetime import datetime, timedelta
from freezegun import freeze_time

from app.models.rapid_response import (
    AlertType,
    AlertLevel,
    AlertStatus,
    ResponderStatus,
    ResponderRole,
)
from app.database.rapid_response_repository import RapidResponseRepository
from app.services.rapid_response_service import RapidResponseService
from app.services.bundle_service import BundleService
from app.services.crypto_service import CryptoService
from app.models.priority import Priority


class TestRapidResponseE2E:
    """End-to-end rapid response flow tests"""

    @pytest_asyncio.fixture(autouse=True)
    async def setup_and_teardown(self):
        """Set up test database and service"""
        # Setup
        # Create temp database
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")

        # Run migrations
        import aiosqlite
        async with aiosqlite.connect(self.db_path) as db:
            # Base schema
            with open("app/database/db.py") as f:
                content = f.read()
                # Extract CREATE TABLE statements for bundles, metadata, proposals, users
                base_schema = """
                CREATE TABLE IF NOT EXISTS bundles (
                    bundleId TEXT PRIMARY KEY,
                    queue TEXT NOT NULL,
                    createdAt TEXT NOT NULL,
                    expiresAt TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    audience TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    tags TEXT NOT NULL,
                    payloadType TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    hopLimit INTEGER NOT NULL,
                    hopCount INTEGER NOT NULL DEFAULT 0,
                    receiptPolicy TEXT NOT NULL,
                    signature TEXT NOT NULL,
                    authorPublicKey TEXT NOT NULL,
                    sizeBytes INTEGER NOT NULL,
                    addedToQueueAt TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS proposals (
                    proposal_id TEXT PRIMARY KEY,
                    agent_name TEXT NOT NULL,
                    proposal_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    explanation TEXT NOT NULL,
                    inputs_used TEXT NOT NULL,
                    constraints TEXT NOT NULL,
                    data TEXT NOT NULL,
                    requires_approval TEXT NOT NULL,
                    approvals TEXT NOT NULL,
                    approval_reasons TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT,
                    executed_at TEXT,
                    bundle_id TEXT
                );
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
                await db.executescript(base_schema)

            # Rapid response migration
            with open("app/database/migrations/005_add_rapid_response.sql") as f:
                migration_sql = f.read()
            await db.executescript(migration_sql)
            await db.commit()

        # Create services
        self.crypto_service = CryptoService()
        self.bundle_service = BundleService(self.crypto_service)
        self.service = RapidResponseService(self.db_path, self.bundle_service)

        yield  # Run the test

        # Teardown
        os.close(self.db_fd)
        os.unlink(self.db_path)

    @pytest.mark.asyncio
    async def test_full_rapid_response_flow(self):
        """
        E2E test - 2-tap alert → network propagation → responder coordination → resolution → after-action review

        Complete flow:
        1. Alice triggers ICE raid alert (high trust user)
        2. Alert bundle created with EMERGENCY priority
        3. Alert propagates to network
        4. Bob (coordinator) claims coordination role
        5. Carol and Dave respond as available
        6. Coordinator posts update (de-escalation)
        7. Coordinator resolves alert
        8. After-action review completed

        Scenario:
        - Alice (trust 0.85) sees ICE raid downtown
        - Triggers CRITICAL alert
        - 3 responders mobilize
        - Situation de-escalates
        - Alert resolved with lessons learned
        """

        # ===== Step 1: Alice creates CRITICAL alert =====
        # Alice has high trust (0.85 > 0.7 required for CRITICAL)
        alice_id = "user-alice"
        cell_id = "cell-downtown"

        with freeze_time("2025-12-19T10:00:00Z"):
            alert = await self.service.create_alert(
                user_id=alice_id,
                cell_id=cell_id,
                alert_type=AlertType.ICE_RAID,
                alert_level=AlertLevel.CRITICAL,
                location_hint="7th & Main, downtown Phoenix",
                description="ICE vans spotted, 4-5 agents, entering workplace",
                people_affected=2,
                user_trust_score=0.85
            )

        # Verify alert created
        assert alert.id is not None
        assert alert.alert_type == AlertType.ICE_RAID
        assert alert.alert_level == AlertLevel.CRITICAL
        assert alert.status == AlertStatus.ACTIVE
        assert alert.reported_by == alice_id
        assert alert.location_hint == "7th & Main, downtown Phoenix"
        assert alert.people_affected == 2
        assert not alert.confirmed  # Not yet confirmed
        assert alert.auto_downgrade_at is not None  # Should auto-downgrade if not confirmed in 5 min

        # Verify DTN bundle created with EMERGENCY priority
        assert alert.bundle_id is not None
        bundle = await self.bundle_service.get_bundle(alert.bundle_id)
        assert bundle is not None
        assert bundle.priority == Priority.EMERGENCY
        assert "rapid-response" in bundle.tags
        assert "ice_raid" in bundle.tags
        assert "critical" in bundle.tags

        # ===== Step 2: Bob confirms alert (within 5 min window) =====
        # This prevents auto-downgrade to WATCH
        bob_id = "user-bob"

        with freeze_time("2025-12-19T10:02:00Z"):
            confirmed_alert = self.service.confirm_alert(alert.id, bob_id)

        assert confirmed_alert.confirmed
        assert confirmed_alert.confirmed_by == bob_id
        assert confirmed_alert.auto_downgrade_at is None  # Cancelled

        # ===== Step 3: Bob claims coordinator role =====
        with freeze_time("2025-12-19T10:03:00Z"):
            coordinator_alert = self.service.claim_coordinator(alert.id, bob_id)

        assert coordinator_alert.coordinator_id == bob_id
        assert coordinator_alert.coordinator_claimed_at is not None

        # ===== Step 4: Responders join =====
        carol_id = "user-carol"
        dave_id = "user-dave"

        with freeze_time("2025-12-19T10:05:00Z"):
            # Carol responding as legal observer
            responder_carol = self.service.add_responder(
                alert_id=alert.id,
                user_id=carol_id,
                status=ResponderStatus.RESPONDING,
                role=ResponderRole.LEGAL,
                eta_minutes=15,
                notes="Know-your-rights cards + lawyer contact"
            )

            # Dave responding as witness/media
            responder_dave = self.service.add_responder(
                alert_id=alert.id,
                user_id=dave_id,
                status=ResponderStatus.RESPONDING,
                role=ResponderRole.MEDIA,
                eta_minutes=10,
                notes="Bringing camera"
            )

        assert responder_carol.role == ResponderRole.LEGAL
        assert responder_dave.role == ResponderRole.MEDIA

        # Verify responders list
        responders = self.service.get_alert_responders(alert.id)
        assert len(responders) == 2

        # ===== Step 5: Carol arrives on scene =====
        with freeze_time("2025-12-19T10:20:00Z"):
            arrived_carol = self.service.update_responder_status(
                responder_id=responder_carol.id,
                alert_id=alert.id,
                arrived=True
            )

        assert arrived_carol.arrived_at is not None

        # ===== Step 6: Coordinator posts de-escalation update =====
        with freeze_time("2025-12-19T10:30:00Z"):
            update = self.service.add_update(
                alert_id=alert.id,
                posted_by=bob_id,
                update_type="de-escalation",
                message="Agents left building, situation cooling down",
                new_alert_level=AlertLevel.WATCH
            )

        assert update.update_type == "de-escalation"
        assert update.new_alert_level == AlertLevel.WATCH
        assert update.bundle_id is not None  # Update propagated via DTN

        # Verify alert level changed
        updated_alert = self.service.get_alert(alert.id)
        assert updated_alert.alert_level == AlertLevel.WATCH

        # ===== Step 7: Coordinator resolves alert =====
        with freeze_time("2025-12-19T11:00:00Z"):
            resolved_alert = self.service.resolve_alert(
                alert_id=alert.id,
                coordinator_id=bob_id,
                resolution_notes="ICE agents departed, workers safe, no arrests made"
            )

        assert resolved_alert.status == AlertStatus.RESOLVED
        assert resolved_alert.resolved_at is not None
        assert resolved_alert.purge_at is not None  # Should purge 24h after resolution

        # ===== Step 8: After-action review =====
        with freeze_time("2025-12-19T14:00:00Z"):
            review = self.service.create_review(
                alert_id=alert.id,
                completed_by=bob_id,
                response_time_minutes=12,
                total_responders=2,
                successes="Fast response, good coordination, legal observer arrived quickly",
                challenges="Mesh connection dropped briefly, some confusion about roles",
                lessons="Need clearer role assignments upfront, backup comms plan",
                recommendations="Designate backup coordinator, test mesh more often"
            )

        assert review.alert_id == alert.id
        assert review.response_time_minutes == 12
        assert review.total_responders == 2
        assert "Fast response" in review.successes
        assert "backup comms" in review.lessons

        # Verify review stored
        retrieved_review = self.service.get_review(alert.id)
        assert retrieved_review is not None
        assert retrieved_review.id == review.id

    @pytest.mark.asyncio
    async def test_critical_alert_requires_high_trust(self):
        """
        Verify CRITICAL alerts require trust >= 0.7

        Low-trust users can trigger WATCH alerts, but not CRITICAL.
        This prevents panic spam from infiltrators.
        """
        # User with insufficient trust tries to create CRITICAL alert
        low_trust_user = "user-newbie"

        with pytest.raises(ValueError, match="CRITICAL alerts require trust >= 0.7"):
            await self.service.create_alert(
                user_id=low_trust_user,
                cell_id="cell-downtown",
                alert_type=AlertType.ICE_RAID,
                alert_level=AlertLevel.CRITICAL,
                location_hint="somewhere",
                description="might be ICE?",
                user_trust_score=0.5  # Too low for CRITICAL
            )

        # But WATCH alert should work
        watch_alert = await self.service.create_alert(
            user_id=low_trust_user,
            cell_id="cell-downtown",
            alert_type=AlertType.ICE_RAID,
            alert_level=AlertLevel.WATCH,
            location_hint="somewhere",
            description="might be ICE?",
            user_trust_score=0.5  # OK for WATCH
        )

        assert watch_alert.alert_level == AlertLevel.WATCH

    @pytest.mark.asyncio
    async def test_critical_alert_auto_downgrade_if_unconfirmed(self):
        """
        Verify CRITICAL alerts auto-downgrade to WATCH if not confirmed within 5 minutes

        This prevents false alarms from blocking real emergencies.
        """
        with freeze_time("2025-12-19T10:00:00Z") as frozen_time:
            # Create CRITICAL alert
            alert = await self.service.create_alert(
                user_id="user-alice",
                cell_id="cell-downtown",
                alert_type=AlertType.ICE_RAID,
                alert_level=AlertLevel.CRITICAL,
                location_hint="7th & Main",
                description="ICE vans spotted",
                user_trust_score=0.85
            )

            assert alert.alert_level == AlertLevel.CRITICAL
            assert alert.auto_downgrade_at is not None

            # Fast-forward 6 minutes (past auto-downgrade time)
            frozen_time.move_to("2025-12-19T10:06:00Z")

            # Process auto-downgrade
            downgraded_alert = self.service.process_auto_downgrades()

            # Verify alert downgraded to WATCH
            retrieved_alert = self.service.get_alert(alert.id)
            assert retrieved_alert.alert_level == AlertLevel.WATCH

    @pytest.mark.asyncio
    async def test_alert_propagation_priority(self):
        """
        Verify alerts propagate with correct priority:
        - CRITICAL → EMERGENCY priority
        - URGENT → PERISHABLE priority
        - WATCH → STANDARD priority
        """
        # CRITICAL alert → EMERGENCY priority
        critical_alert = await self.service.create_alert(
            user_id="user-alice",
            cell_id="cell-downtown",
            alert_type=AlertType.ICE_RAID,
            alert_level=AlertLevel.CRITICAL,
            location_hint="downtown",
            description="active raid",
            user_trust_score=0.85
        )

        critical_bundle = await self.bundle_service.get_bundle(critical_alert.bundle_id)
        assert critical_bundle.priority == Priority.EMERGENCY

        # URGENT alert → PERISHABLE priority
        urgent_alert = await self.service.create_alert(
            user_id="user-bob",
            cell_id="cell-downtown",
            alert_type=AlertType.CHECKPOINT,
            alert_level=AlertLevel.URGENT,
            location_hint="highway 60",
            description="checkpoint spotted",
            user_trust_score=0.6
        )

        urgent_bundle = await self.bundle_service.get_bundle(urgent_alert.bundle_id)
        assert urgent_bundle.priority == Priority.PERISHABLE

    @pytest.mark.asyncio
    async def test_alert_purge_after_24_hours(self):
        """
        Verify alerts auto-purge 24 hours after resolution

        OPSEC: We don't keep records that could be seized.
        """
        with freeze_time("2025-12-19T10:00:00Z") as frozen_time:
            # Create and resolve alert
            alert = await self.service.create_alert(
                user_id="user-alice",
                cell_id="cell-downtown",
                alert_type=AlertType.ICE_RAID,
                alert_level=AlertLevel.CRITICAL,
                location_hint="downtown",
                description="ICE raid",
                user_trust_score=0.85
            )

            frozen_time.move_to("2025-12-19T11:00:00Z")

            resolved_alert = self.service.resolve_alert(
                alert_id=alert.id,
                resolution_notes="Resolved peacefully"
            )

            assert resolved_alert.purge_at is not None

            # Fast-forward 24 hours
            frozen_time.move_to("2025-12-20T11:01:00Z")

            # Process purges
            self.service.run_auto_purge()

            # Verify alert purged
            retrieved_alert = self.service.get_alert(alert.id)
            assert retrieved_alert is None  # Purged

    @pytest.mark.asyncio
    async def test_responder_coordination_flow(self):
        """
        Verify complete responder coordination:
        - Responders join with roles and ETA
        - Responders mark arrived
        - Coordinator tracks who's on scene
        """
        # Create alert
        alert = await self.service.create_alert(
            user_id="user-alice",
            cell_id="cell-downtown",
            alert_type=AlertType.ICE_RAID,
            alert_level=AlertLevel.CRITICAL,
            location_hint="downtown",
            description="ICE raid",
            user_trust_score=0.85
        )

        # Multiple responders join with different roles
        legal_responder = self.service.add_responder(
            alert_id=alert.id,
            user_id="user-legal",
            status=ResponderStatus.RESPONDING,
            role=ResponderRole.LEGAL,
            eta_minutes=10
        )

        physical_responder = self.service.add_responder(
            alert_id=alert.id,
            user_id="user-physical",
            status=ResponderStatus.RESPONDING,
            role=ResponderRole.PHYSICAL,
            eta_minutes=5
        )

        support_responder = self.service.add_responder(
            alert_id=alert.id,
            user_id="user-support",
            status=ResponderStatus.AVAILABLE_FAR,
            role=ResponderRole.SUPPORT,
            notes="Can provide childcare"
        )

        # Verify all responders tracked
        responders = self.service.get_responders(alert.id)
        assert len(responders) == 3

        # Verify roles
        roles = {r.role for r in responders}
        assert ResponderRole.LEGAL in roles
        assert ResponderRole.PHYSICAL in roles
        assert ResponderRole.SUPPORT in roles

        # Mark arrived
        self.service.update_responder_status(
            responder_id=legal_responder.id,
            alert_id=alert.id,
            arrived=True
        )
        self.service.update_responder_status(
            responder_id=physical_responder.id,
            alert_id=alert.id,
            arrived=True
        )

        # Verify arrival tracking
        updated_responders = self.service.get_alert_responders(alert.id)
        arrived_count = sum(1 for r in updated_responders if r.arrived_at is not None)
        assert arrived_count == 2
