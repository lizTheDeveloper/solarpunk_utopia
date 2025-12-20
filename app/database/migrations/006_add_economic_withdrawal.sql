-- Migration 007: Add Economic Withdrawal - Coordinated Wealth Deconcentration
--
-- Every transaction in the gift economy is a transaction that DIDN'T go to Bezos.
--
-- This is economic strike as praxis. Coordinated campaigns to redirect spending
-- from extractive corporations to regenerative community systems.
--
-- CAMPAIGN TYPES:
-- - Amazon Exit: Collective boycott + local alternatives
-- - Local Food Shift: Redirect grocery spending to community sources
-- - Tool Library: Eliminate individual purchases through sharing
-- - Skill Share: Replace credentialing with free exchange
-- - Housing Mutual Aid: Co-ops instead of rent extraction
-- - Transport Commons: Ride shares instead of Uber/cars

PRAGMA foreign_keys = ON;

-- Create campaigns table
CREATE TABLE IF NOT EXISTS campaigns (
    id TEXT PRIMARY KEY,
    campaign_type TEXT NOT NULL,  -- 'amazon_exit', 'local_food_shift', 'tool_library', etc.
    name TEXT NOT NULL,
    description TEXT NOT NULL,

    -- Targeting
    target_corporation TEXT NOT NULL,
    target_category TEXT,  -- 'online_retail', 'grocery', 'transport', etc.

    -- Scope
    cell_id TEXT,
    network_wide INTEGER DEFAULT 0,

    -- Activation
    created_by TEXT NOT NULL,
    threshold_participants INTEGER NOT NULL,
    current_participants INTEGER DEFAULT 0,
    status TEXT DEFAULT 'gathering',  -- 'gathering', 'active', 'completed', 'cancelled'

    -- Timeline
    pledge_deadline TEXT NOT NULL,
    campaign_start TEXT NOT NULL,
    campaign_end TEXT NOT NULL,

    -- Impact tracking (calculated)
    estimated_economic_impact REAL,
    network_value_circulated REAL,
    local_transactions_facilitated INTEGER DEFAULT 0,

    -- Metadata
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    activated_at TEXT,
    completed_at TEXT,

    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (cell_id) REFERENCES cells(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_campaigns_type ON campaigns(campaign_type);
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status);
CREATE INDEX IF NOT EXISTS idx_campaigns_cell ON campaigns(cell_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_network_wide ON campaigns(network_wide);
CREATE INDEX IF NOT EXISTS idx_campaigns_created ON campaigns(created_at);
CREATE INDEX IF NOT EXISTS idx_campaigns_start ON campaigns(campaign_start);
CREATE INDEX IF NOT EXISTS idx_campaigns_end ON campaigns(campaign_end);

-- Create campaign_pledges table
CREATE TABLE IF NOT EXISTS campaign_pledges (
    id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL,
    user_id TEXT NOT NULL,

    -- Commitment
    commitment_level TEXT DEFAULT 'full',  -- 'full' (100%), 'partial' (reduce by %), 'explore'
    commitment_notes TEXT,

    -- Status
    status TEXT DEFAULT 'committed',  -- 'committed', 'active', 'completed', 'broken'

    -- Impact tracking (self-reported + estimated)
    times_avoided_target INTEGER DEFAULT 0,
    estimated_spending_redirected REAL,
    alternatives_used INTEGER DEFAULT 0,

    -- Buddy system (optional accountability)
    buddy_id TEXT,

    -- Metadata
    pledged_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,

    FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (buddy_id) REFERENCES users(id) ON DELETE SET NULL,
    UNIQUE(campaign_id, user_id)  -- One pledge per user per campaign
);

CREATE INDEX IF NOT EXISTS idx_campaign_pledges_campaign ON campaign_pledges(campaign_id);
CREATE INDEX IF NOT EXISTS idx_campaign_pledges_user ON campaign_pledges(user_id);
CREATE INDEX IF NOT EXISTS idx_campaign_pledges_status ON campaign_pledges(status);
CREATE INDEX IF NOT EXISTS idx_campaign_pledges_pledged ON campaign_pledges(pledged_at);

-- Create corporate_alternatives table
CREATE TABLE IF NOT EXISTS corporate_alternatives (
    id TEXT PRIMARY KEY,
    campaign_type TEXT NOT NULL,

    -- Corporate target
    replaces_corporation TEXT NOT NULL,
    replaces_service TEXT NOT NULL,

    -- Alternative details
    alternative_type TEXT NOT NULL,  -- 'network_sharing', 'local_business', 'co_op', 'mutual_aid'
    name TEXT NOT NULL,
    description TEXT NOT NULL,

    -- Availability
    cell_id TEXT,
    network_wide INTEGER DEFAULT 0,

    -- Contact/access
    contact_user_id TEXT,
    access_instructions TEXT,

    -- Usage tracking
    times_used INTEGER DEFAULT 0,

    -- Metadata
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL,

    FOREIGN KEY (cell_id) REFERENCES cells(id) ON DELETE CASCADE,
    FOREIGN KEY (contact_user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_corporate_alternatives_type ON corporate_alternatives(campaign_type);
CREATE INDEX IF NOT EXISTS idx_corporate_alternatives_cell ON corporate_alternatives(cell_id);
CREATE INDEX IF NOT EXISTS idx_corporate_alternatives_network_wide ON corporate_alternatives(network_wide);
CREATE INDEX IF NOT EXISTS idx_corporate_alternatives_times_used ON corporate_alternatives(times_used);

-- Create exit_progress table
CREATE TABLE IF NOT EXISTS exit_progress (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,

    -- Progress by category (JSON)
    categories TEXT NOT NULL,  -- JSON object with category progress
    -- Example:
    -- {
    --   "amazon": {
    --     "baseline_monthly_spending": 200.0,
    --     "current_monthly_spending": 50.0,
    --     "reduction_percent": 75.0,
    --     "last_purchase": "2025-09-15"
    --   },
    --   "grocery": {...}
    -- }

    -- Overall totals
    total_estimated_redirected REAL DEFAULT 0.0,
    campaigns_participated INTEGER DEFAULT 0,
    campaigns_completed INTEGER DEFAULT 0,

    -- Metadata
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id)  -- One progress record per user
);

CREATE INDEX IF NOT EXISTS idx_exit_progress_user ON exit_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_exit_progress_updated ON exit_progress(updated_at);

-- Create bulk_buy_orders table
CREATE TABLE IF NOT EXISTS bulk_buy_orders (
    id TEXT PRIMARY KEY,
    campaign_id TEXT,  -- Optional link to parent campaign

    -- Item details
    item_name TEXT NOT NULL,
    item_description TEXT NOT NULL,
    unit TEXT NOT NULL,  -- 'lb', 'kg', 'count'

    -- Pricing
    retail_price_per_unit REAL NOT NULL,
    wholesale_price_per_unit REAL NOT NULL,
    savings_percent REAL NOT NULL,

    -- Threshold
    minimum_units INTEGER NOT NULL,
    current_committed_units INTEGER DEFAULT 0,

    -- Coordination
    cell_id TEXT NOT NULL,
    coordinator_id TEXT NOT NULL,
    supplier TEXT,

    -- Timeline
    commitment_deadline TEXT NOT NULL,
    delivery_date TEXT NOT NULL,
    distribution_location TEXT,

    -- Status
    status TEXT DEFAULT 'gathering',  -- 'gathering', 'confirmed', 'ordered', 'delivered', 'distributed'

    -- Metadata
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,

    FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE SET NULL,
    FOREIGN KEY (cell_id) REFERENCES cells(id) ON DELETE CASCADE,
    FOREIGN KEY (coordinator_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_bulk_buy_orders_campaign ON bulk_buy_orders(campaign_id);
CREATE INDEX IF NOT EXISTS idx_bulk_buy_orders_cell ON bulk_buy_orders(cell_id);
CREATE INDEX IF NOT EXISTS idx_bulk_buy_orders_status ON bulk_buy_orders(status);
CREATE INDEX IF NOT EXISTS idx_bulk_buy_orders_deadline ON bulk_buy_orders(commitment_deadline);
CREATE INDEX IF NOT EXISTS idx_bulk_buy_orders_delivery ON bulk_buy_orders(delivery_date);

-- Create bulk_buy_commitments table
CREATE TABLE IF NOT EXISTS bulk_buy_commitments (
    id TEXT PRIMARY KEY,
    bulk_buy_id TEXT NOT NULL,
    user_id TEXT NOT NULL,

    -- Commitment
    units INTEGER NOT NULL,
    total_cost REAL NOT NULL,

    -- Payment/fulfillment
    paid INTEGER DEFAULT 0,
    picked_up INTEGER DEFAULT 0,

    -- Metadata
    committed_at TEXT NOT NULL,

    FOREIGN KEY (bulk_buy_id) REFERENCES bulk_buy_orders(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(bulk_buy_id, user_id)  -- One commitment per user per bulk buy
);

CREATE INDEX IF NOT EXISTS idx_bulk_buy_commitments_bulk_buy ON bulk_buy_commitments(bulk_buy_id);
CREATE INDEX IF NOT EXISTS idx_bulk_buy_commitments_user ON bulk_buy_commitments(user_id);
CREATE INDEX IF NOT EXISTS idx_bulk_buy_commitments_paid ON bulk_buy_commitments(paid);
CREATE INDEX IF NOT EXISTS idx_bulk_buy_commitments_picked_up ON bulk_buy_commitments(picked_up);
