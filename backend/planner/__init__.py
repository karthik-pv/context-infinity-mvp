"""
Stateful planner package.

Modules:
  session_manager   — create / load / save planner sessions (wraps session_store)
  context_retriever — extract only relevant state slices for the LLM
  prompts           — compact nudge prompt templates
  delta_applier     — apply JSON deltas returned by the LLM to session state
  drift_detector    — compare planned state vs actual codebase
"""
