-- Migration 009: Add Ancestor Voting - Ghost Reputation for Marginalized Voices
--
-- "The only good authority is a dead one." - Mikhail Bakunin
--
-- Reputation systems create power hierarchies. Long-term members accumulate
-- influence while newcomers struggle to be heard. This migration implements
-- the "Ghost in the Shell" protocol - when members leave or die, their
-- reputation becomes a Memorial Fund that stewards can use to boost
-- proposals from marginalized voices.
--
-- The ancestors vote for the voiceless.

PRAGMA foreign_keys = ON;

-- Create memorial_funds table
CREATE TABLE IF NOT EXISTS memorial_funds (
    id TEXT PRIMARY KEY,

    -- Source
    created_from_user_id TEXT NOT NULL,
    departed_user_name TEXT NOT NULL,
    departed_user_display_name TEXT,  -- Optional display name

    -- Reputation balance
    initial_reputation REAL NOT NULL,
    current_balance REAL NOT NULL,

    -- Metadata
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,

    -- Privacy
    family_requested_removal INTEGER DEFAULT 0,
    removal_requested_at TEXT,

    FOREIGN KEY (created_from_user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_memorial_funds_user ON memorial_funds(created_from_user_id);
CREATE INDEX IF NOT EXISTS idx_memorial_funds_created ON memorial_funds(created_at);
CREATE INDEX IF NOT EXISTS idx_memorial_funds_balance ON memorial_funds(current_balance);

-- Create ghost_reputation_allocations table
CREATE TABLE IF NOT EXISTS ghost_reputation_allocations (
    id TEXT PRIMARY KEY,
    fund_id TEXT NOT NULL,
    proposal_id TEXT NOT NULL,

    -- Allocation details
    amount REAL NOT NULL,
    allocated_by TEXT NOT NULL,  -- Steward who allocated
    reason TEXT NOT NULL,  -- Required justification

    -- Status
    status TEXT DEFAULT 'active',  -- 'active', 'refunded', 'completed'
    refunded INTEGER DEFAULT 0,
    refund_reason TEXT,

    -- Timestamps
    allocated_at TEXT NOT NULL,
    refunded_at TEXT,
    completed_at TEXT,

    -- Anti-abuse: veto window
    veto_deadline TEXT NOT NULL,  -- 24 hours from allocation
    vetoed INTEGER DEFAULT 0,
    vetoed_by TEXT,
    veto_reason TEXT,
    vetoed_at TEXT,

    FOREIGN KEY (fund_id) REFERENCES memorial_funds(id) ON DELETE CASCADE,
    FOREIGN KEY (allocated_by) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (vetoed_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_ghost_allocations_fund ON ghost_reputation_allocations(fund_id);
CREATE INDEX IF NOT EXISTS idx_ghost_allocations_proposal ON ghost_reputation_allocations(proposal_id);
CREATE INDEX IF NOT EXISTS idx_ghost_allocations_allocator ON ghost_reputation_allocations(allocated_by);
CREATE INDEX IF NOT EXISTS idx_ghost_allocations_status ON ghost_reputation_allocations(status);
CREATE INDEX IF NOT EXISTS idx_ghost_allocations_veto_deadline ON ghost_reputation_allocations(veto_deadline);

-- Create proposal_ancestor_attribution table
CREATE TABLE IF NOT EXISTS proposal_ancestor_attribution (
    id TEXT PRIMARY KEY,
    proposal_id TEXT NOT NULL,
    allocation_id TEXT NOT NULL,
    fund_id TEXT NOT NULL,

    -- Attribution details
    ancestor_name TEXT NOT NULL,
    reputation_amount REAL NOT NULL,

    -- Impact tracking
    proposal_status TEXT NOT NULL,  -- 'pending', 'approved', 'rejected', 'implemented'
    attributed_at TEXT NOT NULL,

    FOREIGN KEY (allocation_id) REFERENCES ghost_reputation_allocations(id) ON DELETE CASCADE,
    FOREIGN KEY (fund_id) REFERENCES memorial_funds(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_ancestor_attribution_proposal ON proposal_ancestor_attribution(proposal_id);
CREATE INDEX IF NOT EXISTS idx_ancestor_attribution_allocation ON proposal_ancestor_attribution(allocation_id);
CREATE INDEX IF NOT EXISTS idx_ancestor_attribution_fund ON proposal_ancestor_attribution(fund_id);
CREATE INDEX IF NOT EXISTS idx_ancestor_attribution_status ON proposal_ancestor_attribution(proposal_status);

-- Create user_departure_records table
CREATE TABLE IF NOT EXISTS user_departure_records (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,

    -- Departure details
    departure_type TEXT NOT NULL,  -- 'voluntary', 'death', 'removal', 'inactive'
    departure_reason TEXT,

    -- Reputation transfer
    final_reputation REAL NOT NULL,
    memorial_fund_id TEXT,

    -- Data handling
    private_data_purged INTEGER DEFAULT 0,
    purged_at TEXT,
    public_contributions_retained INTEGER DEFAULT 1,

    -- Metadata
    departed_at TEXT NOT NULL,
    recorded_by TEXT,  -- Who recorded the departure (admin, steward, family)

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (memorial_fund_id) REFERENCES memorial_funds(id) ON DELETE SET NULL,
    FOREIGN KEY (recorded_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_user_departure_user ON user_departure_records(user_id);
CREATE INDEX IF NOT EXISTS idx_user_departure_type ON user_departure_records(departure_type);
CREATE INDEX IF NOT EXISTS idx_user_departure_date ON user_departure_records(departed_at);
CREATE INDEX IF NOT EXISTS idx_user_departure_memorial ON user_departure_records(memorial_fund_id);

-- Create allocation_priorities table (marginalized voices tracking)
CREATE TABLE IF NOT EXISTS allocation_priorities (
    id TEXT PRIMARY KEY,
    allocation_id TEXT NOT NULL,

    -- Priority factors
    is_new_member INTEGER DEFAULT 0,  -- <3 months
    has_low_reputation INTEGER DEFAULT 0,
    is_controversial INTEGER DEFAULT 0,
    is_marginalized_identity INTEGER DEFAULT 0,  -- Self-disclosed

    -- Scores (calculated)
    priority_score INTEGER NOT NULL,  -- Higher = more priority

    -- Metadata
    calculated_at TEXT NOT NULL,

    FOREIGN KEY (allocation_id) REFERENCES ghost_reputation_allocations(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_allocation_priorities_allocation ON allocation_priorities(allocation_id);
CREATE INDEX IF NOT EXISTS idx_allocation_priorities_score ON allocation_priorities(priority_score);

-- Create memorial_impact_tracking table
CREATE TABLE IF NOT EXISTS memorial_impact_tracking (
    id TEXT PRIMARY KEY,
    fund_id TEXT NOT NULL,

    -- Impact metrics
    total_allocated REAL NOT NULL DEFAULT 0.0,
    total_refunded REAL NOT NULL DEFAULT 0.0,
    proposals_boosted INTEGER NOT NULL DEFAULT 0,
    proposals_approved INTEGER NOT NULL DEFAULT 0,
    proposals_implemented INTEGER NOT NULL DEFAULT 0,

    -- Marginalized voice metrics
    new_members_helped INTEGER NOT NULL DEFAULT 0,
    controversial_proposals_boosted INTEGER NOT NULL DEFAULT 0,

    -- Metadata
    last_updated TEXT NOT NULL,

    FOREIGN KEY (fund_id) REFERENCES memorial_funds(id) ON DELETE CASCADE,
    UNIQUE(fund_id)
);

CREATE INDEX IF NOT EXISTS idx_memorial_impact_fund ON memorial_impact_tracking(fund_id);

-- Create allocation_audit_log table (transparency)
CREATE TABLE IF NOT EXISTS allocation_audit_log (
    id TEXT PRIMARY KEY,
    allocation_id TEXT NOT NULL,

    -- Audit details
    action TEXT NOT NULL,  -- 'allocated', 'vetoed', 'refunded', 'completed'
    actor_id TEXT NOT NULL,
    actor_role TEXT NOT NULL,  -- 'steward', 'system'

    -- Context
    details TEXT,  -- JSON with additional context

    -- Timestamp
    logged_at TEXT NOT NULL,

    FOREIGN KEY (allocation_id) REFERENCES ghost_reputation_allocations(id) ON DELETE CASCADE,
    FOREIGN KEY (actor_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_allocation_audit_allocation ON allocation_audit_log(allocation_id);
CREATE INDEX IF NOT EXISTS idx_allocation_audit_actor ON allocation_audit_log(actor_id);
CREATE INDEX IF NOT EXISTS idx_allocation_audit_logged ON allocation_audit_log(logged_at);
CREATE INDEX IF NOT EXISTS idx_allocation_audit_action ON allocation_audit_log(action);
