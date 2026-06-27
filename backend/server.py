from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db_layer.postgres_access import get_decisions, get_artifact_paths

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
