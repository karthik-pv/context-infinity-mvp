export default function NodeCard({ node }) {
  return (
    <div className="planner-node-card">
      <div className="planner-node-top">
        <span className="planner-node-title">{node.title}</span>
        <span className={`planner-conf ${
          node.confidence >= 0.85 ? 'planner-conf--high'
          : node.confidence >= 0.65 ? 'planner-conf--med'
          : 'planner-conf--low'
        }`}>
          {Math.round(node.confidence * 100)}%
        </span>
      </div>
      <div className="planner-node-decision">{node.decision}</div>
      {node.rationale && (
        <div className="planner-node-rationale">{node.rationale}</div>
      )}
      {node.tradeoffs?.length > 0 && (
        <ul className="planner-node-tradeoffs">
          {node.tradeoffs.map((t, i) => <li key={i}>{t}</li>)}
        </ul>
      )}
      <div className="planner-node-footer">
        {node.tags?.length > 0 && (
          <div className="planner-node-tags">
            {node.tags.map((t, i) => (
              <span key={i} className="planner-tag">{t}</span>
            ))}
          </div>
        )}
        {node.artifact_ref && (
          <span className="planner-artifact-ref">{node.artifact_ref}</span>
        )}
      </div>
    </div>
  );
}
