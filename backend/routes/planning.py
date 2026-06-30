from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from prompt_refinement.session_store import create_session, get_session, save_session, list_sessions
from prompt_refinement.planner import process_chat_message
from db_layer.planning_db import save_finalized_nodes
from db_layer.project_db import update_folder_structure, append_session_summary

router = APIRouter(prefix="/prompt-refinement")


class PlanningChatRequest(BaseModel):
    session_id: str
    message: str


class FinalizeRequest(BaseModel):
    session_id: str


def _generate_session_summary(session) -> str:
    """Compact 2-sentence summary from plan target_files and decision titles."""
    plan_files = [
        sec.get("target_file", "")
        for sec in session.implementation_plan.values()
        if sec.get("target_file", "") and sec.get("target_file", "") != "."
    ]
    decision_titles = [n.get("title", "") for n in session.inferred_nodes]
    parts = []
    if plan_files:
        parts.append("Files: " + ", ".join(plan_files[:8]))
    if decision_titles:
        parts.append("Decisions: " + ", ".join(decision_titles[:8]))
    if not parts:
        return "Empty session."
    return ". ".join(parts) + "."


@router.get("/sessions")
def get_planning_sessions():
    """List all planning sessions with lightweight metadata, newest first."""
    result = []
    for session in list_sessions():
        user_msgs = [m for m in session.chat_history if m.role == "user"]
        first = user_msgs[0].content if user_msgs else ""
        title = (first[:44] + "…") if len(first) > 44 else (first or "New Session")
        result.append({
            "session_id": session.session_id,
            "status": session.status,
            "message_count": len(user_msgs),
            "title": title,
        })
    return {"sessions": result}


@router.get("/session/{session_id}")
def get_planning_session(session_id: str):
    """Get the full state of a planning session."""
    session = get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.model_dump()


@router.post("/session")
def create_planning_session():
    """Create a new planning session and return its ID."""
    session = create_session()
    return {"session_id": session.session_id}


@router.post("/chat")
async def planning_chat(body: PlanningChatRequest):
    """
    Send a message to the planner. Returns the full updated session state
    (chat_history, implementation_plan, inferred_nodes).
    """
    try:
        session = await process_chat_message(body.session_id, body.message)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return session.model_dump()


@router.post("/finalize")
def finalize_planning_session(body: FinalizeRequest):
    """Persist all inferred decision nodes to the DB and mark the session finalized."""
    session = get_session(body.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status == "finalized":
        raise HTTPException(status_code=400, detail="Session already finalized")
    save_finalized_nodes(session.inferred_nodes)
    update_folder_structure(session.session_folder_structure)
    append_session_summary(_generate_session_summary(session))
    session.status = "finalized"
    save_session(session)
    return {"status": "finalized"}
