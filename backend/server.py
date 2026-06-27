from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from db_layer.postgres_access import get_decisions, get_artifact_paths, get_decision_by_id, update_decision_by_id


class DecisionUpdate(BaseModel):
    title: str
    decision: str
    rationale: Optional[str] = None
    tradeoffs: list[str] = []
    confidence: float = Field(ge=0.0, le=1.0)
    tags: list[str] = []

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def hello():
    return {"message": "Hello World"}


@app.get("/v1/decisions")
def decisions():
    return {
        "nodes": get_decisions(),
        "paths": get_artifact_paths(),
    }


@app.get("/v1/decisions/{decision_id}")
def decision_detail(decision_id: str):
    node = get_decision_by_id(decision_id)
    if node is None:
        raise HTTPException(status_code=404, detail="Not found")
    return node


@app.put("/v1/decisions/{decision_id}")
def decision_update(decision_id: str, body: DecisionUpdate):
    node = update_decision_by_id(decision_id, body.model_dump())
    if node is None:
        raise HTTPException(status_code=404, detail="Not found")
    return node
