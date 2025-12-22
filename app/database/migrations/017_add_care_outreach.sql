-- Migration 017: Add Care Outreach - Saboteur Conversion Through Care
--
-- "We have to be better than the world that shaped us." - adrienne maree brown
--
-- This isn't a security system. It's a care system. Exclusion is failure.
-- If we exclude someone, we've failed to build utopia for them.
--
-- When the system flags someone as potentially problematic, instead of banning them,
-- we assign them to a care volunteer. That volunteer does the work of care:
-- - Meets them where they are
-- - Connects them to resources
-- - Builds relationship
-- - Helps them re-engage with the community
--
-- Because often, "saboteurs" are just people in crisis.

PRAGMA foreign_keys = ON;

-- Create care_volunteers table
CREATE TABLE IF NOT EXISTS care_volunteers (
    user_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,

    -- Training they've received (JSON array)
    training TEXT NOT NULL,  -- ["active_listening", "trauma_informed", "conflict_de_escalation"]

    -- Capacity - they're human, they have limits
    currently_supporting INTEGER DEFAULT 0,
    max_capacity INTEGER DEFAULT 3,

    -- Support for the supporter
    supervision_partner_id TEXT,
    last_supervision TEXT,

    -- Metadata
    joined_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (supervision_partner_id) REFERENCES care_volunteers(user_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_care_volunteers_capacity ON care_volunteers(currently_supporting, max_capacity);
CREATE INDEX IF NOT EXISTS idx_care_volunteers_supervision ON care_volunteers(supervision_partner_id);

-- Create outreach_assignments table
CREATE TABLE IF NOT EXISTS outreach_assignments (
    id TEXT PRIMARY KEY,

    -- Who is being cared for
    flagged_user_id TEXT NOT NULL,

    -- Who is caring for them
    outreach_volunteer_id TEXT NOT NULL,

    -- Why were they flagged (detection reason)
    detection_reason TEXT NOT NULL,

    -- Details about the flagging
    detection_details TEXT,  -- JSON with specifics

    -- Status of outreach
    status TEXT DEFAULT 'active',  -- 'active', 'converted', 'chose_to_leave', 'still_trying'

    -- Timeline
    started_at TEXT NOT NULL,
    ended_at TEXT,
    needs_assessment TEXT,  -- JSON
    converted_at TEXT,  -- When they came around
    conversion_story TEXT,

    FOREIGN KEY (flagged_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (outreach_volunteer_id) REFERENCES care_volunteers(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_outreach_assignments_flagged_user ON outreach_assignments(flagged_user_id);
CREATE INDEX IF NOT EXISTS idx_outreach_assignments_volunteer ON outreach_assignments(outreach_volunteer_id);
CREATE INDEX IF NOT EXISTS idx_outreach_assignments_status ON outreach_assignments(status);

-- Create outreach_notes table (private notes from volunteers)
CREATE TABLE IF NOT EXISTS outreach_notes (
    id TEXT PRIMARY KEY,

    -- Which assignment this note belongs to
    assignment_id TEXT NOT NULL,

    -- Who wrote this note
    volunteer_id TEXT NOT NULL,

    -- The note content
    note TEXT NOT NULL,

    -- Type of contact
    contact_type TEXT,  -- 'meeting', 'phone_call', 'resource_connection', 'event_invitation', 'follow_up'

    -- Metadata
    created_at TEXT NOT NULL DEFAULT (datetime('now')),

    FOREIGN KEY (assignment_id) REFERENCES outreach_assignments(id) ON DELETE CASCADE,
    FOREIGN KEY (volunteer_id) REFERENCES care_volunteers(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_outreach_notes_assignment ON outreach_notes(assignment_id);
CREATE INDEX IF NOT EXISTS idx_outreach_notes_volunteer ON outreach_notes(volunteer_id);
CREATE INDEX IF NOT EXISTS idx_outreach_notes_created ON outreach_notes(created_at);

-- Create conversion_experiences table (stories of coming around)
CREATE TABLE IF NOT EXISTS conversion_experiences (
    id TEXT PRIMARY KEY,

    -- Who converted
    user_id TEXT NOT NULL,

    -- Their story (anonymized, with permission)
    story TEXT NOT NULL,

    -- What helped them
    what_helped TEXT NOT NULL,

    -- Status
    is_public INTEGER DEFAULT 0,  -- Only public with explicit permission
    approved_by_user INTEGER DEFAULT 0,

    -- Metadata
    created_at TEXT NOT NULL DEFAULT (datetime('now')),

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_conversion_experiences_user ON conversion_experiences(user_id);
CREATE INDEX IF NOT EXISTS idx_conversion_experiences_public ON conversion_experiences(is_public);

-- Create needs_assessments table (what does this person need?)
CREATE TABLE IF NOT EXISTS needs_assessments (
    id TEXT PRIMARY KEY,

    -- Which assignment
    assignment_id TEXT NOT NULL,

    -- Assessment
    housing_status TEXT,  -- 'stable', 'precarious', 'housing_insecure', 'unhoused'
    employment_status TEXT,  -- 'full_time', 'part_time', 'gig_work', 'unemployed', 'disabled'
    care_responsibilities TEXT,  -- 'children', 'elderly_parents', 'disabled_family', 'none'

    -- Immediate needs (JSON array)
    immediate_needs TEXT,  -- ["food", "housing", "healthcare", "childcare"]

    -- Resources connected to (JSON array)
    resources_connected TEXT,  -- ["mutual_aid_food", "housing_cell", "childcare_collective"]

    -- Notes
    assessment_notes TEXT,

    -- Metadata
    assessed_at TEXT NOT NULL,
    assessed_by TEXT NOT NULL,

    FOREIGN KEY (assignment_id) REFERENCES outreach_assignments(id) ON DELETE CASCADE,
    FOREIGN KEY (assessed_by) REFERENCES care_volunteers(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_needs_assessments_assignment ON needs_assessments(assignment_id);

-- Create care_outreach_metrics table (success tracking - not surveillance)
CREATE TABLE IF NOT EXISTS care_outreach_metrics (
    id TEXT PRIMARY KEY,

    -- Timeframe
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,

    -- Counts
    total_flagged INTEGER DEFAULT 0,
    total_assigned INTEGER DEFAULT 0,
    total_converted INTEGER DEFAULT 0,
    total_chose_to_leave INTEGER DEFAULT 0,
    total_still_trying INTEGER DEFAULT 0,

    -- Success metric: conversion rate (not as judgment, but as measure of care effectiveness)
    conversion_rate REAL DEFAULT 0.0,

    -- Volunteer metrics
    active_volunteers INTEGER DEFAULT 0,
    volunteers_at_capacity INTEGER DEFAULT 0,
    volunteers_needing_supervision INTEGER DEFAULT 0,

    -- Metadata
    calculated_at TEXT NOT NULL,

    UNIQUE(period_start, period_end)
);

CREATE INDEX IF NOT EXISTS idx_care_outreach_metrics_period ON care_outreach_metrics(period_start, period_end);
