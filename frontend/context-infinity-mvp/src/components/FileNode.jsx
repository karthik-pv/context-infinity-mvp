import { useDroppable } from '@dnd-kit/core';
import DecisionCard from './DecisionCard';

export default function FileNode({ path, name, nodes, onNodeClick }) {
  const { isOver, setNodeRef } = useDroppable({ id: path });

  return (
    <div className={`file-node${isOver ? ' drop-over' : ''}`}>
      <div className="file-label">
        <span className="file-icon">&#128196;</span>
        {name}
      </div>
      <div ref={setNodeRef} className="node-drop-area file-drop-area">
        {nodes.length === 0 && (
          <span className="empty-hint">Drop a node here</span>
        )}
        {nodes.map(n => (
          <DecisionCard key={n.id} node={n} onNodeClick={onNodeClick} />
        ))}
      </div>
    </div>
  );
}
