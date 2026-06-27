"""
DB persistence for finalized planning sessions.
Inserts decision nodes and their artifacts into Postgres.
Artifact placement is resolved by artifact_resolver, not taken from the node dict.
"""
import os

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

from prompt_refinement.artifact_resolver import resolve_artifact

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "")


def save_finalized_nodes(nodes: list[dict]) -> list[str]:
    """
    Persist a list of decision nodes to the database.

    For each node:
      1. Insert into decision_nodes (semantic fields only).
      2. Resolve artifact placement via heuristic rules.
      3. Insert into decision_artifacts using the resolved placement.

    Returns the list of inserted decision_node UUIDs as strings.
    """
    inserted_ids: list[str] = []

    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        for node in nodes:
            # Step 1: insert the decision node (no artifact fields)
            row = conn.execute(
                """
                INSERT INTO decision_nodes (title, decision, rationale, tradeoffs, confidence, tags)
                VALUES (%s, %s, %s, %s::text[], %s::numeric, %s::text[])
                RETURNING id::text
                """,
                (
                    node.get("title", ""),
                    node.get("decision", ""),
                    node.get("rationale", ""),
                    node.get("tradeoffs", []),
                    node.get("confidence", 0.8),
                    node.get("tags", []),
                ),
            ).fetchone()

            decision_id = row["id"]
            inserted_ids.append(decision_id)

            # Step 2: resolve artifact placement from tags
            artifact = resolve_artifact(node)

            # Step 3: insert the artifact anchor
            conn.execute(
                """
                INSERT INTO decision_artifacts
                    (decision_id, artifact_type, artifact_ref, is_display_anchor)
                VALUES (%s::uuid, %s, %s, %s)
                """,
                (
                    decision_id,
                    artifact["artifact_type"],
                    artifact["artifact_ref"],
                    artifact["is_display_anchor"],
                ),
            )

        conn.commit()

    return inserted_ids
