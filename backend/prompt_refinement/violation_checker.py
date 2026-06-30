"""
Violation checker: deep LLM analysis of plan changes and decision nodes against
existing architectural decisions.

Detects direct, indirect, and tangential violations by asking the LLM to reason
about whether proposed implementation changes conflict with established decisions.
"""
import json
import re

from ai_adapters.factory import get_adapter
from db_layer.postgres_access import get_decisions

_VIOLATION_PROMPT = """\
You are a strict architectural compliance analyzer. Detect violations of existing
architectural decisions in proposed implementation plan changes and new decision nodes.

=== CHANGED PLAN SECTIONS ===
{changed_sections}

=== NEW/CHANGED DECISION NODES ===
{changed_nodes}

=== EXISTING ARCHITECTURAL DECISIONS ===
{decisions}

=== ANALYSIS INSTRUCTIONS ===

Analyze whether any changed plan section or new decision node VIOLATES any existing
architectural decision. Think deeply and systematically. For each change, check against
each decision at three levels:

1. DIRECT VIOLATIONS — The change explicitly contradicts the decision.
   Decision says "Use JWT auth" but change says "Implement Basic Auth".

2. INDIRECT VIOLATIONS — The change introduces something that undermines the
   decision's rationale or creates a conflicting dependency.
   Decision says "Use PostgreSQL for all storage" but change adds SQLite.
   Decision says "Use repository pattern" but change adds raw SQL in routes.

3. TANGENTIAL VIOLATIONS — The change affects a component, assumption, or pattern
   that the decision depends on, even if the change is in a different file.
   Decision says "API must be stateless" but change adds session storage.
   Decision says "All config via env vars" but change hardcodes config values.
   Decision says "Use async for all I/O" but change adds synchronous file ops.

CRITICAL: Interpret the SPIRIT and RATIONALE of each decision, not just its literal text.
A decision that says "server.py should only handle routing, no API client logic" reflects
a broader principle: server.py should remain thin — ALL business logic, computation,
and integration logic belongs in the services layer. Adding ANY non-routing code to
server.py violates this principle, even if the specific code isn't an "API client call".
When a decision establishes a separation of concerns, ANY code that crosses that
separation is a violation, regardless of whether the specific type of code was mentioned.

A new decision node that contradicts an existing decision is ALSO a violation. For example,
if an existing decision says "server.py should only handle routing" and a new decision node
says "Add emoji enrichment logic in server.py", the new decision node violates the existing one.

Consider technology choices, architectural patterns, dependency direction, data flow,
naming conventions, and implicit assumptions. Trace indirect relationships:
- A change in one file can violate a decision about another file if they share
  a dependency chain or architectural layer.
- A change that introduces a new library can violate a decision about technology
  standards even if the decision doesn't mention that specific library.
- A change that alters data flow can violate a decision about separation of concerns
  even if the files are different.
- A change that adds logic to a file that a decision says should only contain routing
  is a violation even if the logic is different from what the decision specifically mentions.

Only report ACTUAL violations where the change genuinely conflicts with a decision
or its underlying rationale. Do NOT report mere "related" items without a real conflict.

=== RESPONSE FORMAT ===

Respond with ONLY a JSON object, no other text, no markdown fences:
{{
  "violations": [
    {{
      "decision_title": "title of the violated decision",
      "decision": "the decision text",
      "change_section": "section_id of the violating plan section, or null if this is a decision node violation",
      "violated_node_title": "title of the violating decision node, or null if this is a plan section violation",
      "change_content": "brief summary of the violating change",
      "violation_type": "direct" | "indirect" | "tangential",
      "explanation": "detailed explanation of why this is a violation, including the chain of reasoning from the change to the decision and its rationale"
    }}
  ]
}}

If there are no violations, return: {{"violations": []}}
"""


def _extract_json(raw: str) -> dict | None:
    """Robustly extract a JSON object from LLM output that may have markdown fences or preamble."""
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
    return "\n\n".join(
        f"- Title: {d.get('title', '?')}\n"
        f"  Decision: {d.get('decision', '?')}\n"
        f"  Rationale: {d.get('rationale', '(none)')}\n"
        f"  Target file: {d.get('target_file', d.get('location', '?'))}\n"
        f"  Tags: {', '.join(d.get('tags', []))}"
        for d in decisions
    )


async def check_violations(
    changed_sections: dict[str, dict],
    changed_nodes: list[dict],
    session_decisions: list[dict],
) -> list[dict]:
    """
    Use the LLM to deeply analyze whether plan changes and new decision nodes
    violate any existing decisions. Combines session-scoped decisions with all
    persisted historical decisions. Returns a list of violation dicts.
    """
    if not changed_sections and not changed_nodes:
        return []

    all_decisions = list(session_decisions)
    try:
        all_decisions.extend(get_decisions())
    except Exception:
        pass

    if not all_decisions:
        return []

    sections_text = "(none)" if not changed_sections else "\n\n".join(
        f"[{sid}] -> {sec.get('target_file', '?')}\n{sec.get('content', '')}"
        for sid, sec in changed_sections.items()
    )

    nodes_text = "(none)" if not changed_nodes else "\n\n".join(
        f"- Title: {n.get('title', '?')}\n"
        f"  Decision: {n.get('decision', '?')}\n"
        f"  Target file: {n.get('target_file', '?')}\n"
        f"  Confidence: {n.get('confidence', '?')}"
        for n in changed_nodes
    )

    prompt = _VIOLATION_PROMPT.format(
        changed_sections=sections_text,
        changed_nodes=nodes_text,
        decisions=_format_decisions(all_decisions),
    )

    adapter = get_adapter()
    raw = await adapter.chat(prompt)

    parsed = _extract_json(raw)
    if parsed is None:
        print(f"[violation_checker] WARNING: could not parse LLM response as JSON")
        print(f"[violation_checker] raw response (first 500 chars): {raw[:500] if raw else '(empty)'}")
        return []

    return parsed.get("violations", [])
