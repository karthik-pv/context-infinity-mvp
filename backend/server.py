from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from db_layer.postgres_access import get_decisions, get_artifact_paths, get_decision_by_id, update_decision_by_id
from ai_adapters.factory import get_adapter
from prompt_refinement.session_store import create_session, get_session, save_session, list_sessions
from prompt_refinement.planner import process_chat_message
from db_layer.planning_db import save_finalized_nodes


# ── Existing request models ───────────────────────────────────────────────────

class DecisionUpdate(BaseModel):
    title: str
    decision: str
    rationale: Optional[str] = None
    tradeoffs: list[str] = []
    confidence: float = Field(ge=0.0, le=1.0)
    tags: list[str] = []


class ChatMessage(BaseModel):
    message: str


# ── Prompt-refinement request models ─────────────────────────────────────────

class PlanningChatRequest(BaseModel):
    session_id: str
    message: str


class FinalizeRequest(BaseModel):
    session_id: str


# ── App setup ─────────────────────────────────────────────────────────────────

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Existing routes ───────────────────────────────────────────────────────────

@app.get("/")
def hello():
    return {"message": "Hello World"}


@app.get("/v1/decisions")
def decisions():
    return {
        "nodes": get_decisions(),
        "paths": get_artifact_paths(),
    }


@app.get("/v1/decisions/{decision_id}")
def decision_detail(decision_id: str):
    node = get_decision_by_id(decision_id)
    if node is None:
        raise HTTPException(status_code=404, detail="Not found")
    return node


@app.put("/v1/decisions/{decision_id}")
def decision_update(decision_id: str, body: DecisionUpdate):
    node = update_decision_by_id(decision_id, body.model_dump())
    if node is None:
        raise HTTPException(status_code=404, detail="Not found")
    return node


@app.post("/v1/chat")
async def chat(body: ChatMessage):
    adapter = get_adapter()
    reply = await adapter.chat(body.message)
    return {"reply": reply}


# ── Prompt-refinement routes ──────────────────────────────────────────────────

@app.get("/prompt-refinement/sessions")
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


@app.get("/prompt-refinement/session/{session_id}")
def get_planning_session(session_id: str):
    """Get the full state of a planning session."""
    session = get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.model_dump()


@app.post("/prompt-refinement/session")
def create_planning_session():
    """Create a new planning session and return its ID."""
    session = create_session()
    return {"session_id": session.session_id}


@app.post("/prompt-refinement/chat")
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


@app.post("/prompt-refinement/finalize")
def finalize_planning_session(body: FinalizeRequest):
    """
    Persist all inferred decision nodes to the DB and mark the session finalized.
    """
    session = get_session(body.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status == "finalized":
        raise HTTPException(status_code=400, detail="Session already finalized")

    save_finalized_nodes(session.inferred_nodes)
    session.status = "finalized"
    save_session(session)
    return {"status": "finalized"}
