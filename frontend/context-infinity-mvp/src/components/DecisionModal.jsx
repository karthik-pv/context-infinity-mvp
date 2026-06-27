import { useDecisionDetail } from '../hooks/useDecisionDetail';
import ModalViewMode from './modal/ModalViewMode';
import ModalEditMode from './modal/ModalEditMode';

export default function DecisionModal({ nodeId, onClose }) {
  const {
    node, loading, fetchError,
    mode, editData, saving, saveError,
    enterEdit, cancelEdit, handleSave, field,
  } = useDecisionDetail(nodeId, onClose);

  return (
    <div className="modal-overlay" onClick={mode === 'view' ? onClose : undefined}>
      <div className="modal-panel" onClick={e => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>&#x2715;</button>

        {loading && <p className="modal-status">Loading…</p>}
        {fetchError && <p className="modal-status modal-error">Error: {fetchError}</p>}

        {node && mode === 'view' && (
          <ModalViewMode node={node} onEdit={enterEdit} />
        )}

        {node && mode === 'edit' && (
          <ModalEditMode
            editData={editData}
            saving={saving}
            saveError={saveError}
            onChange={field}
            onSave={handleSave}
            onCancel={cancelEdit}
          />
        )}
      </div>
    </div>
  );
}
