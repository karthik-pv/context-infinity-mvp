"""
In-memory session store keyed by session_id.
No DB persistence — sessions live for the process lifetime (MVP only).
"""
from .models import PlanningSession

_sessions: dict[str, PlanningSession] = {}


def create_session() -> PlanningSession:
    session = PlanningSession()
    _sessions[session.session_id] = session
    return session


def get_session(session_id: str) -> PlanningSession | None:
    return _sessions.get(session_id)


def save_session(session: PlanningSession) -> None:
    _sessions[session.session_id] = session


def list_sessions() -> list[PlanningSession]:
    """Return all sessions, newest first."""
    return list(reversed(list(_sessions.values())))
