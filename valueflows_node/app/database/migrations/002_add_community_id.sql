-- Migration 002: Add community_id to key tables for multi-community support
--
-- Adds community_id column to listings, matches, and exchanges
-- to support multiple communities on a single server.

PRAGMA foreign_keys = ON;

-- Add community_id to listings table
ALTER TABLE listings ADD COLUMN community_id TEXT;

-- Add community_id to matches table
ALTER TABLE matches ADD COLUMN community_id TEXT;

-- Add community_id to exchanges table
ALTER TABLE exchanges ADD COLUMN community_id TEXT;

-- Create indexes for efficient community-scoped queries
CREATE INDEX IF NOT EXISTS idx_listings_community ON listings(community_id);
CREATE INDEX IF NOT EXISTS idx_matches_community ON matches(community_id);
CREATE INDEX IF NOT EXISTS idx_exchanges_community ON exchanges(community_id);

-- Note: For existing data, you should run:
-- UPDATE listings SET community_id = 'default' WHERE community_id IS NULL;
-- UPDATE matches SET community_id = 'default' WHERE community_id IS NULL;
-- UPDATE exchanges SET community_id = 'default' WHERE community_id IS NULL;
