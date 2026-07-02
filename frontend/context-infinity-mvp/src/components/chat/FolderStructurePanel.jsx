import { buildTree } from '../../data/treeStructure';

function TreeView({ items, depth = 0 }) {
  return items.map(item => (
    <div key={item.path}>
      <div className="folder-tree-item" style={{ paddingLeft: depth * 14 }}>
        <span className="folder-tree-icon">
          {item.type === 'folder' ? '\u{1F4C1}' : '\u{1F4C4}'}
        </span>
        <span className="folder-tree-name">
          {item.name}{item.type === 'folder' ? '/' : ''}
        </span>
      </div>
      {item.children && <TreeView items={item.children} depth={depth + 1} />}
    </div>
  ));
}

export default function FolderStructurePanel({ paths }) {
  if (!paths || paths.length === 0) {
    return (
      <div className="planner-empty planner-empty--sm">
        Folder structure will appear as you plan.
      </div>
    );
  }

  const typedPaths = paths.map(p => ({
    ref: p,
    type: p.endsWith('/') ? 'folder' : 'file',
  }));
  const tree = buildTree(typedPaths);

  return <div className="folder-tree"><TreeView items={tree} /></div>;
}
