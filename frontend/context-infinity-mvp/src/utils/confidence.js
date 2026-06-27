export function confidenceColor(c) {
  if (c >= 0.93) return 'var(--confidence-high)';
  if (c >= 0.87) return 'var(--confidence-med)';
  return 'var(--confidence-low)';
}
