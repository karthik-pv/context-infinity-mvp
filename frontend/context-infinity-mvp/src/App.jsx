import { useState, useMemo, useEffect } from 'react';
import { DndContext, DragOverlay, PointerSensor, useSensor, useSensors } from '@dnd-kit/core';
import { fetchDecisions } from './data/api';
import { buildTree } from './data/treeStructure';
import FolderNode from './components/FolderNode';
import DecisionCard from './components/DecisionCard';

export default function App() {
  const [nodes, setNodes] = useState([]);
  const [nodeLocations, setNodeLocations] = useState({});
  const [treeStructure, setTreeStructure] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeId, setActiveId] = useState(null);

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

  const nodesByPath = useMemo(() => {
    const map = {};
    nodes.forEach(n => {
      const path = nodeLocations[n.id];
      if (!map[path]) map[path] = [];
      map[path].push(n);
    });
    return map;
  }, [nodes, nodeLocations]);

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

  if (loading) return (
    <div className="app-shell">
      <header className="app-header">
        <span className="logo-mark">&#9670;</span>
        <h1>Context Infinity</h1>
        <span className="header-sub">Decision Node Explorer</span>
      </header>
      <main className="tree-canvas" style={{ padding: '2rem', opacity: 0.5 }}>Loading…</main>
    </div>
  );

  if (error) return (
    <div className="app-shell">
      <header className="app-header">
        <span className="logo-mark">&#9670;</span>
        <h1>Context Infinity</h1>
        <span className="header-sub">Decision Node Explorer</span>
      </header>
      <main className="tree-canvas" style={{ padding: '2rem', color: 'var(--confidence-low)' }}>
        Error: {error}
      </main>
    </div>
  );

  return (
    <DndContext sensors={sensors} onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
      <div className="app-shell">
        <header className="app-header">
          <span className="logo-mark">&#9670;</span>
          <h1>Context Infinity</h1>
          <span className="header-sub">Decision Node Explorer</span>
        </header>

        <main className="tree-canvas">
          {treeStructure.map(folder => (
            <FolderNode key={folder.path} folder={folder} nodesByPath={nodesByPath} />
          ))}
        </main>
      </div>

      <DragOverlay dropAnimation={null}>
        {activeNode ? <DecisionCard node={activeNode} isDragOverlay /> : null}
      </DragOverlay>
    </DndContext>
  );
}
