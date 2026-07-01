"""
Stage 1: Planner Agent — plan/folder mutations + clarifications/suggestions/blockers.

Input:
  - current implementation plan (session-scoped)
  - current folder structure
  - current user prompt
  - planner system prompt

Output JSON:
  {
    plan_mutations: { add, update, delete },
    folder_mutations: { add, remove, move },
    clarifications: [],
    suggestions: [],
    blockers: []
  }

Responsibility:
  - understand user intent
  - mutate implementation plan
  - mutate folder structure
  - ask clarification questions
  - emit optional suggestions / blockers

Explicitly does NOT:
  - extract decisions (Stage 2 handles this)
  - retrieve historical context (Stage 3 handles this)
  - perform violation checking (Stage 4 handles this)
"""
import json
import re
from dataclasses import dataclass, field

from prompt_refinement.session_store import get_session, save_session
from prompt_refinement.models import ChatEntry, PlanningSession
from ai_adapters.factory import get_adapter

from planner.context_retriever import get_relevant_context
from planner.prompts import PLANNER_SYSTEM_PROMPT


@dataclass
class PlannerOutput:
    """Result of Stage 1 — mutations + UI items + token usage."""
    plan_mutations: dict = field(default_factory=dict)
    folder_mutations: dict = field(default_factory=dict)
    clarifications: list = field(default_factory=list)
    suggestions: list = field(default_factory=list)
    blockers: list = field(default_factory=list)
    usage: dict = field(default_factory=lambda: {"input_tokens": 0, "output_tokens": 0})
    prompt: str = ""
    raw_response: str = ""


def _extract_json(raw: str) -> dict | None:
    """Robustly extract a JSON object from LLM output."""
    if not raw:
        return None
    text = raw.strip()

    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    return None


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


def _apply_plan_mutations(session: PlanningSession, mutations: dict) -> None:
    """Apply add/update/delete plan mutations to session.implementation_plan."""
    if not mutations:
        return
    plan = session.implementation_plan

    for sid in (mutations.get("delete") or []):
        plan.pop(sid, None)

    for sec in (mutations.get("update") or []):
        sid = sec.get("section_id", "")
        if not sid:
            continue
        if sid in plan:
            plan[sid]["content"] = sec.get("content", plan[sid].get("content", ""))
            if sec.get("target_file") is not None:
                plan[sid]["target_file"] = sec["target_file"]
            plan[sid].pop("risky", None)
            plan[sid].pop("violation_reason", None)
        else:
            plan[sid] = {
                "content": sec.get("content", ""),
                "target_file": sec.get("target_file", "."),
            }

    for sec in (mutations.get("add") or []):
        sid = sec.get("section_id", "")
        if not sid:
            continue
        plan[sid] = {
            "content": sec.get("content", ""),
            "target_file": sec.get("target_file", "."),
        }

    _recompute_folder_structure(session)

    # Debug: confirm plan state after mutation
    print(f"[planner] _apply_plan_mutations: {len(mutations.get('add') or [])} add, "
          f"{len(mutations.get('update') or [])} update, "
          f"{len(mutations.get('delete') or [])} delete -> "
          f"{len(plan)} total sections: {list(plan.keys())}")


def _apply_folder_mutations(session: PlanningSession, mutations: dict) -> None:
    """Apply add/remove/move folder mutations to session."""
    if not mutations:
        return
    paths = set(session.session_folder_structure)
    deleted = set(session.deleted_paths)

    for path in (mutations.get("add") or []):
        if path and path != ".":
            paths.add(path)
            deleted.discard(path)

    for path in (mutations.get("remove") or []):
        if path:
            paths.discard(path)
            deleted.add(path)

    for move in (mutations.get("move") or []):
        old = move.get("from", "")
        new = move.get("to", "")
        if not old or not new:
            continue
        # Update folder paths
        updated = set()
        for p in paths:
            if p == old or p.startswith(old.rstrip("/") + "/"):
                updated.add(new + p[len(old):])
            else:
                updated.add(p)
        paths = updated
        deleted.add(old)
        # Update plan section target_files
        for sec in session.implementation_plan.values():
            if isinstance(sec, dict):
                tf = sec.get("target_file", "")
                if tf and (tf == old or tf.startswith(old.rstrip("/") + "/")):
                    sec["target_file"] = new + tf[len(old):]

    session.session_folder_structure = sorted(paths)
    session.deleted_paths = sorted(deleted)
    _recompute_folder_structure(session)

    # Debug: confirm folder structure after mutation
    print(f"[planner] _apply_folder_mutations: {len(mutations.get('add') or [])} add, "
          f"{len(mutations.get('remove') or [])} remove, "
          f"{len(mutations.get('move') or [])} move -> "
          f"{len(session.session_folder_structure)} total paths")


