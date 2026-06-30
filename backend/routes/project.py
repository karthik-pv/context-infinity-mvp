import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db_layer.project_db import get_project_info, update_project_info, update_actual_folder_structure

router = APIRouter(prefix="/project")

_IGNORE_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build",
    ".next", ".nuxt", ".cache", ".swarm", ".opencode", "env",
}
_IGNORE_EXTS = {".pyc", ".pyo", ".log"}
_MAX_FILES = 5000


class UpdateProjectRequest(BaseModel):
    project_path: str | None = None
    project_brief: str | list[str] | None = None


@router.get("/info")
def get_info():
    return get_project_info()


@router.put("/info")
def update_info(body: UpdateProjectRequest):
    return update_project_info(body.project_path, body.project_brief)


@router.post("/sync")
def sync_folder_structure():
    """Scan the filesystem at project_path and store the actual folder structure."""
    info = get_project_info()
    project_path = info.get("project_path", "")
    if not project_path or not os.path.isdir(project_path):
        raise HTTPException(status_code=400, detail="Project path is not set or does not exist")

    paths = []
    for root, dirs, files in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in _IGNORE_DIRS]
        rel_root = os.path.relpath(root, project_path).replace("\\", "/")
        if rel_root == ".":
            rel_root = ""
        for d in dirs:
            if len(paths) >= _MAX_FILES:
                break
            paths.append(f"{rel_root}/{d}/" if rel_root else f"{d}/")
        for f in files:
            if os.path.splitext(f)[1] in _IGNORE_EXTS:
                continue
            if len(paths) >= _MAX_FILES:
                break
            paths.append(f"{rel_root}/{f}" if rel_root else f)

    paths.sort()
    update_actual_folder_structure(paths)
    return {"actual_folder_structure": paths}
