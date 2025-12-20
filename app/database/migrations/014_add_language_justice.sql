-- Migration 015: Add Language Justice
--
-- "So, if you want to really hurt me, talk badly about my language." - Gloria Anzaldúa
--
-- English-only systems exclude billions. We build multi-language support from the start,
-- not as an afterthought. Community translation system with human review ensures
-- cultural adaptation, not just word-for-word translation.
--
-- No "English as default" - equal treatment of all languages.

PRAGMA foreign_keys = ON;

-- Add language preferences to users table
ALTER TABLE users ADD COLUMN preferred_language TEXT DEFAULT 'en';  -- ISO 639-1 codes
ALTER TABLE users ADD COLUMN language_auto_detected TEXT;  -- What we detected from browser/device
ALTER TABLE users ADD COLUMN rtl_enabled INTEGER DEFAULT 0;  -- Right-to-left layout

CREATE INDEX IF NOT EXISTS idx_users_preferred_language ON users(preferred_language);

-- Create supported_languages table
CREATE TABLE IF NOT EXISTS supported_languages (
    id TEXT PRIMARY KEY,

    -- Language details
    language_code TEXT UNIQUE NOT NULL,  -- ISO 639-1: 'en', 'es', 'ar', 'he', etc.
    language_name TEXT NOT NULL,  -- 'English', 'Español', 'العربية', 'עברית'
    native_name TEXT NOT NULL,  -- Name in that language
    rtl INTEGER DEFAULT 0,  -- Right-to-left script

    -- Support status
    status TEXT DEFAULT 'in_progress',  -- 'in_progress', 'community_supported', 'official'
    completion_percentage REAL DEFAULT 0.0,  -- % of strings translated

    -- Community
    lead_translator_id TEXT,  -- User coordinating this language
    contributor_count INTEGER DEFAULT 0,

    -- Metadata
    added_at TEXT NOT NULL,
    last_updated_at TEXT,

    FOREIGN KEY (lead_translator_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_supported_languages_code ON supported_languages(language_code);
CREATE INDEX IF NOT EXISTS idx_supported_languages_status ON supported_languages(status);

-- Create translation_strings table for all UI strings
CREATE TABLE IF NOT EXISTS translation_strings (
    id TEXT PRIMARY KEY,

    -- String identification
    string_key TEXT UNIQUE NOT NULL,  -- 'offer.create.title', 'nav.home', etc.
    context TEXT,  -- Where it appears, additional context

    -- Source (English)
    source_text TEXT NOT NULL,
    source_language TEXT DEFAULT 'en',

    -- Categorization
    category TEXT,  -- 'ui', 'errors', 'help', 'onboarding'
    component TEXT,  -- Which component uses this

    -- Metadata
    character_limit INTEGER,  -- For UI space constraints
    variables TEXT,  -- JSON array of variable names {user}, {count}, etc.
    plural_forms INTEGER DEFAULT 0,  -- Does this need plural handling?

    -- Created
    created_at TEXT NOT NULL,
    last_modified_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_translation_strings_key ON translation_strings(string_key);
CREATE INDEX IF NOT EXISTS idx_translation_strings_category ON translation_strings(category);

-- Create translations table for actual translations
CREATE TABLE IF NOT EXISTS translations (
    id TEXT PRIMARY KEY,

    -- What's being translated
    string_id TEXT NOT NULL,
    language_code TEXT NOT NULL,

    -- Translation
    translated_text TEXT NOT NULL,

    -- Quality
    translation_status TEXT DEFAULT 'draft',  -- 'draft', 'reviewed', 'approved', 'needs_review'
    translation_method TEXT DEFAULT 'community',  -- 'community', 'machine', 'professional'

    -- Contributors
    translator_id TEXT,  -- Who did the translation
    reviewer_id TEXT,  -- Who reviewed it
    reviewed_at TEXT,

    -- Community feedback
    upvotes INTEGER DEFAULT 0,
    downvotes INTEGER DEFAULT 0,
    report_count INTEGER DEFAULT 0,  -- How many users reported this as incorrect

    -- Cultural adaptation notes
    adaptation_notes TEXT,  -- Notes on cultural context

    -- Metadata
    created_at TEXT NOT NULL,
    updated_at TEXT,

    FOREIGN KEY (string_id) REFERENCES translation_strings(id) ON DELETE CASCADE,
    FOREIGN KEY (language_code) REFERENCES supported_languages(language_code) ON DELETE CASCADE,
    FOREIGN KEY (translator_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (reviewer_id) REFERENCES users(id) ON DELETE SET NULL,
    UNIQUE(string_id, language_code)
);

CREATE INDEX IF NOT EXISTS idx_translations_string ON translations(string_id);
CREATE INDEX IF NOT EXISTS idx_translations_language ON translations(language_code);
CREATE INDEX IF NOT EXISTS idx_translations_status ON translations(translation_status);
CREATE INDEX IF NOT EXISTS idx_translations_translator ON translations(translator_id);

-- Create translation_suggestions table for community contributions
CREATE TABLE IF NOT EXISTS translation_suggestions (
    id TEXT PRIMARY KEY,

    -- What's being suggested
    string_id TEXT NOT NULL,
    language_code TEXT NOT NULL,

    -- Suggestion
    suggested_text TEXT NOT NULL,
    suggestion_notes TEXT,  -- Why this translation is better

    -- Suggester
    suggested_by TEXT NOT NULL,
    suggested_at TEXT NOT NULL,

    -- Status
    status TEXT DEFAULT 'pending',  -- 'pending', 'accepted', 'rejected'

    -- Review
    reviewed_by TEXT,
    reviewed_at TEXT,
    review_notes TEXT,

    FOREIGN KEY (string_id) REFERENCES translation_strings(id) ON DELETE CASCADE,
    FOREIGN KEY (language_code) REFERENCES supported_languages(language_code) ON DELETE CASCADE,
    FOREIGN KEY (suggested_by) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (reviewed_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_translation_suggestions_string ON translation_suggestions(string_id);
CREATE INDEX IF NOT EXISTS idx_translation_suggestions_language ON translation_suggestions(language_code);
CREATE INDEX IF NOT EXISTS idx_translation_suggestions_status ON translation_suggestions(status);

-- Create language_usage_stats table to track adoption
CREATE TABLE IF NOT EXISTS language_usage_stats (
    id TEXT PRIMARY KEY,

    -- Timeframe
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,

    -- Overall stats
    total_active_users INTEGER DEFAULT 0,

    -- Per-language breakdown (stored as JSON)
    users_by_language TEXT,  -- {"en": 150, "es": 80, "ar": 20}

    -- Success metric: >20% using non-English
    non_english_percentage REAL DEFAULT 0.0,

    -- Translation quality
    total_translation_strings INTEGER DEFAULT 0,
    fully_translated_languages INTEGER DEFAULT 0,
    community_contributions INTEGER DEFAULT 0,

    -- Metadata
    calculated_at TEXT NOT NULL,

    UNIQUE(period_start, period_end)
);

CREATE INDEX IF NOT EXISTS idx_language_usage_stats_period ON language_usage_stats(period_start, period_end);

-- Create language_detection_log table for auto-detection tracking
CREATE TABLE IF NOT EXISTS language_detection_log (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,

    -- Detection
    detected_language TEXT NOT NULL,
    detection_method TEXT NOT NULL,  -- 'browser', 'device', 'ip_location', 'manual'
    detection_confidence REAL DEFAULT 1.0,

    -- User action
    user_accepted INTEGER DEFAULT 0,  -- Did they keep it or change it?
    user_selected_language TEXT,  -- What they actually chose

    -- Metadata
    detected_at TEXT NOT NULL,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_language_detection_log_user ON language_detection_log(user_id);
CREATE INDEX IF NOT EXISTS idx_language_detection_log_detected ON language_detection_log(detected_language);

-- Create translation_quality_reports table for community moderation
CREATE TABLE IF NOT EXISTS translation_quality_reports (
    id TEXT PRIMARY KEY,

    -- What's being reported
    translation_id TEXT NOT NULL,

    -- Report
    reported_by TEXT NOT NULL,
    issue_type TEXT NOT NULL,  -- 'incorrect', 'offensive', 'culturally_insensitive', 'grammatically_wrong'
    description TEXT NOT NULL,

    -- Suggested fix
    suggested_correction TEXT,

    -- Status
    status TEXT DEFAULT 'open',  -- 'open', 'resolved', 'dismissed'
    resolved_by TEXT,
    resolved_at TEXT,
    resolution_notes TEXT,

    -- Metadata
    reported_at TEXT NOT NULL,

    FOREIGN KEY (translation_id) REFERENCES translations(id) ON DELETE CASCADE,
    FOREIGN KEY (reported_by) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (resolved_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_translation_quality_reports_translation ON translation_quality_reports(translation_id);
CREATE INDEX IF NOT EXISTS idx_translation_quality_reports_status ON translation_quality_reports(status);

-- Create translation_contributors table to track community translators
CREATE TABLE IF NOT EXISTS translation_contributors (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,

    -- Languages they contribute to
    languages TEXT,  -- JSON array of language codes

    -- Contribution stats
    translations_submitted INTEGER DEFAULT 0,
    translations_approved INTEGER DEFAULT 0,
    suggestions_accepted INTEGER DEFAULT 0,

    -- Quality
    average_rating REAL DEFAULT 0.0,

    -- Status
    is_verified_translator INTEGER DEFAULT 0,  -- Trusted translator
    can_review INTEGER DEFAULT 0,  -- Can review others' work

    -- Metadata
    first_contribution_at TEXT NOT NULL,
    last_contribution_at TEXT,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id)
);

CREATE INDEX IF NOT EXISTS idx_translation_contributors_user ON translation_contributors(user_id);
CREATE INDEX IF NOT EXISTS idx_translation_contributors_verified ON translation_contributors(is_verified_translator);
