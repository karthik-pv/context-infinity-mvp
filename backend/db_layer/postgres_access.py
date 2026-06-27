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


def get_artifact_paths():
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT artifact_ref AS ref, artifact_type AS type
                FROM decision_artifacts
                WHERE is_display_anchor = TRUE
            """)
            return cur.fetchall()
