"""
Tests for Temporal Justice

Tests for temporal justice features: availability windows, slow exchanges,
time contributions, chunk offers, and async voting.
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta, UTC
import aiosqlite

from app.database.temporal_justice_repository import TemporalJusticeRepository
from app.services.temporal_justice_service import TemporalJusticeService
from app.models.temporal_justice import (
    RecurrenceType,
    SlowExchangeStatus,
    ContributionType,
)


@pytest_asyncio.fixture
async def db():
    """Create in-memory database for testing"""
    conn = await aiosqlite.connect(":memory:")
    conn.row_factory = aiosqlite.Row

    # Create tables
    await conn.executescript("""
        CREATE TABLE users (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            created_at TEXT NOT NULL,
            temporal_availability_preference TEXT DEFAULT 'synchronous',
            has_care_responsibilities INTEGER DEFAULT 0,
            prefers_slow_exchanges INTEGER DEFAULT 0
        );

        CREATE TABLE proposals (
            proposal_id TEXT PRIMARY KEY,
            temporal_justice_mode INTEGER DEFAULT 0,
            voting_window_days INTEGER DEFAULT 1,
            async_participation_enabled INTEGER DEFAULT 0
        );

        CREATE TABLE availability_windows (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            day_of_week INTEGER,
            start_time TEXT,
            end_time TEXT,
            duration_minutes INTEGER NOT NULL,
            specific_date TEXT,
            specific_start_time TEXT,
            recurrence_type TEXT DEFAULT 'weekly',
            description TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE slow_exchanges (
            id TEXT PRIMARY KEY,
            proposal_id TEXT,
            offerer_id TEXT NOT NULL,
            requester_id TEXT NOT NULL,
            what TEXT NOT NULL,
            category TEXT NOT NULL,
            expected_duration_days INTEGER NOT NULL,
            deadline TEXT,
            status TEXT DEFAULT 'coordinating',
            last_contact_at TEXT,
            next_proposed_contact TEXT,
            check_ins_count INTEGER DEFAULT 0,
            coordination_notes TEXT,
            created_at TEXT NOT NULL,
            started_at TEXT,
            completed_at TEXT,
            FOREIGN KEY (offerer_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (requester_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE time_contributions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            contribution_type TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT,
            hours_contributed REAL NOT NULL,
            contributed_at TEXT NOT NULL,
            acknowledged_by TEXT,
            acknowledgment_count INTEGER DEFAULT 0,
            related_exchange_id TEXT,
            related_cell_id TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE chunk_offers (
            id TEXT PRIMARY KEY,
            proposal_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            availability_window_id TEXT NOT NULL,
            what_offered TEXT NOT NULL,
            category TEXT NOT NULL,
            status TEXT DEFAULT 'available',
            claimed_by_user_id TEXT,
            claimed_at TEXT,
            created_at TEXT NOT NULL,
            completed_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (availability_window_id) REFERENCES availability_windows(id) ON DELETE CASCADE
        );

        CREATE TABLE async_voting_records (
            id TEXT PRIMARY KEY,
            proposal_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            vote TEXT NOT NULL,
            voted_at TEXT NOT NULL,
            time_to_vote_hours REAL,
            voting_notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(proposal_id, user_id)
        );

        CREATE TABLE temporal_justice_metrics (
            id TEXT PRIMARY KEY,
            period_start TEXT NOT NULL,
            period_end TEXT NOT NULL,
            total_active_members INTEGER DEFAULT 0,
            members_with_fragmented_availability INTEGER DEFAULT 0,
            members_with_care_responsibilities INTEGER DEFAULT 0,
            total_exchanges INTEGER DEFAULT 0,
            slow_exchanges_count INTEGER DEFAULT 0,
            slow_exchanges_completed INTEGER DEFAULT 0,
            avg_slow_exchange_duration_days REAL DEFAULT 0.0,
            total_time_contributions_hours REAL DEFAULT 0.0,
            care_work_acknowledged_hours REAL DEFAULT 0.0,
            fragmented_availability_percentage REAL DEFAULT 0.0,
            calculated_at TEXT NOT NULL,
            UNIQUE(period_start, period_end)
        );
    """)

    # Create test users
    now = datetime.now(UTC).isoformat()
    await conn.execute(
        "INSERT INTO users (id, name, email, created_at) VALUES (?, ?, ?, ?)",
        ("user1", "Test User 1", "user1@test.com", now),
    )
    await conn.execute(
        "INSERT INTO users (id, name, email, created_at, has_care_responsibilities) VALUES (?, ?, ?, ?, ?)",
        ("user2", "Test User 2", "user2@test.com", now, 1),
    )
    await conn.commit()

    yield conn
    await conn.close()


@pytest_asyncio.fixture
async def service(db):
    """Create service with test database"""
    repo = TemporalJusticeRepository(db)
    return TemporalJusticeService(repo)


@pytest.mark.asyncio
async def test_create_availability_window(service):
    """Test creating an availability window"""
    window = await service.add_availability_window(
        user_id="user1",
        duration_minutes=30,
        recurrence_type="weekly",
        day_of_week=2,  # Tuesday
        start_time="19:00",
        end_time="19:30",
        description="After kids sleep",
    )

    assert window.user_id == "user1"
    assert window.duration_minutes == 30
    assert window.day_of_week == 2
    assert window.description == "After kids sleep"


@pytest.mark.asyncio
async def test_get_user_availability(service):
    """Test getting user availability windows"""
    # Create windows
    await service.add_availability_window(
        user_id="user1",
        duration_minutes=30,
        recurrence_type="weekly",
        day_of_week=2,
        start_time="19:00",
        end_time="19:30",
    )

    await service.add_availability_window(
        user_id="user1",
        duration_minutes=45,
        recurrence_type="weekly",
        day_of_week=5,
        start_time="12:00",
        end_time="12:45",
    )

    # Get windows
    windows = await service.get_user_availability("user1")

    assert len(windows) == 2
    assert windows[0].day_of_week == 2
    assert windows[1].day_of_week == 5


@pytest.mark.asyncio
async def test_create_slow_exchange(service):
    """Test creating a slow exchange"""
    exchange = await service.create_slow_exchange(
        offerer_id="user1",
        requester_id="user2",
        what="Gardening help - 3 hours total over 2 weeks",
        category="labor",
        expected_duration_days=14,
        deadline_days=21,
    )

    assert exchange.offerer_id == "user1"
    assert exchange.requester_id == "user2"
    assert exchange.expected_duration_days == 14
    assert exchange.status == SlowExchangeStatus.COORDINATING


@pytest.mark.asyncio
async def test_update_slow_exchange_status(service):
    """Test updating slow exchange status"""
    # Create exchange
    exchange = await service.create_slow_exchange(
        offerer_id="user1",
        requester_id="user2",
        what="Test exchange",
        category="labor",
        expected_duration_days=7,
    )

    # Update status
    await service.update_slow_exchange(
        exchange_id=exchange.id,
        status="in_progress",
        note="Started working together",
    )

    # Get updated exchanges
    exchanges = await service.get_user_slow_exchanges("user1", status="in_progress")

    assert len(exchanges) == 1
    assert exchanges[0].status == SlowExchangeStatus.IN_PROGRESS


@pytest.mark.asyncio
async def test_record_time_contribution(service):
    """Test recording time contribution"""
    contribution = await service.record_contribution(
        user_id="user2",
        contribution_type="care_work",
        description="Childcare during cell meeting",
        hours_contributed=2.5,
        category="childcare",
    )

    assert contribution.user_id == "user2"
    assert contribution.contribution_type == ContributionType.CARE_WORK
    assert contribution.hours_contributed == 2.5


@pytest.mark.asyncio
async def test_acknowledge_contribution(service):
    """Test acknowledging time contribution"""
    # Record contribution
    contribution = await service.record_contribution(
        user_id="user2",
        contribution_type="care_work",
        description="Childcare",
        hours_contributed=2.0,
    )

    # Acknowledge it
    await service.acknowledge_contribution(contribution.id, "user1")

    # Verify (would need to query to verify acknowledgment count)
    # For now, just check it doesn't error


@pytest.mark.asyncio
async def test_chunk_offers(service, db):
    """Test chunk offer creation and claiming"""
    # Create availability window
    window = await service.add_availability_window(
        user_id="user1",
        duration_minutes=30,
        recurrence_type="one_time",
        specific_date="2025-01-15",
        specific_start_time="14:00",
    )

    # Create a proposal
    await db.execute(
        "INSERT INTO proposals (proposal_id) VALUES (?)",
        ("proposal1",),
    )
    await db.commit()

    # Create chunk offer
    chunk = await service.create_chunk_offer(
        proposal_id="proposal1",
        user_id="user1",
        availability_window_id=window.id,
        what_offered="Computer help",
        category="tech_support",
    )

    assert chunk.user_id == "user1"
    assert chunk.what_offered == "Computer help"

    # Claim chunk offer
    claimed = await service.claim_chunk_offer(chunk.id, "user2")

    assert claimed.claimed_by_user_id == "user2"


@pytest.mark.asyncio
async def test_temporal_justice_metrics(service):
    """Test calculating temporal justice metrics"""
    # Create some data
    await service.add_availability_window(
        user_id="user1",
        duration_minutes=30,
        recurrence_type="weekly",
        day_of_week=2,
        start_time="19:00",
        end_time="19:30",
    )

    await service.create_slow_exchange(
        offerer_id="user1",
        requester_id="user2",
        what="Test",
        category="labor",
        expected_duration_days=7,
    )

    await service.record_contribution(
        user_id="user2",
        contribution_type="care_work",
        description="Childcare",
        hours_contributed=3.0,
    )

    # Calculate metrics
    metrics = await service.get_temporal_justice_metrics(days_back=30)

    assert metrics.total_active_members == 2
    assert metrics.members_with_fragmented_availability >= 1
    assert metrics.members_with_care_responsibilities == 1
    assert metrics.slow_exchanges_count >= 1
    assert metrics.care_work_acknowledged_hours >= 0


@pytest.mark.asyncio
async def test_success_metric(service):
    """Test that success metric is calculated: >30% fragmented availability"""
    # Create availability windows for user1
    await service.add_availability_window(
        user_id="user1",
        duration_minutes=30,
        recurrence_type="weekly",
        day_of_week=2,
        start_time="19:00",
        end_time="19:30",
    )

    # Calculate metrics
    metrics = await service.get_temporal_justice_metrics(days_back=30)

    # With 2 users and 1 having fragmented availability:
    # 1/2 = 50% which is > 30%, so success!
    assert metrics.fragmented_availability_percentage == 50.0
