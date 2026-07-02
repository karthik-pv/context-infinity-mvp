import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def _conn():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def get_decisions():
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    n.id::text         AS id,
                    n.title,
                    n.decision,
                    n.rationale,
                    n.tradeoffs,
                    n.confidence::float AS confidence,
                    n.tags,
                    a.artifact_ref     AS location
                FROM decision_nodes n
                LEFT JOIN decision_artifacts a
                    ON a.decision_id = n.id AND a.is_display_anchor = TRUE
                ORDER BY n.created_at
            """)
            return cur.fetchall()


def get_decision_by_id(decision_id: str):
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    n.id::text,
                    n.title,
                    n.decision,
                    n.rationale,
                    n.tradeoffs,
                    n.confidence::float AS confidence,
                    n.tags,
                    n.created_at::text,
                    n.updated_at::text,
                    COALESCE(
                        json_agg(
                            json_build_object(
                                'ref',       a.artifact_ref,
                                'type',      a.artifact_type,
                                'is_anchor', a.is_display_anchor
                            ) ORDER BY a.is_display_anchor DESC, a.artifact_ref
                        ) FILTER (WHERE a.id IS NOT NULL),
                        '[]'::json
                    ) AS artifacts
                FROM decision_nodes n
                LEFT JOIN decision_artifacts a ON a.decision_id = n.id
                WHERE n.id = %s::uuid
                GROUP BY n.id
            """, (decision_id,))
            return cur.fetchone()


def update_decision_by_id(decision_id: str, data: dict):
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE decision_nodes
                SET title      = %s,
                    decision   = %s,
                    rationale  = %s,
                    tradeoffs  = %s::text[],
                    confidence = %s::numeric,
                    tags       = %s::text[],
                    updated_at = NOW()
                WHERE id = %s::uuid
            """, (
                data['title'],
                data['decision'],
                data.get('rationale'),
                data['tradeoffs'],
                data['confidence'],
                data['tags'],
                decision_id,
            ))
    return get_decision_by_id(decision_id)


def get_artifact_paths():
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT artifact_ref AS ref, artifact_type AS type
                FROM decision_artifacts
                WHERE is_display_anchor = TRUE
            """)
            return cur.fetchall()
