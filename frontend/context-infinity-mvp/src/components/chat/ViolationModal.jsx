import { useState, useEffect } from 'react';
import { fetchDecisionById, updateDecision } from '../../data/api';

export default function ViolationModal({ violations, onClose, onReprocess }) {
  const [decisionCache, setDecisionCache] = useState({});
  const [editingId, setEditingId] = useState(null);
  const [editData, setEditData] = useState(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);
  const [reprocessing, setReprocessing] = useState(false);

  // Fetch full decision details for each violated historical decision
  useEffect(() => {
    const ids = violations
      .map(v => v.violated_decision_id)
      .filter(id => id && !decisionCache[id]);

    if (ids.length === 0) return;

    let cancelled = false;
    Promise.all(ids.map(id => fetchDecisionById(id).catch(() => null)))
      .then(results => {
        if (cancelled) return;
        setDecisionCache(prev => {
          const next = { ...prev };
          results.forEach((node, i) => {
            if (node) next[ids[i]] = node;
          });
          return next;
        });
      });
    return () => { cancelled = true; };
  }, [violations]); // eslint-disable-line react-hooks/exhaustive-deps

  function startEdit(decisionId) {
    const node = decisionCache[decisionId];
    if (!node) return;
    setEditData({
      title:      node.title,
      decision:   node.decision,
      rationale:  node.rationale || '',
      tradeoffs:  (node.tradeoffs || []).join('\n'),
      confidence: node.confidence,
      tags:       (node.tags || []).join('\n'),
    });
    setSaveError(null);
    setEditingId(decisionId);
  }

  function cancelEdit() {
    setEditingId(null);
    setEditData(null);
    setSaveError(null);
  }

  async function handleSave(decisionId) {
    setSaving(true);
    setSaveError(null);
    try {
      const updated = await updateDecision(decisionId, {
        title:      editData.title.trim(),
        decision:   editData.decision.trim(),
        rationale:  editData.rationale.trim() || null,
        tradeoffs:  editData.tradeoffs.split('\n').map(s => s.trim()).filter(Boolean),
        confidence: parseFloat(editData.confidence),
        tags:       editData.tags.split('\n').map(s => s.trim()).filter(Boolean),
      });
      setDecisionCache(prev => ({ ...prev, [decisionId]: updated }));
      setEditingId(null);
      setEditData(null);

      // Reprocess to see if violations changed
      setReprocessing(true);
      await onReprocess();
      setReprocessing(false);
    } catch (err) {
      setSaveError(err.message);
    } finally {
      setSaving(false);
      setReprocessing(false);
    }
  }

  function field(key) {
    return e => setEditData(prev => ({ ...prev, [key]: e.target.value }));
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-panel modal-panel--wide" onClick={e => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>&#x2715;</button>

        <div className="modal-header">
          <span className="modal-title">Decision Violations Detected</span>
          <span className="violation-count">{violations.length}</span>
        </div>

        <div className="modal-body">
          <p className="violation-intro">
            The following new decisions violate existing architectural decisions.
            Edit a violated decision to resolve the conflict, then reprocess to check again.
          </p>

          {reprocessing && (
            <p className="violation-reprocessing">
              <span className="planner-spinner" /> Reprocessing violations…
            </p>
          )}

          {violations.map((v, i) => {
            const decisionId = v.violated_decision_id;
            const decision = decisionId ? decisionCache[decisionId] : null;
            const isEditing = editingId === decisionId;
            const vType = v.type || v.violation_type || 'direct';

            return (
              <div key={i} className="violation-card">
                <div className="violation-card-header">
                  <span className={`violation-type violation-type--${vType}`}>
                    {vType}
                  </span>
                  <span className="violation-decision-title">
                    {decision?.title || v.violated_decision_title || 'Unknown decision'}
                  </span>
                  {v.severity && (
                    <span className={`violation-severity violation-severity--${v.severity}`}>
                      {v.severity}
                    </span>
                  )}
                </div>

                {v.violating_node_title && (
                  <div className="violation-section">
                    <span className="violation-label">Violating decision:</span>
                    <span className="violation-change-section">{v.violating_node_title}</span>
                  </div>
                )}

                <p className="violation-explanation">{v.explanation}</p>

                {v.suggested_resolution && (
                  <div className="violation-resolution">
                    <span className="violation-label">Suggested resolution:</span>
                    <p className="violation-resolution-text">{v.suggested_resolution}</p>
                  </div>
                )}

                {decision && !isEditing && (
                  <div className="violation-decision-detail">
                    <div className="violation-decision-detail-header">
                      <span className="violation-label">Violated decision:</span>
                      <button className="btn-edit" onClick={() => startEdit(decisionId)}>
                        Edit
                      </button>
                    </div>
                    <p className="violation-decision-text">{decision.decision}</p>
                    {decision.rationale && (
                      <p className="violation-decision-rationale">Rationale: {decision.rationale}</p>
                    )}
                  </div>
                )}

                {decision && isEditing && (
                  <div className="violation-edit-form">
                    <div className="edit-field">
                      <label>Title</label>
                      <input className="edit-input" value={editData.title} onChange={field('title')} autoFocus />
                    </div>
                    <div className="edit-field">
                      <label>Decision</label>
                      <textarea className="edit-textarea" rows={3} value={editData.decision} onChange={field('decision')} />
                    </div>
                    <div className="edit-field">
                      <label>Rationale</label>
                      <textarea className="edit-textarea" rows={2} value={editData.rationale} onChange={field('rationale')} />
                    </div>
                    <div className="edit-field">
                      <label>Tags <span className="field-hint">one per line</span></label>
                      <textarea className="edit-textarea" rows={3} value={editData.tags} onChange={field('tags')} />
                    </div>
                    {saveError && <p className="modal-save-error">Save failed: {saveError}</p>}
                    <div className="modal-actions">
                      <button className="btn-cancel" onClick={cancelEdit} disabled={saving}>Cancel</button>
                      <button className="btn-save" onClick={() => handleSave(decisionId)} disabled={saving}>
                        {saving ? 'Saving…' : 'Save & Reprocess'}
                      </button>
                    </div>
                  </div>
                )}

                {!decision && decisionId && (
                  <p className="violation-decision-loading">Loading decision details…</p>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
