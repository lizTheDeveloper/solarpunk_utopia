-- ValueFlows Node SQLite Schema (VF-Full v1.0)
-- Complete schema for all 13 VF object types
-- Includes indexes, foreign keys, and constraints

-- Enable foreign key support
PRAGMA foreign_keys = ON;

-- =============================================================================
-- AGENTS
-- =============================================================================

CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,  -- Usually Ed25519 public key
    name TEXT NOT NULL,
    agent_type TEXT NOT NULL CHECK(agent_type IN ('person', 'group', 'place')),
    description TEXT,
    image_url TEXT,
    primary_location_id TEXT,
    contact_info TEXT,  -- Can be encrypted
    created_at TEXT NOT NULL,
    updated_at TEXT,
    author TEXT,  -- Public key of creator
    signature TEXT,  -- Ed25519 signature

    -- GAP-62: Loafer's Rights (Goldman + Kropotkin) - Rest Mode Support
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'resting', 'sabbatical')),
    status_note TEXT,  -- Optional explanation: "Recovering from burnout", etc.
    status_updated_at TEXT,  -- When status was last changed

    FOREIGN KEY (primary_location_id) REFERENCES locations(id)
);

CREATE INDEX IF NOT EXISTS idx_agents_type ON agents(agent_type);
CREATE INDEX IF NOT EXISTS idx_agents_created ON agents(created_at);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_agents_resting ON agents(status) WHERE status IN ('resting', 'sabbatical');

-- =============================================================================
-- LOCATIONS
-- =============================================================================

CREATE TABLE IF NOT EXISTS locations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    address TEXT,
    latitude REAL,
    longitude REAL,
    parent_location_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT,
    author TEXT,
    signature TEXT,
    FOREIGN KEY (parent_location_id) REFERENCES locations(id)
);

CREATE INDEX IF NOT EXISTS idx_locations_parent ON locations(parent_location_id);
CREATE INDEX IF NOT EXISTS idx_locations_coords ON locations(latitude, longitude) WHERE latitude IS NOT NULL;

-- =============================================================================
-- RESOURCE SPECS
-- =============================================================================

CREATE TABLE IF NOT EXISTS resource_specs (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL CHECK(category IN ('food', 'tools', 'seeds', 'skills', 'labor', 'knowledge', 'housing', 'transportation', 'materials', 'other')),
    description TEXT,
    subcategory TEXT,
    image_url TEXT,
    default_unit TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT,
    author TEXT,
    signature TEXT,

    -- GAP-64: Battery Warlord Detection (Bakunin) - Resource Criticality
    critical BOOLEAN DEFAULT FALSE,  -- Is this a critical resource?
    criticality_reason TEXT,  -- Why is this critical? (e.g., "Only power source")
    criticality_category TEXT  -- Category: power, water, medical, communication, food, shelter, skills
);

CREATE INDEX IF NOT EXISTS idx_resource_specs_category ON resource_specs(category);
CREATE INDEX IF NOT EXISTS idx_resource_specs_subcategory ON resource_specs(subcategory);
CREATE INDEX IF NOT EXISTS idx_resource_specs_name ON resource_specs(name);
CREATE INDEX IF NOT EXISTS idx_resource_specs_critical ON resource_specs(critical) WHERE critical = TRUE;
CREATE INDEX IF NOT EXISTS idx_resource_specs_criticality_category ON resource_specs(criticality_category) WHERE criticality_category IS NOT NULL;

-- =============================================================================
-- RESOURCE INSTANCES
-- =============================================================================

CREATE TABLE IF NOT EXISTS resource_instances (
    id TEXT PRIMARY KEY,
    resource_spec_id TEXT NOT NULL,
    quantity REAL NOT NULL,
    unit TEXT NOT NULL,
    state TEXT NOT NULL CHECK(state IN ('available', 'in_use', 'in_transit', 'consumed', 'damaged', 'in_repair', 'expired')),
    current_location_id TEXT,
    label TEXT,
    description TEXT,
    image_url TEXT,
    expires_at TEXT,  -- ISO 8601 datetime
    current_custodian_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT,
    author TEXT,
    signature TEXT,
    FOREIGN KEY (resource_spec_id) REFERENCES resource_specs(id),
    FOREIGN KEY (current_location_id) REFERENCES locations(id),
    FOREIGN KEY (current_custodian_id) REFERENCES agents(id)
);

