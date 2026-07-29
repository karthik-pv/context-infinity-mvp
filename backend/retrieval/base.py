"""
Interface for historical decision retrieval strategies.

An implementation receives everything Stage 3 has available — the affected
files and tags derived from Stage 2, plus the session's prompt history — and
returns the historical decisions it judges relevant. Swapping strategies
(e.g. tiered scoring vs. an embedding/LLM-based retriever) only requires a
new class satisfying this interface; callers depend on `HistoricalRetriever`,
not on any specific implementation.
"""
from abc import ABC, abstractmethod


class HistoricalRetriever(ABC):
    @abstractmethod
    def retrieve(
        self,
        affected_files: list[str],
        relevant_tags: list[str],
        chat_history: list[dict],
    ) -> list[dict]:
        """
        Retrieve historical decisions relevant to the current session.

        Args:
            affected_files: target_files from the updated session decisions.
            relevant_tags: tags from the updated session decisions.
            chat_history: the session's prompt history so far, each entry
                          {"role": "user"|"assistant", "content": str}.

        Returns a list of decision dicts, most relevant first.
        """
        ...
