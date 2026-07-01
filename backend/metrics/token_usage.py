"""
Token usage metrics — logs per-request token consumption to backend/logs/.

Tracks planner, decision extractor, retrieval count, and violation checker
input/output tokens so we can measure the multi-pass pipeline's efficiency.
"""
import os
import json
from datetime import datetime

_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")


def log_token_usage(session_id: str, metrics: dict) -> None:
    """
    Log token usage metrics for a single planning turn.

    Expected metrics keys:
      - planner_input_tokens
      - planner_output_tokens
      - extractor_input_tokens
      - extractor_output_tokens
      - retrieval_count
      - violation_input_tokens
      - violation_output_tokens
    """
    os.makedirs(_LOG_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"tokens_{timestamp}_{session_id}.json"
    filepath = os.path.join(_LOG_DIR, filename)

    total_input = (
        metrics.get("planner_input_tokens", 0)
        + metrics.get("extractor_input_tokens", 0)
        + metrics.get("violation_input_tokens", 0)
    )
    total_output = (
        metrics.get("planner_output_tokens", 0)
        + metrics.get("extractor_output_tokens", 0)
        + metrics.get("violation_output_tokens", 0)
    )

    entry = {
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "planner_input_tokens": metrics.get("planner_input_tokens", 0),
        "planner_output_tokens": metrics.get("planner_output_tokens", 0),
        "extractor_input_tokens": metrics.get("extractor_input_tokens", 0),
        "extractor_output_tokens": metrics.get("extractor_output_tokens", 0),
        "retrieval_count": metrics.get("retrieval_count", 0),
        "violation_input_tokens": metrics.get("violation_input_tokens", 0),
        "violation_output_tokens": metrics.get("violation_output_tokens", 0),
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "total_tokens": total_input + total_output,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(entry, f, indent=2)
