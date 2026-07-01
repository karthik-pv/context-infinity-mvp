// Builds a nested tree from a flat array of { ref, type } artifact paths.
// Intermediate parent folders that are not explicitly listed are inferred.
export function buildTree(paths) {
  const typeMap = {};

  paths.forEach(({ ref, type }) => {
    typeMap[ref] = type;
  });

  // Normalize: ensure folder refs end with '/'
  const normalized = {};
  Object.entries(typeMap).forEach(([ref, type]) => {
    const normalizedRef =
      type === 'folder' && !ref.endsWith('/') ? ref + '/' : ref;
    normalized[normalizedRef] = type;
  });

  // Infer missing parent folders
  Object.keys(normalized).forEach(ref => {
    const parts = ref.replace(/\/$/, '').split('/');

    for (let i = 1; i < parts.length; i++) {
      const parent = parts.slice(0, i).join('/') + '/';
      if (!normalized[parent]) {
        normalized[parent] = 'folder';
      }
    }
  });

  const allPaths = Object.keys(normalized).sort();

  function buildChildren(parentPath = '') {
    // parentPath for folders already includes trailing '/'
    const prefix = parentPath || '';

    return allPaths
      .filter(p => {
        if (p === parentPath) return false;
        if (!p.startsWith(prefix)) return false;

        const remainder = p.slice(prefix.length);
        if (!remainder) return false;

        // Remove trailing slash before checking nesting depth
        const trimmed = remainder.replace(/\/$/, '');

        // Only direct children allowed
        return !trimmed.includes('/');
      })
      .map(p => {
        const name = p.replace(/\/$/, '').split('/').pop();

        const node = {
          type: normalized[p],
          name,
          path: p,
        };

        if (normalized[p] === 'folder') {
          node.children = buildChildren(p);
        }

        return node;
      });
  }

  return buildChildren('');
}