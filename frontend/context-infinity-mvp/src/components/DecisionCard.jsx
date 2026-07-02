import { useDraggable } from '@dnd-kit/core';
import { CSS } from '@dnd-kit/utilities';

function confidenceColor(c) {
  if (c >= 0.93) return 'var(--confidence-high)';
  if (c >= 0.87) return 'var(--confidence-med)';
  return 'var(--confidence-low)';
}

export default function DecisionCard({ node, isDragOverlay = false, onNodeClick }) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: node.id,
    disabled: isDragOverlay,
  });

  const style = {
    transform: CSS.Translate.toString(transform),
    opacity: isDragging ? 0.35 : 1,
    zIndex: isDragging ? 1000 : 'auto',
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
      className={`decision-card${isDragOverlay ? ' drag-overlay' : ''}`}
      onClick={() => !isDragging && onNodeClick?.(node.id)}
    >
      <div className="card-header">
        <span className="card-title">{node.title}</span>
        <span
          className="card-confidence"
          style={{ color: confidenceColor(node.confidence) }}
        >
          {Math.round(node.confidence * 100)}%
        </span>
      </div>
      <p className="card-decision">{node.decision}</p>
      <div className="card-tags">
        {node.tags.map(t => (
          <span key={t} className="tag">{t}</span>
        ))}
      </div>
    </div>
  );
}
