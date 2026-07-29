# Context Infinity

Architectural memory for AI-assisted development — acts as a guardrail that prevents LLM-generated code from violating previously established architectural decisions.

## The Problem

When developers use LLMs to plan and implement features across multiple sessions, the LLM has no memory of past architectural decisions. This leads to:

- **Decision drift** — new code contradicts earlier choices (e.g., "use JWT" in session 1, "use session auth" in session 3)
- **Context loss** — each session starts blank, repeating or undoing prior work
- **No enforcement** — nothing checks if new plans respect the existing architecture

## The Solution — 4-Stage Multi-Pass Pipeline

Instead of one giant LLM prompt, each user message flows through four narrow stages. Each stage does one job, keeping prompts small and token growth proportional to relevant context.

```
User Message
    │
    ▼
Stage 1: Planner           → plan/folder mutations + clarifications + suggestions
Stage 2: Decision Extractor → extract architectural decisions from plan changes
Stage 3: Retrieval          → fetch relevant historical decisions from DB (no LLM)
Stage 4: Violation Checker  → compare new decisions vs historical, flag conflicts
    │
    ▼
Updated session state → UI renders plan, decisions, violations, clarifications
```

| Stage | LLM? | Input | Output |
|-------|------|-------|--------|
| 1 — Planner | Yes | Plan + folders + user message | Plan mutations, folder mutations, clarifications, suggestions |
| 2 — Decision Extractor | Yes | User message + plan changes + existing decisions | Decision mutations (add/update/delete) |
| 3 — Retrieval | No | Decision target files + tags + session chat history | Relevant historical decisions (pluggable strategy) |
| 4 — Violation Checker | Yes | New decisions + historical decisions | Violations with type, severity, suggested resolution |

**Key design principle:** The planner never sees historical decisions. Violation checking is done by a separate LLM that compares new vs. old — keeping each prompt focused and impartial.

### Pluggable Retrieval — `HistoricalRetriever` Interface

Stage 3 is defined against an interface, not a concrete algorithm, so the retrieval strategy can be swapped without touching the pipeline:

```
backend/retrieval/
  base.py                      → HistoricalRetriever (ABC) — the interface
  tiered_scoring_retriever.py  → TieredScoringRetriever    — default strategy
  chat_keyword_retriever.py    → ChatKeywordRetriever      — alternate strategy
  factory.py                   → get_retriever() — reads config.json, returns an implementation
```

Every implementation satisfies one method:

```python
def retrieve(
    self,
    affected_files: list[str],   # target_files from the session's updated decisions
    relevant_tags: list[str],    # tags from the session's updated decisions
    chat_history: list[dict],    # the session's prompt history so far
) -> list[dict]:                 # historical decisions, most relevant first
```

Implementations are free to use any subset of the inputs:

- **`TieredScoringRetriever`** (default) — the original non-LLM scorer. Ranks decisions by exact file match (10) → parent folder match (5) → tag overlap (2) → keyword fallback (1). Ignores `chat_history`.
- **`ChatKeywordRetriever`** — scores decisions by keyword overlap with the last 6 chat turns instead, ignoring `affected_files`/`relevant_tags` entirely. Included as a working proof that a second strategy can key off a completely different input and drop in cleanly.

The active strategy is selected via `retrieval_strategy` in `config.json` (`"tiered_scoring"` or `"chat_keyword"`), read by `retrieval/factory.py::get_retriever()` — the same swap-via-config pattern used for LLM adapters. `orchestrator/planning_pipeline.py` only ever calls `get_retriever().retrieve(...)`; it has no knowledge of which strategy is behind the interface. Adding a new strategy (e.g. embedding-based retrieval) means writing one class that implements `HistoricalRetriever` and adding one branch to the factory — no pipeline changes required.

## Screenshots

### Context Page — All Decisions

Hierarchical folder tree with decision cards placed at their artifact locations. Click a folder or file to filter the view.

![All Decisions](assets/decisions_all.png)

### Violation Detection

When a new decision conflicts with a historical one, the violation modal shows the conflict with severity, explanation, and suggested resolution. Edit the violated decision inline and reprocess to re-check.

![Violated Decision](assets/violated_decision.png)

### Context Drift Detection

Sync the planned folder structure against the actual filesystem. Anomalies (files on disk but not planned, or planned but missing) are surfaced with the ability to add missing paths into the planned structure.

![Context Drift](assets/folder_context_drift.png)

## Tech Stack

- **Backend:** FastAPI, PostgreSQL, raw `psycopg` (no ORM)
- **LLM Adapters:** Anthropic, OpenAI, Fireworks (swappable via config)
- **Retrieval Strategy:** `HistoricalRetriever` interface — tiered scoring or chat-keyword, swappable via config
- **Frontend:** React, Vite, dnd-kit (drag-and-drop for decision placement)
- **Pipeline:** Hand-rolled async pipeline (no LangChain — 4 function calls in sequence)
