import { useDroppable } from '@dnd-kit/core';
import DecisionCard from './DecisionCard';
import FileNode from './FileNode';

export default function FolderNode({ folder, nodesByPath, onNodeClick }) {
  const { isOver, setNodeRef } = useDroppable({ id: folder.path });
  const ownNodes = nodesByPath[folder.path] || [];

  return (
    <div className="folder-node">
      <div className="folder-label">
        <span className="folder-icon">&#128193;</span>
        {folder.name}/
      </div>

      {/* Drop zone for nodes assigned directly to this folder */}
      <div ref={setNodeRef} className={`node-drop-area folder-own-area${isOver ? ' drop-over' : ''}`}>
        {ownNodes.length === 0 && (
          <span className="empty-hint">Drop a node here</span>
        )}
        {ownNodes.map(n => (
          <DecisionCard key={n.id} node={n} onNodeClick={onNodeClick} />
        ))}
      </div>

      {/* Children: sub-folders and files */}
      {folder.children && folder.children.length > 0 && (
        <div className="folder-children">
          {folder.children.map(child =>
            child.type === 'folder' ? (
              <FolderNode
                key={child.path}
                folder={child}
                nodesByPath={nodesByPath}
                onNodeClick={onNodeClick}
              />
            ) : (
              <FileNode
                key={child.path}
                path={child.path}
                name={child.name}
                nodes={nodesByPath[child.path] || []}
                onNodeClick={onNodeClick}
              />
            )
          )}
        </div>
      )}
    </div>
  );
}
