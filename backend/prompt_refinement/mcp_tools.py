"""
MCP-style tool implementations for the planning session.

Each tool directly mutates the in-memory session state via session_store and returns
a result dict that the agent loop feeds back to the LLM as a tool result.

Design: plain functions, no framework, no external protocol.
The tool_executor.py registry dispatches calls by name.
"""
from .session_store import get_session, save_session
from .merger import merge_decision_nodes
from .retrieval import retrieve_relevant_context
from .artifact_resolver import resolve_artifact
from .models import PlanningSession


# ── Folder structure helper ──────────────────────────────────────────────────

def _recompute_folder_structure(session: PlanningSession) -> None:
    """Add plan target_files to session_folder_structure, remove deleted_paths."""
    paths = set(session.session_folder_structure)
    for section in session.implementation_plan.values():
        if isinstance(section, dict):
            target = section.get("target_file", "")
            if target and target != ".":
                paths.add(target)
    paths -= set(session.deleted_paths)
    session.session_folder_structure = sorted(paths)


# ── Plan tools ───────────────────────────────────────────────────────────────

def add_plan_section(session_id: str, section_id: str, content: str, target_file: str = ".") -> dict:
    """Create or overwrite a plan action point with its target file."""
    session = _require_session(session_id)
    action = "updated" if section_id in session.implementation_plan else "created"
    session.implementation_plan[section_id] = {"content": content, "target_file": target_file}
    _recompute_folder_structure(session)
    save_session(session)
    return {"ok": True, "section_id": section_id, "action": action, "target_file": target_file}


def update_plan_section(session_id: str, section_id: str, content: str, target_file: str | None = None) -> dict:
    """Update an existing plan action point (error if it does not exist)."""
    session = _require_session(session_id)
    if section_id not in session.implementation_plan:
        return {
            "ok": False,
            "error": f"Section '{section_id}' does not exist. Use add_plan_section to create it.",
        }
    section = session.implementation_plan[section_id]
    section["content"] = content
    if target_file is not None:
        section["target_file"] = target_file
    section.pop("risky", None)
    section.pop("violation_reason", None)
    _recompute_folder_structure(session)
    save_session(session)
    return {"ok": True, "section_id": section_id, "action": "updated"}


def delete_plan_section(session_id: str, section_id: str) -> dict:
    """Remove a section from the implementation plan."""
    session = _require_session(session_id)
    session.implementation_plan.pop(section_id, None)
    _recompute_folder_structure(session)
    save_session(session)
    return {"ok": True, "section_id": section_id, "action": "deleted"}


def get_plan(session_id: str) -> dict:
    """Return the full current implementation plan."""
    session = _require_session(session_id)
    return {"plan": session.implementation_plan}


# ── Decision node tools ──────────────────────────────────────────────────────

def add_decision_node(
    session_id: str,
    title: str,
    decision: str,
    target_file: str = ".",
    rationale: str = "",
    tradeoffs: list | None = None,
    confidence: float = 0.8,
    tags: list | None = None,
) -> dict:
    """
    Add a decision node, or update it in-place if one with the same title exists.
    target_file is stored on the node and used as artifact_ref for traceability.
    """
    session = _require_session(session_id)
    node = {
        "title": title,
        "decision": decision,
        "rationale": rationale,
        "tradeoffs": tradeoffs or [],
        "confidence": max(0.0, min(1.0, confidence)),
        "tags": tags or [],
        "target_file": target_file,
    }
    node.update(resolve_artifact(node))
    session.inferred_nodes = merge_decision_nodes(session.inferred_nodes, [node])
    for n in session.inferred_nodes:
        if n.get("title") == title:
            n.pop("risky", None)
    save_session(session)
    return {"ok": True, "title": title, "action": "added_or_updated", "target_file": target_file}


def update_decision_node(
    session_id: str,
    title: str,
    decision: str | None = None,
    target_file: str | None = None,
    rationale: str | None = None,
    tradeoffs: list | None = None,
    confidence: float | None = None,
    tags: list | None = None,
) -> dict:
    """Partially update a decision node by title (error if not found)."""
    session = _require_session(session_id)
    node = next((n for n in session.inferred_nodes if n.get("title") == title), None)
    if node is None:
        return {
            "ok": False,
            "error": f"Node '{title}' not found. Use add_decision_node to create it.",
        }
    if decision is not None:
        node["decision"] = decision
    if rationale is not None:
        node["rationale"] = rationale
    if tradeoffs is not None:
        node["tradeoffs"] = tradeoffs
    if confidence is not None:
        node["confidence"] = max(0.0, min(1.0, confidence))
    if target_file is not None:
        node["target_file"] = target_file
        node.update(resolve_artifact(node))
    if tags is not None:
        node["tags"] = tags
        node.update(resolve_artifact(node))
    node.pop("risky", None)
    save_session(session)
    return {"ok": True, "title": title, "action": "updated"}


def delete_decision_node(session_id: str, title: str) -> dict:
    """Remove a decision node by title."""
    session = _require_session(session_id)
    before = len(session.inferred_nodes)
    session.inferred_nodes = [n for n in session.inferred_nodes if n.get("title") != title]
    save_session(session)
    return {"ok": True, "title": title, "removed": before - len(session.inferred_nodes)}


def get_decision_nodes(session_id: str) -> dict:
    """Return all current inferred decision nodes."""
    session = _require_session(session_id)
    return {"nodes": session.inferred_nodes}


# ── Chat history tools (used by agent loop, not exposed to LLM) ──────────────

def get_chat_history(session_id: str) -> dict:
    session = _require_session(session_id)
    return {"chat_history": [e.model_dump() for e in session.chat_history]}


def append_chat_message(session_id: str, role: str, content: str) -> dict:
    from .models import ChatEntry
    session = _require_session(session_id)
    session.chat_history.append(ChatEntry(role=role, content=content))
    save_session(session)
    return {"ok": True, "role": role}


# ── Folder structure tools ───────────────────────────────────────────────────

def modify_folder_structure(session_id: str, action: str, path: str) -> dict:
    """
    Add or remove a file/folder path from the session folder structure.
    The structure is modified incrementally — existing paths are preserved
    unless explicitly removed.
    """
    session = _require_session(session_id)
    if action not in ("add", "remove"):
        return {"ok": False, "error": f"Invalid action '{action}'. Use 'add' or 'remove'."}
    if not path or path == ".":
        return {"ok": False, "error": "path is required and cannot be '.'"}

    if action == "add":
        session.deleted_paths = [p for p in session.deleted_paths if p != path]
    elif action == "remove":
        if path not in session.deleted_paths:
            session.deleted_paths.append(path)

    _recompute_folder_structure(session)
    save_session(session)
    return {"ok": True, "action": action, "path": path}


# ── Historical retrieval ─────────────────────────────────────────────────────

def search_historical_decisions(query: str) -> dict:
    """Search persisted decision nodes from previous sessions by keyword overlap."""
    results = retrieve_relevant_context(query)
    return {"results": results}


# ── Internal helper ──────────────────────────────────────────────────────────

def _require_session(session_id: str):
    session = get_session(session_id)
    if session is None:
        raise ValueError(f"Session '{session_id}' not found")
    return session
