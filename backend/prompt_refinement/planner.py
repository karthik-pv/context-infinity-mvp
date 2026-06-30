"""
Core planning pipeline entry point.
Delegates to the orchestrator which runs the multi-agent pipeline:
  planner agent → decision retrieval → violation checker.
"""
from .models import PlanningSession
from .session_store import get_session
from orchestrator.planning_pipeline import run_pipeline


async def process_chat_message(session_id: str, user_message: str) -> PlanningSession:
    """
    Main entry point for a planning turn.
    Runs the multi-agent pipeline and returns the updated session.
    Raises ValueError if the session is not found or already finalized.
    """
    await run_pipeline(session_id, user_message)

    session = get_session(session_id)
    if session is None:
        raise ValueError(f"Session '{session_id}' not found after pipeline run")
    return session
