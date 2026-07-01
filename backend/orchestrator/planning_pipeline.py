"""
Planning Pipeline Orchestrator — ties together the three-stage multi-agent flow.

  1. Planner Agent      → emits tool calls only (batch_update, search_decisions,
                          request_clarification, emit_suggestions, emit_blockers)
  2. Decision Retriever  → derives affected files + tags from session state to
                          fetch relevant historical decisions from DB
  3. Violation Checker   → separate LLM agent checks new changes against historical decisions

The orchestrator applies risky flags from violations to the session, persists
everything via session_store, logs token metrics, and accumulates token usage
into project_info.

No assistant prose is appended to chat_history — the planner is a tool-only
state engine and the UI renders all state changes.

Data flow:
  - Sessions persist in planning_sessions table.
  - On finalize, nodes persist to decision_nodes table + session summary appended
    to project_info.project_brief (text array).
  - Violations from each turn are sent to the planner on the next turn so it can
    fix conflicts.
"""
from prompt_refinement.session_store import get_session, save_session
from db_layer.project_db import add_token_usage

from planner.planner_agent import run as run_planner
from retrieval.decision_retriever import retrieve as retrieve_decisions
from violation.violation_checker import run as run_violation_check
from metrics.token_usage import log_token_usage


async def run_pipeline(session_id: str, user_message: str) -> None:
    """
    Run the complete planning pipeline for one user message.

    Session state is mutated and persisted through the existing session_store
    pipeline. No return value — the caller re-fetches the session.
    """
    # Stage 1: Planner Agent — emits tool calls only, mutates session state
    planner_output = await run_planner(session_id, user_message)

    # Stage 2: Decision Retrieval — derive affected files + tags from session state
    session = get_session(session_id)
    affected_files = [
        sec.get("target_file", "")
        for sec in session.implementation_plan.values()
        if sec.get("target_file", "") and sec.get("target_file", "") != "."
    ]
    relevant_tags: set[str] = set()
    for node in session.inferred_nodes:
        relevant_tags.update(node.get("tags", []))
    retrieved = retrieve_decisions(affected_files, list(relevant_tags))

    # Stage 3: Violation Checker — separate agent checks new changes against historical decisions
    violations, violation_usage = await run_violation_check(
        planner_output.implementation_plan,
        planner_output.inferred_decisions,
        retrieved,
    )

    # Apply risky flags from violations to session
    session.violations = violations

    for v in violations:
        sid = v.get("change_section")
        if sid and sid in session.implementation_plan:
            session.implementation_plan[sid]["risky"] = True
            session.implementation_plan[sid]["violation_reason"] = v.get("explanation", "")

        node_title = v.get("violated_node_title")
        if node_title:
            for node in session.inferred_nodes:
                if node.get("title") == node_title:
                    node["risky"] = True
                    node["confidence"] = 0.3

    save_session(session)

    # Log token metrics
    metrics = {
        "planner_input_tokens": planner_output.usage.get("input_tokens", 0),
        "planner_output_tokens": planner_output.usage.get("output_tokens", 0),
        "retrieval_count": len(retrieved),
        "violation_input_tokens": violation_usage.get("input_tokens", 0),
        "violation_output_tokens": violation_usage.get("output_tokens", 0),
    }
    log_token_usage(session_id, metrics)

    # Accumulate token usage into project_info
    total_input = metrics["planner_input_tokens"] + metrics["violation_input_tokens"]
    total_output = metrics["planner_output_tokens"] + metrics["violation_output_tokens"]
    if total_input > 0 or total_output > 0:
        add_token_usage(total_input, total_output)

    # No assistant message appended — the planner is a tool-only state engine.
    # The UI renders plan, decisions, clarifications, suggestions, blockers, violations.


async def reprocess_violations(session_id: str) -> None:
    """
    Re-run Stage 2 + Stage 3 only (retrieval + violation check) without calling
    the planner again.  Used after a user edits a historical decision or an
    inferred node to see if violations have changed.

    Session state is mutated and persisted.  No return value.
    """
    session = get_session(session_id)
    if session is None:
        raise ValueError(f"Session '{session_id}' not found")

    # Stage 2: re-derive affected files + tags from current session state
    affected_files = [
        sec.get("target_file", "")
        for sec in session.implementation_plan.values()
        if sec.get("target_file", "") and sec.get("target_file", "") != "."
    ]
    relevant_tags: set[str] = set()
    for node in session.inferred_nodes:
        relevant_tags.update(node.get("tags", []))
    retrieved = retrieve_decisions(affected_files, list(relevant_tags))

    # Stage 3: violation checker
    violations, violation_usage = await run_violation_check(
        session.implementation_plan,
        session.inferred_nodes,
        retrieved,
    )

    # Apply risky flags from violations to session
    session.violations = violations

    for v in violations:
        sid = v.get("change_section")
        if sid and sid in session.implementation_plan:
            session.implementation_plan[sid]["risky"] = True
            session.implementation_plan[sid]["violation_reason"] = v.get("explanation", "")

        node_title = v.get("violated_node_title")
        if node_title:
            for node in session.inferred_nodes:
                if node.get("title") == node_title:
                    node["risky"] = True
                    node["confidence"] = 0.3

    save_session(session)

    # Log token metrics
    metrics = {
        "planner_input_tokens": 0,
        "planner_output_tokens": 0,
        "retrieval_count": len(retrieved),
        "violation_input_tokens": violation_usage.get("input_tokens", 0),
        "violation_output_tokens": violation_usage.get("output_tokens", 0),
    }
    log_token_usage(session_id, metrics)

    # Accumulate token usage into project_info
    total_input = metrics["violation_input_tokens"]
    total_output = metrics["violation_output_tokens"]
    if total_input > 0 or total_output > 0:
        add_token_usage(total_input, total_output)
