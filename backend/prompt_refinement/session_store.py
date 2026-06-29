"""
DB-backed session store.
Sessions are persisted to the planning_sessions table on every state change.
Reads reconstruct the full PlanningSession from the DB row.
"""
import os
import json

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

from .models import PlanningSession, ChatEntry

load_dotenv()
_DATABASE_URL = os.getenv("DATABASE_URL", "")


def _conn():
    return psycopg.connect(_DATABASE_URL, row_factory=dict_row)


def create_session() -> PlanningSession:
    session = PlanningSession()
    with _conn() as conn:
        conn.execute(
            """
            INSERT INTO planning_sessions (session_id, status, chat_history, implementation_plan, inferred_nodes, folder_structure)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                session.session_id,
                session.status,
                json.dumps([]),
                json.dumps({}),
                json.dumps([]),
                [],
            ),
        )
        conn.commit()
    return session


def get_session(session_id: str) -> PlanningSession | None:
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM planning_sessions WHERE session_id = %s",
            (session_id,),
        ).fetchone()
    if row is None:
        return None
    return _row_to_session(row)


def save_session(session: PlanningSession) -> None:
    chat_json = json.dumps([e.model_dump() for e in session.chat_history])
    plan_json = json.dumps(session.implementation_plan)
    nodes_json = json.dumps(session.inferred_nodes)
    with _conn() as conn:
        conn.execute(
            """
            INSERT INTO planning_sessions
                (session_id, status, chat_history, implementation_plan, inferred_nodes, folder_structure, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (session_id) DO UPDATE SET
                status              = EXCLUDED.status,
                chat_history        = EXCLUDED.chat_history,
                implementation_plan = EXCLUDED.implementation_plan,
                inferred_nodes      = EXCLUDED.inferred_nodes,
                folder_structure    = EXCLUDED.folder_structure,
                updated_at          = NOW()
            """,
            (
                session.session_id,
                session.status,
                chat_json,
                plan_json,
                nodes_json,
                session.folder_structure,
            ),
        )
        conn.commit()


def list_sessions() -> list[PlanningSession]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM planning_sessions ORDER BY updated_at DESC"
        ).fetchall()
    return [_row_to_session(row) for row in rows]


def _row_to_session(row: dict) -> PlanningSession:
    chat_data = row.get("chat_history", [])
    chat_history = [ChatEntry(**e) for e in chat_data]
    return PlanningSession(
        session_id=row["session_id"],
        chat_history=chat_history,
        implementation_plan=row.get("implementation_plan", {}),
        inferred_nodes=row.get("inferred_nodes", []),
        folder_structure=row.get("folder_structure", []),
        status=row.get("status", "planning"),
    )
