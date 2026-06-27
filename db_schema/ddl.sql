-- =====================================================
-- EXTENSIONS
-- =====================================================
CREATE EXTENSION IF NOT EXISTS pgcrypto;


-- =====================================================
-- TABLE: decision_nodes
-- Primary entity representing architectural decisions
-- =====================================================
CREATE TABLE decision_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Short title for UI node display
    title TEXT NOT NULL,

    -- Full decision statement
    decision TEXT NOT NULL,

    -- Why the decision was made
    rationale TEXT,

    -- Tradeoffs considered
    tradeoffs TEXT[] DEFAULT '{}',

    -- Confidence score from LLM extraction
    confidence NUMERIC(3,2) NOT NULL DEFAULT 0.80 CHECK (
        confidence >= 0 AND confidence <= 1
    ),

    -- Tags for retrieval / filtering
    tags TEXT[] DEFAULT '{}',

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);


-- =====================================================
-- TABLE: decision_artifacts
-- Maps decisions to files/folders/modules/projects
-- Also stores UI display anchor
-- =====================================================
CREATE TABLE decision_artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    decision_id UUID NOT NULL
        REFERENCES decision_nodes(id)
        ON DELETE CASCADE,

    artifact_type TEXT NOT NULL CHECK (
        artifact_type IN (
            'project',
            'folder',
            'module',
            'file'
        )
    ),

    -- Examples:
    -- project-root
    -- db
    -- db/redis
    -- db/redis/jwt.py
    artifact_ref TEXT NOT NULL,

    -- Only ONE artifact per decision should be used for rendering in UI
    is_display_anchor BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);


-- =====================================================
-- INDEXES
-- =====================================================

-- Fast artifact lookup
CREATE INDEX idx_decision_artifacts_ref
ON decision_artifacts(artifact_ref);

-- Fast reverse lookup by decision
CREATE INDEX idx_decision_artifacts_decision_id
ON decision_artifacts(decision_id);

-- Tag search
CREATE INDEX idx_decision_nodes_tags
ON decision_nodes USING GIN(tags);

-- Ensure only one display anchor per decision
CREATE UNIQUE INDEX one_display_anchor_per_decision
ON decision_artifacts(decision_id)
WHERE is_display_anchor = TRUE;