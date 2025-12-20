-- Migration 008: Add Saturnalia Protocol - Prevent Role Crystallization
--
-- "All authority is a mask, not a face." - Paulo Freire
--
-- Power crystallizes. Even in anarchist systems, informal hierarchies emerge.
-- The Saturnalia Protocol creates temporary inversions to prevent roles from
-- hardening into identities.
--
-- Named after the Roman festival where masters served slaves, creating
-- temporary social fluidity to prevent permanent ossification.
--
-- MODES:
-- - Role Swap: Stewards become regular members, new stewards randomly selected
-- - Anonymous Period: All posts/offers/needs are anonymous
-- - Reputation Blindness: Trust scores hidden from UI
-- - Random Facilitation: Meeting facilitators chosen randomly, not by seniority
-- - Voice Inversion: New members' voices weighted higher in polls

PRAGMA foreign_keys = ON;

-- Create saturnalia_config table
CREATE TABLE IF NOT EXISTS saturnalia_config (
    id TEXT PRIMARY KEY,
    cell_id TEXT,  -- NULL means network-wide
    community_id TEXT,  -- NULL means all communities

    -- Configuration
    enabled INTEGER DEFAULT 1,

    -- Modes (JSON array of enabled modes)
    enabled_modes TEXT NOT NULL,  -- JSON: ["role_swap", "anonymous_period", "reputation_blindness", "random_facilitation", "voice_inversion"]

    -- Schedule
    frequency TEXT NOT NULL,  -- 'annually', 'biannually', 'quarterly', 'manual'
    duration_hours INTEGER NOT NULL,  -- How long each event lasts

    -- Safety boundaries
    exclude_safety_critical INTEGER DEFAULT 1,  -- Exclude panic, sanctuary, rapid response
    allow_individual_opt_out INTEGER DEFAULT 1,

    -- Next event
    next_scheduled_start TEXT,

    -- Metadata
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    created_by TEXT NOT NULL,

    FOREIGN KEY (cell_id) REFERENCES cells(id) ON DELETE CASCADE,
    FOREIGN KEY (community_id) REFERENCES communities(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_saturnalia_config_cell ON saturnalia_config(cell_id);
CREATE INDEX IF NOT EXISTS idx_saturnalia_config_community ON saturnalia_config(community_id);
CREATE INDEX IF NOT EXISTS idx_saturnalia_config_enabled ON saturnalia_config(enabled);
CREATE INDEX IF NOT EXISTS idx_saturnalia_config_next_scheduled ON saturnalia_config(next_scheduled_start);

-- Create saturnalia_events table
CREATE TABLE IF NOT EXISTS saturnalia_events (
    id TEXT PRIMARY KEY,
    config_id TEXT NOT NULL,

    -- Event details
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,

    -- Modes active during this event
    active_modes TEXT NOT NULL,  -- JSON array

    -- Status
    status TEXT DEFAULT 'scheduled',  -- 'scheduled', 'active', 'completed', 'cancelled'

    -- Triggered by
    trigger_type TEXT NOT NULL,  -- 'scheduled', 'manual'
    triggered_by TEXT,  -- User ID if manual trigger

    -- Metadata
    created_at TEXT NOT NULL,
    activated_at TEXT,
    completed_at TEXT,
    cancelled_at TEXT,
    cancellation_reason TEXT,

    FOREIGN KEY (config_id) REFERENCES saturnalia_config(id) ON DELETE CASCADE,
    FOREIGN KEY (triggered_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_saturnalia_events_config ON saturnalia_events(config_id);
CREATE INDEX IF NOT EXISTS idx_saturnalia_events_status ON saturnalia_events(status);
CREATE INDEX IF NOT EXISTS idx_saturnalia_events_start ON saturnalia_events(start_time);
CREATE INDEX IF NOT EXISTS idx_saturnalia_events_end ON saturnalia_events(end_time);

-- Create saturnalia_role_swaps table
CREATE TABLE IF NOT EXISTS saturnalia_role_swaps (
    id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,

    -- Original role holder
    original_user_id TEXT NOT NULL,
    original_role TEXT NOT NULL,  -- 'steward', 'facilitator', etc.

    -- Temporary role holder
    temporary_user_id TEXT NOT NULL,

    -- Scope
    scope_type TEXT NOT NULL,  -- 'cell', 'community', 'network'
    scope_id TEXT,  -- ID of cell/community if applicable

    -- Status
    status TEXT DEFAULT 'active',  -- 'active', 'restored'

    -- Metadata
    swapped_at TEXT NOT NULL,
    restored_at TEXT,

    FOREIGN KEY (event_id) REFERENCES saturnalia_events(id) ON DELETE CASCADE,
    FOREIGN KEY (original_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (temporary_user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_saturnalia_role_swaps_event ON saturnalia_role_swaps(event_id);
CREATE INDEX IF NOT EXISTS idx_saturnalia_role_swaps_original_user ON saturnalia_role_swaps(original_user_id);
CREATE INDEX IF NOT EXISTS idx_saturnalia_role_swaps_temporary_user ON saturnalia_role_swaps(temporary_user_id);
CREATE INDEX IF NOT EXISTS idx_saturnalia_role_swaps_status ON saturnalia_role_swaps(status);

-- Create saturnalia_opt_outs table
CREATE TABLE IF NOT EXISTS saturnalia_opt_outs (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,

    -- Opt-out scope
    mode TEXT NOT NULL,  -- Which mode they're opting out of
    scope_type TEXT NOT NULL,  -- 'all', 'cell', 'community'
    scope_id TEXT,  -- Cell or community ID if applicable

    -- Reason (optional, for learning)
    reason TEXT,

    -- Duration
    is_permanent INTEGER DEFAULT 0,
    expires_at TEXT,  -- NULL if permanent

    -- Metadata
    opted_out_at TEXT NOT NULL,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_saturnalia_opt_outs_user ON saturnalia_opt_outs(user_id);
CREATE INDEX IF NOT EXISTS idx_saturnalia_opt_outs_mode ON saturnalia_opt_outs(mode);
CREATE INDEX IF NOT EXISTS idx_saturnalia_opt_outs_expires ON saturnalia_opt_outs(expires_at);

-- Create saturnalia_anonymous_posts table (for revealing authors after event)
CREATE TABLE IF NOT EXISTS saturnalia_anonymous_posts (
    id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,

    -- Post details
    post_type TEXT NOT NULL,  -- 'offer', 'need', 'message', 'proposal'
    post_id TEXT NOT NULL,  -- ID of the actual post
    actual_author_id TEXT NOT NULL,  -- Hidden during event, revealed after

    -- Metadata
    created_at TEXT NOT NULL,
    revealed_at TEXT,

    FOREIGN KEY (event_id) REFERENCES saturnalia_events(id) ON DELETE CASCADE,
    FOREIGN KEY (actual_author_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_saturnalia_anonymous_posts_event ON saturnalia_anonymous_posts(event_id);
CREATE INDEX IF NOT EXISTS idx_saturnalia_anonymous_posts_post_id ON saturnalia_anonymous_posts(post_id);
CREATE INDEX IF NOT EXISTS idx_saturnalia_anonymous_posts_author ON saturnalia_anonymous_posts(actual_author_id);

-- Create saturnalia_reflections table (post-event learning)
CREATE TABLE IF NOT EXISTS saturnalia_reflections (
    id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    user_id TEXT NOT NULL,

    -- Reflection
    what_learned TEXT NOT NULL,
    what_surprised TEXT,
    what_changed TEXT,

    -- Suggestions
    suggestions TEXT,

    -- Rating (1-5)
    overall_rating INTEGER,
    would_do_again INTEGER DEFAULT 1,

    -- Metadata
    submitted_at TEXT NOT NULL,

    FOREIGN KEY (event_id) REFERENCES saturnalia_events(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(event_id, user_id)  -- One reflection per user per event
);

CREATE INDEX IF NOT EXISTS idx_saturnalia_reflections_event ON saturnalia_reflections(event_id);
CREATE INDEX IF NOT EXISTS idx_saturnalia_reflections_user ON saturnalia_reflections(user_id);
CREATE INDEX IF NOT EXISTS idx_saturnalia_reflections_rating ON saturnalia_reflections(overall_rating);
