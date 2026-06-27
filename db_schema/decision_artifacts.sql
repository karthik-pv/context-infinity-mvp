CREATE TABLE decision_artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    decision_id UUID NOT NULL REFERENCES decision_nodes(id) ON DELETE CASCADE,

    artifact_type TEXT NOT NULL CHECK (
        artifact_type IN ('project', 'folder', 'module', 'file')
    ),

    artifact_ref TEXT NOT NULL,

    is_display_anchor BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);