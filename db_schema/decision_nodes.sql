CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE decision_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Short UI title
    title TEXT NOT NULL,

    -- Full decision text
    decision TEXT NOT NULL,

    -- Why this decision exists
    rationale TEXT,

    -- Tradeoffs made while deciding
    tradeoffs TEXT [] DEFAULT '{}',

    -- LLM confidence in extraction
    confidence NUMERIC(3,2) NOT NULL DEFAULT 0.80 CHECK (
        confidence >= 0 AND confidence <= 1
    ),

    -- Semantic retrieval before embeddings
    tags TEXT[] DEFAULT '{}',

    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);