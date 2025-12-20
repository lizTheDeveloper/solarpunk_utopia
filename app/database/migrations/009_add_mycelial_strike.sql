-- Migration 010: Add Mycelial Strike - Automated Solidarity Defense
--
-- "Mutual Aid includes Mutual Defense." - Peter Kropotkin
--
-- The mycelium doesn't just share nutrients - it also fights infections.
-- When extractive behavior is detected, nearby nodes automatically throttle
-- interaction with the abuser. No committee meeting required. Instant,
-- collective response.
--
-- This is mutual aid AND mutual defense. You cannot have one without the other.

PRAGMA foreign_keys = ON;

-- Create warlord_alerts table
CREATE TABLE IF NOT EXISTS warlord_alerts (
    id TEXT PRIMARY KEY,

    -- Target of the alert
    target_user_id TEXT NOT NULL,

    -- Severity and type
    severity INTEGER NOT NULL CHECK(severity >= 1 AND severity <= 10),
    abuse_type TEXT NOT NULL,  -- 'battery_warlord', 'extraction_pattern', 'harassment', etc.

    -- Evidence (JSON array)
    evidence TEXT NOT NULL,  -- JSON: [{"type": "exchange", "details": "..."}]

    -- Source
    reporting_node_fingerprint TEXT NOT NULL,
    reporting_user_id TEXT,

    -- Propagation
    trusted_source INTEGER DEFAULT 1,  -- 0 if from untrusted node
    propagation_count INTEGER DEFAULT 0,  -- How many nodes have this alert

    -- Lifecycle
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,  -- 7 days default
    cancelled INTEGER DEFAULT 0,
    cancelled_by TEXT,
    cancellation_reason TEXT,
    cancelled_at TEXT,

    FOREIGN KEY (target_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (reporting_user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (cancelled_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_warlord_alerts_target ON warlord_alerts(target_user_id);
CREATE INDEX IF NOT EXISTS idx_warlord_alerts_severity ON warlord_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_warlord_alerts_reporting_node ON warlord_alerts(reporting_node_fingerprint);
CREATE INDEX IF NOT EXISTS idx_warlord_alerts_expires ON warlord_alerts(expires_at);
CREATE INDEX IF NOT EXISTS idx_warlord_alerts_cancelled ON warlord_alerts(cancelled);

-- Create local_strikes table
CREATE TABLE IF NOT EXISTS local_strikes (
    id TEXT PRIMARY KEY,
    alert_id TEXT NOT NULL,
    target_user_id TEXT NOT NULL,

    -- Throttle configuration
    throttle_level TEXT NOT NULL,  -- 'low', 'medium', 'high', 'critical'

    -- Throttle actions (JSON)
    throttle_actions TEXT NOT NULL,  -- JSON: {"deprioritize_matching": true, "add_message_latency": 5000, ...}

    -- Status
    status TEXT DEFAULT 'active',  -- 'active', 'deactivated', 'overridden'
    automatic INTEGER DEFAULT 1,  -- Was this auto-triggered or manual?

    -- Behavior tracking
    behavior_score_at_start REAL NOT NULL,
    current_behavior_score REAL NOT NULL,

    -- Timestamps
    activated_at TEXT NOT NULL,
    deactivated_at TEXT,

    -- Override
    overridden_by TEXT,
    override_reason TEXT,
    overridden_at TEXT,

    FOREIGN KEY (alert_id) REFERENCES warlord_alerts(id) ON DELETE CASCADE,
    FOREIGN KEY (target_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (overridden_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_local_strikes_alert ON local_strikes(alert_id);
CREATE INDEX IF NOT EXISTS idx_local_strikes_target ON local_strikes(target_user_id);
CREATE INDEX IF NOT EXISTS idx_local_strikes_status ON local_strikes(status);
CREATE INDEX IF NOT EXISTS idx_local_strikes_throttle_level ON local_strikes(throttle_level);

-- Create strike_evidence table
CREATE TABLE IF NOT EXISTS strike_evidence (
    id TEXT PRIMARY KEY,
    alert_id TEXT NOT NULL,

    -- Evidence details
    evidence_type TEXT NOT NULL,  -- 'exchange', 'pattern', 'report', 'behavior'
    evidence_data TEXT NOT NULL,  -- JSON with details

    -- Source
    collected_by TEXT NOT NULL,  -- Node fingerprint

    -- Weight
    reliability_score REAL DEFAULT 1.0,  -- Based on source trust

    -- Timestamp
    collected_at TEXT NOT NULL,

    FOREIGN KEY (alert_id) REFERENCES warlord_alerts(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_strike_evidence_alert ON strike_evidence(alert_id);
CREATE INDEX IF NOT EXISTS idx_strike_evidence_type ON strike_evidence(evidence_type);
CREATE INDEX IF NOT EXISTS idx_strike_evidence_collected ON strike_evidence(collected_at);

-- Create strike_propagation table
CREATE TABLE IF NOT EXISTS strike_propagation (
    id TEXT PRIMARY KEY,
    alert_id TEXT NOT NULL,

    -- Propagation details
    from_node_fingerprint TEXT NOT NULL,
    to_node_fingerprint TEXT NOT NULL,

    -- Trust
    trust_score REAL NOT NULL,  -- Trust between nodes
    accepted INTEGER DEFAULT 1,  -- Did receiving node accept the alert?
    rejection_reason TEXT,

    -- Timestamp
    propagated_at TEXT NOT NULL,

    FOREIGN KEY (alert_id) REFERENCES warlord_alerts(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_strike_propagation_alert ON strike_propagation(alert_id);
CREATE INDEX IF NOT EXISTS idx_strike_propagation_from ON strike_propagation(from_node_fingerprint);
CREATE INDEX IF NOT EXISTS idx_strike_propagation_to ON strike_propagation(to_node_fingerprint);
CREATE INDEX IF NOT EXISTS idx_strike_propagation_accepted ON strike_propagation(accepted);

-- Create behavior_tracking table
CREATE TABLE IF NOT EXISTS behavior_tracking (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    strike_id TEXT,  -- NULL if not currently under strike

    -- Behavior metrics
    exchanges_given INTEGER DEFAULT 0,
    exchanges_received INTEGER DEFAULT 0,
    offers_posted INTEGER DEFAULT 0,
    needs_posted INTEGER DEFAULT 0,

    -- Calculated score
    behavior_score REAL NOT NULL,  -- 0-10, higher is better

    -- Tracking period
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,
    last_updated TEXT NOT NULL,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (strike_id) REFERENCES local_strikes(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_behavior_tracking_user ON behavior_tracking(user_id);
CREATE INDEX IF NOT EXISTS idx_behavior_tracking_strike ON behavior_tracking(strike_id);
CREATE INDEX IF NOT EXISTS idx_behavior_tracking_score ON behavior_tracking(behavior_score);

-- Create strike_deescalation_log table
CREATE TABLE IF NOT EXISTS strike_deescalation_log (
    id TEXT PRIMARY KEY,
    strike_id TEXT NOT NULL,

    -- De-escalation details
    previous_level TEXT NOT NULL,
    new_level TEXT NOT NULL,
    trigger_reason TEXT NOT NULL,  -- 'behavior_improved', 'time_elapsed', 'steward_override'

    -- Behavior at time of de-escalation
    behavior_score REAL NOT NULL,

    -- Timestamp
    deescalated_at TEXT NOT NULL,

    FOREIGN KEY (strike_id) REFERENCES local_strikes(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_strike_deescalation_strike ON strike_deescalation_log(strike_id);
CREATE INDEX IF NOT EXISTS idx_strike_deescalation_deescalated ON strike_deescalation_log(deescalated_at);

-- Create strike_override_log table
CREATE TABLE IF NOT EXISTS strike_override_log (
    id TEXT PRIMARY KEY,

    -- What was overridden
    strike_id TEXT,
    alert_id TEXT,

    -- Override details
    action TEXT NOT NULL,  -- 'cancel_strike', 'cancel_alert', 'adjust_severity', 'whitelist_user'
    override_by TEXT NOT NULL,  -- Steward user ID
    reason TEXT NOT NULL,

    -- Before/after
    before_state TEXT,  -- JSON snapshot
    after_state TEXT,   -- JSON snapshot

    -- Timestamp
    overridden_at TEXT NOT NULL,

    FOREIGN KEY (strike_id) REFERENCES local_strikes(id) ON DELETE SET NULL,
    FOREIGN KEY (alert_id) REFERENCES warlord_alerts(id) ON DELETE SET NULL,
    FOREIGN KEY (override_by) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_strike_override_strike ON strike_override_log(strike_id);
CREATE INDEX IF NOT EXISTS idx_strike_override_alert ON strike_override_log(alert_id);
CREATE INDEX IF NOT EXISTS idx_strike_override_overridden ON strike_override_log(overridden_at);
CREATE INDEX IF NOT EXISTS idx_strike_override_override_by ON strike_override_log(override_by);

-- Create user_strike_whitelist table
CREATE TABLE IF NOT EXISTS user_strike_whitelist (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,

    -- Whitelist details
    whitelisted_by TEXT NOT NULL,  -- Steward user ID
    reason TEXT NOT NULL,

    -- Scope
    scope TEXT NOT NULL,  -- 'all', 'specific_abuse_type'
    abuse_type TEXT,  -- If scope is specific

    -- Duration
    is_permanent INTEGER DEFAULT 0,
    expires_at TEXT,

    -- Timestamp
    whitelisted_at TEXT NOT NULL,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (whitelisted_by) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_user_strike_whitelist_user ON user_strike_whitelist(user_id);
CREATE INDEX IF NOT EXISTS idx_user_strike_whitelist_expires ON user_strike_whitelist(expires_at);

-- Create strike_network_stats table (aggregate metrics)
CREATE TABLE IF NOT EXISTS strike_network_stats (
    id TEXT PRIMARY KEY,

    -- Timeframe
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,

    -- Alert metrics
    total_alerts_created INTEGER DEFAULT 0,
    total_alerts_propagated INTEGER DEFAULT 0,
    total_alerts_cancelled INTEGER DEFAULT 0,

    -- Strike metrics
    total_strikes_activated INTEGER DEFAULT 0,
    total_strikes_deescalated INTEGER DEFAULT 0,
    total_strikes_overridden INTEGER DEFAULT 0,

    -- False positive tracking
    false_positive_count INTEGER DEFAULT 0,
    false_positive_rate REAL DEFAULT 0.0,

    -- Effectiveness
    behavior_improvement_count INTEGER DEFAULT 0,  -- Users who improved after strike

    -- Timestamp
    calculated_at TEXT NOT NULL,

    UNIQUE(period_start, period_end)
);

CREATE INDEX IF NOT EXISTS idx_strike_network_stats_period ON strike_network_stats(period_start, period_end);
