"""
Context retriever — sends the full current session state to the LLM every turn.

Full state (compact form) is sent every prompt so the LLM always sees consistent
data.  This eliminates broken state where a folder rename updates one slice but
leaves stale references in another — the LLM sees everything and can update all
references in a single batch_update call.
"""
from prompt_refinement.models import PlanningSession
from db_layer.project_db import get_project_info


def get_relevant_context(user_message: str, session: PlanningSession) -> dict:
    """Return the full current state for the system prompt."""
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
        "inferred_decisions": [
            {
                "title": n.get("title", "?"),
                "decision": n.get("decision", ""),
                "target_file": n.get("target_file", "?"),
                "tags": n.get("tags", []),
            }
            for n in session.inferred_nodes
        ],
        "violations": session.violations,
    }
