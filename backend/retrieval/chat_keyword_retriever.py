"""
Chat-history keyword retrieval — non-LLM.

Alternate Stage 3 strategy that mines the session's recent prompt history for
keywords and scores historical decisions by overlap with their title,
decision, rationale, and tags. Unlike TieredScoringRetriever (which scores
purely on affected_files/relevant_tags and ignores chat_history), this
strategy keys entirely off chat_history — proving HistoricalRetriever
implementations are free to draw on either input independently.
"""
from db_layer.postgres_access import get_decisions

from .base import HistoricalRetriever

TOP_K = 10
RECENT_TURNS = 6
_STRIP_CHARS = ".,!?;:()[]{}\"'"


class ChatKeywordRetriever(HistoricalRetriever):
    """Non-LLM retrieval strategy: scores historical decisions by keyword overlap with recent chat history."""

    def retrieve(
        self,
        affected_files: list[str],
        relevant_tags: list[str],
        chat_history: list[dict],
    ) -> list[dict]:
        all_decisions = get_decisions()
        if not all_decisions:
            return []

        recent = chat_history[-RECENT_TURNS:] if chat_history else []
        keywords = set()
        for entry in recent:
            content = entry.get("content", "") or ""
            for word in content.lower().split():
                word = word.strip(_STRIP_CHARS)
                if len(word) > 3:
                    keywords.add(word)

        if not keywords:
            return []

        scored: list[tuple[int, dict]] = []
        for node in all_decisions:
            title_words = set(node.get("title", "").lower().split())
            decision_words = set(node.get("decision", "").lower().split())
            rationale_words = set(node.get("rationale", "").lower().split())
            tag_words = {t.lower() for t in node.get("tags", [])}

            overlap = keywords & (title_words | decision_words | rationale_words | tag_words)
            if overlap:
                scored.append((len(overlap), node))

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
