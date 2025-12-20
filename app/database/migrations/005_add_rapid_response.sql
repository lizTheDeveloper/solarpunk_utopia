-- Migration 006: Add Rapid Response Coordination
--
-- When ICE shows up. When someone is detained. When we need to mobilize NOW.
--
-- CRITICAL FEATURES:
-- - High-priority DTN bundles for alerts (<30 sec propagation)
-- - Coordinator coordination (first steward claims)
-- - Responder tracking (who's coming, ETA, role)
-- - Situation updates timeline
-- - Encrypted media documentation
-- - Auto-purge after 24 hours

PRAGMA foreign_keys = ON;

-- Create rapid_alerts table
CREATE TABLE IF NOT EXISTS rapid_alerts (
    id TEXT PRIMARY KEY,
    alert_type TEXT NOT NULL,  -- 'ice_raid', 'checkpoint', 'detention', 'workplace_raid', 'threat', 'other'
    alert_level TEXT NOT NULL,  -- 'critical', 'urgent', 'watch'
    status TEXT DEFAULT 'active',  -- 'active', 'resolved', 'expired', 'false_alarm'

    -- Source
    reported_by TEXT NOT NULL,
    cell_id TEXT NOT NULL,

    -- Location (general only - no precise addresses)
    location_hint TEXT NOT NULL,
    coordinates TEXT,  -- JSON: {lat, lon} - optional

    -- Details
    description TEXT NOT NULL,
    people_affected INTEGER,

    -- Coordinator (first steward to claim)
    coordinator_id TEXT,
    coordinator_claimed_at TEXT,

    -- Resolution
    resolved_at TEXT,
    resolution_notes TEXT,

    -- Confirmation (anti-false-alarm)
    confirmed INTEGER DEFAULT 0,
    confirmed_by TEXT,
    confirmed_at TEXT,
    auto_downgrade_at TEXT,  -- Auto-downgrade to WATCH if not confirmed within 5 min

    -- DTN propagation
    bundle_id TEXT,
    propagation_radius_km REAL DEFAULT 50.0,

    -- Auto-purge
    purge_at TEXT,  -- 24 hours after resolution

    -- Metadata
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,

    FOREIGN KEY (reported_by) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (cell_id) REFERENCES cells(id) ON DELETE CASCADE,
    FOREIGN KEY (coordinator_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (confirmed_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_rapid_alerts_status ON rapid_alerts(status);
CREATE INDEX IF NOT EXISTS idx_rapid_alerts_level ON rapid_alerts(alert_level);
CREATE INDEX IF NOT EXISTS idx_rapid_alerts_cell ON rapid_alerts(cell_id);
CREATE INDEX IF NOT EXISTS idx_rapid_alerts_created ON rapid_alerts(created_at);
CREATE INDEX IF NOT EXISTS idx_rapid_alerts_expires ON rapid_alerts(expires_at);
CREATE INDEX IF NOT EXISTS idx_rapid_alerts_bundle ON rapid_alerts(bundle_id);
CREATE INDEX IF NOT EXISTS idx_rapid_alerts_purge ON rapid_alerts(purge_at);

-- Create alert_responders table
CREATE TABLE IF NOT EXISTS alert_responders (
    id TEXT PRIMARY KEY,
    alert_id TEXT NOT NULL,
    user_id TEXT NOT NULL,

    -- Status
    status TEXT NOT NULL,  -- 'responding', 'available_far', 'unavailable'
    role TEXT NOT NULL,  -- 'witness', 'coordinator', 'physical', 'legal', 'media', 'support'

    -- Details
    eta_minutes INTEGER,
    notes TEXT,

    -- Timestamps
    responded_at TEXT NOT NULL,
    arrived_at TEXT,
    departed_at TEXT,

    FOREIGN KEY (alert_id) REFERENCES rapid_alerts(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(alert_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_alert_responders_alert ON alert_responders(alert_id);
CREATE INDEX IF NOT EXISTS idx_alert_responders_user ON alert_responders(user_id);
CREATE INDEX IF NOT EXISTS idx_alert_responders_status ON alert_responders(status);
CREATE INDEX IF NOT EXISTS idx_alert_responders_role ON alert_responders(role);

-- Create alert_updates table
CREATE TABLE IF NOT EXISTS alert_updates (
    id TEXT PRIMARY KEY,
    alert_id TEXT NOT NULL,
    posted_by TEXT NOT NULL,

    -- Update content
    update_type TEXT NOT NULL,  -- 'status_change', 'escalation', 'de_escalation', 'info'
    message TEXT NOT NULL,

    -- Level change (if escalation/de-escalation)
    new_alert_level TEXT,  -- 'critical', 'urgent', 'watch'

    -- DTN propagation
    bundle_id TEXT,

    -- Metadata
    posted_at TEXT NOT NULL,

    FOREIGN KEY (alert_id) REFERENCES rapid_alerts(id) ON DELETE CASCADE,
    FOREIGN KEY (posted_by) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_alert_updates_alert ON alert_updates(alert_id);
CREATE INDEX IF NOT EXISTS idx_alert_updates_posted ON alert_updates(posted_at);
CREATE INDEX IF NOT EXISTS idx_alert_updates_type ON alert_updates(update_type);

-- Create alert_media table (encrypted documentation)
CREATE TABLE IF NOT EXISTS alert_media (
    id TEXT PRIMARY KEY,
    alert_id TEXT NOT NULL,
    captured_by TEXT NOT NULL,

    -- Media details
    media_type TEXT NOT NULL,  -- 'photo', 'video', 'audio', 'document'
    encrypted_data TEXT,  -- Encrypted media or reference to distributed storage
    storage_bundle_id TEXT,  -- DTN bundle ID if stored in mesh
    file_size_bytes INTEGER NOT NULL,

    -- Metadata (encrypted)
    encrypted_metadata TEXT,  -- GPS, timestamp, device info (all encrypted)

    -- Access control
    shared_with_legal INTEGER DEFAULT 0,
    shared_with_media INTEGER DEFAULT 0,

    -- Auto-purge
    purge_at TEXT NOT NULL,  -- 24 hours after alert resolution

    -- Timestamps
    captured_at TEXT NOT NULL,

    FOREIGN KEY (alert_id) REFERENCES rapid_alerts(id) ON DELETE CASCADE,
    FOREIGN KEY (captured_by) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_alert_media_alert ON alert_media(alert_id);
CREATE INDEX IF NOT EXISTS idx_alert_media_type ON alert_media(media_type);
CREATE INDEX IF NOT EXISTS idx_alert_media_purge ON alert_media(purge_at);

-- Create after_action_reviews table
CREATE TABLE IF NOT EXISTS after_action_reviews (
    id TEXT PRIMARY KEY,
    alert_id TEXT NOT NULL,
    completed_by TEXT NOT NULL,

    -- Response analysis
    response_time_minutes INTEGER,
    total_responders INTEGER NOT NULL,

    -- What went well
    successes TEXT NOT NULL,

    -- What needs improvement
    challenges TEXT NOT NULL,

    -- Lessons learned
    lessons TEXT NOT NULL,

    -- Recommendations
    recommendations TEXT NOT NULL,

    -- Metadata
    completed_at TEXT NOT NULL,

    FOREIGN KEY (alert_id) REFERENCES rapid_alerts(id) ON DELETE CASCADE,
    FOREIGN KEY (completed_by) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(alert_id)  -- One review per alert
);

CREATE INDEX IF NOT EXISTS idx_after_action_reviews_alert ON after_action_reviews(alert_id);
CREATE INDEX IF NOT EXISTS idx_after_action_reviews_completed ON after_action_reviews(completed_at);
