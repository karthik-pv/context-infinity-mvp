export default function DriftModal({ drift, onClose }) {
  const { missing, extra } = drift;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-panel" onClick={e => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>&#x2715;</button>

        <div className="modal-header">
          <span className="modal-title">Context Drift Detected</span>
        </div>

        <div className="modal-body">
          <p className="drift-intro">
            The planned folder structure does not match the actual project filesystem.
          </p>

          {missing.length > 0 && (
            <div className="modal-section">
              <h3>Planned but not on disk ({missing.length})</h3>
              <ul className="drift-list drift-list--missing">
                {missing.map(p => <li key={p}>{p}</li>)}
              </ul>
            </div>
          )}

          {extra.length > 0 && (
            <div className="modal-section">
              <h3>On disk but not planned ({extra.length})</h3>
              <ul className="drift-list drift-list--extra">
                {extra.map(p => <li key={p}>{p}</li>)}
              </ul>
            </div>
          )}

          {missing.length === 0 && extra.length === 0 && (
            <p className="drift-intro">No differences found — structures are in sync.</p>
          )}
        </div>
      </div>
    </div>
  );
}
