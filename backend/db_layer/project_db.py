"""
DB access for the project_info singleton table.
Stores project_path, project_brief, and folder_structure.
"""
import os

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()
_DATABASE_URL = os.getenv("DATABASE_URL", "")


def _conn():
    return psycopg.connect(_DATABASE_URL, row_factory=dict_row)


def get_project_info() -> dict:
    with _conn() as conn:
        row = conn.execute(
            "SELECT project_path, project_brief, folder_structure, actual_folder_structure, "
            "input_tokens_consumed, output_tokens_consumed, cost "
            "FROM project_info WHERE id = 1"
        ).fetchone()
    if row is None:
        return {
            "project_path": "",
            "project_brief": [],
            "folder_structure": [],
            "actual_folder_structure": [],
            "input_tokens_consumed": 0,
            "output_tokens_consumed": 0,
            "cost": 0,
        }
    return {
        "project_path": row["project_path"],
        "project_brief": row["project_brief"],
        "folder_structure": row.get("folder_structure", []),
        "actual_folder_structure": row.get("actual_folder_structure", []),
        "input_tokens_consumed": row.get("input_tokens_consumed") or 0,
        "output_tokens_consumed": row.get("output_tokens_consumed") or 0,
        "cost": float(row.get("cost") or 0),
    }


def update_project_info(
    project_path: str | None = None,
    project_brief: str | list[str] | None = None,
) -> dict:
    sets = []
    params = []
    if project_path is not None:
        sets.append("project_path = %s")
        params.append(project_path)
    if project_brief is not None:
        brief_list = [project_brief] if isinstance(project_brief, str) else project_brief
        sets.append("project_brief = %s")
        params.append(brief_list)
    if not sets:
        return get_project_info()
    sets.append("updated_at = NOW()")
    with _conn() as conn:
        conn.execute(
            f"UPDATE project_info SET {', '.join(sets)} WHERE id = 1",
            params,
        )
        conn.commit()
    return get_project_info()


def append_session_summary(summary: str) -> None:
    """Append a session summary string to the project_brief text array."""
    with _conn() as conn:
        conn.execute(
            "UPDATE project_info SET "
            "  project_brief = array_append(COALESCE(project_brief, '{}'), %s), "
            "  updated_at = NOW() "
            "WHERE id = 1",
            (summary,),
        )
        conn.commit()


def update_folder_structure(paths: list[str]) -> None:
    with _conn() as conn:
        conn.execute(
            "UPDATE project_info SET folder_structure = %s, updated_at = NOW() WHERE id = 1",
            (paths,),
        )
        conn.commit()


def get_folder_structure() -> list[str]:
    with _conn() as conn:
        row = conn.execute(
            "SELECT folder_structure FROM project_info WHERE id = 1"
        ).fetchone()
    return row.get("folder_structure", []) if row else []


def update_actual_folder_structure(paths: list[str]) -> None:
    with _conn() as conn:
        conn.execute(
            "UPDATE project_info SET actual_folder_structure = %s, updated_at = NOW() WHERE id = 1",
            (paths,),
        )
        conn.commit()


def add_token_usage(input_tokens: int, output_tokens: int) -> None:
    """Accumulate token usage into the project_info singleton."""
    with _conn() as conn:
        conn.execute(
            "UPDATE project_info SET "
            "  input_tokens_consumed = COALESCE(input_tokens_consumed, 0) + %s, "
            "  output_tokens_consumed = COALESCE(output_tokens_consumed, 0) + %s, "
            "  updated_at = NOW() "
            "WHERE id = 1",
            (input_tokens, output_tokens),
        )
        conn.commit()
