export default function FolderTree({ paths }) {
  if (!paths || paths.length === 0) {
    return <p className="project-tree-empty">No files planned yet.</p>;
  }

  const tree = buildTree(paths);

  return (
    <div className="project-tree">
      {tree.map(node => renderNode(node, 0))}
    </div>
  );
}

function renderNode(node, depth) {
  const isFile = !node.children;
  return (
    <div key={node.path} className="project-tree-node">
      <div className="project-tree-row" style={{ paddingLeft: `${depth * 16 + 8}px` }}>
        <span className="project-tree-icon">{isFile ? '\u{1F4C4}' : '\u{1F4C1}'}</span>
        <span className={isFile ? 'project-tree-file' : 'project-tree-folder'}>
          {node.name}{isFile ? '' : '/'}
        </span>
      </div>
      {node.children && node.children.map(child => renderNode(child, depth + 1))}
    </div>
  );
}

function buildTree(paths) {
  const typeMap = {};
  paths.forEach(p => { typeMap[p] = 'file'; });

  Object.keys(typeMap).forEach(p => {
    const parts = p.split('/');
    for (let i = 1; i < parts.length; i++) {
      const parent = parts.slice(0, i).join('/');
      if (!typeMap[parent]) typeMap[parent] = 'folder';
    }
  });

  const all = Object.keys(typeMap).sort();

  function buildChildren(parentPath) {
    const prefix = parentPath ? parentPath + '/' : '';
    return all
      .filter(p => p.startsWith(prefix) && !p.slice(prefix.length).includes('/'))
      .map(p => {
        const name = p.split('/').pop();
        if (typeMap[p] === 'folder') {
          return { name, path: p, children: buildChildren(p) };
        }
        return { name, path: p };
      });
  }

  return buildChildren('');
}
