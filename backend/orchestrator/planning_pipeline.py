"""
Planning Pipeline Orchestrator — 4-stage multi-pass architecture.

  Stage 1: Planner           → plan/folder mutations + clarifications/suggestions/blockers
  Stage 2: Decision Extractor → decision mutations (add/update/delete)
  Stage 3: Retrieval          → fetch relevant historical decisions from DB (non-LLM)
  Stage 4: Violation Checker  → detect conflicts between new and historical decisions

Each LLM performs exactly one narrow task, reducing prompt complexity and making
token growth scale with relevant context instead of total session size.

Logging: each user prompt creates a folder backend/logs/{session_id}-prompt-{N}/
with stage-1.json through stage-4.json (response + usage + notes) and
stage-N-prompt.txt files (readable prompt text).
"""
from prompt_refinement.session_store import get_session, save_session
from db_layer.project_db import add_token_usage

from planner.planner_agent import run as run_planner
from planner.decision_extractor import run as run_decision_extractor
from retrieval.decision_retriever import retrieve as retrieve_decisions
from violation.violation_checker import run as run_violation_check
from prompt_refinement.prompt_logger import get_prompt_number, log_stage


async def run_pipeline(session_id: str, user_message: str) -> None:
    """
    Run the complete 4-stage planning pipeline for one user message.

    Session state is mutated and persisted through the session_store.
    No return value — the caller re-fetches the session.
    """
    # ── Stage 1: Planner ────────────────────────────────────────────────────
    planner_output = await run_planner(session_id, user_message)
    prompt_number = get_prompt_number(session_id)

    # Type check: ensure plan_mutations is a dict before accessing .get()
    assert isinstance(planner_output.plan_mutations, dict), \
        f"plan_mutations must be dict, got {type(planner_output.plan_mutations).__name__}"
    assert isinstance(planner_output.folder_mutations, dict), \
        f"folder_mutations must be dict, got {type(planner_output.folder_mutations).__name__}"

    # Detect empty plan mutations
    plan_add = (planner_output.plan_mutations.get("add") or [])
    plan_update = (planner_output.plan_mutations.get("update") or [])
    plan_delete = (planner_output.plan_mutations.get("delete") or [])
    folder_add = (planner_output.folder_mutations.get("add") or [])
    folder_remove = (planner_output.folder_mutations.get("remove") or [])
    folder_move = (planner_output.folder_mutations.get("move") or [])

    stage1_note = ""
    if not plan_add and not plan_update and not plan_delete:
        stage1_note = "No plan mutations returned by planner."
    if not folder_add and not folder_remove and not folder_move:
        stage1_note = (stage1_note + " " if stage1_note else "") + "No folder mutations returned by planner."
    if not planner_output.raw_response:
        stage1_note = "Empty response from LLM."

    # Log parsed planner output (not raw string) + raw response in extra for debugging
    log_stage(
        session_id, prompt_number, 1,
        prompt=planner_output.prompt,
        response=planner_output.raw_response,
        usage=planner_output.usage,
        extra={
            "plan_mutations": planner_output.plan_mutations,
            "folder_mutations": planner_output.folder_mutations,
            "clarifications": planner_output.clarifications,
            "suggestions": planner_output.suggestions,
            "blockers": planner_output.blockers,
            "raw_response": planner_output.raw_response,
        },
        note=stage1_note,
    )

    # ── Stage 2: Decision Extraction ────────────────────────────────────────
    updated_decisions, extractor_usage, extractor_prompt, extractor_raw = await run_decision_extractor(
        session_id,
        user_message,
        planner_output.plan_mutations,
    )

    stage2_note = ""
    if not updated_decisions:
        stage2_note = "No decisions in session after extraction."
    if not extractor_raw:
        stage2_note = "Empty response from LLM."

    log_stage(
        session_id, prompt_number, 2,
        prompt=extractor_prompt,
        response=extractor_raw,
        usage=extractor_usage,
        note=stage2_note,
    )

    # ── Stage 3: Historical Retrieval ───────────────────────────────────────
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

    stage3_note = ""
    if not retrieved:
        stage3_note = "No historical decisions retrieved (no matching files/tags/keywords in DB)."
    if not affected_files:
        stage3_note = "No affected files derived from session decisions."

    log_stage(
        session_id, prompt_number, 3,
        extra={
            "extraction_metadata": {
                "affected_files": affected_files,
                "relevant_tags": sorted(relevant_tags),
            },
            "retrieved_decisions": retrieved,
            "retrieval_count": len(retrieved),
        },
        note=stage3_note,
    )

    # ── Stage 4: Violation Checker ──────────────────────────────────────────
    violations, violation_usage, violation_prompt, violation_raw = await run_violation_check(
        updated_decisions,
        retrieved,
    )

    stage4_note = ""
    if not retrieved:
        stage4_note = "Skipped — no historical decisions to check against."
    elif not violations:
        stage4_note = "No violations detected."
    if not violation_raw and retrieved:
        stage4_note = "Empty response from LLM."

    log_stage(
        session_id, prompt_number, 4,
        prompt=violation_prompt,
        response=violation_raw,
        usage=violation_usage,
        extra={"violations": violations},
        note=stage4_note,
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

    # ── Accumulate token usage into project_info ────────────────────────────
    total_input = (
        planner_output.usage.get("input_tokens", 0)
        + extractor_usage.get("input_tokens", 0)
        + violation_usage.get("input_tokens", 0)
    )
    total_output = (
        planner_output.usage.get("output_tokens", 0)
        + extractor_usage.get("output_tokens", 0)
        + violation_usage.get("output_tokens", 0)
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

    prompt_number = get_prompt_number(session_id)

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

    stage3_note = ""
    if not retrieved:
        stage3_note = "No historical decisions retrieved (reprocess)."

    log_stage(
        session_id, prompt_number, 3,
        extra={
            "extraction_metadata": {
                "affected_files": affected_files,
                "relevant_tags": sorted(relevant_tags),
                "reprocess": True,
            },
            "retrieved_decisions": retrieved,
            "retrieval_count": len(retrieved),
        },
        note=stage3_note,
    )

    # Stage 4: violation checker
    violations, violation_usage, violation_prompt, violation_raw = await run_violation_check(
        session.inferred_nodes,
        retrieved,
    )

    stage4_note = ""
    if not retrieved:
        stage4_note = "Skipped — no historical decisions to check against (reprocess)."
    elif not violations:
        stage4_note = "No violations detected (reprocess)."

    log_stage(
        session_id, prompt_number, 4,
        prompt=violation_prompt,
        response=violation_raw,
        usage=violation_usage,
        extra={"violations": violations, "reprocess": True},
        note=stage4_note,
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

    # Accumulate token usage into project_info
    total_input = violation_usage.get("input_tokens", 0)
    total_output = violation_usage.get("output_tokens", 0)
    if total_input > 0 or total_output > 0:
        add_token_usage(total_input, total_output)
