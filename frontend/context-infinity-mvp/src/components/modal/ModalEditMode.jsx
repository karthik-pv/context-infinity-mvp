import { confidenceColor } from '../../utils/confidence';

export default function ModalEditMode({ editData, saving, saveError, onChange, onSave, onCancel }) {
  return (
    <>
      <div className="modal-header">
        <h2 className="modal-title">Edit Decision</h2>
      </div>

      <div className="modal-body">
        <div className="edit-field">
          <label>Title</label>
          <input
            className="edit-input"
            value={editData.title}
            onChange={onChange('title')}
            autoFocus
          />
        </div>

        <div className="edit-field">
          <label>Decision</label>
          <textarea
            className="edit-textarea"
            rows={3}
            value={editData.decision}
            onChange={onChange('decision')}
          />
        </div>

        <div className="edit-field">
          <label>Rationale</label>
          <textarea
            className="edit-textarea"
            rows={2}
            value={editData.rationale}
            onChange={onChange('rationale')}
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
            onChange={onChange('confidence')}
          />
        </div>

        <div className="edit-field">
          <label>Tradeoffs <span className="field-hint">one per line</span></label>
          <textarea
            className="edit-textarea"
            rows={3}
            value={editData.tradeoffs}
            onChange={onChange('tradeoffs')}
          />
        </div>

        <div className="edit-field">
          <label>Tags <span className="field-hint">one per line</span></label>
          <textarea
            className="edit-textarea"
            rows={3}
            value={editData.tags}
            onChange={onChange('tags')}
          />
        </div>

        {saveError && <p className="modal-save-error">Save failed: {saveError}</p>}

        <div className="modal-actions">
          <button className="btn-cancel" onClick={onCancel} disabled={saving}>
            Cancel
          </button>
          <button className="btn-save" onClick={onSave} disabled={saving}>
            {saving ? 'Saving…' : 'Save'}
          </button>
        </div>
      </div>
    </>
  );
}
