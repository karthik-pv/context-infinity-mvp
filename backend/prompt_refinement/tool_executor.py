"""
Tool registry and executor for the planning agent.

TOOLS        — callable registry keyed by tool name.
TOOL_SCHEMAS — Anthropic-format tool definitions exposed to the LLM.
execute_tool — generic dispatcher that calls the registered function and returns a result dict.
"""
import json
from .mcp_tools import (
    add_plan_section,
    update_plan_section,
    delete_plan_section,
    get_plan,
    add_decision_node,
    update_decision_node,
    delete_decision_node,
    get_decision_nodes,
    get_chat_history,
    append_chat_message,
    search_historical_decisions,
)

# ── Callable registry ────────────────────────────────────────────────────────

TOOLS: dict[str, callable] = {
    "add_plan_section":          add_plan_section,
    "update_plan_section":       update_plan_section,
    "delete_plan_section":       delete_plan_section,
    "get_plan":                  get_plan,
    "add_decision_node":         add_decision_node,
    "update_decision_node":      update_decision_node,
    "delete_decision_node":      delete_decision_node,
    "get_decision_nodes":        get_decision_nodes,
    # Managed by the agent loop — not exposed to the LLM:
    "get_chat_history":          get_chat_history,
    "append_chat_message":       append_chat_message,
    "search_historical_decisions": search_historical_decisions,
}

# ── Tool schemas (Anthropic format) shown to the LLM ────────────────────────
# get_chat_history and append_chat_message are excluded: the agent loop manages
# chat history directly so the LLM never needs to call those tools.

TOOL_SCHEMAS: list[dict] = [
    {
        "name": "add_plan_section",
        "description": (
            "Create or overwrite a section in the implementation plan. "
            "Use for new sections or when replacing an entire section's content."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "Current planning session ID"},
                "section_id": {
                    "type": "string",
                    "description": "Stable snake_case identifier, e.g. 'auth_strategy' or 'data_model'",
                },
                "content": {
                    "type": "string",
                    "description": "Full prose content for this plan section",
                },
            },
            "required": ["session_id", "section_id", "content"],
        },
    },
    {
        "name": "update_plan_section",
        "description": (
            "Update the content of an existing plan section. "
            "Returns an error if the section does not exist — use add_plan_section to create it."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string"},
                "section_id": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["session_id", "section_id", "content"],
        },
    },
    {
        "name": "delete_plan_section",
        "description": "Remove a section from the implementation plan.",
        "input_schema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string"},
                "section_id": {"type": "string"},
            },
            "required": ["session_id", "section_id"],
        },
    },
    {
        "name": "get_plan",
        "description": (
            "Return the current implementation plan in full. "
            "Call this to inspect current plan state before making targeted updates."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string"},
            },
            "required": ["session_id"],
        },
    },
    {
        "name": "add_decision_node",
        "description": (
            "Add a new architectural decision node, or update one with the same title if it already exists. "
            "Use for stable, important design choices worth documenting. "
            "Artifact placement is resolved automatically from tags."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string"},
                "title": {"type": "string", "description": "Short, unique decision title"},
                "decision": {"type": "string", "description": "What was decided"},
                "rationale": {"type": "string", "description": "Why this approach was chosen"},
                "tradeoffs": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of trade-off strings (pros and cons)",
                },
                "confidence": {
                    "type": "number",
                    "description": "0.0–1.0: 0.6=tentative, 0.85=well-reasoned, 0.95+=confirmed by user",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Semantic tags from: auth, db, api, frontend, infra, architecture, global",
                },
            },
            "required": ["session_id", "title", "decision"],
        },
    },
    {
        "name": "update_decision_node",
        "description": (
            "Partially update an existing decision node by title. "
            "Only pass fields you want to change. "
            "Returns an error if the node is not found."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string"},
                "title": {"type": "string", "description": "Exact title of the node to update"},
                "decision": {"type": "string"},
                "rationale": {"type": "string"},
                "tradeoffs": {"type": "array", "items": {"type": "string"}},
                "confidence": {"type": "number"},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["session_id", "title"],
        },
    },
    {
        "name": "delete_decision_node",
        "description": "Remove a decision node by title.",
        "input_schema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string"},
                "title": {"type": "string"},
            },
            "required": ["session_id", "title"],
        },
    },
    {
        "name": "get_decision_nodes",
        "description": (
            "Return all current inferred decision nodes. "
            "Call this to inspect current nodes before making targeted updates."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string"},
            },
            "required": ["session_id"],
        },
    },
    {
        "name": "search_historical_decisions",
        "description": (
            "Search previously persisted architectural decisions from past planning sessions. "
            "Use when the user discusses a topic that may have relevant prior decisions."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Keywords describing the architecture area to search",
                },
            },
            "required": ["query"],
        },
    },
]


# ── Generic executor ─────────────────────────────────────────────────────────

def execute_tool(tool_name: str, args: dict) -> dict:
    """
    Dispatch a tool call by name, execute it, and return the result as a dict.
    Never raises — errors are returned as {"ok": False, "error": "..."}.
    """
    fn = TOOLS.get(tool_name)
    if fn is None:
        return {"ok": False, "error": f"Unknown tool: {tool_name!r}"}
    try:
        return fn(**args)
    except TypeError as exc:
        return {"ok": False, "error": f"Bad arguments for {tool_name!r}: {exc}"}
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}
    except Exception as exc:
        return {"ok": False, "error": f"Tool {tool_name!r} raised an unexpected error: {exc}"}
