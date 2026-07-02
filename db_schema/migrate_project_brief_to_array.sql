-- Migration: convert project_brief from TEXT to TEXT[]
-- Each finalized session appends a 2-sentence summary as one array entry.
ALTER TABLE project_info ALTER COLUMN project_brief TYPE text[]
    USING CASE
        WHEN project_brief IS NULL OR project_brief = '' THEN '{}'
        ELSE ARRAY[project_brief]
    END;
ALTER TABLE project_info ALTER COLUMN project_brief SET DEFAULT '{}';
