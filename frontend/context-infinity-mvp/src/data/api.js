const API_BASE = '/v1';

export async function fetchDecisions() {
  const res = await fetch(`${API_BASE}/decisions`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}
