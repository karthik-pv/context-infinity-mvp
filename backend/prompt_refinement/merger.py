"""
Decision node merger for the planning session.
Handles deduplication and incremental updates when new nodes are added via tools.
"""


def merge_decision_nodes(existing: list[dict], new_nodes: list[dict]) -> list[dict]:
    """
    Merge new_nodes into existing, deduplicating by title.
    For duplicates:
      - rationale: overwrite with newer value
      - confidence: keep the higher value
      - tags / tradeoffs: union (order-preserving, no duplicates)
      - artifact_ref: overwrite if new node provides one
    """
    by_title: dict[str, dict] = {n["title"]: dict(n) for n in existing}

    for node in new_nodes:
        title = node.get("title", "").strip()
        if not title:
            continue

        if title in by_title:
            ex = by_title[title]

            if node.get("rationale"):
                ex["rationale"] = node["rationale"]

            ex["confidence"] = max(
                float(ex.get("confidence", 0.0)),
                float(node.get("confidence", 0.0)),
            )

            merged_tags = list(ex.get("tags", []))
            seen_tags = set(merged_tags)
            for t in node.get("tags", []):
                if t not in seen_tags:
                    merged_tags.append(t)
                    seen_tags.add(t)
            ex["tags"] = merged_tags

            merged_tradeoffs = list(ex.get("tradeoffs", []))
            seen_tradeoffs = set(merged_tradeoffs)
            for t in node.get("tradeoffs", []):
                if t not in seen_tradeoffs:
                    merged_tradeoffs.append(t)
                    seen_tradeoffs.add(t)
            ex["tradeoffs"] = merged_tradeoffs

            if node.get("artifact_ref"):
                ex["artifact_ref"] = node["artifact_ref"]
                ex["artifact_type"] = node.get("artifact_type", "module")
        else:
            by_title[title] = dict(node)

    return list(by_title.values())
