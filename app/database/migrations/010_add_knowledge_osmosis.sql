-- Migration 011: Add Knowledge Osmosis - Study Circles Share Learning
--
-- "Knowledge emerges only through invention and re-invention." - Paulo Freire
--
-- Study circles create knowledge but too often hoard it. Knowledge Osmosis
-- ensures that when study circles complete their work, they output artifacts
-- to the Common Heap: zines, guides, unanswered questions, resources.
--
-- The network becomes a learning organism where knowledge osmoses from
-- circle to circle.

PRAGMA foreign_keys = ON;

-- Create study_circles table
CREATE TABLE IF NOT EXISTS study_circles (
    id TEXT PRIMARY KEY,

    -- Circle details
    name TEXT NOT NULL,
    description TEXT,
    topic TEXT NOT NULL,

    -- Membership
    facilitator_user_id TEXT,
    member_count INTEGER DEFAULT 0,

    -- Status
    status TEXT DEFAULT 'forming',  -- 'forming', 'active', 'completed', 'archived'

    -- Commitment
    artifact_commitment TEXT,  -- What they committed to produce

    -- Metadata
    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    created_by TEXT NOT NULL,

    FOREIGN KEY (facilitator_user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_study_circles_status ON study_circles(status);
CREATE INDEX IF NOT EXISTS idx_study_circles_topic ON study_circles(topic);
CREATE INDEX IF NOT EXISTS idx_study_circles_facilitator ON study_circles(facilitator_user_id);
CREATE INDEX IF NOT EXISTS idx_study_circles_created ON study_circles(created_at);

-- Create study_circle_members table
CREATE TABLE IF NOT EXISTS study_circle_members (
    id TEXT PRIMARY KEY,
    circle_id TEXT NOT NULL,
    user_id TEXT NOT NULL,

    -- Role
    role TEXT DEFAULT 'member',  -- 'member', 'facilitator'

    -- Participation
    joined_at TEXT NOT NULL,
    left_at TEXT,

    FOREIGN KEY (circle_id) REFERENCES study_circles(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(circle_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_study_circle_members_circle ON study_circle_members(circle_id);
CREATE INDEX IF NOT EXISTS idx_study_circle_members_user ON study_circle_members(user_id);

-- Create learning_artifacts table (Common Heap)
CREATE TABLE IF NOT EXISTS learning_artifacts (
    id TEXT PRIMARY KEY,

    -- Source
    circle_id TEXT NOT NULL,
    created_by_user_id TEXT NOT NULL,

    -- Artifact details
    title TEXT NOT NULL,
    description TEXT,
    artifact_type TEXT NOT NULL,  -- 'zine', 'guide', 'questions', 'resources', 'synthesis'
    content TEXT NOT NULL,  -- Markdown content

    -- Metadata
    topic TEXT NOT NULL,
    tags TEXT,  -- JSON array
    difficulty TEXT,  -- 'beginner', 'intermediate', 'advanced'
    language TEXT DEFAULT 'en',

    -- Attribution
    builds_on_artifact_id TEXT,  -- If building on previous artifact
    attribution_text TEXT,  -- "Based on learning by Circle 42"

    -- Discovery
    view_count INTEGER DEFAULT 0,
    use_count INTEGER DEFAULT 0,  -- How many circles used this

    -- Timestamps
    published_at TEXT NOT NULL,
    updated_at TEXT,

    FOREIGN KEY (circle_id) REFERENCES study_circles(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (builds_on_artifact_id) REFERENCES learning_artifacts(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_learning_artifacts_circle ON learning_artifacts(circle_id);
CREATE INDEX IF NOT EXISTS idx_learning_artifacts_topic ON learning_artifacts(topic);
CREATE INDEX IF NOT EXISTS idx_learning_artifacts_type ON learning_artifacts(artifact_type);
CREATE INDEX IF NOT EXISTS idx_learning_artifacts_difficulty ON learning_artifacts(difficulty);
CREATE INDEX IF NOT EXISTS idx_learning_artifacts_published ON learning_artifacts(published_at);
CREATE INDEX IF NOT EXISTS idx_learning_artifacts_use_count ON learning_artifacts(use_count);

-- Create artifact_usage table (tracking osmosis)
CREATE TABLE IF NOT EXISTS artifact_usage (
    id TEXT PRIMARY KEY,
    artifact_id TEXT NOT NULL,
    used_by_circle_id TEXT NOT NULL,
    used_by_user_id TEXT NOT NULL,

    -- Usage context
    how_used TEXT,  -- Freeform description

    -- Timestamp
    used_at TEXT NOT NULL,

    FOREIGN KEY (artifact_id) REFERENCES learning_artifacts(id) ON DELETE CASCADE,
    FOREIGN KEY (used_by_circle_id) REFERENCES study_circles(id) ON DELETE CASCADE,
    FOREIGN KEY (used_by_user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_artifact_usage_artifact ON artifact_usage(artifact_id);
CREATE INDEX IF NOT EXISTS idx_artifact_usage_circle ON artifact_usage(used_by_circle_id);
CREATE INDEX IF NOT EXISTS idx_artifact_usage_used ON artifact_usage(used_at);

-- Create unanswered_questions table
CREATE TABLE IF NOT EXISTS unanswered_questions (
    id TEXT PRIMARY KEY,
    artifact_id TEXT NOT NULL,
    circle_id TEXT NOT NULL,

    -- Question
    question TEXT NOT NULL,
    context TEXT,  -- Why this question matters

    -- Status
    status TEXT DEFAULT 'open',  -- 'open', 'answered', 'exploring'

    -- Attribution
    answered_by_circle_id TEXT,
    answer_artifact_id TEXT,

    -- Timestamps
    asked_at TEXT NOT NULL,
    answered_at TEXT,

    FOREIGN KEY (artifact_id) REFERENCES learning_artifacts(id) ON DELETE CASCADE,
    FOREIGN KEY (circle_id) REFERENCES study_circles(id) ON DELETE CASCADE,
    FOREIGN KEY (answered_by_circle_id) REFERENCES study_circles(id) ON DELETE SET NULL,
    FOREIGN KEY (answer_artifact_id) REFERENCES learning_artifacts(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_unanswered_questions_artifact ON unanswered_questions(artifact_id);
CREATE INDEX IF NOT EXISTS idx_unanswered_questions_circle ON unanswered_questions(circle_id);
CREATE INDEX IF NOT EXISTS idx_unanswered_questions_status ON unanswered_questions(status);

-- Create learning_lineages table (knowledge genealogy)
CREATE TABLE IF NOT EXISTS learning_lineages (
    id TEXT PRIMARY KEY,
    artifact_id TEXT NOT NULL,
    ancestor_artifact_id TEXT NOT NULL,

    -- Relationship
    relationship_type TEXT NOT NULL,  -- 'builds_on', 'answers', 'extends', 'critiques'

    -- Depth
    depth INTEGER NOT NULL,  -- How many generations removed

    -- Timestamp
    linked_at TEXT NOT NULL,

    FOREIGN KEY (artifact_id) REFERENCES learning_artifacts(id) ON DELETE CASCADE,
    FOREIGN KEY (ancestor_artifact_id) REFERENCES learning_artifacts(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_learning_lineages_artifact ON learning_lineages(artifact_id);
CREATE INDEX IF NOT EXISTS idx_learning_lineages_ancestor ON learning_lineages(ancestor_artifact_id);
CREATE INDEX IF NOT EXISTS idx_learning_lineages_depth ON learning_lineages(depth);

-- Create knowledge_osmosis_stats table (aggregate metrics)
CREATE TABLE IF NOT EXISTS knowledge_osmosis_stats (
    id TEXT PRIMARY KEY,

    -- Timeframe
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,

    -- Circle metrics
    total_circles_formed INTEGER DEFAULT 0,
    total_circles_completed INTEGER DEFAULT 0,
    circles_producing_artifacts INTEGER DEFAULT 0,

    -- Artifact metrics
    total_artifacts_published INTEGER DEFAULT 0,
    artifacts_by_type TEXT,  -- JSON: {"zine": 10, "guide": 5, ...}

    -- Osmosis metrics
    artifacts_reused INTEGER DEFAULT 0,
    questions_answered INTEGER DEFAULT 0,
    avg_lineage_depth REAL DEFAULT 0.0,

    -- Success metric
    artifact_production_rate REAL DEFAULT 0.0,  -- % of circles producing artifacts

    -- Timestamp
    calculated_at TEXT NOT NULL,

    UNIQUE(period_start, period_end)
);

CREATE INDEX IF NOT EXISTS idx_knowledge_osmosis_stats_period ON knowledge_osmosis_stats(period_start, period_end);
