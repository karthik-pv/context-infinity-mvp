import { useState } from 'react';
import { useProject } from '../hooks/useProject';
import FolderStructurePanel from '../components/chat/FolderStructurePanel';
import DriftModal from '../components/project/DriftModal';

function formatTokens(n) {
  if (!n) return '0';
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
  return String(n);
}

function BriefBubble({ entry, index, onEdit, onDelete, saving }) {
  const [editing, setEditing] = useState(false);
  const [text, setText] = useState(entry);

  function handleSave() {
    const trimmed = text.trim();
    if (trimmed && trimmed !== entry) {
      onEdit(index, trimmed);
    }
    setEditing(false);
  }

  if (editing) {
    return (
      <div className="brief-bubble brief-bubble--editing">
        <textarea
          className="brief-bubble-textarea"
          value={text}
          onChange={e => setText(e.target.value)}
          rows={3}
          autoFocus
        />
        <div className="brief-bubble-actions">
          <button className="btn-cancel" onClick={() => { setText(entry); setEditing(false); }} disabled={saving}>
            Cancel
          </button>
          <button className="btn-save" onClick={handleSave} disabled={saving}>
            {saving ? 'Saving…' : 'Save'}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="brief-bubble">
      <div className="brief-bubble-text">{entry}</div>
      <div className="brief-bubble-actions">
        <button className="brief-bubble-edit" onClick={() => { setText(entry); setEditing(true); }} title="Edit">
          Edit
        </button>
        <button className="brief-bubble-delete" onClick={() => onDelete(index)} title="Remove" disabled={saving}>
          &#x2715;
        </button>
      </div>
    </div>
  );
}

export default function ProjectPage() {
  const {
    projectPath, projectBrief, folderStructure, actualFolderStructure,
    inputTokens, outputTokens,
    loading, saving, syncing, error,
    savePath, syncFolders,
    addPaths, editBrief, addBrief, removeBrief,
  } = useProject();

  const [pathInput, setPathInput] = useState('');
  const [editingPath, setEditingPath] = useState(false);
  const [drift, setDrift] = useState(null);
  const [addingBrief, setAddingBrief] = useState(false);
  const [newBriefText, setNewBriefText] = useState('');

  if (loading) {
    return (
      <div className="project-shell project-shell--centered">
        <span className="planner-spinner" /> Loading project…
      </div>
    );
  }

  async function handleSync() {
    const actual = await syncFolders();
    if (actual) {
      const plannedSet = new Set(folderStructure);
      const actualSet = new Set(actual);
      const missing = folderStructure.filter(p => !actualSet.has(p));
      // Don't show a folder as "extra" if any planned path is inside it
      const extra = actual.filter(p => {
        if (plannedSet.has(p)) return false;
        if (p.endsWith('/')) {
          return !folderStructure.some(planned => planned.startsWith(p));
        }
        return true;
      });
      if (missing.length > 0 || extra.length > 0) {
        setDrift({ missing, extra });
      }
    }
  }

  async function handleAddPath(path) {
    await addPaths([path]);
    // Update drift to remove the added path from extra
    if (drift) {
      setDrift({
        ...drift,
        extra: drift.extra.filter(p => p !== path),
      });
    }
  }

  async function handleAddBrief() {
    const trimmed = newBriefText.trim();
    if (!trimmed) return;
    await addBrief(trimmed);
    setNewBriefText('');
    setAddingBrief(false);
  }

  return (
    <div className="project-shell">
      <div className="project-left">
        <div className="project-panel-header">
          <span className="project-panel-title">Folder Structure</span>
          <button
            className="project-sync-btn"
            onClick={handleSync}
            disabled={syncing || !projectPath}
            title="Scan actual filesystem and compare"
          >
            {syncing ? 'Syncing…' : 'Sync'}
          </button>
        </div>
        <div className="project-tree-split">
          <div className="project-tree-half">
            <div className="project-tree-half-label">Planned</div>
            <div className="project-tree-container">
              <FolderStructurePanel paths={folderStructure} />
            </div>
          </div>
          <div className="project-tree-half">
            <div className="project-tree-half-label">Actual</div>
            <div className="project-tree-container">
              <FolderStructurePanel paths={actualFolderStructure} />
            </div>
          </div>
        </div>
      </div>

      <div className="project-right">
        <div className="project-tokens">
          <div className="project-token-badge">
            <span className="project-token-label">In</span>
            <span className="project-token-value">{formatTokens(inputTokens)}</span>
          </div>
          <div className="project-token-badge">
            <span className="project-token-label">Out</span>
            <span className="project-token-value">{formatTokens(outputTokens)}</span>
          </div>
        </div>
        <div className="project-right-top">
          <label className="project-field-label">Project Path</label>
          <div className="project-path-row">
            <input
              className="project-path-input"
              value={editingPath ? pathInput : projectPath}
              placeholder="/path/to/your/project"
              onChange={e => { setPathInput(e.target.value); setEditingPath(true); }}
              onBlur={() => {
                if (editingPath && pathInput !== projectPath) savePath(pathInput);
                setEditingPath(false);
              }}
              onKeyDown={e => {
                if (e.key === 'Enter') e.target.blur();
              }}
            />
          </div>
          {saving && <span className="project-saving">Saving…</span>}
          {error && <span className="project-error">{error}</span>}
        </div>

        <div className="project-right-summary">
          <div className="project-panel-header">
            <span className="project-panel-title">Project Brief</span>
            <button
              className="project-add-brief-btn"
              onClick={() => setAddingBrief(!addingBrief)}
              title="Add brief entry"
            >
              {addingBrief ? 'Cancel' : '+ Add'}
            </button>
          </div>
          <div className="project-summary-body">
            {addingBrief && (
              <div className="brief-bubble brief-bubble--editing">
                <textarea
                  className="brief-bubble-textarea"
                  value={newBriefText}
                  onChange={e => setNewBriefText(e.target.value)}
                  placeholder="Enter a brief summary entry…"
                  rows={3}
                  autoFocus
                />
                <div className="brief-bubble-actions">
                  <button className="btn-save" onClick={handleAddBrief} disabled={saving || !newBriefText.trim()}>
                    {saving ? 'Saving…' : 'Add Entry'}
                  </button>
                </div>
              </div>
            )}

            {projectBrief.length === 0 && !addingBrief ? (
              <p className="project-summary-empty">
                No project brief yet. Finalize a planning session to generate a summary,
                or click "+ Add" to write one manually.
              </p>
            ) : (
              <div className="brief-bubbles">
                {projectBrief.map((entry, i) => (
                  <BriefBubble
                    key={i}
                    entry={entry}
                    index={i}
                    onEdit={editBrief}
                    onDelete={removeBrief}
                    saving={saving}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {drift && (
        <DriftModal
          drift={drift}
          onClose={() => setDrift(null)}
          onAddPath={handleAddPath}
        />
      )}
    </div>
  );
}
