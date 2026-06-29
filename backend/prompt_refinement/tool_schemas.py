"""
Anthropic-format tool schemas exposed to the LLM during planning sessions.
Imported by tool_executor.py and planner_agent.py.
"""

TOOL_SCHEMAS: list[dict] = [
    {
        "name": "add_plan_section",
        "description": (
            "Create or overwrite an atomic action point in the implementation plan. "
            "Each action point must be associated with a specific file or folder path. "
            "Use for new action points or when replacing an entire action point's content."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "Current planning session ID"},
                "section_id": {
                    "type": "string",
                    "description": "Stable snake_case identifier, e.g. 'create_flask_server' or 'jwt_auth_route'",
                },
                "content": {
                    "type": "string",
                    "description": "Full prose content describing the atomic action to perform",
                },
                "target_file": {
                    "type": "string",
                    "description": "File or folder path this action point belongs to, e.g. 'backend/server.py' or 'backend/auth/'",
                },
            },
            "required": ["session_id", "section_id", "content", "target_file"],
        },
    },
    {
        "name": "update_plan_section",
        "description": (
            "Update the content of an existing plan action point. "
            "Returns an error if the section does not exist — use add_plan_section to create it."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string"},
                "section_id": {"type": "string"},
                "content": {"type": "string"},
                "target_file": {
                    "type": "string",
                    "description": "File or folder path this action point belongs to",
                },
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
            "Always specify target_file so the decision is traceable to the exact file where it is implemented. "
            "Use '.' only for project-wide architectural decisions that have no single file."
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
                "target_file": {
                    "type": "string",
                    "description": "File path where this decision is implemented, e.g. 'backend/server.py'. Use '.' for project-wide decisions only.",
                },
            },
            "required": ["session_id", "title", "decision", "target_file"],
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
                "target_file": {
                    "type": "string",
                    "description": "File path where this decision is implemented",
                },
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
