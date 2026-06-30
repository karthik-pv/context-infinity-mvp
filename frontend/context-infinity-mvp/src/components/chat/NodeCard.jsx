export default function NodeCard({ node, onClick }) {
  const risky = node.risky;
  const confidence = risky ? 0.3 : node.confidence;

  return (
    <div
      className={`planner-node-card planner-node-card--clickable${risky ? ' planner-node-card--risky' : ''}`}
      onClick={onClick}
    >
      <div className="planner-node-top">
        <span className="planner-node-title">{node.title}</span>
        <span className={`planner-conf ${
          confidence >= 0.85 ? 'planner-conf--high'
          : confidence >= 0.65 ? 'planner-conf--med'
          : 'planner-conf--low'
        }`}>
          {Math.round(confidence * 100)}%
        </span>
      </div>
      <div className="planner-node-decision">{node.decision}</div>
      {risky && <div className="planner-node-risk">&#9888; Violates existing decision</div>}
    </div>
  );
}
