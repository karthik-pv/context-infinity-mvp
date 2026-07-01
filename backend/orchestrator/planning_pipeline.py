"""
Planning Pipeline Orchestrator — 4-stage multi-pass architecture.

  Stage 1: Planner           → plan/folder mutations + clarifications/suggestions/blockers
  Stage 2: Decision Extractor → decision mutations (add/update/delete)
  Stage 3: Retrieval          → fetch relevant historical decisions from DB (non-LLM)
  Stage 4: Violation Checker  → detect conflicts between new and historical decisions

Each LLM performs exactly one narrow task, reducing prompt complexity and making
token growth scale with relevant context instead of total session size.

Data flow:
  - Sessions persist in planning_sessions table.
  - On finalize, nodes persist to decision_nodes table + session summary appended
    to project_info.project_brief (text array).
  - Violations from each turn are sent to the planner on the next turn so it can
    fix conflicts (via the session state, not the planner prompt — the planner
    doesn't see violations directly).
"""
from prompt_refinement.session_store import get_session, save_session
from db_layer.project_db import add_token_usage

from planner.planner_agent import run as run_planner
from planner.decision_extractor import run as run_decision_extractor
from retrieval.decision_retriever import retrieve as retrieve_decisions
from violation.violation_checker import run as run_violation_check
from metrics.token_usage import log_token_usage


async def run_pipeline(session_id: str, user_message: str) -> None:
    """
    Run the complete 4-stage planning pipeline for one user message.

    Session state is mutated and persisted through the session_store.
    No return value — the caller re-fetches the session.
    """
    # ── Stage 1: Planner ────────────────────────────────────────────────────
    # Input: plan + folders + user prompt
    # Output: plan_mutations, folder_mutations, clarifications, suggestions, blockers
    # Applies mutations to session.implementation_plan + session_folder_structure
    planner_output = await run_planner(session_id, user_message)

    # ── Stage 2: Decision Extraction ────────────────────────────────────────
    # Input: user prompt + plan mutations from Stage 1 + existing session decisions
    # Output: decision_mutations (add/update/delete)
    # Applies mutations to session.inferred_nodes
    updated_decisions, extractor_usage = await run_decision_extractor(
        session_id,
        user_message,
        planner_output.plan_mutations,
    )

    # ── Stage 3: Historical Retrieval ───────────────────────────────────────
    # Input: updated decisions (target_files + tags)
    # Output: relevant historical decisions from DB
    # Non-LLM — pure DB retrieval with tiered scoring
    session = get_session(session_id)
    affected_files = [
        node.get("target_file", "")
        for node in session.inferred_nodes
        if node.get("target_file", "") and node.get("target_file", "") != "."
    ]
    relevant_tags: set[str] = set()
    for node in session.inferred_nodes:
        relevant_tags.update(node.get("tags", []))
    retrieved = retrieve_decisions(affected_files, list(relevant_tags))

    # ── Stage 4: Violation Checker ──────────────────────────────────────────
    # Input: new session decisions + retrieved historical decisions
    # Output: violations with type, violated_decision_id, explanation, severity, suggested_resolution
    violations, violation_usage = await run_violation_check(
        updated_decisions,
        retrieved,
    )

    # ── Apply violations to session ─────────────────────────────────────────
    session.violations = violations

    for v in violations:
        node_title = v.get("violating_node_title")
        if node_title:
            for node in session.inferred_nodes:
                if node.get("title") == node_title:
                    node["risky"] = True
                    node["confidence"] = 0.3
                    node["violation_reason"] = v.get("explanation", "")

    save_session(session)

    # ── Log token metrics ───────────────────────────────────────────────────
    metrics = {
        "planner_input_tokens": planner_output.usage.get("input_tokens", 0),
        "planner_output_tokens": planner_output.usage.get("output_tokens", 0),
        "extractor_input_tokens": extractor_usage.get("input_tokens", 0),
        "extractor_output_tokens": extractor_usage.get("output_tokens", 0),
        "retrieval_count": len(retrieved),
        "violation_input_tokens": violation_usage.get("input_tokens", 0),
        "violation_output_tokens": violation_usage.get("output_tokens", 0),
    }
    log_token_usage(session_id, metrics)

    # Accumulate token usage into project_info
    total_input = (
        metrics["planner_input_tokens"]
        + metrics["extractor_input_tokens"]
        + metrics["violation_input_tokens"]
    )
    total_output = (
        metrics["planner_output_tokens"]
        + metrics["extractor_output_tokens"]
        + metrics["violation_output_tokens"]
    )
    if total_input > 0 or total_output > 0:
        add_token_usage(total_input, total_output)


async def reprocess_violations(session_id: str) -> None:
    """
    Re-run Stage 3 + Stage 4 only (retrieval + violation check) without calling
    the planner or decision extractor again.  Used after a user edits a historical
    decision or an inferred node to see if violations have changed.
    """
    session = get_session(session_id)
    if session is None:
        raise ValueError(f"Session '{session_id}' not found")

    # Stage 3: re-derive affected files + tags from current session decisions
    affected_files = [
        node.get("target_file", "")
        for node in session.inferred_nodes
        if node.get("target_file", "") and node.get("target_file", "") != "."
    ]
    relevant_tags: set[str] = set()
    for node in session.inferred_nodes:
        relevant_tags.update(node.get("tags", []))
    retrieved = retrieve_decisions(affected_files, list(relevant_tags))

    # Stage 4: violation checker
    violations, violation_usage = await run_violation_check(
        session.inferred_nodes,
        retrieved,
    )

    # Apply violations to session
    session.violations = violations

    for v in violations:
        node_title = v.get("violating_node_title")
        if node_title:
            for node in session.inferred_nodes:
                if node.get("title") == node_title:
                    node["risky"] = True
                    node["confidence"] = 0.3
                    node["violation_reason"] = v.get("explanation", "")

    save_session(session)

    # Log token metrics
    metrics = {
        "planner_input_tokens": 0,
        "planner_output_tokens": 0,
        "extractor_input_tokens": 0,
        "extractor_output_tokens": 0,
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