CREATE INDEX IF NOT EXISTS idx_resource_instances_spec ON resource_instances(resource_spec_id);
CREATE INDEX IF NOT EXISTS idx_resource_instances_state ON resource_instances(state);
CREATE INDEX IF NOT EXISTS idx_resource_instances_location ON resource_instances(current_location_id);
CREATE INDEX IF NOT EXISTS idx_resource_instances_expires ON resource_instances(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_resource_instances_custodian ON resource_instances(current_custodian_id);

-- =============================================================================
-- LISTINGS (Offers and Needs)
-- =============================================================================

CREATE TABLE IF NOT EXISTS listings (
    id TEXT PRIMARY KEY,
    listing_type TEXT NOT NULL CHECK(listing_type IN ('offer', 'need')),
    resource_spec_id TEXT NOT NULL,
    agent_id TEXT,  -- Nullable for anonymous gifts (GAP-61)
    anonymous INTEGER NOT NULL DEFAULT 0,  -- GAP-61: Emma Goldman - anonymous gifts
    location_id TEXT,
    quantity REAL NOT NULL DEFAULT 1.0,
    unit TEXT NOT NULL DEFAULT 'items',
    available_from TEXT,
    available_until TEXT,
    title TEXT,
    description TEXT,
    image_url TEXT,
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'fulfilled', 'expired', 'cancelled')),
    resource_instance_id TEXT,
    community_id TEXT,
    visibility TEXT CHECK(visibility IN (
        'my_cell', 'my_community', 'trusted_network', 'anyone_local', 'network_wide'
    )),  -- If NULL, use user's sharing_preference
    created_at TEXT NOT NULL,
    updated_at TEXT,
    author TEXT,
    signature TEXT,
    FOREIGN KEY (resource_spec_id) REFERENCES resource_specs(id),
    FOREIGN KEY (agent_id) REFERENCES agents(id),
    FOREIGN KEY (location_id) REFERENCES locations(id),
    FOREIGN KEY (resource_instance_id) REFERENCES resource_instances(id)
);

CREATE INDEX IF NOT EXISTS idx_listings_type ON listings(listing_type);
CREATE INDEX IF NOT EXISTS idx_listings_status ON listings(status);
CREATE INDEX IF NOT EXISTS idx_listings_spec ON listings(resource_spec_id);
CREATE INDEX IF NOT EXISTS idx_listings_agent ON listings(agent_id);
CREATE INDEX IF NOT EXISTS idx_listings_location ON listings(location_id);
CREATE INDEX IF NOT EXISTS idx_listings_created ON listings(created_at);
CREATE INDEX IF NOT EXISTS idx_listings_available_until ON listings(available_until) WHERE available_until IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_listings_community ON listings(community_id);
CREATE INDEX IF NOT EXISTS idx_listings_anonymous ON listings(anonymous) WHERE anonymous = 1;

-- Composite index for common queries
CREATE INDEX IF NOT EXISTS idx_listings_type_status ON listings(listing_type, status);
CREATE INDEX IF NOT EXISTS idx_listings_community_shelf ON listings(listing_type, anonymous, status) WHERE anonymous = 1 AND listing_type = 'offer' AND status = 'active';

-- =============================================================================
-- MATCHES
-- =============================================================================

