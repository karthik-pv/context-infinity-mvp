from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from prompt_refinement.session_store import create_session, get_session, save_session, list_sessions
from prompt_refinement.planner import process_chat_message
from orchestrator.planning_pipeline import reprocess_violations
from db_layer.planning_db import save_finalized_nodes
from db_layer.project_db import update_folder_structure, append_session_summary, add_token_usage
from ai_adapters.factory import get_adapter

router = APIRouter(prefix="/prompt-refinement")


class PlanningChatRequest(BaseModel):
    session_id: str
    message: str


class FinalizeRequest(BaseModel):
    session_id: str


class UpdateNodeRequest(BaseModel):
    session_id: str
    title: str
    original_title: str | None = None
    decision: str | None = None
    rationale: str | None = None
    tradeoffs: list[str] | None = None
    confidence: float | None = None
    tags: list[str] | None = None
    target_file: str | None = None


_FINALIZE_SUMMARY_PROMPT = """\
You are summarizing a planning session for a software project. Given the implementation \
plan below, write a concise summary of what this session YIELDED — the outcomes, key \
decisions made, and architecture choices. Do NOT list implementation steps. Keep it to \
2-3 sentences. Write in plain prose, no bullet points.

Implementation plan:
{plan}
"""


def _format_plan_for_summary(session) -> str:
    """Format the implementation plan as readable text for the LLM."""
    if not session.implementation_plan:
        return "(empty)"
    return "\n\n".join(
        f"[{sid}] -> {sec.get('target_file', '?')}\n{sec.get('content', '')}"
        for sid, sec in session.implementation_plan.items()
    )


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


@router.post("/reprocess")
async def reprocess_session(body: FinalizeRequest):
    """
    Re-run the violation checker against the current session state without
    calling the planner again.  Used after a user edits a historical decision
    or an inferred node to see if violations have changed.
    """
    try:
        await reprocess_violations(body.session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    session = get_session(body.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.model_dump()


@router.put("/node")
def update_node(body: UpdateNodeRequest):
    """
    Update an inferred decision node in the current session.
    Uses original_title (if provided) to find the node, then applies all fields.
    Returns the full updated session state.
    """
    session = get_session(body.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    lookup_title = body.original_title or body.title
    node = next((n for n in session.inferred_nodes if n.get("title") == lookup_title), None)
    if node is None:
        raise HTTPException(status_code=400, detail=f"Node '{lookup_title}' not found")

    if body.title:
        node["title"] = body.title
    if body.decision is not None:
        node["decision"] = body.decision
    if body.rationale is not None:
        node["rationale"] = body.rationale
    if body.tradeoffs is not None:
        node["tradeoffs"] = body.tradeoffs
    if body.confidence is not None:
        node["confidence"] = max(0.0, min(1.0, body.confidence))
    if body.target_file is not None:
        node["target_file"] = body.target_file
    if body.tags is not None:
        node["tags"] = body.tags
    node.pop("risky", None)

    save_session(session)
    return session.model_dump()


@router.post("/finalize")
async def finalize_planning_session(body: FinalizeRequest):
    """Persist all inferred decision nodes to the DB and mark the session finalized."""
    session = get_session(body.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status == "finalized":
        raise HTTPException(status_code=400, detail="Session already finalized")

    # Generate LLM outcome summary from the implementation plan
    summary = ""
    summary_usage = {"input_tokens": 0, "output_tokens": 0}
    if session.implementation_plan:
        adapter = get_adapter()
        prompt = _FINALIZE_SUMMARY_PROMPT.format(
            plan=_format_plan_for_summary(session),
        )
        summary, summary_usage = await adapter.chat(prompt)

    save_finalized_nodes(session.inferred_nodes)
    update_folder_structure(session.session_folder_structure)
    if summary:
        append_session_summary(summary.strip())
    session.status = "finalized"
    save_session(session)

    # Log token usage for the finalize LLM call
    total_input = summary_usage.get("input_tokens", 0)
    total_output = summary_usage.get("output_tokens", 0)
    if total_input > 0 or total_output > 0:
        add_token_usage(total_input, total_output)

    return {"status": "finalized", "summary": summary.strip() if summary else ""}
