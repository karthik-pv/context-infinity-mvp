"""
Pydantic models for the prompt-refinement planning engine.
Covers session state only — LLM output schema models removed after migration to tool-calling.
"""
from __future__ import annotations
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class ChatEntry(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class PlanningSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    chat_history: list[ChatEntry] = []
    implementation_plan: dict[str, dict] = Field(default_factory=dict)
    inferred_nodes: list[dict] = []
    folder_structure: list[str] = []            # global, read-only during session
    session_folder_structure: list[str] = []    # session-scoped working copy
    deleted_paths: list[str] = []               # paths explicitly removed
    violations: list[dict] = []                 # decision violations from last turn
    clarifications: list[dict] = []             # pending clarification questions for UI
    suggestions: list[dict] = []                # architecture suggestions for UI
    blockers: list[dict] = []                   # critical blockers for UI
    retrieval_query: dict = Field(default_factory=dict)  # {files, tags} for historical lookup
    status: Literal["planning", "finalized"] = "planning"