CREATE TABLE IF NOT EXISTS matches (
    id TEXT PRIMARY KEY,
    offer_id TEXT NOT NULL,
    need_id TEXT NOT NULL,
    provider_id TEXT NOT NULL,
    receiver_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'suggested' CHECK(status IN ('suggested', 'accepted', 'rejected', 'expired')),
    provider_approved INTEGER NOT NULL DEFAULT 0,
    receiver_approved INTEGER NOT NULL DEFAULT 0,
    provider_approved_at TEXT,
    receiver_approved_at TEXT,
    match_score REAL,  -- 0.0-1.0
    match_reason TEXT,
    proposed_quantity REAL,
    proposed_unit TEXT,
    community_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT,
    author TEXT,
    signature TEXT,
    FOREIGN KEY (offer_id) REFERENCES listings(id),
    FOREIGN KEY (need_id) REFERENCES listings(id),
    FOREIGN KEY (provider_id) REFERENCES agents(id),
    FOREIGN KEY (receiver_id) REFERENCES agents(id)
);

CREATE INDEX IF NOT EXISTS idx_matches_offer ON matches(offer_id);
CREATE INDEX IF NOT EXISTS idx_matches_need ON matches(need_id);
CREATE INDEX IF NOT EXISTS idx_matches_provider ON matches(provider_id);
CREATE INDEX IF NOT EXISTS idx_matches_receiver ON matches(receiver_id);
CREATE INDEX IF NOT EXISTS idx_matches_status ON matches(status);
CREATE INDEX IF NOT EXISTS idx_matches_community ON matches(community_id);

-- =============================================================================
-- EXCHANGES
-- =============================================================================

CREATE TABLE IF NOT EXISTS exchanges (
    id TEXT PRIMARY KEY,
    match_id TEXT,
    provider_id TEXT NOT NULL,
    receiver_id TEXT NOT NULL,
    resource_spec_id TEXT NOT NULL,
    quantity REAL NOT NULL,
    unit TEXT NOT NULL,
    location_id TEXT,
    scheduled_start TEXT,
    scheduled_end TEXT,
    status TEXT NOT NULL DEFAULT 'planned' CHECK(status IN ('planned', 'in_progress', 'completed', 'cancelled')),
    constraints TEXT,
    notes TEXT,
    provider_completed INTEGER NOT NULL DEFAULT 0,
    receiver_completed INTEGER NOT NULL DEFAULT 0,
    provider_event_id TEXT,
    receiver_event_id TEXT,
    provider_commitment_id TEXT,
    receiver_commitment_id TEXT,
    community_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT,
    author TEXT,
    signature TEXT,
    FOREIGN KEY (match_id) REFERENCES matches(id),
    FOREIGN KEY (provider_id) REFERENCES agents(id),
    FOREIGN KEY (receiver_id) REFERENCES agents(id),
    FOREIGN KEY (resource_spec_id) REFERENCES resource_specs(id),
    FOREIGN KEY (location_id) REFERENCES locations(id),
    FOREIGN KEY (provider_event_id) REFERENCES events(id),
    FOREIGN KEY (receiver_event_id) REFERENCES events(id),
    FOREIGN KEY (provider_commitment_id) REFERENCES commitments(id),
    FOREIGN KEY (receiver_commitment_id) REFERENCES commitments(id)
);

CREATE INDEX IF NOT EXISTS idx_exchanges_provider ON exchanges(provider_id);
CREATE INDEX IF NOT EXISTS idx_exchanges_receiver ON exchanges(receiver_id);
CREATE INDEX IF NOT EXISTS idx_exchanges_status ON exchanges(status);
CREATE INDEX IF NOT EXISTS idx_exchanges_scheduled ON exchanges(scheduled_start) WHERE scheduled_start IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_exchanges_community ON exchanges(community_id);

-- =============================================================================
-- EVENTS
-- =============================================================================

CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    action TEXT NOT NULL CHECK(action IN ('transfer', 'transfer-out', 'receive', 'produce', 'consume', 'work', 'use', 'pickup', 'dropoff', 'accept', 'modify', 'cite', 'deliver-service')),
    resource_spec_id TEXT,
    resource_instance_id TEXT,
    quantity REAL,
    unit TEXT,
    agent_id TEXT NOT NULL,
    to_agent_id TEXT,
    from_agent_id TEXT,
    location_id TEXT,
    occurred_at TEXT NOT NULL,
    process_id TEXT,
    exchange_id TEXT,
    commitment_id TEXT,
    note TEXT,
    image_url TEXT,
    created_at TEXT NOT NULL,
    author TEXT,
    signature TEXT,
    FOREIGN KEY (resource_spec_id) REFERENCES resource_specs(id),
    FOREIGN KEY (resource_instance_id) REFERENCES resource_instances(id),
    FOREIGN KEY (agent_id) REFERENCES agents(id),
    FOREIGN KEY (to_agent_id) REFERENCES agents(id),
    FOREIGN KEY (from_agent_id) REFERENCES agents(id),
    FOREIGN KEY (location_id) REFERENCES locations(id),
    FOREIGN KEY (process_id) REFERENCES processes(id),
    FOREIGN KEY (exchange_id) REFERENCES exchanges(id),
    FOREIGN KEY (commitment_id) REFERENCES commitments(id)
);

CREATE INDEX IF NOT EXISTS idx_events_action ON events(action);
CREATE INDEX IF NOT EXISTS idx_events_agent ON events(agent_id);
CREATE INDEX IF NOT EXISTS idx_events_occurred ON events(occurred_at);
CREATE INDEX IF NOT EXISTS idx_events_process ON events(process_id);
CREATE INDEX IF NOT EXISTS idx_events_exchange ON events(exchange_id);
CREATE INDEX IF NOT EXISTS idx_events_resource_instance ON events(resource_instance_id);

-- =============================================================================
-- PROCESSES
-- =============================================================================

CREATE TABLE IF NOT EXISTS processes (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'planned' CHECK(status IN ('planned', 'in_progress', 'completed', 'cancelled')),
    protocol_id TEXT,
    description TEXT,
    location_id TEXT,
    planned_start TEXT,
    planned_end TEXT,
    actual_start TEXT,
    actual_end TEXT,
    inputs TEXT,  -- JSON array of ProcessInput objects
    outputs TEXT,  -- JSON array of ProcessOutput objects
    participant_ids TEXT,  -- JSON array of Agent IDs
    plan_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT,
    author TEXT,
    signature TEXT,
    FOREIGN KEY (protocol_id) REFERENCES protocols(id),
    FOREIGN KEY (location_id) REFERENCES locations(id),
    FOREIGN KEY (plan_id) REFERENCES plans(id)
);

CREATE INDEX IF NOT EXISTS idx_processes_status ON processes(status);
CREATE INDEX IF NOT EXISTS idx_processes_protocol ON processes(protocol_id);
CREATE INDEX IF NOT EXISTS idx_processes_plan ON processes(plan_id);
CREATE INDEX IF NOT EXISTS idx_processes_planned_start ON processes(planned_start) WHERE planned_start IS NOT NULL;

-- =============================================================================
-- COMMITMENTS
-- =============================================================================

CREATE TABLE IF NOT EXISTS commitments (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    action TEXT NOT NULL,
    resource_spec_id TEXT,
    quantity REAL,
    unit TEXT,
    due_date TEXT,
    status TEXT NOT NULL DEFAULT 'proposed' CHECK(status IN ('proposed', 'accepted', 'in_progress', 'fulfilled', 'cancelled')),
    exchange_id TEXT,
    process_id TEXT,
    plan_id TEXT,
    fulfilled_by_event_id TEXT,
    note TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT,
    author TEXT,
    signature TEXT,
    FOREIGN KEY (agent_id) REFERENCES agents(id),
    FOREIGN KEY (resource_spec_id) REFERENCES resource_specs(id),
    FOREIGN KEY (exchange_id) REFERENCES exchanges(id),
    FOREIGN KEY (process_id) REFERENCES processes(id),
    FOREIGN KEY (plan_id) REFERENCES plans(id),
    FOREIGN KEY (fulfilled_by_event_id) REFERENCES events(id)
);

CREATE INDEX IF NOT EXISTS idx_commitments_agent ON commitments(agent_id);
CREATE INDEX IF NOT EXISTS idx_commitments_status ON commitments(status);
CREATE INDEX IF NOT EXISTS idx_commitments_due_date ON commitments(due_date) WHERE due_date IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_commitments_exchange ON commitments(exchange_id);
CREATE INDEX IF NOT EXISTS idx_commitments_process ON commitments(process_id);
CREATE INDEX IF NOT EXISTS idx_commitments_plan ON commitments(plan_id);

