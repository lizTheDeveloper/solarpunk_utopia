-- Migration 012: Algorithmic Transparency
-- Philosopher: Joy Buolamwini (Algorithmic Justice)
-- Enables users to understand AI matching decisions

-- Match Explanation Details
-- Stores detailed score breakdown for each match
CREATE TABLE IF NOT EXISTS match_explanations (
    id TEXT PRIMARY KEY,
    match_id TEXT NOT NULL,

    -- Score breakdown (stored as JSON for flexibility)
    category_score REAL NOT NULL,
    location_score REAL NOT NULL,
    time_score REAL NOT NULL,
    quantity_score REAL NOT NULL,
    total_score REAL NOT NULL,

    -- Applied weights at time of matching
    category_weight REAL NOT NULL,
    location_weight REAL NOT NULL,
    time_weight REAL NOT NULL,
    quantity_weight REAL NOT NULL,

    -- Human-readable explanation
    explanation_text TEXT NOT NULL,

    -- Distance details (for transparency)
    distance_km REAL,
    distance_description TEXT,

    -- Category match details
    category_match_type TEXT, -- 'exact', 'parent', 'semantic', 'none'

    -- Time details
    time_buffer_hours REAL,

    -- Quantity details
    quantity_ratio REAL,

    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Foreign keys
    FOREIGN KEY (match_id) REFERENCES matches(id)
);

CREATE INDEX IF NOT EXISTS idx_match_explanations_match_id ON match_explanations(match_id);

-- Matching Weights Configuration
-- Allows communities to adjust matching priorities
CREATE TABLE IF NOT EXISTS matching_weights (
    id TEXT PRIMARY KEY,
    community_id TEXT,  -- NULL = system default

    -- Weights (must sum to 1.0)
    category_weight REAL NOT NULL DEFAULT 0.4,
    location_weight REAL NOT NULL DEFAULT 0.3,
    time_weight REAL NOT NULL DEFAULT 0.2,
    quantity_weight REAL NOT NULL DEFAULT 0.1,

    -- Description
    name TEXT NOT NULL,
    description TEXT,

    -- Activation
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,  -- User who created this config

    -- Ensure only one active config per community
    UNIQUE(community_id, is_active) WHERE is_active = TRUE
);

CREATE INDEX idx_matching_weights_community_id ON matching_weights(community_id);
CREATE INDEX idx_matching_weights_active ON matching_weights(is_active) WHERE is_active = TRUE;

-- Insert default system weights
INSERT INTO matching_weights (
    id,
    community_id,
    category_weight,
    location_weight,
    time_weight,
    quantity_weight,
    name,
    description,
    is_active
) VALUES (
    'weights:system:default',
    NULL,
    0.4,
    0.3,
    0.2,
    0.1,
    'System Default',
    'Balanced matching: category (40%), location (30%), time (20%), quantity (10%)',
    TRUE
);

-- Matching Audit Trail
-- Records all matching decisions for research and bias detection
CREATE TABLE IF NOT EXISTS matching_audit_log (
    id TEXT PRIMARY KEY,

    -- What was matched
    match_id TEXT,  -- NULL if no match was created
    offer_id TEXT NOT NULL,
    need_id TEXT NOT NULL,

    -- Score
    match_score REAL NOT NULL,
    threshold_score REAL NOT NULL,
    matched BOOLEAN NOT NULL,  -- TRUE if match was created, FALSE if score too low

    -- Weights used
    weights_config_id TEXT NOT NULL,

    -- Demographic data (for bias detection)
    -- Stored as hashed/anonymized data
    provider_demographic_hash TEXT,
    receiver_demographic_hash TEXT,

    -- Location zones (for detecting geographic bias)
    provider_zone TEXT,
    receiver_zone TEXT,

    -- Categories (for detecting category bias)
    offer_category TEXT,
    need_category TEXT,

    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    agent_version TEXT,

    FOREIGN KEY (match_id) REFERENCES matches(id),
    FOREIGN KEY (weights_config_id) REFERENCES matching_weights(id)
);

CREATE INDEX idx_matching_audit_log_created_at ON matching_audit_log(created_at);
CREATE INDEX idx_matching_audit_log_matched ON matching_audit_log(matched);
CREATE INDEX idx_matching_audit_log_offer_id ON matching_audit_log(offer_id);
CREATE INDEX idx_matching_audit_log_need_id ON matching_audit_log(need_id);

-- Bias Detection Reports
-- Aggregated analysis of matching patterns
CREATE TABLE IF NOT EXISTS bias_detection_reports (
    id TEXT PRIMARY KEY,

    -- Time window analyzed
    analysis_start TIMESTAMP NOT NULL,
    analysis_end TIMESTAMP NOT NULL,

    -- What was analyzed
    community_id TEXT,
    category TEXT,  -- NULL = all categories

    -- Findings
    total_matches_analyzed INTEGER NOT NULL,

    -- Geographic bias detection
    geographic_bias_score REAL,  -- 0-1, higher = more bias detected
    geographic_bias_details TEXT,  -- JSON with specifics

    -- Category bias detection
    category_bias_score REAL,
    category_bias_details TEXT,

    -- Demographic bias detection
    demographic_bias_score REAL,
    demographic_bias_details TEXT,

    -- Overall assessment
    overall_bias_score REAL,
    bias_detected BOOLEAN NOT NULL,
    recommendations TEXT,  -- JSON with suggested weight adjustments

    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,  -- 'system' or user_id

    -- Status
    status TEXT NOT NULL DEFAULT 'draft',  -- 'draft', 'published', 'archived'

    -- Community review
    community_reviewed BOOLEAN DEFAULT FALSE,
    community_response TEXT
);

CREATE INDEX idx_bias_reports_created_at ON bias_detection_reports(created_at);
CREATE INDEX idx_bias_reports_community_id ON bias_detection_reports(community_id);
CREATE INDEX idx_bias_reports_bias_detected ON bias_detection_reports(bias_detected);
CREATE INDEX idx_bias_reports_status ON bias_detection_reports(status);

-- User Transparency Preferences
-- Users can control how much explanation they want
CREATE TABLE IF NOT EXISTS transparency_preferences (
    user_id TEXT PRIMARY KEY,

    -- Explanation detail level
    detail_level TEXT NOT NULL DEFAULT 'medium',  -- 'minimal', 'medium', 'detailed'

    -- Show score breakdowns
    show_score_breakdown BOOLEAN NOT NULL DEFAULT TRUE,

    -- Show weights used
    show_weights BOOLEAN NOT NULL DEFAULT TRUE,

    -- Show why NOT matched
    show_rejection_reasons BOOLEAN NOT NULL DEFAULT FALSE,

    -- Receive bias reports
    receive_bias_reports BOOLEAN NOT NULL DEFAULT TRUE,

    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_transparency_prefs_detail_level ON transparency_preferences(detail_level);
