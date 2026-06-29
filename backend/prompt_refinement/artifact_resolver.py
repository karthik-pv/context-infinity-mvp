"""
Artifact resolver: maps a decision node to a filesystem anchor.
The LLM specifies target_file explicitly; this module validates and falls back to tag heuristics.

Priority (first match wins):
  1. Explicit target_file on the node  →  that file/folder path
  2. architecture / global / system    →  project root
  3. auth / jwt / session / oauth      →  auth folder
  4. db / redis / database / cache     →  db folder
  5. fallback                          →  project root
"""
from typing import TypedDict

ArtifactInfo = TypedDict("ArtifactInfo", {
    "artifact_type": str,
    "artifact_ref": str,
    "is_display_anchor": bool,
})

# (tag_keywords, artifact_type, artifact_ref)
_RULES: list[tuple[set[str], str, str]] = [
    ({"architecture", "global", "system", "cross-cutting"}, "project", "."),
    ({"auth", "jwt", "session", "oauth", "authentication", "authorization"}, "folder", "auth"),
    ({"db", "redis", "database", "cache", "postgres", "sql", "storage"}, "folder", "db"),
    ({"api", "rest", "endpoint", "route", "http"}, "folder", "api"),
    ({"frontend", "ui", "react", "component", "view"}, "folder", "frontend"),
    ({"infra", "infrastructure", "ci", "deploy", "docker", "k8s"}, "folder", "infra"),
]

_FALLBACK: ArtifactInfo = {
    "artifact_type": "project",
    "artifact_ref": ".",
    "is_display_anchor": True,
}


def resolve_artifact(node: dict, implementation_plan: dict | None = None) -> ArtifactInfo:
    """
    Return artifact placement metadata for a decision node.

    Args:
        node: dict with 'tags' key and optional 'target_file'.
        implementation_plan: not used yet; reserved for future section-based resolution.

    Returns:
        ArtifactInfo with artifact_type, artifact_ref, is_display_anchor.
    """
    target_file = node.get("target_file", "").strip()
    if target_file and target_file != ".":
        artifact_type = "file" if "." in target_file.split("/")[-1] else "folder"
        return {
            "artifact_type": artifact_type,
            "artifact_ref": target_file,
            "is_display_anchor": True,
        }

    node_tags = {t.lower() for t in node.get("tags", [])}

    for rule_keywords, artifact_type, artifact_ref in _RULES:
        if node_tags & rule_keywords:
            return {
                "artifact_type": artifact_type,
                "artifact_ref": artifact_ref,
                "is_display_anchor": True,
            }

    return dict(_FALLBACK)
