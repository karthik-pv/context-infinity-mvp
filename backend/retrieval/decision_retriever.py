"""
Decision retrieval layer — tiered scoring retrieval of historical decisions.

Given the planner's affected_files and relevant_tags, queries the DB for historical
decision nodes and ranks them by a tiered scoring system:

  Tier 1 — exact file match        (score 10)
  Tier 2 — parent folder match     (score 5)
  Tier 3 — tag match               (score 2)

Only the top-K decisions are returned, keeping token usage sublinear with project
complexity.  The planner agent never sees these — they go directly to the violation
checker agent.
"""
from db_layer.postgres_access import get_decisions

TOP_K = 10

# Scoring weights
_SCORE_EXACT_FILE = 10
_SCORE_FOLDER_MATCH = 5
_SCORE_TAG_MATCH = 2


def _parent_folders(file_path: str) -> list[str]:
    """Return parent folder paths for a file, e.g. 'backend/auth/jwt.py' → ['backend/auth/', 'backend/']."""
    parts = file_path.strip("/").split("/")
    folders = []
    for i in range(len(parts) - 1, 0, -1):
        folders.append("/".join(parts[:i]) + "/")
    return folders


def retrieve(affected_files: list[str], relevant_tags: list[str]) -> list[dict]:
    """
    Retrieve historical decisions relevant to the affected files and tags.

    Returns a list of RetrievedDecision dicts sorted by score (descending),
    limited to TOP_K results.
    """
    all_decisions = get_decisions()
    if not all_decisions:
        return []

    tags_lower = {t.lower() for t in relevant_tags}
    scored: list[tuple[int, dict]] = []

    for node in all_decisions:
        node_file = (node.get("location") or "").strip()
        node_tags = {t.lower() for t in node.get("tags", [])}
        score = 0

        # Tier 1 — exact file match
        if node_file and node_file in affected_files:
            score += _SCORE_EXACT_FILE

        # Tier 2 — parent folder match
        if node_file and score < _SCORE_EXACT_FILE:
            for af in affected_files:
                if node_file in _parent_folders(af):
                    score += _SCORE_FOLDER_MATCH
                    break

        # Tier 3 — tag match
        if tags_lower and node_tags:
            overlap = tags_lower & node_tags
            score += len(overlap) * _SCORE_TAG_MATCH

        if score > 0:
            scored.append((score, node))

    scored.sort(key=lambda x: x[0], reverse=True)

    return [
        {
            "id": node.get("id", ""),
            "title": node.get("title", ""),
            "decision": node.get("decision", ""),
            "rationale": node.get("rationale", ""),
            "target_file": node.get("location", ""),
            "tags": node.get("tags", []),
            "score": score,
        }
        for score, node in scored[:TOP_K]
    ]
