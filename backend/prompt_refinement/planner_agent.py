"""
Agentic planning loop.

Architecture: LLM ↔ tool calls (mutate session state) → final text response.

Instead of asking the LLM to return a giant JSON payload that gets parsed and applied,
the LLM now calls tools directly to mutate session state (plan sections, decision nodes).
The loop continues until the LLM returns a response with no tool calls — that response is
the final user-facing message.

This eliminates the structured-output parsing failures caused by schema mismatches.
"""
import json
from .session_store import get_session, save_session
from .models import ChatEntry
from .retrieval import retrieve_relevant_context
from .prompt_builder import (
    AGENT_SYSTEM_PROMPT,
    format_chat_history,
    format_plan,
    format_nodes,
    format_historical,
)
from .tool_executor import TOOL_SCHEMAS, execute_tool
from ai_adapters.factory import get_adapter

# Safety cap: stop the tool-calling loop after this many iterations
_MAX_TOOL_ITERATIONS = 10


async def run_planner_agent(session_id: str, user_message: str) -> str:
    """
    Run a full planning turn for the given session.

    Steps:
    1. Persist the user message to chat history immediately.
    2. Retrieve relevant historical decisions for context.
    3. Build the system prompt with full current session state.
    4. Run the agent loop: LLM → tool calls → execute → feed results back → repeat.
    5. When no tool calls remain, persist the final assistant response.
    6. Return the final user-facing text.
    """
    session = get_session(session_id)
    if session is None:
        raise ValueError(f"Session '{session_id}' not found")
    if session.status == "finalized":
        raise ValueError("Session is already finalized")

    # Step 1: persist user message before calling LLM (so tools see it in chat history)
    session.chat_history.append(ChatEntry(role="user", content=user_message))
    save_session(session)

    # Step 2: retrieve relevant historical context
    historical = retrieve_relevant_context(user_message)

    # Step 3: build system prompt with current state snapshot
    system_prompt = AGENT_SYSTEM_PROMPT.format(
        session_id=session_id,
        chat_history=format_chat_history(session.chat_history),
        implementation_plan=format_plan(session.implementation_plan),
        inferred_nodes=format_nodes(session.inferred_nodes),
        historical_decisions=format_historical(historical),
    )

    # Step 4: agent loop
    # Each adapter.chat_with_tools call is a single LLM turn.
    # Messages accumulate within this agent turn only; they are NOT persisted.
    # Session state (plan, nodes) is mutated by tool calls and persisted by each tool.
    adapter = get_adapter()
    messages = [{"role": "user", "content": user_message}]

    final_text = None
    for _ in range(_MAX_TOOL_ITERATIONS):
        final_text, tool_calls = await adapter.chat_with_tools(
            system=system_prompt,
            messages=messages,
            tools=TOOL_SCHEMAS,
        )

        if not tool_calls:
            # No tool calls → this is the final response; exit loop
            break

        # Append the assistant's tool-call turn to the message history
        # (OpenAI wire format — adapters convert to their native format internally)
        messages.append({
            "role": "assistant",
            "content": final_text or "",
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

        # Execute each tool and append results to the message history
        for tc in tool_calls:
            result = execute_tool(tc["name"], tc["input"])
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "name": tc["name"],
                "content": json.dumps(result),
            })

    if not final_text:
        final_text = "Done. The plan and decisions have been updated for this turn."

    # Step 5: persist the assistant's final response
    # Re-fetch session because tools may have mutated it since step 1
    session = get_session(session_id)
    session.chat_history.append(ChatEntry(role="assistant", content=final_text))
    save_session(session)

    return final_text
