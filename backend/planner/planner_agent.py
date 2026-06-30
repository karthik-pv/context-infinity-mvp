"""
Planner Agent — tool-only state engine.

The planner is NOT a chatbot. It emits only tool calls to mutate session state:
  - batch_update          → plan sections, decision nodes, folder structure
  - search_decisions      → get historical decisions from DB by file or tag
  - request_clarification → questions for the UI
  - emit_suggestions      → architecture suggestions for the UI
  - emit_blockers         → critical blockers for the UI

No prose response is ever produced. The UI renders all state changes.

Output: PlannerOutput containing the session's plan, decisions, retrieval_query
(for the orchestrator to fetch historical decisions), and token usage metrics.
"""
import json
from dataclasses import dataclass, field

from prompt_refinement.session_store import get_session, save_session
from prompt_refinement.models import ChatEntry
from prompt_refinement.prompt_logger import log_prompt
from prompt_refinement.tool_executor import TOOL_SCHEMAS, execute_tool
from ai_adapters.factory import get_adapter

from planner.context_retriever import get_relevant_context
from planner.prompts import PLANNER_SYSTEM_PROMPT

_MAX_TOOL_ITERATIONS = 10


@dataclass
class PlannerOutput:
    """Result of a planner agent turn — no user-facing response text."""
    implementation_plan: dict = field(default_factory=dict)
    inferred_decisions: list = field(default_factory=list)
    retrieval_query: dict = field(default_factory=dict)
    usage: dict = field(default_factory=lambda: {"input_tokens": 0, "output_tokens": 0})


async def run(session_id: str, user_message: str) -> PlannerOutput:
    """
    Run the planner state engine for one turn.

    Returns PlannerOutput with plan, decisions, retrieval_query, and token usage.
    Session state is mutated via tool calls and persisted through the existing
    mcp_tools / session_store pipeline. No assistant message is appended to
    chat_history — the planner produces no prose.
    """
    session = get_session(session_id)
    if session is None:
        raise ValueError(f"Session '{session_id}' not found")
    if session.status == "finalized":
        raise ValueError("Session is already finalized")

    # Persist user message and reset per-turn state before calling LLM
    session.chat_history.append(ChatEntry(role="user", content=user_message))
    session.violations = []
    session.clarifications = []
    session.suggestions = []
    session.blockers = []
    session.retrieval_query = {}
    save_session(session)

    # Retrieve relevant context slices (NO historical decisions — planner doesn't see them)
    context = get_relevant_context(user_message, session)

    # Build compact system prompt with full current state
    system_prompt = PLANNER_SYSTEM_PROMPT.format(
        session_id=session_id,
        project_brief=json.dumps(context["project_brief"]),
        folder_structure=json.dumps(context["folder_structure"]),
        implementation_plan=json.dumps(context["implementation_plan"]),
        inferred_decisions=json.dumps(context["inferred_decisions"]),
        violations=json.dumps(context["violations"]),
        user_message=user_message,
    )

    log_prompt(session_id, system_prompt, [])

    # Agent loop — tool calling.  Break after first iteration unless
    # search_decisions was called (needs a follow-up to act on results).
    adapter = get_adapter()
    messages = [{"role": "user", "content": user_message}]

    total_input_tokens = 0
    total_output_tokens = 0

    for i in range(_MAX_TOOL_ITERATIONS):
        _, tool_calls, usage = await adapter.chat_with_tools(
            system=system_prompt,
            messages=messages,
            tools=TOOL_SCHEMAS,
        )

        total_input_tokens += usage.get("input_tokens", 0)
        total_output_tokens += usage.get("output_tokens", 0)

        if not tool_calls:
            break

        called_search = any(tc["name"] == "search_decisions" for tc in tool_calls)

        messages.append({
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": json.dumps(tc["input"]),
                    },
                }
                for tc in tool_calls
            ],
        })

        for tc in tool_calls:
            result = execute_tool(tc["name"], tc["input"])
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "name": tc["name"],
                "content": json.dumps(result),
            })

        # Only loop back if search_decisions was called — its results need
        # a follow-up turn so the LLM can act on them.  All other tools
        # (batch_update, emit_suggestions, etc.) are fire-and-forget.
        if not called_search:
            break

    # Read final session state (mutated by tool calls)
    session = get_session(session_id)

    return PlannerOutput(
        implementation_plan=dict(session.implementation_plan),
        inferred_decisions=list(session.inferred_nodes),
        retrieval_query=dict(session.retrieval_query),
        usage={"input_tokens": total_input_tokens, "output_tokens": total_output_tokens},
    )
