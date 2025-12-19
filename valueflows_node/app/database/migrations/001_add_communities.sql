-- Migration 001: Add Communities and Community Memberships
--
-- Creates the communities table and community_memberships table
-- to support multi-community operation.

PRAGMA foreign_keys = ON;

-- =============================================================================
-- COMMUNITIES
-- =============================================================================

CREATE TABLE IF NOT EXISTS communities (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL,
    settings TEXT DEFAULT '{}',  -- JSON
    is_public INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_communities_name ON communities(name);
CREATE INDEX IF NOT EXISTS idx_communities_is_public ON communities(is_public);

-- =============================================================================
-- COMMUNITY MEMBERSHIPS
-- =============================================================================

CREATE TABLE IF NOT EXISTS community_memberships (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    community_id TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'member' CHECK(role IN ('creator', 'admin', 'member')),
    joined_at TEXT NOT NULL,
    FOREIGN KEY (community_id) REFERENCES communities(id) ON DELETE CASCADE,
    UNIQUE(user_id, community_id)
);

CREATE INDEX IF NOT EXISTS idx_memberships_user ON community_memberships(user_id);
CREATE INDEX IF NOT EXISTS idx_memberships_community ON community_memberships(community_id);
CREATE INDEX IF NOT EXISTS idx_memberships_role ON community_memberships(role);

-- =============================================================================
-- METADATA
-- =============================================================================

-- Record migration version
INSERT OR REPLACE INTO metadata (key, value) VALUES ('migration_001_applied', datetime('now'));
