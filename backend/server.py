from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.decisions import router as decisions_router
from routes.planning import router as planning_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(decisions_router)
app.include_router(planning_router)
