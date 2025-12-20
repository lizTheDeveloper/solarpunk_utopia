-- Migration: Multi-Steward Sanctuary Verification (GAP-109)
-- Date: 2025-12-19
-- Purpose: Require 2+ steward verifications for sanctuary resources

PRAGMA foreign_keys = ON;

-- Create base sanctuary_resources table (if it doesn't exist)
CREATE TABLE IF NOT EXISTS sanctuary_resources (
    id TEXT PRIMARY KEY,
    resource_type TEXT NOT NULL CHECK(resource_type IN ('safe_space', 'transport', 'legal', 'supplies', 'skills', 'intel')),
    description TEXT NOT NULL,
    offered_by TEXT NOT NULL,
    sensitivity TEXT NOT NULL CHECK(sensitivity IN ('HIGH', 'MEDIUM', 'LOW')),
    trust_threshold REAL NOT NULL,  -- Minimum trust score required to see this resource
    cell_id TEXT,
    verified_at TEXT,  -- When first verified
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (offered_by) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (cell_id) REFERENCES cells(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_sanctuary_resources_type ON sanctuary_resources(resource_type);
CREATE INDEX IF NOT EXISTS idx_sanctuary_resources_sensitivity ON sanctuary_resources(sensitivity);
CREATE INDEX IF NOT EXISTS idx_sanctuary_resources_cell ON sanctuary_resources(cell_id);

-- Create base sanctuary_requests table (if it doesn't exist)
CREATE TABLE IF NOT EXISTS sanctuary_requests (
    id TEXT PRIMARY KEY,
    request_type TEXT NOT NULL CHECK(request_type IN ('safe_space', 'transport', 'legal', 'supplies', 'skills', 'intel')),
    description TEXT NOT NULL,
    requested_by TEXT NOT NULL,
    verified_by_steward TEXT,  -- Steward who verified this is legitimate
    urgency TEXT NOT NULL CHECK(urgency IN ('CRITICAL', 'URGENT', 'MODERATE')),
    cell_id TEXT,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'matched', 'completed', 'purged')),
    created_at TEXT DEFAULT (datetime('now')),
    purge_at TEXT,  -- Auto-delete time
    FOREIGN KEY (requested_by) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (verified_by_steward) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (cell_id) REFERENCES cells(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_sanctuary_requests_type ON sanctuary_requests(request_type);
CREATE INDEX IF NOT EXISTS idx_sanctuary_requests_urgency ON sanctuary_requests(urgency);
CREATE INDEX IF NOT EXISTS idx_sanctuary_requests_status ON sanctuary_requests(status);
CREATE INDEX IF NOT EXISTS idx_sanctuary_requests_cell ON sanctuary_requests(cell_id);
CREATE INDEX IF NOT EXISTS idx_sanctuary_requests_purge ON sanctuary_requests(purge_at);

-- Table: sanctuary_verifications
-- Tracks individual steward verifications for sanctuary resources
CREATE TABLE IF NOT EXISTS sanctuary_verifications (
    id TEXT PRIMARY KEY,
    resource_id TEXT NOT NULL,
    steward_id TEXT NOT NULL,
    verified_at TEXT NOT NULL,
    verification_method TEXT NOT NULL CHECK(verification_method IN ('in_person', 'video_call', 'trusted_referral')),
    notes TEXT,  -- Encrypted steward-only notes
    escape_routes_verified INTEGER DEFAULT 0,
    capacity_verified INTEGER DEFAULT 0,
    buddy_protocol_available INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (resource_id) REFERENCES sanctuary_resources(id) ON DELETE CASCADE,
    UNIQUE(resource_id, steward_id)  -- One verification per steward per resource
);

CREATE INDEX IF NOT EXISTS idx_sanctuary_verifications_resource
    ON sanctuary_verifications(resource_id);
CREATE INDEX IF NOT EXISTS idx_sanctuary_verifications_steward
    ON sanctuary_verifications(steward_id);

-- Table: sanctuary_uses
-- Tracks successful sanctuary uses for quality filtering
CREATE TABLE IF NOT EXISTS sanctuary_uses (
    id TEXT PRIMARY KEY,
    resource_id TEXT NOT NULL,
    request_id TEXT NOT NULL,
    completed_at TEXT NOT NULL,
    outcome TEXT NOT NULL CHECK(outcome IN ('success', 'failed', 'compromised')),
    purge_at TEXT NOT NULL,  -- Auto-delete after 30 days
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (resource_id) REFERENCES sanctuary_resources(id) ON DELETE CASCADE,
    FOREIGN KEY (request_id) REFERENCES sanctuary_requests(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_sanctuary_uses_resource
    ON sanctuary_uses(resource_id);
CREATE INDEX IF NOT EXISTS idx_sanctuary_uses_purge
    ON sanctuary_uses(purge_at);

-- Add columns to sanctuary_resources for multi-steward verification
-- Note: SQLite doesn't support adding columns with CHECK constraints in ALTER TABLE,
-- so we check these at the application level

-- first_verified_at: When first steward verified
ALTER TABLE sanctuary_resources
    ADD COLUMN first_verified_at TEXT;

-- last_check: Most recent verification check
ALTER TABLE sanctuary_resources
    ADD COLUMN last_check TEXT;

-- expires_at: When verification expires (90 days from last_check)
ALTER TABLE sanctuary_resources
    ADD COLUMN expires_at TEXT;

-- successful_uses: Count of successful sanctuary uses (for critical need filtering)
ALTER TABLE sanctuary_resources
    ADD COLUMN successful_uses INTEGER DEFAULT 0;

-- Update existing verified resources to have first_verified_at = verified_at
UPDATE sanctuary_resources
SET first_verified_at = verified_at
WHERE verified_at IS NOT NULL;

-- Update existing verified resources to have last_check = verified_at
UPDATE sanctuary_resources
SET last_check = verified_at
WHERE verified_at IS NOT NULL;

-- Update existing verified resources to set expires_at = 90 days from now (grace period)
UPDATE sanctuary_resources
SET expires_at = datetime(datetime('now'), '+90 days')
WHERE verified_at IS NOT NULL;
