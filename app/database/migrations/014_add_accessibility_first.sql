-- Migration 014: Add Accessibility First
--
-- "Disability justice means designing for the most marginalized first." - Mia Mingus
--
-- Most tech is inaccessible to disabled people. "Accessible version coming later"
-- never comes. We design accessibility into core constraints, not as an add-on.
--
-- ONE version that works for all, not a separate "accessible version".

PRAGMA foreign_keys = ON;

-- Add accessibility preferences to users table
ALTER TABLE users ADD COLUMN accessibility_preferences TEXT DEFAULT '{}';  -- JSON
ALTER TABLE users ADD COLUMN uses_screen_reader INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN uses_voice_control INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN uses_high_contrast INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN preferred_font_size TEXT DEFAULT 'medium';  -- 'small', 'medium', 'large', 'extra_large'
ALTER TABLE users ADD COLUMN reading_level_preference TEXT DEFAULT 'standard';  -- 'simple', 'standard', 'technical'
ALTER TABLE users ADD COLUMN accessibility_mode_enabled INTEGER DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_users_screen_reader ON users(uses_screen_reader);
CREATE INDEX IF NOT EXISTS idx_users_accessibility_mode ON users(accessibility_mode_enabled);

-- Create accessibility_feature_usage table to track which features are used
CREATE TABLE IF NOT EXISTS accessibility_feature_usage (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,

    -- Feature used
    feature_name TEXT NOT NULL,  -- 'screen_reader', 'voice_control', 'high_contrast', 'large_font', 'simple_language'

    -- Usage tracking
    first_used_at TEXT NOT NULL,
    last_used_at TEXT NOT NULL,
    usage_count INTEGER DEFAULT 1,

    -- Context
    platform TEXT,  -- 'android', 'web', 'ios'
    device_info TEXT,  -- JSON

    -- Metadata
    created_at TEXT NOT NULL,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, feature_name)
);

CREATE INDEX IF NOT EXISTS idx_accessibility_feature_usage_user ON accessibility_feature_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_accessibility_feature_usage_feature ON accessibility_feature_usage(feature_name);
CREATE INDEX IF NOT EXISTS idx_accessibility_feature_usage_platform ON accessibility_feature_usage(platform);

