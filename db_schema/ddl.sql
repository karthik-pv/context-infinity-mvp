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


-- =====================================================
-- TABLE: planning_sessions
-- Persisted planning session state (chat, plan, nodes)
-- One row per session, upserted on every state change
-- =====================================================
CREATE TABLE planning_sessions (
    session_id TEXT PRIMARY KEY,

    status TEXT NOT NULL DEFAULT 'planning' CHECK (
        status IN ('planning', 'finalized')
    ),

    -- Full chat history as array of {role, content} objects
    chat_history JSONB NOT NULL DEFAULT '[]',

    -- Implementation plan: {section_id: {content, target_file}}
    implementation_plan JSONB NOT NULL DEFAULT '{}',

    -- Inferred decision nodes (session-scoped, not yet finalized)
    inferred_nodes JSONB NOT NULL DEFAULT '[]',

    -- Session-scoped working copy of folder structure (only persisted to
    -- project_info.folder_structure on finalize)
    session_folder_structure JSONB NOT NULL DEFAULT '[]',

    -- Paths explicitly removed via modify_folder_structure tool
    deleted_paths JSONB NOT NULL DEFAULT '[]',

    -- Decision violations detected in the last planning turn
    violations JSONB NOT NULL DEFAULT '[]',

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Migration for existing databases
ALTER TABLE planning_sessions ADD COLUMN IF NOT EXISTS session_folder_structure JSONB NOT NULL DEFAULT '[]';
ALTER TABLE planning_sessions ADD COLUMN IF NOT EXISTS deleted_paths JSONB NOT NULL DEFAULT '[]';
ALTER TABLE planning_sessions ADD COLUMN IF NOT EXISTS violations JSONB NOT NULL DEFAULT '[]';


-- =====================================================
-- INDEXES: planning_sessions
-- =====================================================
CREATE INDEX idx_planning_sessions_status
ON planning_sessions(status);

CREATE INDEX idx_planning_sessions_updated
ON planning_sessions(updated_at DESC);


-- =====================================================
-- TABLE: project_info
-- Singleton row (id = 1) storing project-level metadata
-- =====================================================
CREATE TABLE project_info (
    id INT PRIMARY KEY DEFAULT 1 CHECK (id = 1),

    -- Filesystem path of the target project
    project_path TEXT NOT NULL DEFAULT '',

    -- Free-text brief / summary of the project
    project_brief TEXT NOT NULL DEFAULT '',

    -- Compact sorted list of file/folder paths derived from the plan
    folder_structure TEXT[] NOT NULL DEFAULT '{}',

    -- Actual filesystem scan of project_path (updated via sync)
    actual_folder_structure TEXT[] NOT NULL DEFAULT '{}',

    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Seed the singleton row
INSERT INTO project_info (id) VALUES (1) ON CONFLICT DO NOTHING;

-- Migration for existing databases
ALTER TABLE project_info ADD COLUMN IF NOT EXISTS actual_folder_structure TEXT[] NOT NULL DEFAULT '{}';