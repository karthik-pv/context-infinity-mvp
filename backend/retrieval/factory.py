import json
import os
from .base import HistoricalRetriever

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.json")


def get_retriever() -> HistoricalRetriever:
    with open(_CONFIG_PATH) as f:
        config = json.load(f)

    strategy = config.get("retrieval_strategy", "tiered_scoring")

    if strategy == "tiered_scoring":
        from .tiered_scoring_retriever import TieredScoringRetriever
        return TieredScoringRetriever()
    elif strategy == "chat_keyword":
        from .chat_keyword_retriever import ChatKeywordRetriever
        return ChatKeywordRetriever()
    else:
        raise ValueError(f"Unknown retrieval_strategy: {strategy!r}")
