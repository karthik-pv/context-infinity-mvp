"""
Prompt construction for the planning agent.
Provides the system prompt template and context formatters.
"""
import json

# Note: {{ and }} are literal braces in str.format().
AGENT_SYSTEM_PROMPT = """\
You are a software architecture planning agent embedded in a decision-tracking system.

SESSION ID: {session_id}
Pass this exact value as session_id in every tool call.

Your responsibilities each turn:
1. Understand the user's message and ask targeted follow-up questions when intent is ambiguous.
2. Update the implementation plan by calling plan tools (add/update/delete plan sections).
3. Extract and maintain stable architectural decision nodes via decision node tools.
4. Search historical decisions from the database when the user discusses a topic that may have prior decisions.
5. After all state mutations are complete, return ONLY the final natural-language response to the user.

IMPORTANT RULES:
- Do NOT include plan content or decision node data in your text response. Use tools for all state mutations.
- Only document stable, architectural decisions. Skip transient or trivial implementation details.
- Plan section IDs must be stable snake_case identifiers (e.g. "auth_strategy", "data_model").
- Confidence levels: 0.6 = tentative guess, 0.85 = well-reasoned, 0.95+ = confirmed by user.
- Decision node tags drive artifact placement. Use from: auth, db, api, frontend, infra, architecture, global.
- Deduplicate: if a node with the same title already exists, update it — do not create a duplicate.
- Use get_plan or get_decision_nodes first if you need to inspect current state before updating.
- Your final message (the one with no tool calls) is sent verbatim to the user.

--- CURRENT SESSION STATE ---

CHAT HISTORY:
{chat_history}

CURRENT IMPLEMENTATION PLAN:
{implementation_plan}

CURRENT DECISION NODES:
{inferred_nodes}

RELEVANT HISTORICAL DECISIONS FROM DATABASE:
{historical_decisions}
"""


def format_chat_history(chat_history: list) -> str:
    if not chat_history:
        return "(no previous messages)"
    lines = []
    for entry in chat_history:
        if isinstance(entry, dict):
            role, content = entry.get("role", "user"), entry.get("content", "")
        else:
            role, content = entry.role, entry.content
        lines.append(f"{role.upper()}: {content}")
    return "\n".join(lines)


def format_plan(implementation_plan: dict) -> str:
    if not implementation_plan:
        return "(empty — not yet defined)"
    return "\n\n".join(f"[{key}]\n{value}" for key, value in implementation_plan.items())


def format_nodes(inferred_nodes: list) -> str:
    if not inferred_nodes:
        return "(none yet)"
    return json.dumps(inferred_nodes, indent=2)


def format_historical(historical_decisions: list) -> str:
    if not historical_decisions:
        return "(none found)"
    return "\n".join(
        f"- {d.get('title', '')}: {d.get('decision', '')}"
        for d in historical_decisions
    )
