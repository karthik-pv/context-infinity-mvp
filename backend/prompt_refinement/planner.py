"""
Core planning pipeline entry point.
Delegates to planner_agent which runs the tool-calling agent loop.
"""
from .models import PlanningSession
from .session_store import get_session
from .planner_agent import run_planner_agent


async def process_chat_message(session_id: str, user_message: str) -> PlanningSession:
    """
    Main entry point for a planning turn.
    Runs the tool-calling agent loop and returns the updated session.
    Raises ValueError if the session is not found or already finalized.
    """
    await run_planner_agent(session_id, user_message)

    session = get_session(session_id)
    if session is None:
        raise ValueError(f"Session '{session_id}' not found after agent run")
    return session
