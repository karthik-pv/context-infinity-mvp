import { useEffect, useState } from 'react';
import { fetchDecisionById, updateDecision } from '../data/api';

function confidenceColor(c) {
  if (c >= 0.93) return 'var(--confidence-high)';
  if (c >= 0.87) return 'var(--confidence-med)';
  return 'var(--confidence-low)';
}

export default function DecisionModal({ nodeId, onClose }) {
  const [node, setNode] = useState(null);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState(null);

  const [mode, setMode] = useState('view');
  const [editData, setEditData] = useState(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setNode(null);
    setFetchError(null);
    setMode('view');
    fetchDecisionById(nodeId)
      .then(data => { setNode(data); setLoading(false); })
      .catch(err => { setFetchError(err.message); setLoading(false); });
  }, [nodeId]);

  useEffect(() => {
    function onKey(e) {
      if (e.key !== 'Escape') return;
      if (mode === 'edit') setMode('view');
      else onClose();
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose, mode]);

  function enterEdit() {
    setEditData({
      title:      node.title,
      decision:   node.decision,
      rationale:  node.rationale || '',
      tradeoffs:  (node.tradeoffs || []).join('\n'),
      confidence: node.confidence,
      tags:       (node.tags || []).join('\n'),
    });
    setSaveError(null);
    setMode('edit');
  }

  function cancelEdit() {
    setMode('view');
    setSaveError(null);
  }

  async function handleSave() {
    setSaving(true);
    setSaveError(null);
    try {
      const updated = await updateDecision(nodeId, {
        title:      editData.title.trim(),
        decision:   editData.decision.trim(),
        rationale:  editData.rationale.trim() || null,
        tradeoffs:  editData.tradeoffs.split('\n').map(s => s.trim()).filter(Boolean),
        confidence: parseFloat(editData.confidence),
        tags:       editData.tags.split('\n').map(s => s.trim()).filter(Boolean),
      });
      setNode(updated);
      setMode('view');
    } catch (err) {
      setSaveError(err.message);
    } finally {
      setSaving(false);
    }
  }

  function field(key) {
    return e => setEditData(prev => ({ ...prev, [key]: e.target.value }));
  }

  return (
    <div className="modal-overlay" onClick={mode === 'view' ? onClose : undefined}>
      <div className="modal-panel" onClick={e => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>&#x2715;</button>

        {loading && <p className="modal-status">Loading…</p>}
        {fetchError && <p className="modal-status modal-error">Error: {fetchError}</p>}

        {/* ── View mode ── */}
        {node && mode === 'view' && <>
          <div className="modal-header">
            <h2 className="modal-title">{node.title}</h2>
            <div className="modal-header-right">
              <span className="modal-confidence" style={{ color: confidenceColor(node.confidence) }}>
                {Math.round(node.confidence * 100)}%
              </span>
              <button className="btn-edit" onClick={enterEdit}>Edit</button>
            </div>
          </div>

          <div className="modal-body">
            <section className="modal-section">
              <h3>Decision</h3>
              <p>{node.decision}</p>
            </section>

            {node.rationale && (
              <section className="modal-section">
                <h3>Rationale</h3>
                <p>{node.rationale}</p>
              </section>
            )}

            {node.tradeoffs?.length > 0 && (
              <section className="modal-section">
                <h3>Tradeoffs</h3>
                <ul className="modal-list">
                  {node.tradeoffs.map(t => <li key={t}>{t}</li>)}
                </ul>
              </section>
            )}

            {node.tags?.length > 0 && (
              <section className="modal-section">
                <h3>Tags</h3>
                <div className="card-tags">
                  {node.tags.map(t => <span key={t} className="tag">{t}</span>)}
                </div>
              </section>
            )}

            {node.artifacts?.length > 0 && (
              <section className="modal-section">
                <h3>Artifacts</h3>
                <ul className="modal-artifacts">
                  {node.artifacts.map(a => (
                    <li key={a.ref} className={a.is_anchor ? 'anchor' : ''}>
                      <span className="artifact-type">{a.type}</span>
                      <span className="artifact-ref">{a.ref}</span>
                      {a.is_anchor && <span className="anchor-badge">anchor</span>}
                    </li>
                  ))}
                </ul>
              </section>
            )}
          </div>
        </>}

        {/* ── Edit mode ── */}
        {node && mode === 'edit' && <>
          <div className="modal-header">
            <h2 className="modal-title">Edit Decision</h2>
          </div>

          <div className="modal-body">
            <div className="edit-field">
              <label>Title</label>
              <input
                className="edit-input"
                value={editData.title}
                onChange={field('title')}
                autoFocus
              />
            </div>

            <div className="edit-field">
              <label>Decision</label>
              <textarea
                className="edit-textarea"
                rows={3}
                value={editData.decision}
                onChange={field('decision')}
              />
            </div>

            <div className="edit-field">
              <label>Rationale</label>
              <textarea
                className="edit-textarea"
                rows={2}
                value={editData.rationale}
                onChange={field('rationale')}
              />
            </div>

            <div className="edit-field">
              <label>
                Confidence
                <span className="confidence-preview" style={{ color: confidenceColor(editData.confidence) }}>
                  {Math.round(editData.confidence * 100)}%
                </span>
              </label>
              <input
                type="range"
                className="edit-range"
                min="0" max="1" step="0.01"
                value={editData.confidence}
                onChange={field('confidence')}
              />
            </div>

            <div className="edit-field">
              <label>Tradeoffs <span className="field-hint">one per line</span></label>
              <textarea
                className="edit-textarea"
                rows={3}
                value={editData.tradeoffs}
                onChange={field('tradeoffs')}
              />
            </div>

            <div className="edit-field">
              <label>Tags <span className="field-hint">one per line</span></label>
              <textarea
                className="edit-textarea"
                rows={3}
                value={editData.tags}
                onChange={field('tags')}
              />
            </div>

            {saveError && (
              <p className="modal-save-error">Save failed: {saveError}</p>
            )}

            <div className="modal-actions">
              <button className="btn-cancel" onClick={cancelEdit} disabled={saving}>
                Cancel
              </button>
              <button className="btn-save" onClick={handleSave} disabled={saving}>
                {saving ? 'Saving…' : 'Save'}
              </button>
            </div>
          </div>
        </>}
      </div>
    </div>
  );
}
