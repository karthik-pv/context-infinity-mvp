import { useState, useMemo, useEffect } from 'react';
import { DndContext, DragOverlay, PointerSensor, useSensor, useSensors } from '@dnd-kit/core';
import { fetchDecisions } from '../data/api';
import { buildTree } from '../data/treeStructure';
import FolderNode from '../components/FolderNode';
import DecisionCard from '../components/DecisionCard';
import DecisionModal from '../components/DecisionModal';

function SelectableTree({ items, depth = 0, selectedPath, onSelect }) {
  return items.map(item => (
    <div key={item.path}>
      <div
        className={`ctx-tree-item${selectedPath === item.path ? ' ctx-tree-item--selected' : ''}`}
        style={{ paddingLeft: depth * 14 }}
        onClick={() => onSelect(item.path, item.type)}
      >
        <span className="ctx-tree-icon">
          {item.type === 'folder' ? '\u{1F4C1}' : '\u{1F4C4}'}
        </span>
        <span className="ctx-tree-name">
          {item.name}{item.type === 'folder' ? '/' : ''}
        </span>
      </div>
      {item.children && (
        <SelectableTree
          items={item.children}
          depth={depth + 1}
          selectedPath={selectedPath}
          onSelect={onSelect}
        />
      )}
    </div>
  ));
}

// Find a node in the tree by path. Returns the node or null.
function findNode(tree, path) {
  for (const node of tree) {
    if (node.path === path) return node;
    if (node.children) {
      const found = findNode(node.children, path);
      if (found) return found;
    }
  }
  return null;
}

// Find the parent folder of a path in the tree.
function findParentFolder(tree, path) {
  for (const node of tree) {
    if (node.children) {
      for (const child of node.children) {
        if (child.path === path) return node;
      }
      const found = findParentFolder(node.children, path);
      if (found) return found;
    }
  }
  return null;
}

export default function ContextPage() {
  const [nodes, setNodes] = useState([]);
  const [nodeLocations, setNodeLocations] = useState({});
  const [treeStructure, setTreeStructure] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeId, setActiveId] = useState(null);
  const [selectedNodeId, setSelectedNodeId] = useState(null);
  const [selectedPath, setSelectedPath] = useState(null);
  const [selectedType, setSelectedType] = useState(null);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } })
  );

  useEffect(() => {
    fetchDecisions()
      .then(({ nodes: apiNodes, paths }) => {
        const locations = {};
        apiNodes.forEach(n => { locations[n.id] = n.location; });
        setNodes(apiNodes);
        setNodeLocations(locations);
        setTreeStructure(buildTree(paths));
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  // Map of path -> decision nodes at that path
  const nodesByPath = useMemo(() => {
    const map = {};
    nodes.forEach(n => {
      const path = nodeLocations[n.id];
      if (!map[path]) map[path] = [];
      map[path].push(n);
    });
    return map;
  }, [nodes, nodeLocations]);

  // Determine which tree nodes to render based on selection.
  // "whatever i click on should become the outermost box"
  const renderTree = useMemo(() => {
    if (!selectedPath) return treeStructure;

    if (selectedType === 'folder') {
      // Selected folder is the outermost box
      const node = findNode(treeStructure, selectedPath);
      return node ? [node] : [];
    }

    // File selected — find parent folder, render it as outermost box
    // so the file appears inside its parent folder box
    const parent = findParentFolder(treeStructure, selectedPath);
    if (parent) {
      // Filter parent's children to only show the selected file
      const filteredParent = {
        ...parent,
        children: (parent.children || []).filter(c => c.path === selectedPath),
      };
      return [filteredParent];
    }

    // File is at root level (no parent folder) — render it directly
    const fileNode = findNode(treeStructure, selectedPath);
    return fileNode ? [{ ...fileNode, type: 'folder', children: [fileNode] }] : [];
  }, [treeStructure, selectedPath, selectedType]);

  const activeNode = activeId ? nodes.find(n => n.id === activeId) : null;

  function handleDragStart({ active }) {
    setActiveId(active.id);
  }

  function handleDragEnd({ active, over }) {
    setActiveId(null);
    if (over && over.id !== nodeLocations[active.id]) {
      setNodeLocations(prev => ({ ...prev, [active.id]: over.id }));
    }
  }

  function handleSelect(path, type) {
    if (selectedPath === path) {
      setSelectedPath(null);
      setSelectedType(null);
    } else {
      setSelectedPath(path);
      setSelectedType(type);
    }
  }

  if (loading) return (
    <main className="tree-canvas" style={{ padding: '2rem', opacity: 0.5 }}>Loading…</main>
  );

  if (error) return (
    <main className="tree-canvas" style={{ padding: '2rem', color: 'var(--confidence-low)' }}>
      Error: {error}
    </main>
  );

  return (
    <DndContext sensors={sensors} onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
      <div className="ctx-shell">
        {/* Left: folder tree sidebar for navigation */}
        <div className="ctx-tree-sidebar">
          <div className="ctx-tree-header">
            <span className="ctx-tree-title">Folders</span>
            {selectedPath && (
              <button className="ctx-tree-clear" onClick={() => { setSelectedPath(null); setSelectedType(null); }}>
                Show all
              </button>
            )}
          </div>
          <div className="ctx-tree-body">
            {treeStructure.length === 0 ? (
              <p className="ctx-tree-empty">No folders yet.</p>
            ) : (
              <SelectableTree
                items={treeStructure}
                selectedPath={selectedPath}
                onSelect={handleSelect}
              />
            )}
          </div>
        </div>

        {/* Right: hierarchical box-within-box view */}
        <div className="ctx-canvas-panel">
          <div className="ctx-canvas-header">
            <span className="ctx-canvas-title">
              {selectedPath ? selectedPath : 'All Folders'}
            </span>
          </div>
          <div className="ctx-canvas-body">
            {renderTree.length === 0 ? (
              <p className="ctx-decisions-empty">
                {selectedPath
                  ? 'No content at this location.'
                  : 'No decisions yet. Finalize a planning session to populate.'}
              </p>
            ) : (
              renderTree.map(folder => (
                <FolderNode
                  key={folder.path}
                  folder={folder}
                  nodesByPath={nodesByPath}
                  onNodeClick={setSelectedNodeId}
                />
              ))
            )}
          </div>
        </div>
      </div>

      <DragOverlay dropAnimation={null}>
        {activeNode ? <DecisionCard node={activeNode} isDragOverlay /> : null}
      </DragOverlay>

      {selectedNodeId && (
        <DecisionModal nodeId={selectedNodeId} onClose={() => setSelectedNodeId(null)} />
      )}
    </DndContext>
  );
}
