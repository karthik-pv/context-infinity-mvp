const API_BASE = '/v1';

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