-- =============================================================================
-- PLANS
-- =============================================================================

CREATE TABLE IF NOT EXISTS plans (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft', 'active', 'completed', 'cancelled')),
    description TEXT,
    goal TEXT,
    start_date TEXT,
    end_date TEXT,
    process_ids TEXT,  -- JSON array of Process IDs
    commitment_ids TEXT,  -- JSON array of Commitment IDs
    dependencies TEXT,  -- JSON array of PlanDependency objects
    location_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT,
    author TEXT,
    signature TEXT,
    FOREIGN KEY (location_id) REFERENCES locations(id)
);

CREATE INDEX IF NOT EXISTS idx_plans_status ON plans(status);
CREATE INDEX IF NOT EXISTS idx_plans_start_date ON plans(start_date) WHERE start_date IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_plans_end_date ON plans(end_date) WHERE end_date IS NOT NULL;

-- =============================================================================
-- PROTOCOLS
-- =============================================================================

CREATE TABLE IF NOT EXISTS protocols (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    instructions TEXT,
    expected_inputs TEXT,
    expected_outputs TEXT,
    estimated_duration TEXT,
    difficulty_level TEXT,
    lesson_ids TEXT,  -- JSON array of Lesson IDs
    file_hashes TEXT,  -- JSON array of content hashes
    tags TEXT,  -- JSON array of strings
    created_at TEXT NOT NULL,
    updated_at TEXT,
    author TEXT,
    signature TEXT
);

CREATE INDEX IF NOT EXISTS idx_protocols_category ON protocols(category);
CREATE INDEX IF NOT EXISTS idx_protocols_name ON protocols(name);

-- Full-text search on protocols (if needed)
-- CREATE VIRTUAL TABLE protocols_fts USING fts5(name, description, instructions, content=protocols, content_rowid=rowid);

-- =============================================================================
-- LESSONS
-- =============================================================================

CREATE TABLE IF NOT EXISTS lessons (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    lesson_type TEXT NOT NULL,
    description TEXT,
    content TEXT,
    file_hash TEXT,
    file_url TEXT,
    estimated_duration TEXT,
    difficulty_level TEXT,
    skill_tags TEXT,  -- JSON array of strings
    protocol_ids TEXT,  -- JSON array of Protocol IDs
    resource_spec_ids TEXT,  -- JSON array of ResourceSpec IDs
    prerequisite_lesson_ids TEXT,  -- JSON array of Lesson IDs
    created_at TEXT NOT NULL,
    updated_at TEXT,
    author TEXT,
    signature TEXT
);

CREATE INDEX IF NOT EXISTS idx_lessons_type ON lessons(lesson_type);
CREATE INDEX IF NOT EXISTS idx_lessons_title ON lessons(title);

-- =============================================================================
-- USERS
-- =============================================================================

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    public_key TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_public_key ON users(public_key);

-- =============================================================================
-- CELLS (Local Groups)
-- =============================================================================

CREATE TABLE IF NOT EXISTS cells (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT
);

-- =============================================================================
-- PROPOSALS (Governance)
-- =============================================================================

CREATE TABLE IF NOT EXISTS proposals (
    proposal_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    proposer_id TEXT NOT NULL,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected', 'active', 'completed')),
    created_at TEXT NOT NULL,
    updated_at TEXT,
    FOREIGN KEY (proposer_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_proposals_status ON proposals(status);
CREATE INDEX IF NOT EXISTS idx_proposals_proposer ON proposals(proposer_id);

-- =============================================================================
-- METADATA TABLE (for schema versioning and node info)
-- =============================================================================

CREATE TABLE IF NOT EXISTS metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Insert schema version
INSERT OR REPLACE INTO metadata (key, value) VALUES ('schema_version', '1.0');
INSERT OR REPLACE INTO metadata (key, value) VALUES ('created_at', datetime('now'));
