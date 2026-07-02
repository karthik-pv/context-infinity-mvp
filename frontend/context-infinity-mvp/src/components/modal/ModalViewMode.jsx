import { confidenceColor } from '../../utils/confidence';

export default function ModalViewMode({ node, onEdit }) {
  return (
    <>
      <div className="modal-header">
        <h2 className="modal-title">{node.title}</h2>
        <div className="modal-header-right">
          <span className="modal-confidence" style={{ color: confidenceColor(node.confidence) }}>
            {Math.round(node.confidence * 100)}%
          </span>
          <button className="btn-edit" onClick={onEdit}>Edit</button>
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
    </>
  );
}
