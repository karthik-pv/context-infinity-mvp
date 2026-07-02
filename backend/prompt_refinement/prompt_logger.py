"""
Pipeline logger — writes per-prompt, per-stage logs to backend/logs/.

For each user message (prompt), creates a folder:
  backend/logs/{session_id}-prompt-{N}/

Inside that folder, writes per stage:
  stage-1.json        — Planner (response, token usage, notes)
  stage-1-prompt.txt  — Planner prompt (readable text file)
  stage-2.json        — Decision Extractor (response, token usage, notes)
  stage-2-prompt.txt  — Decision Extractor prompt
  stage-3.json        — Retrieval (extraction metadata + retrieved decisions, no LLM)
  stage-4.json        — Violation Checker (response, token usage, violations, notes)
  stage-4-prompt.txt  — Violation Checker prompt

If a stage returns empty results or encounters an error, a "note" field is added
to the JSON explaining what happened.
"""
import os
import json
from datetime import datetime

_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")


def _prompt_dir(session_id: str, prompt_number: int) -> str:
    """Return the directory path for a specific prompt's logs."""
    return os.path.join(_LOG_DIR, f"{session_id}-prompt-{prompt_number}")


def get_prompt_number(session_id: str) -> int:
    """
    Determine the current prompt number by counting user messages in chat_history.
    Called AFTER the user message is appended to chat_history, so the count
    equals the current prompt number.
    """
    from prompt_refinement.session_store import get_session
    session = get_session(session_id)
    if session is None:
        return 1
    user_msgs = [m for m in session.chat_history if m.role == "user"]
    return len(user_msgs)


def log_stage(
    session_id: str,
    prompt_number: int,
    stage: int,
    *,
    prompt: str = "",
    response: str = "",
    usage: dict | None = None,
    extra: dict | None = None,
    note: str = "",
) -> None:
    """
    Write a single stage log file.

    Args:
        session_id: Session ID.
        prompt_number: 1-indexed prompt number for this session.
        stage: Stage number (1-4).
        prompt: The full prompt text sent to the LLM (written as .txt file).
        response: The raw LLM response text (empty for non-LLM stages).
        usage: Token usage dict {"input_tokens": N, "output_tokens": N}.
        extra: Additional structured data to include (e.g. retrieval metadata).
        note: Explanation if the stage returned empty results or encountered an error.
    """
    dir_path = _prompt_dir(session_id, prompt_number)
    os.makedirs(dir_path, exist_ok=True)

    # Write prompt as a readable text file
    if prompt:
        prompt_path = os.path.join(dir_path, f"stage-{stage}-prompt.txt")
        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write(prompt)

    # Write the JSON metadata (no prompt string — it's in the .txt file)
    entry = {
        "session_id": session_id,
        "prompt_number": prompt_number,
        "stage": stage,
        "timestamp": datetime.now().isoformat(),
    }

    if response:
        # Try to parse response as JSON for readability; fall back to raw string
        try:
            entry["response"] = json.loads(response)
        except (json.JSONDecodeError, TypeError):
            entry["response"] = response
    if usage:
        entry["usage"] = usage
    if note:
        entry["note"] = note
    if extra:
        entry.update(extra)

    filepath = os.path.join(dir_path, f"stage-{stage}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(entry, f, indent=2, default=str)
