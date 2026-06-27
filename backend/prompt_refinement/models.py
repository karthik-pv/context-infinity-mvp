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
    implementation_plan: dict[str, str] = Field(default_factory=dict)
    inferred_nodes: list[dict] = []
    status: Literal["planning", "finalized"] = "planning"
