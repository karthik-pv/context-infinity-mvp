"""
Context retriever for Stage 1 (Planner).

Sends only the implementation plan and folder structure to the planner LLM.
The planner does NOT see decisions or violations — those are handled by
separate stages (Stage 2: decision extraction, Stage 4: violation checking).
"""
from db_layer.project_db import get_project_info


def get_relevant_context(session) -> dict:
    """Return the current plan + folder state for the planner system prompt."""
    project_info = get_project_info()

    return {
        "project_brief": project_info.get("project_brief", []),
        "folder_structure": session.session_folder_structure,
        "implementation_plan": [
            {
                "section_id": sid,
                "target_file": sec.get("target_file", "?"),
                "content": sec.get("content", ""),
            }
            for sid, sec in session.implementation_plan.items()
        ],
    }
