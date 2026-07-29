"""
Stage 3: Historical Retrieval — non-LLM tiered scoring retrieval.

Input:
  - updated decisions from Stage 2
  - current project folder structure
  - tag metadata

Retrieval strategy (tiered scoring):
  Tier 1 — exact file match        (score 10)
  Tier 2 — parent folder match     (score 5)
  Tier 3 — tag match               (score 2)
  Tier 4 — keyword match (fallback) (score 1)

No LLM involved. Pure DB retrieval. Does not use chat_history — this
strategy scores purely on the file/tag/keyword signals derived from
session decisions.
"""
from db_layer.postgres_access import get_decisions

from .base import HistoricalRetriever

TOP_K = 10

# Scoring weights
_SCORE_EXACT_FILE = 10
_SCORE_FOLDER_MATCH = 5
_SCORE_TAG_MATCH = 2
_SCORE_KEYWORD_MATCH = 1


def _parent_folders(file_path: str) -> list[str]:
    """Return parent folder paths for a file, e.g. 'backend/auth/jwt.py' → ['backend/auth/', 'backend/']."""
    parts = file_path.strip("/").split("/")
    folders = []
    for i in range(len(parts) - 1, 0, -1):
        folders.append("/".join(parts[:i]) + "/")
    return folders


class TieredScoringRetriever(HistoricalRetriever):
    """Non-LLM retrieval strategy: scores historical decisions by file/folder/tag/keyword overlap."""

    def retrieve(
        self,
        affected_files: list[str],
        relevant_tags: list[str],
        chat_history: list[dict],
    ) -> list[dict]:
        all_decisions = get_decisions()
        if not all_decisions:
            return []

        tags_lower = {t.lower() for t in relevant_tags}
        # Collect keywords from affected file paths for fallback matching
        keywords = set()
        for f in affected_files:
            for part in f.replace("/", " ").replace(".", " ").lower().split():
                if len(part) > 2:
                    keywords.add(part)

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

            # Tier 4 — keyword match (fallback)
            if score == 0 and keywords:
                title_words = set(node.get("title", "").lower().split())
                decision_words = set(node.get("decision", "").lower().split())
                if keywords & (title_words | decision_words):
                    score += _SCORE_KEYWORD_MATCH

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
