import { useState } from 'react';

export default function NodeDetailModal({ node, onClose, finalized, onUpdateNode, onReprocess }) {
  const [mode, setMode] = useState('view');
  const [editData, setEditData] = useState(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);

  const canEdit = !finalized && onUpdateNode;

  function enterEdit() {
    setEditData({
      title:      node.title,
      decision:   node.decision || '',
      rationale:  node.rationale || '',
      tradeoffs:  (node.tradeoffs || []).join('\n'),
      confidence: node.confidence ?? 0.8,
      tags:       (node.tags || []).join('\n'),
      target_file: node.target_file || '',
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
      const result = await onUpdateNode({
        title:      editData.title.trim(),
        original_title: node.title,
        decision:   editData.decision.trim(),
        rationale:  editData.rationale.trim() || null,
        tradeoffs:  editData.tradeoffs.split('\n').map(s => s.trim()).filter(Boolean),
        confidence: parseFloat(editData.confidence),
        tags:       editData.tags.split('\n').map(s => s.trim()).filter(Boolean),
        target_file: editData.target_file.trim() || null,
      });
      if (!result) {
        setSaveError('Update failed — check error banner.');
        setSaving(false);
        return;
      }
      // Reprocess violations with the updated node
      if (onReprocess) {
        await onReprocess();
      }
      setMode('view');
      onClose();
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

        {mode === 'view' && (
          <>
            <div className="modal-header">
              <span className="modal-title">{node.title}</span>
              <div className="modal-header-right">
                <span className={`planner-conf ${
                  (node.risky ? 0.3 : node.confidence) >= 0.85 ? 'planner-conf--high'
                  : (node.risky ? 0.3 : node.confidence) >= 0.65 ? 'planner-conf--med'
                  : 'planner-conf--low'
                }`}>
                  {Math.round((node.risky ? 0.3 : node.confidence) * 100)}%
                </span>
                {canEdit && <button className="btn-edit" onClick={enterEdit}>Edit</button>}
              </div>
            </div>

            <div className="modal-body">
              <div className="modal-section">
                <h3>Decision</h3>
                <p>{node.decision}</p>
              </div>

              {node.rationale && (
                <div className="modal-section">
                  <h3>Rationale</h3>
                  <p>{node.rationale}</p>
                </div>
              )}

              {node.tradeoffs?.length > 0 && (
                <div className="modal-section">
                  <h3>Tradeoffs</h3>
                  <ul className="modal-list">
                    {node.tradeoffs.map((t, i) => <li key={i}>{t}</li>)}
                  </ul>
                </div>
              )}

              {node.tags?.length > 0 && (
                <div className="modal-section">
                  <h3>Tags</h3>
                  <div className="planner-node-tags">
                    {node.tags.map((t, i) => (
                      <span key={i} className="planner-tag">{t}</span>
                    ))}
                  </div>
                </div>
              )}

              {node.target_file && (
                <div className="modal-section">
                  <h3>Target File</h3>
                  <p><code className="node-detail-code">{node.target_file}</code></p>
                </div>
              )}

              {node.risky && (
                <div className="modal-section">
                  <p className="planner-node-risk">&#9888; This decision violates an existing architectural decision.</p>
                </div>
              )}
            </div>
          </>
        )}

        {mode === 'edit' && (
          <>
            <div className="modal-header">
              <h2 className="modal-title">Edit Decision</h2>
            </div>

            <div className="modal-body">
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
                <label>Target File</label>
                <input className="edit-input" value={editData.target_file} onChange={field('target_file')} />
              </div>

              <div className="edit-field">
                <label>Confidence</label>
                <input type="range" className="edit-range" min="0" max="1" step="0.01"
                  value={editData.confidence} onChange={field('confidence')} />
              </div>

              <div className="edit-field">
                <label>Tradeoffs <span className="field-hint">one per line</span></label>
                <textarea className="edit-textarea" rows={3} value={editData.tradeoffs} onChange={field('tradeoffs')} />
              </div>

              <div className="edit-field">
                <label>Tags <span className="field-hint">one per line</span></label>
                <textarea className="edit-textarea" rows={3} value={editData.tags} onChange={field('tags')} />
              </div>

              {saveError && <p className="modal-save-error">Save failed: {saveError}</p>}

              <div className="modal-actions">
                <button className="btn-cancel" onClick={cancelEdit} disabled={saving}>Cancel</button>
                <button className="btn-save" onClick={handleSave} disabled={saving}>
                  {saving ? 'Saving…' : 'Save & Reprocess'}
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
