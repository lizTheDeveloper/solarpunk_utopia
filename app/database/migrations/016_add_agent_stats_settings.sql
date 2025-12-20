-- Migration 018: Add Agent Stats and Settings Tables
-- Addresses GAP-66, GAP-67, GAP-68 (fix-mock-data proposal)

-- Agent runs tracking table
CREATE TABLE IF NOT EXISTS agent_runs (
    id TEXT PRIMARY KEY,
    agent_name TEXT NOT NULL,
    run_at TEXT NOT NULL,
    proposals_created INTEGER NOT NULL DEFAULT 0,
    errors TEXT,
    duration_seconds REAL,
    status TEXT NOT NULL DEFAULT 'completed'
);

CREATE INDEX IF NOT EXISTS idx_agent_runs_agent_name ON agent_runs(agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_runs_run_at ON agent_runs(run_at DESC);

-- Agent settings persistence table
CREATE TABLE IF NOT EXISTS agent_settings (
    agent_name TEXT PRIMARY KEY,
    settings TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_agent_settings_updated_at ON agent_settings(updated_at DESC);
