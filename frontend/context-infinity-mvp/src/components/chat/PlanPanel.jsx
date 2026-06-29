import { useState } from 'react';
import NodeCard from './NodeCard';
import NodeDetailModal from './NodeDetailModal';
import FolderStructurePanel from './FolderStructurePanel';

export default function PlanPanel({ plan, nodes, folderStructure }) {
  const [selectedNode, setSelectedNode] = useState(null);
  const [copied, setCopied] = useState(false);

  function handleCopyPlan() {
    const text = Object.entries(plan)
      .map(([key, value]) => {
        const content = typeof value === 'object' ? value.content : value;
        const targetFile = typeof value === 'object' ? value.target_file : null;
        const header = key.replace(/_/g, ' ');
        const target = targetFile ? ` → ${targetFile}` : '';
        return `[${header}]${target}\n${content}`;
      })
      .join('\n\n');
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div className="planner-right-panel">

      <div className="planner-plan-panel">
        <div className="planner-panel-header">
          <span className="planner-panel-title">Implementation Plan</span>
          <button
            className="planner-copy-btn"
            onClick={handleCopyPlan}
            disabled={Object.keys(plan).length === 0}
            title="Copy plan to clipboard"
          >
            {copied ? '✓ Copied' : 'Copy'}
          </button>
          <span className="planner-panel-count">{Object.keys(plan).length} sections</span>
        </div>
        <div className="planner-panel-body">
          {Object.keys(plan).length === 0 ? (
            <div className="planner-empty planner-empty--sm">
              Plan sections will appear as you chat.
            </div>
          ) : (
            Object.entries(plan).map(([key, value]) => {
              const content = typeof value === 'object' ? value.content : value;
              const targetFile = typeof value === 'object' ? value.target_file : null;
              return (
                <div key={key} className="plan-section">
                  <div className="plan-section-id">{key.replace(/_/g, ' ')}</div>
                  {targetFile && <div className="plan-section-file">{targetFile}</div>}
                  <div className="plan-section-content">{content}</div>
                </div>
              );
            })
          )}
        </div>
      </div>

      <div className="planner-right-bottom">
        <div className="planner-nodes-panel">
          <div className="planner-panel-header">
            <span className="planner-panel-title">Inferred Decisions</span>
            <span className="planner-panel-count">{nodes.length} nodes</span>
          </div>
          <div className="planner-panel-body">
            {nodes.length === 0 ? (
              <div className="planner-empty planner-empty--sm">
                Architectural decisions will be extracted from your conversation.
              </div>
            ) : (
              nodes.map((node, i) => (
                <NodeCard key={i} node={node} onClick={() => setSelectedNode(node)} />
              ))
            )}
          </div>
        </div>

        <div className="planner-folder-panel">
          <div className="planner-panel-header">
            <span className="planner-panel-title">Folder Structure</span>
            <span className="planner-panel-count">{folderStructure.length} paths</span>
          </div>
          <div className="planner-panel-body">
            <FolderStructurePanel paths={folderStructure} />
          </div>
        </div>
      </div>

      {selectedNode && (
        <NodeDetailModal node={selectedNode} onClose={() => setSelectedNode(null)} />
      )}

    </div>
  );
}
