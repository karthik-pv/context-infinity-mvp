"""
Anthropic-format tool schemas for the planning agent.

Bare-minimum schemas to conserve tokens.  No nested property descriptions —
the LLM infers field meaning from names + system prompt rules.
"""

_BATCH_UPDATE = {
    "name": "batch_update",
    "description": "Apply all plan, decision, and folder changes in one call.",
    "input_schema": {
        "type": "object",
        "properties": {
            "session_id": {"type": "string"},
            "plan_sections": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "section_id": {"type": "string"},
                        "content": {"type": "string"},
                        "target_file": {"type": "string"},
                    },
                    "required": ["section_id", "content", "target_file"],
                },
            },
            "delete_plan_sections": {"type": "array", "items": {"type": "string"}},
            "decision_nodes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "decision": {"type": "string"},
                        "target_file": {"type": "string"},
                        "rationale": {"type": "string"},
                        "tradeoffs": {"type": "array", "items": {"type": "string"}},
                        "confidence": {"type": "number"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["title", "decision", "target_file"],
                },
            },
            "delete_decision_nodes": {"type": "array", "items": {"type": "string"}},
            "folder_changes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["add", "remove"]},
                        "path": {"type": "string"},
                    },
                    "required": ["action", "path"],
                },
            },
        },
        "required": ["session_id"],
    },
}

_SEARCH_DECISIONS = {
    "name": "search_decisions",
    "description": "Get historical decisions from DB by file or tag.",
    "input_schema": {
        "type": "object",
        "properties": {
            "session_id": {"type": "string"},
            "file": {"type": "string"},
            "tag": {"type": "string"},
        },
        "required": ["session_id"],
    },
}

_REQUEST_CLARIFICATION = {
    "name": "request_clarification",
    "description": "Ask user when intent is ambiguous.",
    "input_schema": {
        "type": "object",
        "properties": {
            "session_id": {"type": "string"},
            "questions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "question": {"type": "string"},
                        "type": {"type": "string", "enum": ["text", "single_select", "multi_select"]},
                        "options": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["id", "question", "type"],
                },
            },
        },
        "required": ["session_id", "questions"],
    },
}

_EMIT_SUGGESTIONS = {
    "name": "emit_suggestions",
    "description": "Propose architecture improvements.",
    "input_schema": {
        "type": "object",
        "properties": {
            "session_id": {"type": "string"},
            "suggestions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                    },
                    "required": ["id", "title", "description", "priority"],
                },
            },
        },
        "required": ["session_id", "suggestions"],
    },
}

_EMIT_BLOCKERS = {
    "name": "emit_blockers",
    "description": "Flag critical conflicts or blockers.",
    "input_schema": {
        "type": "object",
        "properties": {
            "session_id": {"type": "string"},
            "blockers": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                        "title": {"type": "string"},
                        "reason": {"type": "string"},
                    },
                    "required": ["severity", "title", "reason"],
                },
            },
        },
        "required": ["session_id", "blockers"],
    },
}

TOOL_SCHEMAS: list[dict] = [
    _BATCH_UPDATE,
    _SEARCH_DECISIONS,
    _REQUEST_CLARIFICATION,
    _EMIT_SUGGESTIONS,
    _EMIT_BLOCKERS,
]

TOOL_SCHEMAS_MINIMAL: list[dict] = TOOL_SCHEMAS
