export default function ViolationModal({ violations, onClose }) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-panel" onClick={e => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>&#x2715;</button>

        <div className="modal-header">
          <span className="modal-title">Decision Violations Detected</span>
          <span className="violation-count">{violations.length}</span>
        </div>

        <div className="modal-body">
          <p className="violation-intro">
            The following plan changes violate existing architectural decisions.
          </p>

          {violations.map((v, i) => (
            <div key={i} className="violation-card">
              <div className="violation-card-header">
                <span className={`violation-type violation-type--${v.violation_type}`}>
                  {v.violation_type}
                </span>
                <span className="violation-decision-title">{v.decision_title}</span>
              </div>
              <div className="violation-section">
                <span className="violation-label">Violating change:</span>
                <span className="violation-change-section">{v.change_section}</span>
              </div>
              <p className="violation-decision-text">{v.decision}</p>
              <p className="violation-explanation">{v.explanation}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
