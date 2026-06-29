"""
Prompt logger: writes each LLM prompt + retrieved decisions to backend/logs/.
One file per prompt, filename includes timestamp and session_id.
"""
import os
import json
from datetime import datetime

_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")


def log_prompt(session_id: str, system_prompt: str, historical_decisions: list) -> None:
    os.makedirs(_LOG_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{session_id}.txt"
    filepath = os.path.join(_LOG_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("=== SYSTEM PROMPT ===\n\n")
        f.write(system_prompt)
        f.write("\n\n=== RETRIEVED HISTORICAL DECISIONS ===\n\n")
        if historical_decisions:
            f.write(json.dumps(historical_decisions, indent=2, default=str))
        else:
            f.write("(none found)\n")
