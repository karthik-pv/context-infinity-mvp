"""
Retrieval service: keyword-overlap search over existing DB decision nodes.
No embeddings for MVP — uses title words, tags, and artifact path tokens.
"""
from db_layer.postgres_access import get_decisions

_MAX_RESULTS = 5


def retrieve_relevant_context(user_message: str) -> list[dict]:
    """
    Return up to _MAX_RESULTS existing decision nodes most relevant to user_message.
    Scoring: title word overlap (×2), tag substring match (×3), artifact path tokens (×1).
    """
    all_decisions = get_decisions()
    message_lower = user_message.lower()
    message_words = set(message_lower.split())

    scored: list[tuple[int, dict]] = []
    for node in all_decisions:
        score = 0

        title_words = set(node.get("title", "").lower().split())
        score += len(message_words & title_words) * 2

        for tag in node.get("tags", []):
            if tag.lower() in message_lower:
                score += 3

        location = node.get("location", "") or ""
        if location:
            path_words = set(location.replace("/", " ").replace(".", " ").lower().split())
            score += len(message_words & path_words)

        if score > 0:
            scored.append((score, node))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [node for _, node in scored[:_MAX_RESULTS]]
