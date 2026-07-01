"""
Violation Checker Agent — separate LLM agent for architectural compliance checking.

Receives the new implementation plan, new inferred decisions, and retrieved
historical decisions.  Determines whether any new changes violate existing
architectural decisions at three levels: direct, indirect, tangential.

This is a separate agent from the planner — the planner never sees historical
decisions, and this agent never generates plan content.  This separation ensures
the violation check is impartial and the planner's token footprint stays small.

Uses tool calling (report_violations) instead of JSON-in-prose so the output
structure is guaranteed.  Falls back to JSON extraction if the model emits prose
instead of a tool call.
"""
import json
import re

from ai_adapters.factory import get_adapter

_VIOLATION_PROMPT = """\
You are a strict architectural compliance analyzer. Detect violations of existing
architectural decisions in proposed implementation plan changes and new decision nodes.

=== NEW IMPLEMENTATION PLAN ===
{new_plan}

=== NEW DECISION NODES ===
{new_decisions}

=== EXISTING ARCHITECTURAL DECISIONS (from DB) ===
{historical_decisions}

=== ANALYSIS INSTRUCTIONS ===

Analyze whether any new plan section or new decision node VIOLATES any existing
architectural decision. Think deeply and systematically. For each change, check
against each decision at three levels:

1. DIRECT VIOLATIONS — The change explicitly contradicts the decision.
   Decision says "Use JWT auth" but change says "Implement Basic Auth".
   Changing a port, framework, or architectural choice that was already decided
   is a direct violation.

2. INDIRECT VIOLATIONS — The change introduces something that undermines the
   decision's rationale or creates a conflicting dependency.
   Decision says "Use PostgreSQL for all storage" but change adds SQLite.

3. TANGENTIAL VIOLATIONS — The change affects a component, assumption, or pattern
   that the decision depends on, even if the change is in a different file.
   Decision says "API must be stateless" but change adds session storage.

CRITICAL: Interpret the SPIRIT and RATIONALE of each decision, not just its literal
text. A decision that establishes a separation of concerns means ANY code crossing
that separation is a violation, regardless of the specific type of code.

A new decision node that contradicts an existing decision is ALSO a violation.
Modifying a file that was finalized by a previous session WITHOUT explicit human
authorization is a violation.

Only report ACTUAL violations where the change genuinely conflicts with a decision
or its underlying rationale. Do NOT report mere "related" items without a real conflict.

Call the report_violations tool with your findings. Include the violated_decision_id
(from the existing decisions list above) so the UI can link to the decision for editing.
If there are no violations, call the tool with an empty violations array.
"""

_VIOLATION_TOOL = {
    "name": "report_violations",
    "description": "Report all architectural violations found in the new changes.",
    "input_schema": {
        "type": "object",
        "properties": {
            "violations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "violated_decision_id": {
                            "type": "string",
                            "description": "The 'id' field of the existing decision being violated, from the list above.",
                        },
                        "violated_decision_title": {
                            "type": "string",
                            "description": "Title of the existing decision being violated.",
                        },
                        "change_section": {
                            "type": "string",
                            "description": "section_id of the violating plan section, or null if none.",
                        },
                        "violated_node_title": {
                            "type": "string",
                            "description": "Title of the violating new decision node, or null if none.",
                        },
                        "violation_type": {
                            "type": "string",
                            "enum": ["direct", "indirect", "tangential"],
                        },
                        "severity": {
                            "type": "string",
                            "enum": ["high", "medium", "low"],
                        },
                        "explanation": {
                            "type": "string",
                            "description": "Detailed explanation of why this is a violation.",
                        },
                    },
                    "required": ["violated_decision_title", "violation_type", "severity", "explanation"],
                },
            },
        },
        "required": ["violations"],
    },
}


def _extract_json(raw: str) -> dict | None:
    """Robustly extract a JSON object from LLM output that may have fences or preamble."""
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


def _format_plan(plan: dict) -> str:
    if not plan:
        return "(empty)"
    return "\n\n".join(
        f"[{sid}] -> {sec.get('target_file', '?')}\n{sec.get('content', '')}"
        for sid, sec in plan.items()
    )


def _format_nodes(nodes: list[dict]) -> str:
    if not nodes:
        return "(none)"
    return "\n\n".join(
        f"- Title: {n.get('title', '?')}\n"
        f"  Decision: {n.get('decision', '?')}\n"
        f"  Target file: {n.get('target_file', '?')}\n"
        f"  Confidence: {n.get('confidence', '?')}"
        for n in nodes
    )


def _format_historical(decisions: list[dict]) -> str:
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
    new_plan: dict,
    new_decisions: list[dict],
    historical_decisions: list[dict],
) -> tuple[list[dict], dict]:
    """
    Run the violation checker agent.

    Returns (violations, usage) where usage is:
      {"input_tokens": int, "output_tokens": int}
    """
    if not historical_decisions:
        return [], {"input_tokens": 0, "output_tokens": 0}

    prompt = _VIOLATION_PROMPT.format(
        new_plan=_format_plan(new_plan),
        new_decisions=_format_nodes(new_decisions),
        historical_decisions=_format_historical(historical_decisions),
    )

    adapter = get_adapter()

    # Primary path: tool calling (guaranteed structure)
    _, tool_calls, usage = await adapter.chat_with_tools(
        system=prompt,
        messages=[{"role": "user", "content": "Analyze the changes and call report_violations with your findings."}],
        tools=[_VIOLATION_TOOL],
    )

    if tool_calls:
        for tc in tool_calls:
            if tc["name"] == "report_violations":
                return tc["input"].get("violations", []), usage

    # Fallback: try to parse JSON from prose (older models that don't support tools)
    raw, fallback_usage = await adapter.chat(prompt)
    merged_usage = {
        "input_tokens": usage.get("input_tokens", 0) + fallback_usage.get("input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0) + fallback_usage.get("output_tokens", 0),
    }

    parsed = _extract_json(raw)
    if parsed is None:
        print(f"[violation_checker] WARNING: could not parse LLM response as JSON")
        print(f"[violation_checker] raw response (first 500 chars): {raw[:500] if raw else '(empty)'}")
        return [], merged_usage

    return parsed.get("violations", []), merged_usage
