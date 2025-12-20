-- Migration 013: Add Temporal Justice - Don't Exclude Caregivers/Workers
--
-- "Wages for Housework meant that the home was a workplace." - Silvia Federici
--
-- Gift economy assumes everyone has "free time" to give. But caregivers, workers
-- with multiple jobs, single parents - they don't have time to participate equally.
-- Excluding them based on availability is unjust.
--
-- Temporal Justice ensures asynchronous participation modes so that fragmented
-- availability doesn't mean exclusion from the network.

PRAGMA foreign_keys = ON;

-- Create availability_windows table for fragmented time chunks
CREATE TABLE IF NOT EXISTS availability_windows (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,

    -- Time window
    day_of_week INTEGER,  -- 0-6 (Sunday-Saturday), NULL for one-time
    start_time TEXT,  -- HH:MM format
    end_time TEXT,  -- HH:MM format
    duration_minutes INTEGER NOT NULL,

    -- Or specific date/time for one-time availability
    specific_date TEXT,  -- YYYY-MM-DD
    specific_start_time TEXT,  -- HH:MM

    -- Recurrence
    recurrence_type TEXT DEFAULT 'weekly',  -- 'weekly', 'one_time', 'flexible'

    -- Context
    description TEXT,  -- "After kids sleep", "Lunch break", etc.

    -- Active status
    is_active INTEGER DEFAULT 1,

    -- Metadata
    created_at TEXT NOT NULL,
    updated_at TEXT,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_availability_windows_user ON availability_windows(user_id);
CREATE INDEX IF NOT EXISTS idx_availability_windows_day ON availability_windows(day_of_week);
CREATE INDEX IF NOT EXISTS idx_availability_windows_active ON availability_windows(is_active);

-- Create slow_exchanges table for matches that can happen over weeks
CREATE TABLE IF NOT EXISTS slow_exchanges (
    id TEXT PRIMARY KEY,

    -- Match/Exchange reference
    proposal_id TEXT,  -- Reference to the match proposal

    -- Parties
    offerer_id TEXT NOT NULL,
    requester_id TEXT NOT NULL,

    -- Exchange details
    what TEXT NOT NULL,
    category TEXT NOT NULL,

    -- Timeline
    expected_duration_days INTEGER NOT NULL,  -- How long this is expected to take
    deadline TEXT,  -- Optional final deadline (flexible)

    -- Status
    status TEXT DEFAULT 'coordinating',  -- 'coordinating', 'in_progress', 'paused', 'completed', 'cancelled'

    -- Progress tracking
    last_contact_at TEXT,
    next_proposed_contact TEXT,
    check_ins_count INTEGER DEFAULT 0,

    -- Notes
    coordination_notes TEXT,  -- JSON array of timestamped notes

    -- Metadata
    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,

    FOREIGN KEY (offerer_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (requester_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_slow_exchanges_offerer ON slow_exchanges(offerer_id);
CREATE INDEX IF NOT EXISTS idx_slow_exchanges_requester ON slow_exchanges(requester_id);
CREATE INDEX IF NOT EXISTS idx_slow_exchanges_status ON slow_exchanges(status);
CREATE INDEX IF NOT EXISTS idx_slow_exchanges_deadline ON slow_exchanges(deadline);

-- Create time_contributions table for acknowledging care work
CREATE TABLE IF NOT EXISTS time_contributions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,

    -- Contribution type
    contribution_type TEXT NOT NULL,  -- 'care_work', 'community_labor', 'availability_sharing', 'coordination'

    -- Details
    description TEXT NOT NULL,
    category TEXT,  -- Link to what kind of care/labor

    -- Time
    hours_contributed REAL NOT NULL,
    contributed_at TEXT NOT NULL,

    -- Attribution
    acknowledged_by TEXT,  -- JSON array of user IDs who witnessed/acknowledged
    acknowledgment_count INTEGER DEFAULT 0,

    -- Context
    related_exchange_id TEXT,  -- If part of a slow exchange
    related_cell_id TEXT,  -- If cell-level care work

    -- Metadata
    created_at TEXT NOT NULL,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (related_exchange_id) REFERENCES slow_exchanges(id) ON DELETE SET NULL,
    FOREIGN KEY (related_cell_id) REFERENCES cells(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_time_contributions_user ON time_contributions(user_id);
CREATE INDEX IF NOT EXISTS idx_time_contributions_type ON time_contributions(contribution_type);
CREATE INDEX IF NOT EXISTS idx_time_contributions_date ON time_contributions(contributed_at);
CREATE INDEX IF NOT EXISTS idx_time_contributions_cell ON time_contributions(related_cell_id);

-- Add temporal_justice_mode to proposals table for flexible voting deadlines
ALTER TABLE proposals ADD COLUMN temporal_justice_mode INTEGER DEFAULT 0;
ALTER TABLE proposals ADD COLUMN voting_window_days INTEGER DEFAULT 1;  -- Default 24 hours = 1 day
ALTER TABLE proposals ADD COLUMN async_participation_enabled INTEGER DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_proposals_temporal_mode ON proposals(temporal_justice_mode);

-- Add temporal_availability_preference to users table
ALTER TABLE users ADD COLUMN temporal_availability_preference TEXT DEFAULT 'synchronous';  -- 'synchronous', 'asynchronous', 'fragmented'
ALTER TABLE users ADD COLUMN has_care_responsibilities INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN prefers_slow_exchanges INTEGER DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_users_temporal_preference ON users(temporal_availability_preference);
CREATE INDEX IF NOT EXISTS idx_users_care_responsibilities ON users(has_care_responsibilities);

-- Create temporal_justice_metrics table for success tracking
CREATE TABLE IF NOT EXISTS temporal_justice_metrics (
    id TEXT PRIMARY KEY,

    -- Timeframe
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,

    -- Participation metrics
    total_active_members INTEGER DEFAULT 0,
    members_with_fragmented_availability INTEGER DEFAULT 0,
    members_with_care_responsibilities INTEGER DEFAULT 0,

    -- Exchange metrics
    total_exchanges INTEGER DEFAULT 0,
    slow_exchanges_count INTEGER DEFAULT 0,
    slow_exchanges_completed INTEGER DEFAULT 0,
    avg_slow_exchange_duration_days REAL DEFAULT 0.0,

    -- Contribution metrics
    total_time_contributions_hours REAL DEFAULT 0.0,
    care_work_acknowledged_hours REAL DEFAULT 0.0,

    -- Success metric: >30% of active members have fragmented availability
    fragmented_availability_percentage REAL DEFAULT 0.0,

    -- Metadata
    calculated_at TEXT NOT NULL,

    UNIQUE(period_start, period_end)
);

CREATE INDEX IF NOT EXISTS idx_temporal_justice_metrics_period ON temporal_justice_metrics(period_start, period_end);

-- Create async_voting_records table to track who has voted when
CREATE TABLE IF NOT EXISTS async_voting_records (
    id TEXT PRIMARY KEY,
    proposal_id TEXT NOT NULL,
    user_id TEXT NOT NULL,

    -- Vote
    vote TEXT NOT NULL,  -- 'approve', 'reject', 'abstain'

    -- Context
    voted_at TEXT NOT NULL,
    time_to_vote_hours REAL,  -- How long after proposal creation

    -- Notes
    voting_notes TEXT,  -- Why they voted this way

    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(proposal_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_async_voting_proposal ON async_voting_records(proposal_id);
CREATE INDEX IF NOT EXISTS idx_async_voting_user ON async_voting_records(user_id);
CREATE INDEX IF NOT EXISTS idx_async_voting_voted_at ON async_voting_records(voted_at);

-- Create chunk_offers table for "I have 30 min Tuesday, 45 min Friday" style offers
CREATE TABLE IF NOT EXISTS chunk_offers (
    id TEXT PRIMARY KEY,
    proposal_id TEXT NOT NULL,  -- Links to the main offer proposal
    user_id TEXT NOT NULL,

    -- Chunk details
    availability_window_id TEXT NOT NULL,  -- Links to specific availability window

    -- What they're offering in this chunk
    what_offered TEXT NOT NULL,
    category TEXT NOT NULL,

    -- Status
    status TEXT DEFAULT 'available',  -- 'available', 'claimed', 'completed'

    -- If claimed/matched
    claimed_by_user_id TEXT,
    claimed_at TEXT,

    -- Metadata
    created_at TEXT NOT NULL,
    completed_at TEXT,

    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (availability_window_id) REFERENCES availability_windows(id) ON DELETE CASCADE,
    FOREIGN KEY (claimed_by_user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_chunk_offers_proposal ON chunk_offers(proposal_id);
CREATE INDEX IF NOT EXISTS idx_chunk_offers_user ON chunk_offers(user_id);
CREATE INDEX IF NOT EXISTS idx_chunk_offers_status ON chunk_offers(status);
CREATE INDEX IF NOT EXISTS idx_chunk_offers_availability ON chunk_offers(availability_window_id);
