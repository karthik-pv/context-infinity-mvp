"""
Tool registry and executor for the planning agent.

TOOLS        — callable registry keyed by tool name.
TOOL_SCHEMAS — re-exported from tool_schemas for backward-compatible imports.
execute_tool — generic dispatcher that calls the registered function and returns a result dict.
"""
from .tool_schemas import TOOL_SCHEMAS
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

TOOLS: dict[str, callable] = {
    "add_plan_section":            add_plan_section,
    "update_plan_section":         update_plan_section,
    "delete_plan_section":         delete_plan_section,
    "get_plan":                    get_plan,
    "add_decision_node":           add_decision_node,
    "update_decision_node":        update_decision_node,
    "delete_decision_node":        delete_decision_node,
    "get_decision_nodes":          get_decision_nodes,
    # Managed by the agent loop — not exposed to the LLM:
    "get_chat_history":            get_chat_history,
    "append_chat_message":         append_chat_message,
    "search_historical_decisions": search_historical_decisions,
}


def execute_tool(tool_name: str, args: dict) -> dict:
    """
    Dispatch a tool call by name and return the result.
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