async def run(session_id: str, user_message: str) -> PlannerOutput:
    """
    Run Stage 1: Planner.

    Returns PlannerOutput with mutations and token usage.
    Session state is mutated and persisted.
    """
    session = get_session(session_id)
    if session is None:
        raise ValueError(f"Session '{session_id}' not found")
    if session.status == "finalized":
        raise ValueError("Session is already finalized")

    # Persist user message and reset per-turn state
    session.chat_history.append(ChatEntry(role="user", content=user_message))
    session.violations = []
    session.clarifications = []
    session.suggestions = []
    session.blockers = []
    save_session(session)

    # Build context — plan + folders only (no decisions, no violations)
    context = get_relevant_context(session)

    # Build system prompt: dynamic data first, then static rules with JSON schema
    system_prompt = (
        f"Session: {session_id}\n\n"
        f"BRIEF: {json.dumps(context['project_brief'])}\n"
        f"FOLDERS: {json.dumps(context['folder_structure'])}\n"
        f"PLAN: {json.dumps(context['implementation_plan'])}\n"
        f"USER: {user_message}\n\n"
        f"{PLANNER_SYSTEM_PROMPT}"
    )

    # Single LLM call — no tool calling, JSON output
    adapter = get_adapter()
    raw, usage = await adapter.chat(system_prompt)

    parsed = _extract_json(raw)
    if parsed is None:
        print(f"[planner] WARNING: could not parse LLM response as JSON")
        print(f"[planner] raw (first 500 chars): {raw[:500] if raw else '(empty)'}")
        return PlannerOutput(usage=usage, prompt=system_prompt, raw_response=raw or "")

    # Debug: log parsed structure for diagnosis
    print(f"[planner] parsed keys: {list(parsed.keys())}")

    # Extract mutations and UI items
    plan_mutations = parsed.get("plan_mutations", {})
    folder_mutations = parsed.get("folder_mutations", {})
    clarifications = parsed.get("clarifications", [])
    suggestions = parsed.get("suggestions", [])
    blockers = parsed.get("blockers", [])

    # Type checks — ensure mutations are dicts, not strings or None
    if not isinstance(plan_mutations, dict):
        print(f"[planner] WARNING: plan_mutations is {type(plan_mutations).__name__}, expected dict. Resetting to {{}}.")
        plan_mutations = {}
    if not isinstance(folder_mutations, dict):
        print(f"[planner] WARNING: folder_mutations is {type(folder_mutations).__name__}, expected dict. Resetting to {{}}.")
        folder_mutations = {}

    # Debug: log mutation details
    print(f"[planner] plan_mutations: add={len(plan_mutations.get('add') or [])}, "
          f"update={len(plan_mutations.get('update') or [])}, "
          f"delete={len(plan_mutations.get('delete') or [])}")
    print(f"[planner] folder_mutations: add={len(folder_mutations.get('add') or [])}, "
          f"remove={len(folder_mutations.get('remove') or [])}, "
          f"move={len(folder_mutations.get('move') or [])}")

    # Apply plan mutations
    _apply_plan_mutations(session, plan_mutations)

    # Apply folder mutations
    _apply_folder_mutations(session, folder_mutations)

    # Debug: log session state after mutations applied
    print(f"[planner] session.implementation_plan sections: {list(session.implementation_plan.keys())}")
    print(f"[planner] session.session_folder_structure ({len(session.session_folder_structure)} paths): "
          f"{session.session_folder_structure[:10]}{'...' if len(session.session_folder_structure) > 10 else ''}")

    # Store UI items on session (current turn — for immediate UI render)
    session.clarifications = clarifications
    session.suggestions = suggestions
    session.blockers = blockers

    # Append assistant message to chat_history so the full conversation
    # (including clarifications/suggestions/blockers) persists across turns.
    # The content is a JSON string the frontend can parse to render output bubbles.
    assistant_content = json.dumps({
        "clarifications": clarifications,
        "suggestions": suggestions,
        "blockers": blockers,
    })
    session.chat_history.append(ChatEntry(role="assistant", content=assistant_content))

    save_session(session)

    return PlannerOutput(
        plan_mutations=plan_mutations,
        folder_mutations=folder_mutations,
        clarifications=clarifications,
        suggestions=suggestions,
        blockers=blockers,
        usage=usage,
        prompt=system_prompt,
        raw_response=raw or "",
    )
