const API_BASE = '/v1';
const PLANNER_BASE = '/prompt-refinement';

// ── Existing decision API ─────────────────────────────────────────────────────

export async function fetchDecisions() {
  const res = await fetch(`${API_BASE}/decisions`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function fetchDecisionById(id) {
  const res = await fetch(`${API_BASE}/decisions/${id}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function updateDecision(id, data) {
  const res = await fetch(`${API_BASE}/decisions/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function sendChatMessage(message) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

// ── Prompt-refinement planning API ───────────────────────────────────────────

export async function fetchPlanningSessions() {
  const res = await fetch(`${PLANNER_BASE}/sessions`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json(); // { sessions: [{session_id, title, message_count, status}] }
}

export async function fetchPlanningSession(sessionId) {
  const res = await fetch(`${PLANNER_BASE}/session/${sessionId}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function createPlanningSession() {
  const res = await fetch(`${PLANNER_BASE}/session`, { method: 'POST' });
  if (!res.ok) throw new Error(`Failed to create session: ${res.status}`);
  return res.json();
}

export async function deletePlanningSession(sessionId) {
  const res = await fetch(`${PLANNER_BASE}/session/${sessionId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function sendPlanningMessage(sessionId, message) {
  const res = await fetch(`${PLANNER_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message }),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(detail.detail || `API error: ${res.status}`);
  }
  return res.json();
}

export async function reprocessSession(sessionId) {
  const res = await fetch(`${PLANNER_BASE}/reprocess`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId }),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(detail.detail || `API error: ${res.status}`);
  }
  return res.json();
}

export async function updateSessionNode(sessionId, data) {
  const res = await fetch(`${PLANNER_BASE}/node`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, ...data }),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(detail.detail || `API error: ${res.status}`);
  }
  return res.json();
}

export async function finalizePlanningSession(sessionId) {
  const res = await fetch(`${PLANNER_BASE}/finalize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId }),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(detail.detail || `API error: ${res.status}`);
  }
  return res.json();
}

// ── Project API ──────────────────────────────────────────────────────────────

const PROJECT_BASE = '/project';

export async function fetchProjectInfo() {
  const res = await fetch(`${PROJECT_BASE}/info`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function updateProjectInfo(data) {
  const res = await fetch(`${PROJECT_BASE}/info`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function syncFolderStructure() {
  const res = await fetch(`${PROJECT_BASE}/sync`, { method: 'POST' });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(detail.detail || `API error: ${res.status}`);
  }
  return res.json();
}

export async function addPathsToPlanned(paths) {
  const res = await fetch(`${PROJECT_BASE}/add-paths`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ paths }),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function updateBriefEntry(index, text) {
  const res = await fetch(`${PROJECT_BASE}/brief/${index}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function addBriefEntry(text) {
  const res = await fetch(`${PROJECT_BASE}/brief`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function deleteBriefEntry(index) {
  const res = await fetch(`${PROJECT_BASE}/brief/${index}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}
