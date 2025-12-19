-- Migration 003: Add Local Cells (Molecules) for human-scale coordination
--
-- Cells are geographic communities of 5-50 people who can meet IRL.
-- Cells provide the fundamental organizing unit of the mesh network.

PRAGMA foreign_keys = ON;

-- Create cells table
CREATE TABLE IF NOT EXISTS cells (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    location_lat REAL,
    location_lon REAL,
    radius_km REAL DEFAULT 5.0,
    created_at TEXT NOT NULL,
    member_count INTEGER DEFAULT 0,
    max_members INTEGER DEFAULT 50,
    is_accepting_members INTEGER DEFAULT 1,
    settings TEXT DEFAULT '{}'  -- JSON: min_trust_to_join, vouch_requirement, etc.
);

CREATE INDEX IF NOT EXISTS idx_cells_location ON cells(location_lat, location_lon);
CREATE INDEX IF NOT EXISTS idx_cells_accepting ON cells(is_accepting_members);

-- Create cell_memberships table
CREATE TABLE IF NOT EXISTS cell_memberships (
    id TEXT PRIMARY KEY,
    cell_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    role TEXT DEFAULT 'member',  -- 'member', 'steward'
    joined_at TEXT NOT NULL,
    vouched_by TEXT,  -- User ID who vouched them in
    term_start_date TEXT,  -- For stewards
    term_end_date TEXT,  -- For stewards (enforced rotation)
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY (cell_id) REFERENCES cells(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (vouched_by) REFERENCES users(id) ON DELETE SET NULL,
    UNIQUE(cell_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_cell_memberships_cell ON cell_memberships(cell_id);
CREATE INDEX IF NOT EXISTS idx_cell_memberships_user ON cell_memberships(user_id);
CREATE INDEX IF NOT EXISTS idx_cell_memberships_role ON cell_memberships(role);
CREATE INDEX IF NOT EXISTS idx_cell_memberships_active ON cell_memberships(is_active);

-- Create cell_settings table for configurable rules
CREATE TABLE IF NOT EXISTS cell_settings (
    cell_id TEXT PRIMARY KEY,
    min_trust_to_join REAL DEFAULT 0.5,
    offer_default_scope TEXT DEFAULT 'cell',  -- 'cell', 'region', 'network'
    vouch_requirement TEXT DEFAULT 'any_member',  -- 'any_member', 'steward_only', 'consensus'
    steward_term_days INTEGER DEFAULT 90,
    max_concurrent_stewards INTEGER DEFAULT 3,
    requires_physical_meetup INTEGER DEFAULT 1,
    FOREIGN KEY (cell_id) REFERENCES cells(id) ON DELETE CASCADE
);

-- Add cell_id to existing tables for cell-scoped data
ALTER TABLE proposals ADD COLUMN cell_id TEXT;
CREATE INDEX IF NOT EXISTS idx_proposals_cell ON proposals(cell_id);

-- Note: For ValueFlows tables (listings, matches, exchanges), we'll need to add
-- cell_id when those tables are created. For now, community_id serves as the scope.

-- Create cell_invitations table
CREATE TABLE IF NOT EXISTS cell_invitations (
    id TEXT PRIMARY KEY,
    cell_id TEXT NOT NULL,
    inviter_id TEXT NOT NULL,
    invitee_id TEXT NOT NULL,
    status TEXT DEFAULT 'pending',  -- 'pending', 'accepted', 'rejected', 'expired'
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    responded_at TEXT,
    FOREIGN KEY (cell_id) REFERENCES cells(id) ON DELETE CASCADE,
    FOREIGN KEY (inviter_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (invitee_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_cell_invitations_cell ON cell_invitations(cell_id);
CREATE INDEX IF NOT EXISTS idx_cell_invitations_invitee ON cell_invitations(invitee_id);
CREATE INDEX IF NOT EXISTS idx_cell_invitations_status ON cell_invitations(status);

-- Create cell_events table for tracking cell gatherings
CREATE TABLE IF NOT EXISTS cell_events (
    id TEXT PRIMARY KEY,
    cell_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    event_type TEXT DEFAULT 'gathering',  -- 'gathering', 'exchange', 'decision_making'
    location_description TEXT,
    scheduled_at TEXT NOT NULL,
    duration_minutes INTEGER DEFAULT 120,
    max_participants INTEGER,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (cell_id) REFERENCES cells(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_cell_events_cell ON cell_events(cell_id);
CREATE INDEX IF NOT EXISTS idx_cell_events_scheduled ON cell_events(scheduled_at);