-- Create accessibility_audit_log table to track compliance
CREATE TABLE IF NOT EXISTS accessibility_audit_log (
    id TEXT PRIMARY KEY,

    -- Feature/component audited
    component_name TEXT NOT NULL,
    component_type TEXT NOT NULL,  -- 'page', 'component', 'flow', 'api'

    -- Audit details
    audit_type TEXT NOT NULL,  -- 'screen_reader', 'keyboard', 'contrast', 'touch_target', 'language'
    passed INTEGER NOT NULL,  -- 0 or 1
    issues_found TEXT,  -- JSON array of issues

    -- Auditor
    audited_by TEXT,  -- User ID or 'automated'
    audit_tool TEXT,  -- 'manual', 'axe', 'lighthouse', 'nvda', 'talkback'

    -- Resolution
    resolved INTEGER DEFAULT 0,
    resolved_at TEXT,
    resolution_notes TEXT,

    -- Metadata
    audited_at TEXT NOT NULL,

    FOREIGN KEY (audited_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_accessibility_audit_log_component ON accessibility_audit_log(component_name);
CREATE INDEX IF NOT EXISTS idx_accessibility_audit_log_passed ON accessibility_audit_log(passed);
CREATE INDEX IF NOT EXISTS idx_accessibility_audit_log_resolved ON accessibility_audit_log(resolved);

-- Create accessibility_feedback table for user-reported issues
CREATE TABLE IF NOT EXISTS accessibility_feedback (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,

    -- Issue details
    issue_type TEXT NOT NULL,  -- 'screen_reader_issue', 'touch_target_too_small', 'language_too_complex', 'contrast_too_low', 'voice_control_broken'
    component_affected TEXT NOT NULL,
    description TEXT NOT NULL,

    -- Severity
    severity TEXT DEFAULT 'medium',  -- 'low', 'medium', 'high', 'critical'
    blocks_usage INTEGER DEFAULT 0,  -- 1 if it prevents them from using the feature

    -- User context
    accessibility_features_used TEXT,  -- JSON array
    device_info TEXT,  -- JSON

    -- Status
    status TEXT DEFAULT 'open',  -- 'open', 'in_progress', 'resolved', 'wont_fix'

    -- Resolution
    resolved_by TEXT,
    resolved_at TEXT,
    resolution_notes TEXT,

    -- Metadata
    reported_at TEXT NOT NULL,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (resolved_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_accessibility_feedback_user ON accessibility_feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_accessibility_feedback_type ON accessibility_feedback(issue_type);
CREATE INDEX IF NOT EXISTS idx_accessibility_feedback_status ON accessibility_feedback(status);
CREATE INDEX IF NOT EXISTS idx_accessibility_feedback_severity ON accessibility_feedback(severity);

-- Create ui_component_metadata table for accessibility compliance tracking
CREATE TABLE IF NOT EXISTS ui_component_metadata (
    id TEXT PRIMARY KEY,

    -- Component identification
    component_name TEXT UNIQUE NOT NULL,
    component_path TEXT NOT NULL,  -- File path
    component_type TEXT NOT NULL,  -- 'page', 'button', 'form', 'list', 'modal'

    -- Accessibility compliance
    meets_touch_target_size INTEGER DEFAULT 0,  -- 48x48px minimum
    has_aria_labels INTEGER DEFAULT 0,
    has_keyboard_navigation INTEGER DEFAULT 0,
    has_high_contrast_support INTEGER DEFAULT 0,
    reading_level TEXT,  -- 'grade_8', 'grade_10', 'grade_12', etc.

    -- Testing
    last_tested_at TEXT,
    last_tested_by TEXT,
    test_results TEXT,  -- JSON

    -- Metadata
    created_at TEXT NOT NULL,
    updated_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_ui_component_metadata_name ON ui_component_metadata(component_name);
CREATE INDEX IF NOT EXISTS idx_ui_component_metadata_type ON ui_component_metadata(component_type);

-- Create accessibility_metrics table for success tracking
CREATE TABLE IF NOT EXISTS accessibility_metrics (
    id TEXT PRIMARY KEY,

    -- Timeframe
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,

    -- User metrics
    total_active_users INTEGER DEFAULT 0,
    users_with_accessibility_features INTEGER DEFAULT 0,

    -- Feature usage breakdown
    screen_reader_users INTEGER DEFAULT 0,
    voice_control_users INTEGER DEFAULT 0,
    high_contrast_users INTEGER DEFAULT 0,
    large_font_users INTEGER DEFAULT 0,

    -- Compliance metrics
    components_audited INTEGER DEFAULT 0,
    components_passing INTEGER DEFAULT 0,
    open_accessibility_issues INTEGER DEFAULT 0,
    critical_issues INTEGER DEFAULT 0,

    -- Success metric: >10% of active users using accessibility features
    accessibility_feature_usage_percentage REAL DEFAULT 0.0,

    -- Metadata
    calculated_at TEXT NOT NULL,

    UNIQUE(period_start, period_end)
);

CREATE INDEX IF NOT EXISTS idx_accessibility_metrics_period ON accessibility_metrics(period_start, period_end);

-- Create simplified_language_alternatives table for plain language versions
CREATE TABLE IF NOT EXISTS simplified_language_alternatives (
    id TEXT PRIMARY KEY,

    -- Original content
    original_text TEXT NOT NULL,
    original_text_hash TEXT NOT NULL,  -- Hash for quick lookup
    context TEXT,  -- Where this text appears

    -- Simplified version
    simplified_text TEXT NOT NULL,
    reading_level TEXT NOT NULL,  -- Target reading level achieved

    -- Quality
    verified_by TEXT,  -- User ID who verified it's clear
    usage_count INTEGER DEFAULT 0,  -- How often it's displayed

    -- Metadata
    created_at TEXT NOT NULL,
    updated_at TEXT,

    FOREIGN KEY (verified_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_simplified_language_hash ON simplified_language_alternatives(original_text_hash);
CREATE INDEX IF NOT EXISTS idx_simplified_language_reading_level ON simplified_language_alternatives(reading_level);

-- Create voice_command_mappings table for voice control
CREATE TABLE IF NOT EXISTS voice_command_mappings (
    id TEXT PRIMARY KEY,

    -- Command
    voice_command TEXT NOT NULL,  -- "offer help", "check messages", "find match"
    alternative_phrases TEXT,  -- JSON array of alternative ways to say it

    -- Action
    action_type TEXT NOT NULL,  -- 'navigate', 'create', 'search', 'update'
    action_target TEXT NOT NULL,  -- Component or route to invoke

    -- Accessibility
    requires_confirmation INTEGER DEFAULT 0,  -- For destructive actions
    feedback_text TEXT,  -- What to say back to user

    -- Usage
    usage_count INTEGER DEFAULT 0,
    success_rate REAL DEFAULT 1.0,  -- Percentage of times it works as expected

    -- Metadata
    created_at TEXT NOT NULL,
    enabled INTEGER DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_voice_command_mappings_command ON voice_command_mappings(voice_command);
CREATE INDEX IF NOT EXISTS idx_voice_command_mappings_enabled ON voice_command_mappings(enabled);

-- Create touch_target_violations table to track UI elements that are too small
CREATE TABLE IF NOT EXISTS touch_target_violations (
    id TEXT PRIMARY KEY,

    -- Component
    component_name TEXT NOT NULL,
    component_path TEXT NOT NULL,

    -- Violation details
    current_size_px TEXT NOT NULL,  -- e.g., "32x32"
    required_size_px TEXT DEFAULT '48x48',

    -- Detection
    detected_by TEXT NOT NULL,  -- 'automated_scan', 'user_report', 'manual_audit'
    detected_at TEXT NOT NULL,

    -- Status
    status TEXT DEFAULT 'open',  -- 'open', 'fixed', 'wont_fix', 'design_exception'
    fixed_at TEXT,
    fix_notes TEXT,

    FOREIGN KEY (component_name) REFERENCES ui_component_metadata(component_name) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_touch_target_violations_component ON touch_target_violations(component_name);
CREATE INDEX IF NOT EXISTS idx_touch_target_violations_status ON touch_target_violations(status);
