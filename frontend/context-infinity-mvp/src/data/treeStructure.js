// Builds a nested tree from a flat array of { ref, type } artifact paths.
// Intermediate parent folders that are not explicitly listed are inferred.
export function buildTree(paths) {
  const typeMap = {};

  paths.forEach(({ ref, type }) => {
    typeMap[ref] = type;
  });

  // Infer implicit parent folders
  Object.keys(typeMap).forEach(ref => {
    const parts = ref.split('/');
    for (let i = 1; i < parts.length; i++) {
      const parent = parts.slice(0, i).join('/');
      if (!typeMap[parent]) typeMap[parent] = 'folder';
    }
  });

  const allPaths = Object.keys(typeMap).sort();

  function buildChildren(parentPath) {
    const prefix = parentPath ? parentPath + '/' : '';
    return allPaths
      .filter(p => p.startsWith(prefix) && !p.slice(prefix.length).includes('/'))
      .map(p => {
        const node = { type: typeMap[p], name: p.split('/').pop(), path: p };
        if (typeMap[p] === 'folder') node.children = buildChildren(p);
        return node;
      });
  }

  return buildChildren('');
}
