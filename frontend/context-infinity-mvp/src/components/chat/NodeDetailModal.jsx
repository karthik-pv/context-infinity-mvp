export default function NodeDetailModal({ node, onClose }) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-panel" onClick={e => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>&#x2715;</button>

        <div className="modal-header">
          <span className="modal-title">{node.title}</span>
          <div className="modal-header-right">
            <span className={`planner-conf ${
              node.confidence >= 0.85 ? 'planner-conf--high'
              : node.confidence >= 0.65 ? 'planner-conf--med'
              : 'planner-conf--low'
            }`}>
              {Math.round(node.confidence * 100)}%
            </span>
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
        </div>
      </div>
    </div>
  );
}
