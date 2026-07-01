from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from db_layer.postgres_access import get_decisions, get_artifact_paths, get_decision_by_id, update_decision_by_id
from db_layer.project_db import add_token_usage
from ai_adapters.factory import get_adapter

router = APIRouter()


class DecisionUpdate(BaseModel):
    title: str
    decision: str
    rationale: Optional[str] = None
    tradeoffs: list[str] = []
    confidence: float = Field(ge=0.0, le=1.0)
    tags: list[str] = []


class ChatMessage(BaseModel):
    message: str


@router.get("/")
def hello():
    return {"message": "Hello World"}


@router.get("/v1/decisions")
def decisions():
    return {
        "nodes": get_decisions(),
        "paths": get_artifact_paths(),
    }


@router.get("/v1/decisions/{decision_id}")
def decision_detail(decision_id: str):
    node = get_decision_by_id(decision_id)
    if node is None:
        raise HTTPException(status_code=404, detail="Not found")
    return node


@router.put("/v1/decisions/{decision_id}")
def decision_update(decision_id: str, body: DecisionUpdate):
    node = update_decision_by_id(decision_id, body.model_dump())
    if node is None:
        raise HTTPException(status_code=404, detail="Not found")
    return node


@router.post("/v1/chat")
async def chat(body: ChatMessage):
    adapter = get_adapter()
    reply, usage = await adapter.chat(body.message)
    add_token_usage(usage.get("input_tokens", 0), usage.get("output_tokens", 0))
    return {"reply": reply}
