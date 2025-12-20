-- Migration: Abundance Osmosis (GAP-63)
-- Kropotkin: In nature, abundance spreads without explicit transactions
-- Date: 2025-12-20

-- Community Shelves: "Take what you need" spaces
CREATE TABLE IF NOT EXISTS community_shelves (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    location TEXT NOT NULL,
    created_by TEXT NOT NULL,  -- Steward who created it
    cell_id TEXT NOT NULL,
    is_virtual INTEGER DEFAULT 0,  -- 0 = physical, 1 = virtual
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (created_by) REFERENCES agents(id),
    FOREIGN KEY (cell_id) REFERENCES local_cells(id)
);

-- Items on community shelves
-- NOTE: No tracking of who took what. When taken, item is deleted.
CREATE TABLE IF NOT EXISTS shelf_items (
    id TEXT PRIMARY KEY,
    shelf_id TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL,  -- "food", "tools", "books", etc.
    added_at TEXT NOT NULL DEFAULT (datetime('now')),
    added_by TEXT,  -- NULL if anonymous (GAP-61)
    still_available INTEGER DEFAULT 1,
    FOREIGN KEY (shelf_id) REFERENCES community_shelves(id) ON DELETE CASCADE,
    FOREIGN KEY (added_by) REFERENCES agents(id)
);

-- Circulating Resources: Shared items tracked by location, not ownership
CREATE TABLE IF NOT EXISTS circulating_resources (
    id TEXT PRIMARY KEY,
    description TEXT NOT NULL,  -- "Dewalt drill"
    category TEXT NOT NULL,  -- "tools"
    current_location TEXT NOT NULL,  -- "Alice's garage" (location, not ownership)
    current_holder_notes TEXT,  -- "Needs new battery"
    last_updated TEXT NOT NULL DEFAULT (datetime('now')),
    cell_id TEXT NOT NULL,
    FOREIGN KEY (cell_id) REFERENCES local_cells(id)
);

-- Overflow Prompts: Gentle suggestions when offers sit too long
CREATE TABLE IF NOT EXISTS overflow_prompts (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    listing_id TEXT NOT NULL,
    days_available INTEGER NOT NULL,
    prompted_at TEXT NOT NULL DEFAULT (datetime('now')),
    status TEXT DEFAULT 'pending',  -- pending, accepted, declined, snoozed
    snoozed_until TEXT,
    FOREIGN KEY (user_id) REFERENCES agents(id),
    FOREIGN KEY (listing_id) REFERENCES listings(id)
);

-- Knowledge Ripples: Suggestions to teach what you learned
CREATE TABLE IF NOT EXISTS knowledge_ripples (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    exchange_id TEXT NOT NULL,
    skill_learned TEXT NOT NULL,
    learned_at TEXT NOT NULL,
    prompted_at TEXT,
    status TEXT DEFAULT 'pending',  -- pending, prompted, accepted, declined, dismissed
    permanently_dismissed INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES agents(id),
    FOREIGN KEY (exchange_id) REFERENCES exchanges(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_shelf_items_shelf ON shelf_items(shelf_id);
CREATE INDEX IF NOT EXISTS idx_shelf_items_available ON shelf_items(still_available);
CREATE INDEX IF NOT EXISTS idx_circulating_resources_cell ON circulating_resources(cell_id);
CREATE INDEX IF NOT EXISTS idx_overflow_prompts_user ON overflow_prompts(user_id);
CREATE INDEX IF NOT EXISTS idx_overflow_prompts_status ON overflow_prompts(status);
CREATE INDEX IF NOT EXISTS idx_knowledge_ripples_user ON knowledge_ripples(user_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_ripples_status ON knowledge_ripples(status);
