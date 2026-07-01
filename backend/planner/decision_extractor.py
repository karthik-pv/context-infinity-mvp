"""
Stage 2: Decision Extraction Pass — pure LLM extraction of architectural decisions.

Input:
  - current user prompt
  - planner mutations from Stage 1
  - current session decisions

Output JSON:
  {
    decision_mutations: { add, update, delete }
  }

Responsibility:
  - identify architectural decisions introduced or modified in current turn
  - create / update / delete decision nodes

This pass is pure extraction:
  - no technical suggestions
  - no architecture reasoning
  - no conflict analysis
"""
import json
import re

from prompt_refinement.session_store import get_session, save_session
from prompt_refinement.merger import merge_decision_nodes
from prompt_refinement.artifact_resolver import resolve_artifact
from ai_adapters.factory import get_adapter

from planner.prompts import DECISION_EXTRACTION_PROMPT


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


def _format_plan_mutations(mutations: dict) -> str:
    """Format plan mutations as readable text for the extractor prompt."""
    if not mutations:
        return "(no plan changes)"

    parts = []
    for sec in (mutations.get("add") or []):
        parts.append(f"+ [{sec.get('section_id', '?')}] -> {sec.get('target_file', '?')}: {sec.get('content', '')}")
    for sec in (mutations.get("update") or []):
        parts.append(f"~ [{sec.get('section_id', '?')}] -> {sec.get('target_file', '?')}: {sec.get('content', '')}")
    for sid in (mutations.get("delete") or []):
        parts.append(f"- [{sid}]")
    return "\n".join(parts) if parts else "(no plan changes)"


def _format_existing_decisions(nodes: list[dict]) -> str:
    """Format existing session decisions for the extractor prompt."""
    if not nodes:
        return "(none)"
    return "\n".join(
        f"- {n.get('title', '?')}: {n.get('decision', '?')}"
        for n in nodes
    )


def _apply_decision_mutations(session, mutations: dict) -> None:
    """Apply add/update/delete decision mutations to session.inferred_nodes."""
    nodes = session.inferred_nodes

    # Delete
    for title in (mutations.get("delete") or []):
        nodes = [n for n in nodes if n.get("title") != title]

    # Update — replace the entire node uniformly to keep title/decision in sync
    for node_data in (mutations.get("update") or []):
        title = node_data.get("title", "")
        if not title:
            continue
        existing = next((n for n in nodes if n.get("title") == title), None)
        if existing:
            # Build a fresh node from the LLM output, preserving only artifact resolution
            refs = node_data.get("artifact_refs") or []
            target_file = refs[0] if refs else existing.get("target_file", ".")
            new_node = {
                "title": title,
                "decision": node_data.get("decision", existing.get("decision", "")),
                "rationale": node_data.get("rationale", existing.get("rationale", "")),
                "tradeoffs": node_data.get("tradeoffs") if node_data.get("tradeoffs") is not None else existing.get("tradeoffs", []),
                "confidence": max(0.0, min(1.0, node_data.get("confidence", existing.get("confidence", 0.8)))),
                "tags": node_data.get("tags") if node_data.get("tags") is not None else existing.get("tags", []),
                "target_file": target_file,
            }
            new_node.update(resolve_artifact(new_node))
            # Replace the old node in-place
            idx = nodes.index(existing)
            nodes[idx] = new_node

    # Add (merge with dedup)
    add_nodes = []
    for node_data in (mutations.get("add") or []):
        title = node_data.get("title", "")
        if not title:
            continue
        refs = node_data.get("artifact_refs") or []
        target_file = refs[0] if refs else node_data.get("target_file", ".")
        node = {
            "title": title,
            "decision": node_data.get("decision", ""),
            "rationale": node_data.get("rationale", ""),
            "tradeoffs": node_data.get("tradeoffs") or [],
            "confidence": max(0.0, min(1.0, node_data.get("confidence", 0.8))),
            "tags": node_data.get("tags") or [],
            "target_file": target_file,
        }
        node.update(resolve_artifact(node))
        add_nodes.append(node)

    if add_nodes:
        nodes = merge_decision_nodes(nodes, add_nodes)

    session.inferred_nodes = nodes


async def run(session_id: str, user_message: str, plan_mutations: dict) -> tuple[list[dict], dict, str, str]:
    """
    Run Stage 2: Decision Extraction.

    Args:
        session_id: The planning session ID.
        user_message: The user's original prompt this turn.
        plan_mutations: The plan mutations from Stage 1.

    Returns:
        (updated_decisions, usage, prompt, raw_response)
    """
    session = get_session(session_id)
    if session is None:
        raise ValueError(f"Session '{session_id}' not found")

    prompt = DECISION_EXTRACTION_PROMPT.format(
        user_message=user_message,
        plan_mutations=_format_plan_mutations(plan_mutations),
        existing_decisions=_format_existing_decisions(session.inferred_nodes),
    )

    adapter = get_adapter()
    raw, usage = await adapter.chat(prompt)

    parsed = _extract_json(raw)
    if parsed is None:
        print(f"[decision_extractor] WARNING: could not parse LLM response as JSON")
        print(f"[decision_extractor] raw (first 500 chars): {raw[:500] if raw else '(empty)'}")
        return list(session.inferred_nodes), usage, prompt, raw or ""

    decision_mutations = parsed.get("decision_mutations", {})
    _apply_decision_mutations(session, decision_mutations)
    save_session(session)

    return list(session.inferred_nodes), usage, prompt, raw or ""
