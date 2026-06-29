export default function NodeCard({ node, onClick }) {
  return (
    <div className="planner-node-card planner-node-card--clickable" onClick={onClick}>
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
    </div>
  );
}
