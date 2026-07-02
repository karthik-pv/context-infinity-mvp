"""
Stage 4: Violation Checking Pass — LLM conflict detection between new and historical decisions.

Input:
  - newly mutated session decisions (from Stage 2)
  - retrieved historical decisions (from Stage 3)
  - violation checker prompt

Output JSON:
  {
    violations: [
      {
        type: "direct" | "indirect" | "tangential",
        violated_decision_id: "uuid",
        violating_node_title: "title of new decision",
        explanation: "...",
        severity: "high" | "medium" | "low",
        suggested_resolution: "..."
      }
    ]
  }

Responsibility:
  - detect architectural conflicts
  - detect context drift
  - detect violations of historical decisions
  - explain why conflict exists
  - suggest how to resolve

This is a separate LLM from the planner and decision extractor. It never generates
plan content or decisions — it only analyzes conflicts.
"""
import json
import re

from ai_adapters.factory import get_adapter
from planner.prompts import VIOLATION_CHECKER_PROMPT


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


def _format_decisions(decisions: list[dict]) -> str:
    """Format decision nodes for the violation checker prompt."""
    if not decisions:
        return "(none)"
    return "\n\n".join(
        f"- Title: {d.get('title', '?')}\n"
        f"  Decision: {d.get('decision', '?')}\n"
        f"  Rationale: {d.get('rationale', '(none)')}\n"
        f"  Target file: {d.get('target_file', d.get('location', '?'))}\n"
        f"  Tags: {', '.join(d.get('tags', []))}"
        for d in decisions
    )


def _format_historical(decisions: list[dict]) -> str:
    """Format historical decisions with IDs for the violation checker prompt."""
    if not decisions:
        return "(none found)"
    return "\n\n".join(
        f"- ID: {d.get('id', '?')}\n"
        f"  Title: {d.get('title', '?')}\n"
        f"  Decision: {d.get('decision', '?')}\n"
        f"  Rationale: {d.get('rationale', '(none)')}\n"
        f"  Target file: {d.get('target_file', d.get('location', '?'))}\n"
        f"  Tags: {', '.join(d.get('tags', []))}\n"
        f"  Score: {d.get('score', 0)}"
        for d in decisions
    )


async def run(
    new_decisions: list[dict],
    historical_decisions: list[dict],
) -> tuple[list[dict], dict, str, str]:
    """
    Run Stage 4: Violation Checker.

    Args:
        new_decisions: The session's inferred decision nodes (after Stage 2).
        historical_decisions: Retrieved historical decisions from DB (from Stage 3).

    Returns:
        (violations, usage, prompt, raw_response)
    """
    if not historical_decisions:
        return [], {"input_tokens": 0, "output_tokens": 0}, "", ""

    prompt = VIOLATION_CHECKER_PROMPT.format(
        new_decisions=_format_decisions(new_decisions),
        historical_decisions=_format_historical(historical_decisions),
    )

    adapter = get_adapter()
    raw, usage = await adapter.chat(prompt)

    parsed = _extract_json(raw)
    if parsed is None:
        print(f"[violation_checker] WARNING: could not parse LLM response as JSON")
        print(f"[violation_checker] raw (first 500 chars): {raw[:500] if raw else '(empty)'}")
        return [], usage, prompt, raw or ""

    return parsed.get("violations", []), usage, prompt, raw or ""
